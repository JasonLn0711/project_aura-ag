from __future__ import annotations

from typing import Any, Callable

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QVBoxLayout, QWidget

from aura.agent.config import AgentConfig
from aura.agent.evidence import EvidenceSelection
from aura.agent.providers.codex_app_server import CodexAppServerProvider
from aura.agent.scheduler import ResourceSnapshot
from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem
from aura.ui.agent_workspace.workspace_view import (
    AgentWorkspaceView,
    ApprovalCard,
    TimelineCard,
    event_copy_text,
)
from aura.ui.messages import UI_TEXT


class AgentWorkspaceTab(QWidget):
    """Thin MainWindow boundary for the composed native Agent Workspace."""

    def __init__(
        self,
        *,
        audit=None,
        strings=UI_TEXT,
        config: AgentConfig | None = None,
        subsystem: AgentWorkspaceSubsystem | None = None,
        codex_provider_factory: Callable[[], CodexAppServerProvider] | None = None,
        url_opener: Callable[[QUrl], bool] | None = None,
        resource_state_provider: Callable[[], ResourceSnapshot] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._view = AgentWorkspaceView(
            audit=audit,
            strings=strings,
            config=config,
            subsystem=subsystem,
            codex_provider_factory=codex_provider_factory,
            url_opener=url_opener,
            resource_state_provider=resource_state_provider,
            parent=self,
        )
        layout.addWidget(self._view)

    @property
    def selected_evidence(self) -> EvidenceSelection | None:
        return self._view.selected_evidence

    @selected_evidence.setter
    def selected_evidence(self, value: EvidenceSelection | None) -> None:
        self._view.selected_evidence = value

    @property
    def evidence_adapter(self) -> Any:
        return self._view.evidence_adapter

    @evidence_adapter.setter
    def evidence_adapter(self, value: Any) -> None:
        self._view.evidence_adapter = value

    def __getattr__(self, name: str) -> Any:
        view = self.__dict__.get("_view")
        if view is not None:
            return getattr(view, name)
        raise AttributeError(name)


__all__ = [
    "AgentWorkspaceTab",
    "ApprovalCard",
    "TimelineCard",
    "event_copy_text",
]
