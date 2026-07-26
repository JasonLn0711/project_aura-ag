#!/usr/bin/env python3
"""Run one real Codex app-server turn and retain sanitized evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

from PyQt6.QtCore import QCoreApplication

from aura.agent.controller import AgentRunController
from aura.agent.persistence import AgentRunStore
from aura.agent.providers.codex_app_server import CodexAppServerProvider
from aura.agent.state import TERMINAL_PHASES


EXPECTED_REPLY = "AURA_LIVE_SMOKE_OK"


def _spin(app: QCoreApplication, predicate, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.002)
    if not predicate():
        raise TimeoutError("Live Codex smoke step timed out.")


def _tracked_state(repository: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()


def _opaque(value: object) -> str | None:
    if not value:
        return None
    return "opaque:" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]


def _safe_payload(event_type: str, payload: dict[str, object]) -> dict[str, object]:
    allowed: dict[str, object] = {}
    for key in (
        "status",
        "phase",
        "mode",
        "safety_profile",
        "raw_audio_excluded",
        "workflow",
        "outcome",
        "error_class",
        "resolved_model",
        "resolved_effort",
        "fallback_approval_required",
    ):
        if key in payload:
            allowed[key] = payload[key]
    if event_type in {
        "message.assistant.delta",
        "message.assistant.completed",
    }:
        text = str(payload.get("text") or "")
        allowed["expected_reply_observed"] = EXPECTED_REPLY in text
        allowed["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if "thread_id" in payload:
        allowed["thread_id"] = _opaque(payload["thread_id"])
    if "turn_id" in payload:
        allowed["turn_id"] = _opaque(payload["turn_id"])
    return allowed


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--safety-profile",
        choices=("read-only", "approved-worktree-write"),
        default="read-only",
    )
    args = parser.parse_args()
    repository = args.repository.expanduser().resolve(strict=True)
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = QCoreApplication.instance() or QCoreApplication([])
    tracked_before = _tracked_state(repository)
    started_at = dt.datetime.now().astimezone()
    wall_start = time.perf_counter()
    preflight_seconds: float | None = None
    turn_seconds: float | None = None
    unexpected_approval = False
    diagnostics: list[str] = []
    run_events = []
    process_pid = 0
    process_tree_clean = False
    status = "BLOCKED_UNRESOLVED"
    failure: str | None = None
    provider: CodexAppServerProvider | None = None

    with tempfile.TemporaryDirectory(prefix="aura-live-codex-") as temporary:
        store = AgentRunStore(Path(temporary) / "runs")
        provider = CodexAppServerProvider(cwd=repository)
        provider.diagnostic_ready.connect(
            lambda _value: diagnostics.append("bounded_provider_diagnostic")
        )
        controller = AgentRunController(provider, store)
        controller.event_emitted.connect(run_events.append)
        provider_started = time.perf_counter()
        try:
            provider.start()
            _spin(
                app,
                lambda: provider.status
                in {
                    "ready",
                    "login_required",
                    "incompatible",
                    "crashed",
                    "degraded",
                    "not_installed",
                },
                timeout_seconds=60,
            )
            preflight_seconds = time.perf_counter() - provider_started
            if provider.status != "ready":
                raise RuntimeError(f"Provider preflight status: {provider.status}")
            if provider.account_status["status"] != "signed_in":
                raise RuntimeError("Codex-owned ChatGPT login is required.")
            process_pid = int(provider.client.process.processId())
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            controller.configure(
                repository_path=str(repository),
                repository_head=head,
                safety_profile=args.safety_profile,
                requested_profile="quick",
                network_access=False,
                data_boundary_confirmed=True,
            )
            turn_start = time.perf_counter()
            run_id = controller.start_run(
                task=(
                    f"Reply with exactly {EXPECTED_REPLY}. "
                    "Do not use tools, run commands, inspect files, or modify anything."
                ),
                workflow="live_provider_smoke",
            )
            deadline = time.monotonic() + 180
            handled_approval: str | None = None
            while (
                controller.state.phase not in TERMINAL_PHASES
                and time.monotonic() < deadline
            ):
                app.processEvents()
                pending = controller.state.pending_approval_id
                if pending and pending != handled_approval:
                    unexpected_approval = True
                    handled_approval = pending
                    controller.resolve_approval(pending, "rejected")
                time.sleep(0.002)
            if controller.state.phase not in TERMINAL_PHASES:
                raise TimeoutError("The real Codex turn did not reach terminal state.")
            turn_seconds = time.perf_counter() - turn_start
            replies = [
                str(event.payload.get("text") or "").strip()
                for event in run_events
                if event.event_type == "message.assistant.completed"
            ]
            if controller.state.phase != "completed":
                raise RuntimeError(
                    f"Real Codex turn ended as {controller.state.phase}."
                )
            if unexpected_approval:
                raise RuntimeError("The no-tool smoke unexpectedly requested approval.")
            if EXPECTED_REPLY not in replies:
                raise RuntimeError("The expected live model reply was not observed.")
            metadata = json.loads(
                (store.run_dir(run_id) / "run.json").read_text(encoding="utf-8")
            )
            if metadata.get("resolved_model") != provider.resolution.model_id:
                raise RuntimeError("Requested and persisted model resolution differ.")
            if metadata.get("reasoning_effort") != provider.resolution.reasoning_effort:
                raise RuntimeError("Requested and persisted effort resolution differ.")
            if _tracked_state(repository) != tracked_before:
                raise RuntimeError("The read-only smoke changed tracked checkout state.")
            status = "LIVE_MINIMUM_COMPLETED"
        except Exception as exc:
            failure = f"{type(exc).__name__}: {exc}"
        finally:
            if provider is not None:
                provider.shutdown()
                _spin(
                    app,
                    lambda: provider.client.process.state().name == "NotRunning",
                    timeout_seconds=5,
                )
                process_tree_clean = not (
                    process_pid > 0 and Path(f"/proc/{process_pid}").exists()
                )
            controller.shutdown()

    ended_at = dt.datetime.now().astimezone()
    tracked_after = _tracked_state(repository)
    safe_events = [
        {
            "sequence": event.sequence,
            "created_at": event.created_at,
            "event_type": event.event_type,
            "source": event.source,
            "severity": event.severity,
            "payload": _safe_payload(event.event_type, dict(event.payload)),
        }
        for event in run_events
    ]
    with (output / "event-trace.jsonl").open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        for event in safe_events:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    with (output / "error-log.jsonl").open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        if failure:
            handle.write(
                json.dumps(
                    {
                        "error_class": failure.split(":", 1)[0],
                        "stage": "live_codex_smoke",
                    }
                )
                + "\n"
            )
    summary = {
        "schema_version": 1,
        "status": status,
        "runtime_classification": (
            "valid_target_runtime"
            if status == "LIVE_MINIMUM_COMPLETED"
            else "blocked_runtime"
        ),
        "provider": "Codex app-server over stdio",
        "transport": "stdio-jsonl-v2",
        "safety_profile": args.safety_profile,
        "installed_version": (
            provider.compatibility.installed_version if provider else None
        ),
        "compatibility_status": (
            provider.compatibility.status if provider else "not_started"
        ),
        "account_status": (
            provider.account_status["status"] if provider else "unknown"
        ),
        "account_type": (
            provider.account_status["account_type"] if provider else None
        ),
        "requested_profile": "quick",
        "resolved_model": provider.resolution.model_id if provider else None,
        "resolved_effort": (
            provider.resolution.reasoning_effort if provider else None
        ),
        "silent_fallback_allowed": False,
        "expected_reply_observed": any(
            event["payload"].get("expected_reply_observed")
            for event in safe_events
        ),
        "unexpected_approval": unexpected_approval,
        "tracked_checkout_unchanged": tracked_after == tracked_before,
        "process_tree_clean_after_shutdown": process_tree_clean,
        "event_count": len(safe_events),
        "provider_diagnostic_count": len(diagnostics),
        "preflight_seconds": (
            round(preflight_seconds, 3) if preflight_seconds is not None else None
        ),
        "turn_seconds": (
            round(turn_seconds, 3) if turn_seconds is not None else None
        ),
        "total_seconds": round(time.perf_counter() - wall_start, 3),
        "started_at": started_at.isoformat(timespec="milliseconds"),
        "ended_at": ended_at.isoformat(timespec="milliseconds"),
        "failure_class": failure.split(":", 1)[0] if failure else None,
        "credential_values_captured": False,
        "raw_audio_transferred": False,
    }
    _write_json(output / "live-run-summary.json", summary)
    (output / "request-summary.jsonl").write_text(
        json.dumps(
            {
                "request_id": "live-smoke-1",
                "workflow": "live_provider_smoke",
                "safety_profile": args.safety_profile,
                "network_access": False,
                "data_boundary": "minimal synthetic instruction",
                "runtime_classification": summary["runtime_classification"],
            }
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / "runtime-validity-report.md").write_text(
        "# Live Codex Runtime Validity\n\n"
        f"Status: **{status}**\n\n"
        f"- Codex app-server: `{summary['runtime_classification']}`\n"
        f"- Installed version: `{summary['installed_version']}`\n"
        f"- Compatibility: `{summary['compatibility_status']}`\n"
        f"- Safety profile: `{summary['safety_profile']}`\n"
        f"- Model: `{summary['resolved_model']}`\n"
        f"- Effort: `{summary['resolved_effort']}`\n"
        f"- Expected model reply observed: `{str(summary['expected_reply_observed']).lower()}`\n"
        f"- Process tree clean after shutdown: `{str(process_tree_clean).lower()}`\n"
        "- Credential values captured: `false`\n"
        "- Raw audio transferred: `false`\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / "latency-report.md").write_text(
        "# Live Codex Latency\n\n"
        f"- Preflight: {summary['preflight_seconds']} seconds\n"
        f"- Read-only turn: {summary['turn_seconds']} seconds\n"
        f"- Total: {summary['total_seconds']} seconds\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / "failure-analysis.md").write_text(
        "# Live Codex Failure Analysis\n\n"
        + (
            "No runtime failure was observed in the minimum live turn. "
            "The full fake-server fault matrix and process-tree shutdown test remain "
            "the broader failure-path evidence.\n"
            if failure is None
            else f"Status remains blocked at `{summary['failure_class']}`. "
            "The error log preserves the class without diagnostic or credential values.\n"
        ),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, ensure_ascii=False))
    if status != "LIVE_MINIMUM_COMPLETED":
        raise RuntimeError(failure or "Live Codex smoke remains blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
