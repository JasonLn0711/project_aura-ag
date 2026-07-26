from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from aura.agent.contracts import OperatingMode
from aura.agent.persistence import AgentCatalog


class WorkloadClass(str, Enum):
    SMALL_READ = "small_read"
    ANALYSIS = "analysis"
    HEAVY = "heavy"
    WRITE = "write"
    PUBLISH = "publish"


@dataclass(frozen=True)
class ResourceLimits:
    command_timeout_seconds: int = 900
    run_timeout_seconds: int = 7200
    maximum_child_processes: int = 4
    maximum_output_bytes: int = 8 * 1024 * 1024
    maximum_artifact_bytes: int = 2 * 1024 * 1024 * 1024
    low_disk_threshold_bytes: int = 5 * 1024 * 1024 * 1024
    memory_pressure_percent: float = 90.0
    cpu_pressure_percent: float = 95.0
    recording_priority: bool = True


@dataclass(frozen=True)
class ResourceSnapshot:
    recording_active: bool
    live_asr_active: bool
    asr_queue_depth: int
    cpu_percent: float
    memory_percent: float
    available_disk_bytes: int
    gpu_pressure_percent: float | None = None


@dataclass(frozen=True)
class ResourceRequest:
    workload: WorkloadClass
    requires_gpu: bool = False
    supports_pause: bool = False


@dataclass(frozen=True)
class GovernorDecision:
    allowed_to_start: bool
    action: str
    reason: str


class ResourceGovernor:
    def __init__(self, limits: ResourceLimits = ResourceLimits()):
        self.limits = limits

    def evaluate_start(
        self,
        request: ResourceRequest,
        snapshot: ResourceSnapshot,
    ) -> GovernorDecision:
        recording = snapshot.recording_active or snapshot.live_asr_active
        if recording and (
            request.workload
            in {
                WorkloadClass.HEAVY,
                WorkloadClass.WRITE,
                WorkloadClass.PUBLISH,
            }
            or request.requires_gpu
        ):
            return GovernorDecision(
                False,
                "queue",
                "等待錄音完成後執行",
            )
        if (
            request.workload
            in {WorkloadClass.HEAVY, WorkloadClass.WRITE, WorkloadClass.PUBLISH}
            and snapshot.available_disk_bytes < self.limits.low_disk_threshold_bytes
        ):
            return GovernorDecision(False, "queue", "可用磁碟空間低於安全門檻")
        if (
            request.workload is not WorkloadClass.SMALL_READ
            and snapshot.memory_percent >= self.limits.memory_pressure_percent
        ):
            return GovernorDecision(False, "queue", "記憶體壓力高，等待資源恢復")
        if (
            request.workload is WorkloadClass.HEAVY
            and snapshot.cpu_percent >= self.limits.cpu_pressure_percent
        ):
            return GovernorDecision(False, "queue", "CPU 負載高，等待資源恢復")
        if request.requires_gpu and (
            snapshot.gpu_pressure_percent is None
            or snapshot.gpu_pressure_percent >= 90
        ):
            return GovernorDecision(False, "queue", "GPU 資源尚未符合啟動條件")
        return GovernorDecision(True, "start", "資源與錄音保護條件已通過")

    def recording_started(
        self,
        request: ResourceRequest,
    ) -> GovernorDecision:
        if request.workload in {
            WorkloadClass.SMALL_READ,
            WorkloadClass.ANALYSIS,
        } and not request.requires_gpu:
            return GovernorDecision(True, "continue", "唯讀工作可與錄音並行")
        if request.supports_pause:
            return GovernorDecision(False, "pause", "錄音優先，已要求安全暫停")
        return GovernorDecision(
            False,
            "user_choice_required",
            "錄音已開始；請選擇停止 Agent 或確認錄音資源風險後繼續",
        )


@dataclass(frozen=True)
class SchedulerResult:
    run_id: str | None
    action: str
    reason: str


class DurableRunScheduler:
    def __init__(
        self,
        catalog: AgentCatalog,
        governor: ResourceGovernor,
    ):
        self.catalog = catalog
        self.governor = governor

    def start_next(
        self,
        snapshot: ResourceSnapshot,
        *,
        provider_ready: bool,
        now: str,
    ) -> SchedulerResult:
        if self.catalog.active_live_runs():
            return SchedulerResult(None, "wait", "另一個 Live 任務正在執行")
        for record in self.catalog.queue():
            if record["provider_mode"] != "live":
                continue
            result = self._start_record(
                record,
                snapshot,
                provider_ready=provider_ready,
                now=now,
            )
            if result.action != "queue":
                return result
        return SchedulerResult(None, "idle", "沒有可執行的 Live 任務")

    def start(
        self,
        run_id: str,
        snapshot: ResourceSnapshot,
        *,
        provider_ready: bool,
        now: str,
    ) -> SchedulerResult:
        if self.catalog.active_live_runs():
            return SchedulerResult(None, "wait", "另一個 Live 任務正在執行")
        record = next(
            (
                item
                for item in self.catalog.queue()
                if item["run_id"] == run_id and item["provider_mode"] == "live"
            ),
            None,
        )
        if record is None:
            raise KeyError(f"Run is not queued for Live execution: {run_id}")
        return self._start_record(
            record,
            snapshot,
            provider_ready=provider_ready,
            now=now,
        )

    def _start_record(
        self,
        record: dict[str, object],
        snapshot: ResourceSnapshot,
        *,
        provider_ready: bool,
        now: str,
    ) -> SchedulerResult:
        run_id = str(record["run_id"])
        if not provider_ready:
            self.catalog.set_queue_wait_reason(
                run_id,
                wait_reason="Codex Provider 尚未就緒",
                updated_at=now,
            )
            return SchedulerResult(None, "wait", "Codex Provider 尚未就緒")
        request = self._resource_request(record)
        decision = self.governor.evaluate_start(request, snapshot)
        if not decision.allowed_to_start:
            self.catalog.set_queue_wait_reason(
                run_id,
                wait_reason=decision.reason,
                updated_at=now,
            )
            return SchedulerResult(None, "queue", decision.reason)
        self.catalog.claim_queued(run_id, started_at=now)
        return SchedulerResult(run_id, "start", decision.reason)

    def stop(self, run_id: str, *, now: str) -> SchedulerResult:
        self.catalog.request_stop(run_id, requested_at=now)
        return SchedulerResult(run_id, "interrupt", "已送出中斷；不會自動重新啟動")

    @staticmethod
    def _resource_request(record: dict[str, object]) -> ResourceRequest:
        mode = OperatingMode(str(record["requested_mode"]))
        workflow = str(record["workflow_template_id"])
        if mode is OperatingMode.ASK_EXPLAIN:
            return ResourceRequest(WorkloadClass.SMALL_READ)
        if mode is OperatingMode.PUBLISH:
            return ResourceRequest(WorkloadClass.PUBLISH)
        if mode is OperatingMode.IMPLEMENT:
            return ResourceRequest(WorkloadClass.WRITE)
        if workflow in {"architecture", "package", "security", "pii"}:
            return ResourceRequest(WorkloadClass.HEAVY)
        return ResourceRequest(WorkloadClass.ANALYSIS)
