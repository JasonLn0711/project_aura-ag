from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from aura.agent.contracts import AgentUiEvent, ProviderEvent
from aura.agent.persistence import AgentRunStore
from aura.agent.state import (
    TERMINAL_PHASES,
    AgentEventReducer,
    AgentWorkspaceState,
)


class AgentRunController(QObject):
    """Single writer for provider events, durable run state, and approvals."""

    event_emitted = pyqtSignal(object)
    state_changed = pyqtSignal(object)
    error_raised = pyqtSignal(str)

    def __init__(
        self,
        provider,
        store: AgentRunStore,
        *,
        audit=None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.store = store
        self.audit = audit
        self.provider = None
        self.reducer = AgentEventReducer()
        self.state = self.reducer.state
        self._sequence = 0
        self._shutting_down = False
        self._context_artifact: dict[str, Any] = {}
        self._evidence_artifact: list[dict[str, Any]] = []
        self._file_change_artifact: list[dict[str, Any]] = []
        self._tests_artifact: dict[str, Any] = {"status": "not_run", "commands": []}
        self._report_artifact: dict[str, Any] = {
            "status": "not_started",
            "files": [],
            "sections": [],
        }
        self.set_provider(provider)

    def set_provider(self, provider) -> None:
        if self.state.active_run_id and self.state.phase not in TERMINAL_PHASES:
            raise RuntimeError("The provider cannot change while a run is active.")
        if self.provider is not None:
            self._disconnect_provider(self.provider)
            self.provider.shutdown()
        self.provider = provider
        provider.event_ready.connect(self._on_provider_event)
        provider.status_changed.connect(self._on_provider_status)
        if hasattr(provider, "account_changed"):
            provider.account_changed.connect(self._on_account_changed)
        if hasattr(provider, "models_changed"):
            provider.models_changed.connect(self._on_models_changed)
        mode = "demo" if provider.provider_id == "demo" else "live"
        safety = "demo" if mode == "demo" else "read-only"
        account = getattr(provider, "account_status", {})
        resolution = getattr(provider, "resolution", None)
        self.state = replace(
            self.state,
            mode=mode,
            provider_status=str(getattr(provider, "status", "stopped")),
            auth_status=str(account.get("status") or "unknown"),
            account_type=account.get("account_type"),
            requested_profile=(
                resolution.requested_profile if resolution else self.state.requested_profile
            ),
            resolved_model=resolution.model_id if resolution else None,
            resolved_effort=resolution.reasoning_effort if resolution else None,
            safety_profile=safety,
        )
        self.reducer.state = self.state
        self.state_changed.emit(self.state)

    def configure(
        self,
        *,
        repository_path: str | None = None,
        repository_head: str | None = None,
        aura_session_id: str | None = None,
        safety_profile: str | None = None,
        requested_profile: str | None = None,
        network_access: bool = False,
        data_boundary_confirmed: bool = False,
    ) -> None:
        if self.state.active_run_id and self.state.phase not in TERMINAL_PHASES:
            raise RuntimeError("Run context cannot change while execution is active.")
        self.state = replace(
            self.state,
            repository_path=repository_path,
            repository_head=repository_head,
            aura_session_id=aura_session_id,
            safety_profile=safety_profile or self.state.safety_profile,
            requested_profile=requested_profile or self.state.requested_profile,
            network_access=network_access,
            data_boundary_confirmed=data_boundary_confirmed,
        )
        self.reducer.state = self.state
        self.state_changed.emit(self.state)

    def start_run(
        self,
        *,
        task: str,
        workflow: str,
        branch: str = "approval",
        run_id: str | None = None,
        resume_thread_id: str | None = None,
    ) -> str:
        if self.state.active_run_id and self.state.phase not in TERMINAL_PHASES:
            raise RuntimeError("Only one Agent run may be active.")
        if not task.strip():
            raise ValueError("A task is required.")
        run_id = run_id or f"run-{uuid.uuid4()}"
        now = dt.datetime.now().astimezone().isoformat(timespec="milliseconds")
        provider_id = str(self.provider.provider_id)
        resolution = getattr(self.provider, "resolution", None)
        fallback_required = bool(
            getattr(resolution, "requires_fallback_approval", False)
        )
        model_identity = {
            "resolved_display_name": getattr(resolution, "display_name", None),
            "fallback_approval_required": fallback_required,
            "fallback_decision": (
                "blocked_no_decision" if fallback_required else "not_required"
            ),
            "model_discovered_at": getattr(
                self.provider,
                "model_discovered_at",
                None,
            ),
        }
        self.state = replace(
            self.state,
            mode="demo" if provider_id == "demo" else "live",
            active_run_id=run_id,
            active_thread_id=None,
            active_turn_id=None,
            phase="draft",
            pending_approval_id=None,
            last_error=None,
        )
        self.reducer = AgentEventReducer(self.state)
        self._sequence = 0
        self._context_artifact = {}
        self._evidence_artifact = []
        self._file_change_artifact = []
        self._tests_artifact = {"status": "not_run", "commands": []}
        self._report_artifact = {
            "status": "not_started",
            "files": [],
            "sections": [],
        }
        self.store.create_run(
            {
                "schema_version": 1,
                "run_id": run_id,
                "created_at": now,
                "started_at": now,
                "ended_at": None,
                "mode": self.state.mode,
                "provider": provider_id,
                "workflow": workflow,
                "task_digest": hashlib.sha256(task.encode("utf-8")).hexdigest(),
                "requested_profile": self.state.requested_profile,
                "resolved_model": self.state.resolved_model,
                "reasoning_effort": self.state.resolved_effort,
                **model_identity,
                "repository_root_identifier": self.state.repository_path,
                "base_commit": self.state.repository_head,
                "worktree_path": None,
                "aura_evidence_references": (
                    [self.state.aura_session_id] if self.state.aura_session_id else []
                ),
                "data_boundary_decision": self.state.data_boundary_confirmed,
                "safety_profile": self.state.safety_profile,
                "network": self.state.network_access,
                "phase": "draft",
                "provider_thread_id": None,
                "requested_resume_thread_id": resume_thread_id,
                "provider_turn_id": None,
                "final_outcome": None,
                "error_class": None,
                "artifact_digests": {},
            }
        )
        self.store.write_json(
            run_id,
            "provider.json",
            {
                "provider_id": provider_id,
                "provider_info": getattr(self.provider, "provider_info", {}),
                "requested_profile": self.state.requested_profile,
                "resolved_model": self.state.resolved_model,
                "reasoning_effort": self.state.resolved_effort,
                **model_identity,
                "discovered_at": now,
            },
        )
        self.state_changed.emit(self.state)
        self.provider.start()
        if provider_id == "demo":
            self.provider.start_run(branch)
        else:
            self.provider.start_run(
                task=task,
                workflow=workflow,
                state=self.state,
                run_id=run_id,
                resume_thread_id=resume_thread_id,
            )
        return run_id

    def resolve_approval(self, request_id: str, decision: str) -> None:
        if request_id != self.state.pending_approval_id:
            raise ValueError("Approval decision does not match the pending request.")
        if decision not in {"approved_once", "rejected", "cancelled"}:
            raise ValueError("Unsupported approval decision.")
        self.provider.resolve_approval(request_id, decision)
        self.store.append_approval(
            self.state.active_run_id,
            {
                "record_type": "decision",
                "approval_id": request_id,
                "decision": decision,
                "actor": "user",
                "decided_at": dt.datetime.now().astimezone().isoformat(timespec="milliseconds"),
            },
        )
        self._audit(
            "agent.approval_decided",
            outcome="success" if decision == "approved_once" else "rejected",
            details={"approval_id": request_id, "decision": decision},
        )

    def stop(self) -> None:
        if not self.state.active_run_id or self.state.phase in TERMINAL_PHASES:
            return
        if hasattr(self.provider, "stop"):
            self.provider.stop()
        elif self.state.active_thread_id and self.state.active_turn_id:
            self.provider.interrupt_turn(
                self.state.active_thread_id,
                self.state.active_turn_id,
            )
        else:
            self._on_provider_event(
                ProviderEvent(
                    "run.interrupted",
                    {"reason": "user_requested_before_turn"},
                    severity="warning",
                    source=str(self.provider.provider_id),
                )
            )

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        try:
            if self.state.active_run_id and self.state.phase not in TERMINAL_PHASES:
                try:
                    self.stop()
                except Exception as exc:
                    self.error_raised.emit(
                        f"Provider stop needs attention: {type(exc).__name__}"
                    )
            try:
                self.provider.shutdown()
            except Exception as exc:
                self.error_raised.emit(
                    f"Provider shutdown needs attention: {type(exc).__name__}"
                )
            if self.state.active_run_id and self.state.phase not in TERMINAL_PHASES:
                self._on_provider_event(
                    ProviderEvent(
                        "run.interrupted",
                        {"reason": "application_shutdown"},
                        severity="warning",
                        source="controller",
                    )
                )
        finally:
            self._shutting_down = False

    def _on_provider_status(self, status: str) -> None:
        previous = self.state.provider_status
        self.state = replace(self.state, provider_status=status)
        self.reducer.state = self.state
        self.state_changed.emit(self.state)
        if status == "starting":
            self._audit(
                "agent.provider_started",
                outcome="success",
                details={"status": status},
            )
        elif status == "ready":
            if previous == "stopped":
                self._audit(
                    "agent.provider_started",
                    outcome="success",
                    details={"status": "starting"},
                )
            self._audit(
                "agent.provider_ready",
                outcome="success",
                details={"status": status},
            )
        elif status in {"crashed", "degraded", "not_installed"}:
            self._audit(
                "agent.provider_failed",
                outcome="error",
                severity="error",
                details={"status": status},
            )
        elif status == "stopped":
            self._audit(
                "agent.provider_stopped",
                outcome="success",
                details={"status": status},
            )

    def _on_account_changed(self, account: dict[str, Any]) -> None:
        self.state = replace(
            self.state,
            auth_status=str(account.get("status") or "unknown"),
            account_type=(
                str(account["account_type"]) if account.get("account_type") else None
            ),
        )
        self.reducer.state = self.state
        self.state_changed.emit(self.state)

    def _on_models_changed(self, _models) -> None:
        resolution = getattr(self.provider, "resolution", None)
        if resolution is None:
            return
        self.state = replace(
            self.state,
            requested_profile=resolution.requested_profile,
            resolved_model=resolution.model_id,
            resolved_effort=resolution.reasoning_effort,
        )
        self.reducer.state = self.state
        self.state_changed.emit(self.state)
        self._audit(
            "agent.model_resolved",
            outcome=(
                "success"
                if resolution.model_id and resolution.reasoning_effort
                else "error"
            ),
            severity=(
                "info"
                if resolution.model_id and resolution.reasoning_effort
                else "warning"
            ),
            details={
                "requested_profile": resolution.requested_profile,
                "resolved_model": resolution.model_id,
                "reasoning_effort": resolution.reasoning_effort,
            },
        )

    def _on_provider_event(self, provider_event: ProviderEvent) -> None:
        run_id = self.state.active_run_id
        if not run_id:
            return
        self._sequence += 1
        event = AgentUiEvent.create(
            run_id=run_id,
            event_type=provider_event.event_type,
            sequence=self._sequence,
            source=provider_event.source,
            severity=provider_event.severity,
            payload=provider_event.payload,
            created_at=dt.datetime.now().astimezone().isoformat(timespec="milliseconds"),
            event_id=str(uuid.uuid4()),
        )
        try:
            next_state = self.reducer.preview(event)
            self.store.append_event(run_id, event)
            self.reducer.apply(event)
        except Exception as exc:
            self._sequence -= 1
            self.error_raised.emit(str(exc))
            self._audit(
                "agent.event_rejected",
                outcome="error",
                severity="error",
                details={"event_type": provider_event.event_type, "error_class": type(exc).__name__},
            )
            return
        self.state = next_state
        self.reducer.state = next_state
        try:
            self._persist_event_artifacts(run_id, event)
        except Exception as exc:
            self.error_raised.emit(
                f"Run event is durable; a derived artifact needs attention: {type(exc).__name__}"
            )
        if event.event_type == "approval.requested":
            serialized = json.dumps(
                dict(event.payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            self.store.append_approval(
                run_id,
                {
                    "record_type": "request",
                    "approval_id": event.payload["approval_id"],
                    "category": event.payload.get("category"),
                    "displayed_summary_hash": hashlib.sha256(
                        serialized.encode("utf-8")
                    ).hexdigest(),
                    "requested_at": event.created_at,
                },
            )
        changes: dict[str, Any] = {
            "phase": next_state.phase,
            "resolved_model": next_state.resolved_model,
            "reasoning_effort": next_state.resolved_effort,
            "provider_thread_id": next_state.active_thread_id,
            "provider_turn_id": next_state.active_turn_id,
            "error_class": next_state.last_error,
        }
        if event.event_type == "run.completed":
            changes["final_outcome"] = event.payload.get("outcome")
        elif event.event_type == "run.failed":
            changes["final_outcome"] = "failed"
        elif event.event_type == "run.interrupted":
            changes["final_outcome"] = "interrupted"
        if next_state.phase in TERMINAL_PHASES:
            changes["ended_at"] = event.created_at
            changes["artifact_digests"] = self.store.artifact_digests(run_id)
        self.store.update_run(run_id, changes)
        self.event_emitted.emit(event)
        self.state_changed.emit(next_state)
        self._audit(
            f"agent.{event.event_type.replace('.', '_')}",
            outcome="error" if event.severity in {"error", "critical"} else "success",
            severity=event.severity,
            details={"run_id": run_id, "sequence": event.sequence},
        )
        alias = {
            "plan.updated": "agent.plan_received",
            "file_change.proposed": "agent.file_change_received",
            "file_change.completed": "agent.file_change_received",
        }.get(event.event_type)
        if alias:
            self._audit(
                alias,
                outcome=(
                    "error"
                    if event.severity in {"error", "critical"}
                    else "success"
                ),
                severity=event.severity,
                details={"run_id": run_id, "sequence": event.sequence},
            )

    def _persist_event_artifacts(self, run_id: str, event: AgentUiEvent) -> None:
        event_type = event.event_type
        payload = dict(event.payload)
        if event_type == "context.snapshot":
            self._context_artifact.update(payload)
            self.store.write_json(run_id, "context.json", self._context_artifact)
        elif event_type.startswith("provider."):
            resolution = getattr(self.provider, "resolution", None)
            fallback_required = bool(
                getattr(resolution, "requires_fallback_approval", False)
            )
            provider_payload = {
                "provider_id": self.provider.provider_id,
                "provider_status": self.state.provider_status,
                "auth_status": self.state.auth_status,
                "account_type": self.state.account_type,
                "requested_profile": self.state.requested_profile,
                "resolved_model": self.state.resolved_model,
                "resolved_display_name": getattr(
                    resolution,
                    "display_name",
                    None,
                ),
                "reasoning_effort": self.state.resolved_effort,
                "fallback_approval_required": fallback_required,
                "fallback_decision": (
                    "blocked_no_decision"
                    if fallback_required
                    else "not_required"
                ),
                "model_discovered_at": getattr(
                    self.provider,
                    "model_discovered_at",
                    None,
                ),
                "provider_info": getattr(self.provider, "provider_info", {}),
                "last_event": event_type,
                "last_event_at": event.created_at,
            }
            self.store.write_json(run_id, "provider.json", provider_payload)
        elif event_type in {"evidence.linked", "evidence.stale", "evidence.rejected"}:
            self._evidence_artifact.append(
                {"event_type": event_type, "created_at": event.created_at, **payload}
            )
            self.store.write_json(
                run_id,
                "evidence.json",
                {"evidence": self._evidence_artifact},
            )
        elif event_type.startswith("command."):
            self.store.append_command(
                run_id,
                {"event_type": event_type, "created_at": event.created_at, **payload},
            )
        elif event_type.startswith("file_change."):
            self._file_change_artifact.append(
                {"event_type": event_type, "created_at": event.created_at, **payload}
            )
            self.store.write_json(
                run_id,
                "file-changes.json",
                {"files": self._file_change_artifact},
            )
        elif event_type == "diff.updated" and payload.get("diff") is not None:
            self.store.write_patch(run_id, str(payload["diff"]))
        elif event_type.startswith("test."):
            status = {
                "test.started": "running",
                "test.completed": "passed",
                "test.failed": "failed",
            }.get(event_type, "unknown")
            self._tests_artifact = {
                "status": status,
                "event_type": event_type,
                "updated_at": event.created_at,
                **payload,
            }
            self.store.write_json(run_id, "tests.json", self._tests_artifact)
        elif event_type == "report.started":
            self._report_artifact.update(
                {
                    "status": "collecting_evidence",
                    "section_total": payload.get("section_total"),
                    "started_at": event.created_at,
                }
            )
            self.store.write_json(
                run_id, "report-manifest.json", self._report_artifact
            )
        elif event_type == "report.section_ready":
            self._report_artifact["sections"].append(payload)
            self._report_artifact["status"] = "drafting"
            self.store.write_json(
                run_id, "report-manifest.json", self._report_artifact
            )
        elif event_type == "report.validation_completed":
            self._report_artifact.update(
                {
                    "status": payload.get("status"),
                    "validation": payload,
                    "validated_at": event.created_at,
                }
            )
            self.store.write_json(
                run_id, "report-manifest.json", self._report_artifact
            )
        elif event_type == "report.ready":
            self._report_artifact.update(
                {
                    "status": "ready"
                    if not self._report_artifact.get("validation")
                    else self._report_artifact.get("status"),
                    "package": payload.get("package"),
                    "ready_at": event.created_at,
                }
            )
            self.store.write_json(
                run_id, "report-manifest.json", self._report_artifact
            )
        elif event_type == "artifact.exported":
            requested = str(payload.get("artifact") or "agent-evidence-packet.zip")
            filename = Path(requested).name
            if not filename.endswith(".zip"):
                filename += ".zip"
            path, digest = self.store.export_run_bundle(run_id, filename)
            self._report_artifact["files"].append(
                {
                    "path": path.relative_to(self.store.run_dir(run_id)).as_posix(),
                    "sha256": digest,
                    "exported_at": event.created_at,
                }
            )
            self.store.write_json(
                run_id, "report-manifest.json", self._report_artifact
            )

    def _disconnect_provider(self, provider) -> None:
        for signal, slot in (
            (provider.event_ready, self._on_provider_event),
            (provider.status_changed, self._on_provider_status),
        ):
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass
        for signal_name, slot in (
            ("account_changed", self._on_account_changed),
            ("models_changed", self._on_models_changed),
        ):
            signal = getattr(provider, signal_name, None)
            if signal is None:
                continue
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

    def _audit(
        self,
        name: str,
        *,
        outcome: str,
        severity: str = "info",
        details: dict[str, Any],
    ) -> None:
        if self.audit is not None:
            self.audit.record(
                name,
                category="agent.workspace",
                actor="system",
                workflow="agent",
                outcome=outcome,
                severity=severity,
                details=details,
            )
