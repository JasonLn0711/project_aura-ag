from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from aura.agent.contracts import ProviderEvent


FIXTURE_ROOT = (
    Path(__file__).resolve().parent.parent
    / "demo"
    / "fixtures"
    / "demo-repository-assurance"
)


class DemoAgentProvider(QObject):
    provider_id = "demo"

    event_ready = pyqtSignal(object)
    status_changed = pyqtSignal(str)

    def __init__(self, *, playback_interval_ms: int = 300, parent: QObject | None = None):
        super().__init__(parent)
        self.playback_interval_ms = max(0, playback_interval_ms)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_next)
        self._events: tuple[ProviderEvent, ...] = ()
        self._index = 0
        self._paused = False
        self._waiting_for_approval = False
        self._branch = "approval"

    def events_for(self, branch: str = "approval") -> tuple[ProviderEvent, ...]:
        events: list[ProviderEvent] = []
        for line in (FIXTURE_ROOT / "events.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item["event_type"] == "diff.updated":
                item.setdefault("payload", {})["diff"] = (
                    FIXTURE_ROOT / "proposed.patch"
                ).read_text(encoding="utf-8")
            events.append(
                ProviderEvent(
                    event_type=item["event_type"],
                    payload=item.get("payload", {}),
                    severity=item.get("severity", "info"),
                    source="demo",
                )
            )
        if branch == "approval":
            return tuple(events)

        def through(event_type: str) -> list[ProviderEvent]:
            index = next(
                index for index, event in enumerate(events) if event.event_type == event_type
            )
            return events[: index + 1]

        def through_phase(phase: str) -> list[ProviderEvent]:
            index = next(
                index
                for index, event in enumerate(events)
                if event.event_type == "run.phase_changed"
                and event.payload.get("phase") == phase
            )
            return events[: index + 1]

        if branch == "rejection":
            branch_events = through("approval.requested")
            branch_events.extend(
                (
                    ProviderEvent(
                        "approval.resolved",
                        {
                            "approval_id": "approval-demo-r002",
                            "decision": "rejected",
                            "actor": "user",
                        },
                        source="demo",
                    ),
                    ProviderEvent(
                        "reasoning.summary.completed",
                        {
                            "summary": "修正未啟動；既有唯讀計畫與證據保留供覆核。",
                        },
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.phase_changed",
                        {"phase": "running"},
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.phase_changed",
                        {"phase": "review_required"},
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.phase_changed",
                        {"phase": "reporting"},
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.completed",
                        {
                            "outcome": "plan_retained_after_rejection",
                            "remediation_applied": False,
                            "fixture_result": True,
                        },
                        source="demo",
                    ),
                )
            )
            return tuple(branch_events)
        if branch == "stop_planning":
            branch_events = through_phase("planning")
            branch_events.extend(
                (
                    ProviderEvent(
                        "run.interrupt_requested",
                        {"phase": "planning"},
                        severity="warning",
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.interrupted",
                        {"phase": "planning", "reason": "user_requested"},
                        severity="warning",
                        source="demo",
                    ),
                )
            )
            return tuple(branch_events)
        if branch == "stop_command":
            branch_events = through("command.started")
            branch_events.extend(
                (
                    ProviderEvent(
                        "run.interrupt_requested",
                        {"phase": "running"},
                        severity="warning",
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.interrupted",
                        {"phase": "running", "reason": "user_requested"},
                        severity="warning",
                        source="demo",
                    ),
                )
            )
            return tuple(branch_events)
        if branch == "provider_failure":
            branch_events = through("run.started")
            branch_events.extend(
                (
                    ProviderEvent(
                        "provider.crashed",
                        {"error_class": "DemoProviderFailure"},
                        severity="error",
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.failed",
                        {"error_class": "ProviderUnavailable"},
                        severity="error",
                        source="demo",
                    ),
                )
            )
            return tuple(branch_events)
        if branch == "test_failure":
            branch_events = through("test.started")
            branch_events.extend(
                (
                    ProviderEvent(
                        "test.failed",
                        {"passed": 7, "failed": 1, "skipped": 0, "simulated": True},
                        severity="error",
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.failed",
                        {"error_class": "TestFailure", "remediation_applied": False},
                        severity="error",
                        source="demo",
                    ),
                )
            )
            return tuple(branch_events)
        if branch == "report_failure":
            first_sections = [
                event for event in events if event.event_type == "report.section_ready"
            ][:5]
            branch_events = through("report.started") + first_sections
            branch_events.extend(
                (
                    ProviderEvent(
                        "report.validation_completed",
                        {
                            "status": "failed",
                            "partial_package_retained": True,
                            "missing_sections": list(range(6, 21)),
                        },
                        severity="error",
                        source="demo",
                    ),
                    ProviderEvent(
                        "run.failed",
                        {"error_class": "ReportValidationFailure"},
                        severity="error",
                        source="demo",
                    ),
                )
            )
            return tuple(branch_events)
        raise ValueError(f"Unsupported Demo branch: {branch}")

    def start(self) -> None:
        self.status_changed.emit("ready")

    def start_run(self, branch: str = "approval") -> None:
        if self._timer.isActive() or (self._events and self._index < len(self._events)):
            raise RuntimeError("A Demo run is already active.")
        self._events = self.events_for(branch)
        self._branch = branch
        self._index = 0
        self._paused = False
        self._waiting_for_approval = False
        self.status_changed.emit("running")
        self._schedule_next()

    def pause(self) -> None:
        self._paused = True
        self._timer.stop()
        self.status_changed.emit("paused")

    def resume(self) -> None:
        if self._waiting_for_approval:
            return
        self._paused = False
        self.status_changed.emit("running")
        self._schedule_next()

    def resolve_approval(self, request_id: str, decision: str) -> None:
        if not self._waiting_for_approval:
            raise ValueError("No Demo approval is pending.")
        if request_id != "approval-demo-r002":
            raise ValueError(f"Unknown Demo approval request: {request_id}")
        expected = "rejected" if self._branch == "rejection" else "approved_once"
        if decision != expected:
            raise ValueError(f"The {self._branch} fixture expects {expected}.")
        self._waiting_for_approval = False
        self._branch = "approval"
        self._paused = False
        self._schedule_next()

    def stop(self) -> None:
        self._timer.stop()
        self._paused = False
        self._waiting_for_approval = False
        self._events = ()
        self._index = 0
        self.event_ready.emit(
            ProviderEvent(
                event_type="run.interrupted",
                payload={"reason": "user_requested"},
                severity="warning",
                source="demo",
            )
        )
        self.status_changed.emit("stopped")

    def reset(self) -> None:
        self._timer.stop()
        self._events = ()
        self._index = 0
        self._paused = False
        self._waiting_for_approval = False
        self.status_changed.emit("ready")

    def shutdown(self) -> None:
        self.reset()
        self.status_changed.emit("stopped")

    def list_models(self) -> tuple:
        return ()

    def interrupt_turn(self, thread_id: str, turn_id: str) -> None:
        self.stop()

    def _schedule_next(self) -> None:
        if self._paused or self._waiting_for_approval:
            return
        if self._index >= len(self._events):
            self.status_changed.emit("ready")
            return
        self._timer.start(self.playback_interval_ms)

    def _emit_next(self) -> None:
        if self._paused or self._index >= len(self._events):
            return
        event = self._events[self._index]
        self._index += 1
        self.event_ready.emit(event)
        if event.event_type == "approval.requested":
            self._waiting_for_approval = True
            self.status_changed.emit("waiting_for_user")
            return
        self._schedule_next()
