from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Mapping

from aura.agent.persistence import AgentRunStore, _sanitize
from aura.agent.policy import path_has_sensitive_component


class SupportBundleExporter:
    def __init__(self, run_store: AgentRunStore):
        self.run_store = run_store

    def export(
        self,
        destination: str | Path,
        *,
        application_version: str,
        codex_version: str,
        compatibility_status: str,
        configuration: Mapping[str, Any],
        provider_diagnostics: tuple[str, ...],
        run_ids: tuple[str, ...] = (),
    ) -> tuple[Path, str]:
        target = Path(destination).expanduser().resolve()
        if target.suffix.lower() != ".zip":
            raise ValueError("Support bundle destination must be a ZIP file.")
        if path_has_sensitive_component(target):
            raise ValueError("Support bundle cannot use a sensitive path.")
        if target.exists():
            raise FileExistsError(f"Support bundle already exists: {target.name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        generated_at = dt.datetime.now().astimezone().isoformat(
            timespec="milliseconds"
        )
        files: dict[str, bytes] = {
            "manifest.json": self._json_bytes(
                {
                    "schema_version": 1,
                    "generated_at": generated_at,
                    "user_triggered": True,
                    "automatic_upload": False,
                    "included_run_ids": run_ids,
                    "excluded": (
                        "credentials",
                        "raw_audio",
                        "audio_spans",
                        "transcripts",
                        "meeting_source_text",
                    ),
                }
            ),
            "system.json": self._json_bytes(
                {
                    "application_version": application_version,
                    "python": platform.python_version(),
                    "platform": platform.platform(),
                    "architecture": platform.machine(),
                    "codex_version": codex_version,
                    "compatibility_status": compatibility_status,
                }
            ),
            "configuration.json": self._json_bytes(
                self._support_sanitize(configuration)
            ),
            "provider-diagnostics.json": self._json_bytes(
                {
                    "messages": self._support_sanitize(provider_diagnostics),
                }
            ),
        }
        for run_id in run_ids:
            run_dir = self.run_store.run_dir(run_id)
            files[f"runs/{run_id}/run.json"] = self._safe_run_json(
                run_dir / "run.json"
            )
            files[f"runs/{run_id}/events.jsonl"] = self._safe_events(
                run_dir / "events.jsonl"
            )
        checksums = "".join(
            f"{hashlib.sha256(content).hexdigest()}  {name}\n"
            for name, content in sorted(files.items())
        ).encode("utf-8")
        files["checksums.sha256"] = checksums
        handle = tempfile.NamedTemporaryFile(
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        )
        temporary = Path(handle.name)
        handle.close()
        try:
            with zipfile.ZipFile(
                temporary,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                for name, content in sorted(files.items()):
                    archive.writestr(name, content)
            with zipfile.ZipFile(temporary) as archive:
                if archive.testzip() is not None:
                    raise OSError("Support bundle failed ZIP validation.")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return target, hashlib.sha256(target.read_bytes()).hexdigest()

    def _safe_run_json(self, path: Path) -> bytes:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key in (
            "prompt",
            "task",
            "transcript",
            "evidence_text",
            "repository_path",
            "worktree_path",
        ):
            payload.pop(key, None)
        return self._json_bytes(self._support_sanitize(payload))

    def _safe_events(self, path: Path) -> bytes:
        lines = []
        with path.open(encoding="utf-8") as stream:
            for index, line in enumerate(stream):
                if index >= 1000:
                    break
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event_type = str(payload.get("event_type") or "")
                event = {
                    "schema_version": payload.get("schema_version"),
                    "event_id": payload.get("event_id"),
                    "run_id": payload.get("run_id"),
                    "work_item_id": payload.get("work_item_id"),
                    "event_type": event_type,
                    "created_at": payload.get("created_at"),
                    "sequence": payload.get("sequence"),
                    "source": payload.get("source"),
                    "severity": payload.get("severity"),
                }
                if event_type in {
                    "provider.protocol_error",
                    "provider.crashed",
                    "run.failed",
                    "run.interrupted",
                    "approval.requested",
                    "approval.resolved",
                    "test.completed",
                    "test.failed",
                }:
                    event["payload"] = self._support_sanitize(
                        payload.get("payload") or {}
                    )
                lines.append(
                    json.dumps(event, ensure_ascii=False, sort_keys=True)
                )
        return (("\n".join(lines) + "\n") if lines else "").encode("utf-8")

    def _support_sanitize(self, value: Any, *, key: str = "") -> Any:
        normalized = key.casefold()
        if normalized.endswith(
            (
                "path",
                "root",
                "directory",
                "cwd",
            )
        ):
            return "[LOCAL_PATH]"
        if isinstance(value, Mapping):
            return {
                str(item_key): self._support_sanitize(
                    item,
                    key=str(item_key),
                )
                for item_key, item in value.items()
            }
        if isinstance(value, (tuple, list)):
            return [
                self._support_sanitize(item, key=key)
                for item in value
            ]
        sanitized = _sanitize(value, key=key)
        if isinstance(sanitized, str):
            for local, alias in (
                (str(Path.home()), "<HOME>"),
                (str(self.run_store.root), "<RUN_ROOT>"),
            ):
                if local and local != "/":
                    sanitized = sanitized.replace(local, alias)
        return sanitized

    @staticmethod
    def _json_bytes(payload: Any) -> bytes:
        return (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
