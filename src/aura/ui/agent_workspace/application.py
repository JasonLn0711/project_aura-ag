from __future__ import annotations

from dataclasses import dataclass
import uuid
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal

from aura.ui.agent_workspace.view_state import AgentWorkspaceViewState
from aura.agent.contracts import (
    AgentRun,
    AgentRunState,
    OperatingMode,
    WorkItem,
    WorkItemSource,
    WorkItemState,
)
from aura.agent.state import TERMINAL_PHASES
from aura.agent.policy import neutralize_runtime_text
from aura.ui.agent_workspace.commands import (
    ApprovalDecision,
    QueuedFollowUp,
    QueueFollowUpRequest,
    StartRunRequest,
    SteerRunRequest,
    StopRunRequest,
)

if TYPE_CHECKING:
    from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem


@dataclass(frozen=True)
class StartContext:
    task_text: str
    live: bool
    active_run: bool
    pending_approval: bool
    data_boundary_confirmed: bool
    transfer_current: bool
    transfer_allowed: bool
    repository_selected: bool
    repository_allowed: bool
    provider_ready: bool
    signed_in: bool
    model_resolved: bool
    evidence_required: bool
    evidence_eligible: bool
    mutating: bool = False
    storage_ready: bool = True

    @classmethod
    def ready(cls, task_text: str, *, live: bool = False) -> "StartContext":
        return cls(
            task_text=task_text,
            live=live,
            active_run=False,
            pending_approval=False,
            data_boundary_confirmed=True,
            transfer_current=True,
            transfer_allowed=True,
            repository_selected=True,
            repository_allowed=True,
            provider_ready=True,
            signed_in=True,
            model_resolved=True,
            evidence_required=False,
            evidence_eligible=True,
            mutating=False,
            storage_ready=True,
        )


@dataclass(frozen=True)
class StartReadiness:
    allowed: bool
    reason_code: str
    message: str


class AgentWorkspaceApplicationService(QObject):
    """Typed application seam between Qt presentation and Agent services."""

    view_state_changed = pyqtSignal(object)

    _MESSAGES = {
        "ready": "可以開始執行。",
        "task_required": "輸入想完成的工作。",
        "active_run": "目前任務正在執行。",
        "pending_approval": "完成目前的核准決策後即可繼續。",
        "transfer_confirmation": "送出前，請先確認要傳給 AI 的內容。",
        "transfer_blocked": "調整受保護內容後即可繼續。",
        "repository_required": "選擇 Repository 後即可開始。",
        "repository_not_allowed": "在 Control Panel 啟用此 Repository 後即可開始。",
        "provider_not_ready": "Codex 執行環境正在準備；完成後即可開始。",
        "login_required": "登入 ChatGPT 後即可啟動 Live 工作。",
        "model_required": "選擇目前可用的模型設定。",
        "evidence_required": "加入已確認且符合來源支持條件的會議證據。",
        "storage_low": "可用空間已達保護門檻；管理儲存空間後即可啟動寫入工作。",
    }

    def __init__(
        self,
        subsystem: "AgentWorkspaceSubsystem",
        *,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.subsystem = subsystem
        from aura.ui.agent_workspace.presenter import AgentWorkspacePresenter

        self.presenter = AgentWorkspacePresenter()

    def evaluate_start(self, context: StartContext) -> StartReadiness:
        reason = self._reason(context)
        return StartReadiness(
            allowed=reason == "ready",
            reason_code=reason,
            message=self._MESSAGES[reason],
        )

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
        state = self.presenter.present(
            title=title,
            repository_name=repository_name,
            draft=draft,
            readiness=readiness,
            phase=phase,
            active_run=active_run,
        )
        self.view_state_changed.emit(state)
        return state

    def start_run(self, request: StartRunRequest) -> None:
        self.subsystem.controller.start_run(
            task=neutralize_runtime_text(request.task),
            workflow=request.workflow,
            branch=request.branch,
            run_id=request.run_id,
            resume_thread_id=request.resume_thread_id,
        )

    def stop_run(self, request: StopRunRequest) -> None:
        state = self.subsystem.controller.state
        if state.active_run_id != request.run_id:
            raise ValueError("Stop intent does not match the active run.")
        self.subsystem.controller.stop()

    def resolve_approval(self, request: ApprovalDecision) -> None:
        state = self.subsystem.controller.state
        if state.active_run_id != request.run_id:
            raise ValueError("Approval intent does not match the active run.")
        if state.pending_approval_id != request.approval_id:
            raise ValueError("Approval intent is stale.")
        self.subsystem.controller.resolve_approval(
            request.approval_id,
            request.decision,
        )

    def steer_run(self, request: SteerRunRequest) -> None:
        state = self.subsystem.controller.state
        if (
            state.active_run_id != request.run_id
            or state.phase in TERMINAL_PHASES
        ):
            raise ValueError("Steer intent does not match an active run.")
        steer = getattr(self.subsystem.controller.provider, "steer_turn", None)
        if steer is None:
            raise RuntimeError("The active provider does not support steer.")
        steer(neutralize_runtime_text(request.text))

    def reconnect_provider(self) -> None:
        self.subsystem.controller.provider.start()

    def queue_follow_up(
        self,
        request: QueueFollowUpRequest,
    ) -> QueuedFollowUp:
        catalog = self.subsystem.catalog
        if catalog is None:
            raise RuntimeError("The local task catalog is unavailable.")
        work_item_id = f"work-{uuid.uuid4()}"
        run_id = f"run-{uuid.uuid4()}"
        requested_mode = OperatingMode(request.requested_mode)
        catalog.create_work_item(
            WorkItem(
                work_item_id=work_item_id,
                source=WorkItemSource.MANUAL,
                title=neutralize_runtime_text(request.title),
                objective=neutralize_runtime_text(request.objective),
                acceptance_criteria=(),
                repository_id=request.repository_id,
                workflow_template_id=request.workflow,
                requested_mode=requested_mode,
                requested_model_profile=request.requested_model_profile,
                evidence_context_id=None,
                created_by=request.actor_id,
                created_at=request.created_at,
            )
        )
        catalog.transition_work_item(
            work_item_id,
            WorkItemState.READY,
            updated_at=request.created_at,
        )
        catalog.create_run(
            AgentRun(
                run_id=run_id,
                work_item_id=work_item_id,
                state=AgentRunState.CREATED,
                provider_mode=request.provider_mode,
                requested_model_profile=request.requested_model_profile,
                requested_mode=requested_mode,
                created_at=request.created_at,
                base_commit=request.base_commit,
            )
        )
        catalog.enqueue(
            run_id,
            enqueued_at=request.created_at,
            wait_reason="active_turn_follow_up",
        )
        return QueuedFollowUp(
            work_item_id=work_item_id,
            run_id=run_id,
        )

    @staticmethod
    def _reason(context: StartContext) -> str:
        if not context.repository_selected:
            return "repository_required"
        if not context.repository_allowed:
            return "repository_not_allowed"
        if not context.task_text.strip():
            return "task_required"
        if context.active_run:
            return "active_run"
        if context.pending_approval:
            return "pending_approval"
        if context.live:
            if not context.data_boundary_confirmed or not context.transfer_current:
                return "transfer_confirmation"
            if not context.transfer_allowed:
                return "transfer_blocked"
        if context.mutating and not context.storage_ready:
            return "storage_low"
        if context.live:
            if not context.provider_ready:
                return "provider_not_ready"
            if not context.signed_in:
                return "login_required"
            if not context.model_resolved:
                return "model_required"
        if context.evidence_required and not context.evidence_eligible:
            return "evidence_required"
        return "ready"
