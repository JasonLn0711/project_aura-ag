from __future__ import annotations

from typing import Any

from aura.ui.agent_workspace.artifact_actions import ArtifactActions
from aura.ui.agent_workspace.evidence_actions import EvidenceActions
from aura.ui.agent_workspace.intent_actions import IntentActions
from aura.ui.agent_workspace.repository_actions import RepositoryActions
from aura.ui.agent_workspace.run_actions import RunActions


class AgentWorkspaceActions:
    """Routes view intentions to focused application/presentation controllers."""

    def __init__(self, view: Any) -> None:
        self._groups = (
            RepositoryActions(view),
            IntentActions(view),
            EvidenceActions(view),
            RunActions(view),
            ArtifactActions(view),
        )

    def __getattr__(self, name: str) -> Any:
        for group in self._groups:
            if name in type(group).__dict__:
                return getattr(group, name)
        raise AttributeError(name)
