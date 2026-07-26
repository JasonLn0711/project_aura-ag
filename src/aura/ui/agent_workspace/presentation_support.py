from __future__ import annotations

import datetime as dt
import getpass
import hashlib
import json
import platform
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from aura.agent.config import AgentConfig
from aura.agent.contracts import (
    AgentRun,
    AgentRunState,
    AgentUiEvent,
    OperatingMode,
    PublicationState,
    RepositoryProfile,
    WorkItem,
    WorkItemSource,
    WorkItemState,
)
from aura.agent.controller import AgentRunController
from aura.agent.evidence import AuraEvidenceAdapter, EvidenceSelection
from aura.agent.persistence import (
    AgentCatalog,
    AgentRunStore,
    AgentStorageManager,
)
from aura.agent.policy import (
    DataClass,
    DataTransferGuard,
    PathPolicy,
    build_transfer_preview,
    path_has_sensitive_component,
)
from aura.agent.publication import (
    PublicationBlocked,
    PublicationFailed,
    PublicationManager,
    build_pr_body,
)
from aura.agent.providers.codex_app_server import CodexAppServerProvider
from aura.agent.providers.codex_rpc import JsonLineRpcClient, redact_diagnostic
from aura.agent.providers.demo import DemoAgentProvider, FIXTURE_ROOT
from aura.agent.reporting import ArchitecturePackageGenerator
from aura.agent.repository_registry import RepositoryRegistry
from aura.agent.scheduler import (
    DurableRunScheduler,
    ResourceGovernor,
    ResourceLimits,
    ResourceSnapshot,
)
from aura.agent.state import TERMINAL_PHASES
from aura.agent.support import SupportBundleExporter
from aura.agent.worktree import WorktreeContext, WorktreeManager
from aura.agent.workflows import WorkflowRegistry
from aura.audit import AuditRecorder
from aura.metadata import __version__
from aura.ui.agent_workspace_components import (
    EnvironmentDialog,
    RecoveryCard,
)
from aura.ui.agent_workspace.application import StartContext
from aura.ui.agent_workspace.agent_composer import AgentComposer
from aura.ui.agent_workspace.artifact_models import changed_files_from_unified_diff
from aura.ui.agent_workspace.artifact_views import (
    DiffArtifactView,
    EvidenceArtifactView,
    ReportArtifactView,
    RunDetailsView,
    TestArtifactView,
)
from aura.ui.agent_workspace.artifact_inspector import ArtifactInspector
from aura.ui.agent_workspace.coalescer import TimelineCoalescer
from aura.ui.agent_workspace.design import apply_agent_workspace_style
from aura.ui.agent_workspace.evidence_picker import EvidenceContextPicker
from aura.ui.agent_workspace.preferences import (
    AgentUiPreferenceStore,
    AgentUiPreferences,
)
from aura.ui.agent_workspace.settings import AgentSettingsDialog
from aura.ui.agent_workspace.sidebar_view import WorkspaceSidebar
from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem
from aura.ui.agent_workspace.timeline_view import ThreadTimelineView
from aura.ui.agent_workspace.text_controls import neutralize_runtime_text
from aura.ui.messages import UI_TEXT


WORKFLOW_COPY = {
    "feature": ("agent_workflow_feature", "agent_task_fix"),
    "bug": ("agent_workflow_bug", "agent_task_fix"),
    "ask": ("agent_workflow_ask", "agent_task_repository_health"),
    "architecture": ("agent_workflow_architecture_new", "agent_task_architecture"),
    "test": ("agent_workflow_test", "agent_task_fix"),
    "security": ("agent_workflow_security_new", "agent_task_security"),
    "pii": ("agent_workflow_pii", "agent_task_security"),
    "queue": ("agent_workflow_queue", "agent_ready_hint"),
    "package": ("agent_workflow_package", "agent_task_architecture"),
    "docs": ("agent_workflow_docs", "agent_task_architecture"),
    "meeting": ("agent_workflow_meeting", "agent_task_action"),
    "publish": ("agent_workflow_publish", "agent_task_fix"),
}
LEGACY_WORKFLOW_ALIASES = {
    "repository_health": "ask",
    "architecture_package": "package",
    "security_review": "security",
    "approved_fix": "feature",
    "confirmed_action": "meeting",
}
DEMO_BRANCHES = (
    ("approval", "Approval"),
    ("rejection", "Rejection"),
    ("stop_planning", "Stop during planning"),
    ("stop_command", "Stop during command"),
    ("provider_failure", "Provider failure"),
    ("test_failure", "Test failure"),
    ("report_failure", "Report validation failure"),
)


@dataclass(frozen=True)
class TimelineEventRecord:
    event: AgentUiEvent
    copy_text: str


def _git_head(repository: Path | None) -> str | None:
    if repository is None:
        return None
    result = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _flatten_payload(value: Any, prefix: str = "") -> list[str]:
    lines: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower()
            if any(part in normalized for part in ("token", "credential", "password", "secret", "email")):
                continue
            label = f"{prefix}{key}"
            if isinstance(item, (dict, list, tuple)):
                lines.extend(_flatten_payload(item, f"{label}."))
            elif item is not None:
                lines.append(f"{label}: {redact_diagnostic(str(item))}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                step = item.get("step") or item.get("title") or item.get("text")
                status = item.get("status")
                if step:
                    lines.append(f"{index}. {step}" + (f" — {status}" if status else ""))
                else:
                    lines.extend(_flatten_payload(item, f"{prefix}{index}."))
            else:
                lines.append(f"{index}. {redact_diagnostic(str(item))}")
    elif value is not None:
        lines.append(redact_diagnostic(str(value)))
    return lines


def event_copy_text(event: AgentUiEvent) -> str:
    payload = event.payload
    event_type = event.event_type
    preferred_keys = {
        "message.user": ("text", "workflow"),
        "message.assistant.delta": ("text",),
        "message.assistant.completed": ("text",),
        "reasoning.summary.delta": ("text",),
        "reasoning.summary.completed": ("summary",),
        "run.phase_changed": ("phase",),
        "run.completed": ("outcome",),
        "run.failed": ("error_class",),
        "run.interrupted": ("reason", "phase"),
        "evidence.linked": ("risk_id", "severity", "source", "confidence"),
        "command.started": ("command", "cwd"),
        "command.output.delta": ("text",),
        "command.completed": ("command", "exit_code", "output"),
        "test.started": ("command",),
        "test.completed": ("passed", "failed", "skipped", "duration_seconds"),
        "test.failed": ("passed", "failed", "skipped"),
        "report.section_ready": ("section", "title", "state"),
        "report.validation_completed": ("status", "missing_evidence"),
        "approval.requested": (
            "category",
            "title",
            "command",
            "cwd",
            "reason",
            "risk",
            "policy_result",
            "network",
            "affected_paths",
            "decision_options",
        ),
        "approval.resolved": ("approval_id", "decision", "actor"),
    }.get(event_type)
    if preferred_keys:
        selected = {key: payload[key] for key in preferred_keys if key in payload}
        lines = _flatten_payload(selected)
    else:
        lines = _flatten_payload(payload)
    return neutralize_runtime_text("\n".join(lines)[:24_000] or event_type)


class TimelineCard(QFrame):
    def __init__(
        self,
        event: AgentUiEvent,
        title: str,
        body: str,
        strings=UI_TEXT,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        title = neutralize_runtime_text(title)
        body = neutralize_runtime_text(body)
        self.event = event
        self.copy_text = (
            f"{title}\n{event.created_at} · Run {event.run_id} · "
            f"{event.severity}\n{body}"
        )
        self.setObjectName(f"agentCard_{event.event_type.replace('.', '_')}")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAccessibleName(f"{title}; {event.severity}; Run {event.run_id}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(4)
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 700;")
        meta = QLabel(
            f"{event.created_at[11:19]}  ·  {event.severity.upper()}  ·  "
            f"{event.run_id[-12:]}"
        )
        meta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        meta.setStyleSheet("color: #7f8f9e; font-size: 10px;")
        copy_button = QToolButton()
        copy_button.setText(strings.agent_copy)
        copy_button.setAccessibleName(strings.agent_copy)
        copy_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.copy_text)
        )
        header.addWidget(title_label)
        header.addStretch(1)
        header.addWidget(meta)
        header.addWidget(copy_button)
        layout.addLayout(header)
        self.body = QPlainTextEdit(body)
        self.body.setReadOnly(True)
        self.body.setFrameShape(QFrame.Shape.NoFrame)
        self.body.setMaximumHeight(86)
        self.body.setAccessibleName(f"{title} details")
        layout.addWidget(self.body)
        self.expand_button = QToolButton()
        self.expand_button.setText(strings.agent_expand)
        self.expand_button.setCheckable(True)
        self.expand_button.setVisible(len(body) > 260 or body.count("\n") > 4)
        self.expand_button.toggled.connect(self._toggle)
        layout.addWidget(self.expand_button, alignment=Qt.AlignmentFlag.AlignLeft)
        color = {
            "error": "#e07178",
            "critical": "#e07178",
            "warning": "#d2a85a",
            "debug": "#7f8f9e",
        }.get(event.severity, "#71c9be")
        self.setStyleSheet(
            f"QFrame#{self.objectName()} {{ border-left: 3px solid {color}; }}"
        )
        self._strings = strings

    def _toggle(self, expanded: bool) -> None:
        self.body.setMaximumHeight(260 if expanded else 86)
        self.expand_button.setText(
            self._strings.agent_collapse if expanded else self._strings.agent_expand
        )


class ApprovalCard(TimelineCard):
    def __init__(
        self,
        event: AgentUiEvent,
        title: str,
        body: str,
        decision_handler: Callable[[str], None],
        stop_handler: Callable[[], None],
        strings=UI_TEXT,
    ):
        super().__init__(event, title, body, strings)
        high_risk = str(event.payload.get("risk") or "") in {
            "W2",
            "P2",
            "D1",
            "X1",
            "B1",
        }
        consequence = QLabel(
            neutralize_runtime_text(
                event.payload.get("reason")
                or event.payload.get("title")
                or "這項動作會在目前核准範圍內執行。"
            )
        )
        consequence.setObjectName("agentApprovalConsequence")
        consequence.setWordWrap(True)
        consequence.setAccessibleName("核准影響")
        self.layout().insertWidget(1, consequence)
        self.body.setVisible(high_risk)
        self.expand_button.setVisible(True)
        self.expand_button.setText(
            strings.agent_hide_details if high_risk else strings.agent_view_details
        )
        self.expand_button.setChecked(high_risk)
        self.expand_button.toggled.disconnect()
        self.expand_button.toggled.connect(self._toggle_approval_details)
        buttons = QHBoxLayout()
        self.approve_button = QPushButton(strings.agent_approve_once)
        self.session_button = QPushButton(strings.agent_repository_session_allow)
        self.reject_button = QPushButton(strings.agent_reject)
        self.stop_button = QPushButton(strings.agent_stop_run)
        self.approve_button.setAccessibleName(strings.agent_approve_once)
        self.session_button.setAccessibleName(strings.agent_repository_session_allow)
        self.reject_button.setAccessibleName(strings.agent_reject)
        self.stop_button.setAccessibleName(strings.agent_stop_run)
        self.approve_button.clicked.connect(
            lambda: self._decide("approved_once", decision_handler)
        )
        self.session_button.clicked.connect(
            lambda: self._decide("approved_for_session", decision_handler)
        )
        self.session_button.setVisible(
            any(
                option
                in {
                    "approved_for_session",
                    "accept_for_session",
                    "acceptForSession",
                }
                for option in event.payload.get("decision_options", ())
            )
        )
        self.reject_button.clicked.connect(
            lambda: self._decide("rejected", decision_handler)
        )
        self.stop_button.clicked.connect(stop_handler)
        self.stop_button.hide()
        self.reject_button.setDefault(True)
        self.reject_button.setFocus()
        buttons.addWidget(self.approve_button)
        buttons.addWidget(self.session_button)
        buttons.addWidget(self.reject_button)
        self.layout().addLayout(buttons)

    def _toggle_approval_details(self, expanded: bool) -> None:
        self.body.setVisible(expanded)
        self.expand_button.setText(
            self._strings.agent_hide_details
            if expanded
            else self._strings.agent_view_details
        )

    def _decide(self, decision: str, handler: Callable[[str], None]) -> None:
        handler(decision)
        self.approve_button.setEnabled(False)
        self.session_button.setEnabled(False)
        self.reject_button.setEnabled(False)


class TrustedRendererRegistry:
    TITLES = {
        "message.user": "使用者工作",
        "context.snapshot": "Context Snapshot",
        "data_boundary.previewed": "已查看要傳給 AI 的內容",
        "data_boundary.confirmed": "已確認要傳給 AI 的內容",
        "run.created": "Run 已建立",
        "run.started": "Run 已開始",
        "run.phase_changed": "執行階段",
        "run.waiting_for_user": "等待使用者",
        "run.resumed": "Run 已繼續",
        "run.interrupt_requested": "已要求停止",
        "run.interrupted": "Run 已中斷",
        "run.completed": "Run 已完成",
        "run.failed": "Run 需要協助確認",
        "provider.ready": "Provider Ready",
        "provider.unavailable": "Provider Unavailable",
        "provider.crashed": "Provider Crashed",
        "provider.protocol_error": "Protocol Error",
        "provider.auth.updated": "帳戶狀態",
        "provider.model_list.updated": "模型解析",
        "plan.updated": "執行計畫",
        "reasoning.summary.delta": "Reasoning Summary",
        "reasoning.summary.completed": "Reasoning Summary",
        "message.assistant.delta": "Agent 回覆",
        "message.assistant.completed": "Agent 回覆完成",
        "evidence.linked": "證據連結",
        "evidence.stale": "證據已標示 Stale",
        "tool.started": "工具開始",
        "tool.output.delta": "工具輸出",
        "tool.completed": "工具完成",
        "tool.failed": "工具需要協助確認",
        "command.requested": "Command Request",
        "command.started": "Command Started",
        "command.output.delta": "Command Output",
        "command.completed": "Command Completed",
        "file_change.proposed": "File Change Proposal",
        "file_change.completed": "File Change Completed",
        "diff.updated": "Diff Updated",
        "approval.requested": "需要人員核准",
        "approval.resolved": "核准決策",
        "approval.expired": "核准已逾時",
        "approval.cancelled": "核准已取消",
        "test.started": "Tests Started",
        "test.completed": "Tests Completed",
        "test.failed": "Tests Failed",
        "report.started": "Report Generation Started",
        "report.section_ready": "Report Section Ready",
        "report.validation_completed": "Report Validation",
        "report.ready": "Report Package Ready",
        "artifact.exported": "Artifact Exported",
        "thread.started": "Provider Thread Started",
        "thread.resumed": "Provider Thread Resumed",
        "turn.started": "Provider Turn Started",
    }

    def render(
        self,
        event: AgentUiEvent,
        *,
        approval_handler: Callable[[str], None],
        stop_handler: Callable[[], None],
        strings=UI_TEXT,
    ) -> TimelineCard | None:
        if event.event_type == "provider.unknown_event":
            return None
        title = self.TITLES.get(event.event_type)
        if title is None:
            title = (
                "警告"
                if event.severity == "warning"
                else "錯誤"
                if event.severity in {"error", "critical"}
                else "Provider Event"
            )
        body = event_copy_text(event)
        if (
            event.event_type == "approval.requested"
            and "approved_once" in event.payload.get("decision_options", ())
        ):
            return ApprovalCard(
                event,
                title,
                body,
                approval_handler,
                stop_handler,
                strings,
            )
        return TimelineCard(event, title, body, strings)
