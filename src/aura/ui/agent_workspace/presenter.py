from __future__ import annotations

from aura.ui.agent_workspace.application import StartReadiness
from aura.ui.agent_workspace.view_state import (
    AgentWorkspaceViewState,
    ComposerViewState,
    PrimaryAction,
    ThreadHeaderViewState,
)


class AgentWorkspacePresenter:
    """Projects application state into immutable display-ready values."""

    def present(
        self,
        *,
        title: str,
        repository_name: str | None,
        draft: str,
        readiness: StartReadiness,
        phase: str = "draft",
        active_run: bool = False,
    ) -> AgentWorkspaceViewState:
        return AgentWorkspaceViewState(
            header=ThreadHeaderViewState(
                title=title,
                repository_name=repository_name,
                phase=phase,
            ),
            composer=ComposerViewState(
                draft=draft,
                primary_action=(
                    PrimaryAction.STOP if active_run else PrimaryAction.SEND
                ),
                primary_enabled=active_run or readiness.allowed,
                disabled_reason_code=(
                    None if active_run or readiness.allowed else readiness.reason_code
                ),
                disabled_reason=(
                    None if active_run or readiness.allowed else readiness.message
                ),
            ),
        )
