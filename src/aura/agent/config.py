from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

from aura.audit import audit_enabled_from_env


def _integer(name: str, default: int, minimum: int) -> int:
    try:
        return max(minimum, int(os.environ.get(name, default)))
    except ValueError:
        return default


def _application_data_root() -> Path:
    value = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    return Path(value) if value else Path.home() / ".local" / "share" / "project_aura"


@dataclass(frozen=True)
class AgentConfig:
    enabled: bool
    default_mode: str
    run_root: Path
    worktree_root: Path
    allowed_repository_roots: tuple[Path, ...]
    codex_executable: str | None
    codex_startup_timeout_ms: int
    codex_request_timeout_ms: int
    codex_max_message_bytes: int
    default_profile: str
    default_safety_profile: str
    network_access_default: bool
    one_live_run_only: bool
    demo_speed_ms: int
    retention_days: int
    redaction_enabled: bool
    audit_enabled: bool
    report_output_root: Path

    def __post_init__(self) -> None:
        if self.default_mode not in {"demo", "live"}:
            raise ValueError("Agent default mode must be demo or live.")
        if self.default_safety_profile != "read-only":
            raise ValueError(
                "P0 Agent safety must default to read-only; approved worktree "
                "write activates per run."
            )
        if self.network_access_default:
            raise ValueError("P0 Agent network access default must remain disabled.")
        if not self.one_live_run_only or not self.redaction_enabled:
            raise ValueError("P0 concurrency and redaction controls must remain enabled.")

    @classmethod
    def from_environment(
        cls,
        *,
        repository_hint: str | Path | None = None,
    ) -> "AgentConfig":
        data_root = _application_data_root()
        allowed_value = os.environ.get("AURA_AGENT_ALLOWED_ROOTS", "")
        if allowed_value:
            allowed = tuple(
                Path(value.strip()).expanduser().resolve(strict=True)
                for value in allowed_value.split(os.pathsep)
                if value.strip()
            )
        else:
            allowed = (
                Path(repository_hint or Path.cwd()).expanduser().resolve(strict=True),
            )
        return cls(
            enabled=True,
            default_mode=os.environ.get("AURA_AGENT_DEFAULT_MODE", "live"),
            run_root=Path(
                os.environ.get("AURA_AGENT_RUN_ROOT", data_root / "agent-runs")
            ).expanduser(),
            worktree_root=Path(
                os.environ.get("AURA_AGENT_WORKTREE_ROOT", data_root / "agent-worktrees")
            ).expanduser(),
            allowed_repository_roots=allowed,
            codex_executable=os.environ.get("AURA_CODEX_EXECUTABLE"),
            codex_startup_timeout_ms=1000
            * _integer("AURA_CODEX_STARTUP_TIMEOUT_SECONDS", 10, 1),
            codex_request_timeout_ms=1000
            * _integer("AURA_CODEX_REQUEST_TIMEOUT_SECONDS", 30, 1),
            codex_max_message_bytes=_integer(
                "AURA_CODEX_MAX_MESSAGE_BYTES", 8 * 1024 * 1024, 1024
            ),
            default_profile=os.environ.get("AURA_AGENT_DEFAULT_PROFILE", "standard"),
            default_safety_profile=os.environ.get(
                "AURA_AGENT_DEFAULT_SAFETY_PROFILE", "read-only"
            ),
            network_access_default=False,
            one_live_run_only=True,
            demo_speed_ms=_integer("AURA_AGENT_DEMO_SPEED_MS", 300, 0),
            retention_days=_integer("AURA_AGENT_RETENTION_DAYS", 0, 0),
            redaction_enabled=True,
            audit_enabled=audit_enabled_from_env(),
            report_output_root=Path(
                os.environ.get(
                    "AURA_AGENT_REPORT_OUTPUT_ROOT",
                    data_root / "agent-reports",
                )
            ).expanduser(),
        )
