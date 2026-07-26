from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import threading
import uuid
import zipfile
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from aura.agent.contracts import (
    AGENT_RUN_TRANSITIONS,
    PUBLICATION_TRANSITIONS,
    WORK_ITEM_TRANSITIONS,
    AgentRun,
    AgentRunState,
    AgentUiEvent,
    Artifact,
    EngineeringTaskLink,
    PublicationState,
    RepositoryProfile,
    RepositorySessionGrant,
    WorkItem,
    WorkItemState,
    validate_transition,
)
from aura.agent.policy import path_has_sensitive_component
from aura.agent.state import TERMINAL_PHASES
from aura.redaction import redact_sensitive_text


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REDACTED_KEYS = {
    "access_token",
    "authorization",
    "credential",
    "password",
    "prompt",
    "raw_account",
    "refresh_token",
    "secret",
    "token",
    "transcript",
}
CATALOG_SCHEMA_VERSION = 1


def _sanitize(value: Any, *, key: str = "") -> Any:
    normalized = key.lower()
    if normalized in REDACTED_KEYS or normalized.endswith(("_token", "_secret", "_password")):
        return "[REDACTED]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, Mapping):
        return {str(item_key): _sanitize(item, key=str(item_key)) for item_key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    return str(value)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(_sanitize(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class AgentRunStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        if path_has_sensitive_component(self.root):
            raise ValueError("Agent run storage cannot use a sensitive path.")
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def create_run(self, metadata: Mapping[str, Any]) -> Path:
        run_id = str(metadata.get("run_id") or "")
        if not RUN_ID_RE.fullmatch(run_id):
            raise ValueError("Run ID must be a stable filename-safe identifier.")
        run_dir = self.root / run_id
        try:
            run_dir.mkdir(parents=False)
        except FileExistsError as exc:
            raise FileExistsError(f"Agent run already exists: {run_id}") from exc
        (run_dir / "export").mkdir()
        for filename in ("events.jsonl", "approvals.jsonl", "commands.jsonl"):
            (run_dir / filename).touch()
        for filename, payload in (
            ("context.json", {}),
            ("provider.json", {}),
            ("evidence.json", {}),
            ("file-changes.json", {"files": []}),
            ("tests.json", {"status": "not_run", "commands": []}),
            ("report-manifest.json", {"status": "not_started", "files": []}),
        ):
            _atomic_write_json(run_dir / filename, payload)
        _atomic_write_json(run_dir / "run.json", metadata)
        return run_dir

    def run_dir(self, run_id: str) -> Path:
        if not RUN_ID_RE.fullmatch(run_id):
            raise ValueError("Invalid run ID.")
        path = self.root / run_id
        if not path.is_dir():
            raise FileNotFoundError(f"Unknown agent run: {run_id}")
        return path

    def append_event(self, run_id: str, event: AgentUiEvent) -> None:
        if event.run_id != run_id:
            raise ValueError("Event run ID does not match the target run.")
        self._append_jsonl(self.run_dir(run_id) / "events.jsonl", event.to_dict())

    def append_approval(self, run_id: str, approval: Mapping[str, Any]) -> None:
        self._append_jsonl(self.run_dir(run_id) / "approvals.jsonl", approval)

    def append_command(self, run_id: str, command: Mapping[str, Any]) -> None:
        self._append_jsonl(self.run_dir(run_id) / "commands.jsonl", command)

    def write_patch(self, run_id: str, patch: str) -> Path:
        path = self.run_dir(run_id) / "diff.patch"
        sanitized = str(_sanitize(patch))
        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        )
        temporary = Path(handle.name)
        try:
            with handle:
                handle.write(sanitized)
                if sanitized and not sanitized.endswith("\n"):
                    handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return path

    def update_run(self, run_id: str, changes: Mapping[str, Any]) -> dict[str, Any]:
        path = self.run_dir(run_id) / "run.json"
        current = json.loads(path.read_text(encoding="utf-8"))
        current.update(changes)
        _atomic_write_json(path, current)
        return current

    def write_json(self, run_id: str, filename: str, payload: Mapping[str, Any]) -> Path:
        if filename not in {
            "context.json",
            "provider.json",
            "evidence.json",
            "file-changes.json",
            "tests.json",
            "report-manifest.json",
        }:
            raise ValueError(f"Unsupported run artifact: {filename}")
        path = self.run_dir(run_id) / filename
        _atomic_write_json(path, payload)
        return path

    def discover_incomplete(self) -> list[dict[str, Any]]:
        incomplete: list[dict[str, Any]] = []
        for path in sorted(self.root.glob("*/run.json")):
            try:
                metadata = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if metadata.get("phase") not in TERMINAL_PHASES:
                incomplete.append(metadata)
        return incomplete

    def mark_interrupted(self, run_id: str, *, reason: str) -> dict[str, Any]:
        metadata_path = self.run_dir(run_id) / "run.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("phase") in TERMINAL_PHASES:
            return metadata
        sequence = 0
        events_path = self.run_dir(run_id) / "events.jsonl"
        with events_path.open(encoding="utf-8") as events:
            for line in events:
                try:
                    sequence = max(
                        sequence,
                        AgentUiEvent.from_dict(json.loads(line)).sequence,
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    continue
        now = dt.datetime.now().astimezone().isoformat(timespec="milliseconds")
        self.append_event(
            run_id,
            AgentUiEvent.create(
                run_id=run_id,
                event_type="run.interrupted",
                sequence=sequence + 1,
                source="recovery",
                severity="warning",
                payload={
                    "reason": reason,
                    "prior_phase": metadata.get("phase"),
                    "explanation": "No supported provider thread is available for explicit resume.",
                },
                created_at=now,
                event_id=str(uuid.uuid4()),
            ),
        )
        return self.update_run(
            run_id,
            {
                "phase": "interrupted",
                "ended_at": now,
                "final_outcome": "interrupted",
                "error_class": "RecoveryNotSupported",
                "artifact_digests": self.artifact_digests(run_id),
            },
        )

    def artifact_digests(self, run_id: str) -> dict[str, str]:
        digests: dict[str, str] = {}
        root = self.run_dir(run_id)
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.name != "run.json":
                digests[path.relative_to(root).as_posix()] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
        return digests

    def export_run_bundle(
        self,
        run_id: str,
        filename: str = "agent-evidence-packet.zip",
    ) -> tuple[Path, str]:
        if Path(filename).name != filename or not filename.endswith(".zip"):
            raise ValueError("Run export filename must be a safe ZIP basename.")
        root = self.run_dir(run_id)
        target = root / "export" / filename
        if target.exists():
            raise FileExistsError(f"Run export already exists: {filename}")
        temporary = target.with_name(f".{target.name}.tmp")
        included = (
            "run.json",
            "context.json",
            "events.jsonl",
            "approvals.jsonl",
            "provider.json",
            "evidence.json",
            "commands.jsonl",
            "file-changes.json",
            "diff.patch",
            "tests.json",
            "report-manifest.json",
        )
        try:
            with zipfile.ZipFile(
                temporary,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:
                for name in included:
                    path = root / name
                    if path.is_file():
                        archive.write(path, name)
            with zipfile.ZipFile(temporary) as archive:
                if archive.testzip() is not None:
                    raise OSError("Run export ZIP failed CRC validation.")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return target, hashlib.sha256(target.read_bytes()).hexdigest()

    def _append_jsonl(self, path: Path, payload: Mapping[str, Any]) -> None:
        line = json.dumps(_sanitize(payload), ensure_ascii=False, sort_keys=True) + "\n"
        with self._lock, path.open("a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


class AgentCatalog:
    """Transactional task/queue index; per-run files remain execution evidence."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        if path_has_sensitive_component(self.path):
            raise ValueError("Agent catalog cannot use a sensitive path.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._preexisting = self.path.exists() and self.path.stat().st_size > 0
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self.path,
            timeout=5,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA synchronous = FULL")
        self._connection.execute("PRAGMA busy_timeout = 5000")
        journal_mode = self._connection.execute(
            "PRAGMA journal_mode = WAL"
        ).fetchone()[0]
        if str(journal_mode).lower() != "wal":
            self.close()
            raise RuntimeError("Agent catalog requires SQLite WAL mode.")
        self.last_migration_backup: Path | None = None
        self._migrate()
        self.validate()

    def __enter__(self) -> "AgentCatalog":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    @property
    def schema_version(self) -> int:
        return int(self._execute("PRAGMA user_version").fetchone()[0])

    def validate(self) -> None:
        integrity = self._execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Agent catalog integrity check failed: {integrity}")
        foreign_keys = self._execute("PRAGMA foreign_key_check").fetchall()
        if foreign_keys:
            raise RuntimeError("Agent catalog foreign-key validation failed.")

    def register_repository(self, profile: RepositoryProfile) -> None:
        payload = _jsonable(profile)
        with self._transaction():
            self._execute(
                """
                INSERT INTO repositories (
                    repository_id, display_name, canonical_root, root_fingerprint,
                    allowed, default_base_branch, allowed_remote_urls_json,
                    allowed_branch_prefixes_json, data_classification,
                    instruction_policy, network_policy_id, command_policy_id,
                    publication_policy_id, retention_policy_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(repository_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    canonical_root = excluded.canonical_root,
                    root_fingerprint = excluded.root_fingerprint,
                    allowed = excluded.allowed,
                    default_base_branch = excluded.default_base_branch,
                    allowed_remote_urls_json = excluded.allowed_remote_urls_json,
                    allowed_branch_prefixes_json = excluded.allowed_branch_prefixes_json,
                    data_classification = excluded.data_classification,
                    instruction_policy = excluded.instruction_policy,
                    network_policy_id = excluded.network_policy_id,
                    command_policy_id = excluded.command_policy_id,
                    publication_policy_id = excluded.publication_policy_id,
                    retention_policy_id = excluded.retention_policy_id,
                    updated_at = excluded.updated_at
                """,
                (
                    payload["repository_id"],
                    payload["display_name"],
                    payload["canonical_root"],
                    payload["root_fingerprint"],
                    int(payload["allowed"]),
                    payload["default_base_branch"],
                    json.dumps(payload["allowed_remote_urls"]),
                    json.dumps(payload["allowed_branch_prefixes"]),
                    payload["data_classification"],
                    payload["instruction_policy"],
                    payload["network_policy_id"],
                    payload["command_policy_id"],
                    payload["publication_policy_id"],
                    payload["retention_policy_id"],
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )

    def set_repository_allowed(
        self,
        repository_id: str,
        *,
        allowed: bool,
        updated_at: str,
    ) -> None:
        with self._transaction():
            cursor = self._execute(
                "UPDATE repositories SET allowed = ?, updated_at = ? "
                "WHERE repository_id = ?",
                (int(allowed), updated_at, repository_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Unknown repository: {repository_id}")

    def repositories(self, *, allowed_only: bool = False) -> list[dict[str, Any]]:
        suffix = " WHERE allowed = 1" if allowed_only else ""
        rows = self._execute(
            "SELECT * FROM repositories" + suffix + " ORDER BY display_name"
        ).fetchall()
        return [self._repository_record(row) for row in rows]

    def repository(self, repository_id: str) -> dict[str, Any]:
        row = self._execute(
            "SELECT * FROM repositories WHERE repository_id = ?",
            (repository_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown repository: {repository_id}")
        return self._repository_record(row)

    def create_work_item(self, item: WorkItem) -> None:
        payload = _jsonable(item)
        with self._transaction():
            self._execute(
                """
                INSERT INTO work_items (
                    work_item_id, source, title, objective,
                    acceptance_criteria_json, repository_id,
                    workflow_template_id, requested_mode,
                    requested_model_profile, evidence_context_id,
                    created_by, created_at, updated_at, state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["work_item_id"],
                    payload["source"],
                    payload["title"],
                    payload["objective"],
                    json.dumps(payload["acceptance_criteria"], ensure_ascii=False),
                    payload["repository_id"],
                    payload["workflow_template_id"],
                    payload["requested_mode"],
                    payload["requested_model_profile"],
                    payload["evidence_context_id"],
                    payload["created_by"],
                    payload["created_at"],
                    payload["updated_at"] or payload["created_at"],
                    payload["state"],
                ),
            )

    def work_item(self, work_item_id: str) -> dict[str, Any]:
        row = self._execute(
            "SELECT * FROM work_items WHERE work_item_id = ?",
            (work_item_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown WorkItem: {work_item_id}")
        result = dict(row)
        result["acceptance_criteria"] = json.loads(
            result.pop("acceptance_criteria_json")
        )
        return result

    def work_items(
        self,
        *,
        repository_id: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._execute(
            "SELECT * FROM work_items"
            + (" WHERE repository_id = ?" if repository_id else "")
            + " ORDER BY updated_at DESC, created_at DESC",
            (repository_id,) if repository_id else (),
        ).fetchall()
        records = []
        for row in rows:
            record = dict(row)
            record["acceptance_criteria"] = json.loads(
                record.pop("acceptance_criteria_json")
            )
            records.append(record)
        return records

    def update_work_item_draft(
        self,
        work_item_id: str,
        *,
        title: str,
        objective: str,
        workflow_template_id: str,
        requested_mode: str,
        requested_model_profile: str,
        evidence_context_id: str | None,
        updated_at: str,
    ) -> None:
        record = self.work_item(work_item_id)
        if record["state"] != WorkItemState.DRAFT.value:
            raise ValueError("Only draft WorkItems can be edited.")
        if not title.strip() or not objective.strip():
            raise ValueError("Draft title and objective are required.")
        with self._transaction():
            self._execute(
                """
                UPDATE work_items
                SET title = ?, objective = ?, workflow_template_id = ?,
                    requested_mode = ?, requested_model_profile = ?,
                    evidence_context_id = ?, updated_at = ?
                WHERE work_item_id = ?
                """,
                (
                    title,
                    objective,
                    workflow_template_id,
                    requested_mode,
                    requested_model_profile,
                    evidence_context_id,
                    updated_at,
                    work_item_id,
                ),
            )

    def rename_work_item(
        self,
        work_item_id: str,
        *,
        title: str,
        updated_at: str,
    ) -> None:
        normalized = title.strip()
        if not normalized:
            raise ValueError("WorkItem title is required.")
        with self._transaction():
            cursor = self._execute(
                "UPDATE work_items SET title = ?, updated_at = ? "
                "WHERE work_item_id = ?",
                (normalized, updated_at, work_item_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Unknown WorkItem: {work_item_id}")

    def transition_work_item(
        self,
        work_item_id: str,
        state: WorkItemState,
        *,
        updated_at: str,
    ) -> None:
        current = WorkItemState(self.work_item(work_item_id)["state"])
        validate_transition(current, state, WORK_ITEM_TRANSITIONS)
        with self._transaction():
            self._execute(
                "UPDATE work_items SET state = ?, updated_at = ? "
                "WHERE work_item_id = ?",
                (state.value, updated_at, work_item_id),
            )

    def create_run(self, run: AgentRun) -> None:
        payload = _jsonable(run)
        with self._transaction():
            self._execute(
                """
                INSERT INTO runs (
                    run_id, work_item_id, state, provider_mode,
                    requested_model_profile, requested_mode, created_at,
                    base_commit, workspace_id, resolved_model_id,
                    resolved_effort, provider_version, continuation_of_run_id,
                    publication_state, validation_status, started_at, ended_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(
                    payload[key]
                    for key in (
                        "run_id",
                        "work_item_id",
                        "state",
                        "provider_mode",
                        "requested_model_profile",
                        "requested_mode",
                        "created_at",
                        "base_commit",
                        "workspace_id",
                        "resolved_model_id",
                        "resolved_effort",
                        "provider_version",
                        "continuation_of_run_id",
                        "publication_state",
                        "validation_status",
                        "started_at",
                        "ended_at",
                    )
                ),
            )

    def run(self, run_id: str) -> dict[str, Any]:
        row = self._execute(
            "SELECT * FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown AgentRun: {run_id}")
        return dict(row)

    def transition_run(
        self,
        run_id: str,
        state: AgentRunState,
        *,
        timestamp: str,
        validation_status: str | None = None,
    ) -> None:
        record = self.run(run_id)
        current = AgentRunState(record["state"])
        validate_transition(current, state, AGENT_RUN_TRANSITIONS)
        if state is AgentRunState.COMPLETED and (
            validation_status or record["validation_status"]
        ) not in {"passed", "not_required"}:
            raise ValueError("A run cannot complete while validation is unknown or failed.")
        started_at = (
            timestamp
            if record["started_at"] is None
            and state
            not in {
                AgentRunState.CREATED,
                AgentRunState.QUEUED,
                AgentRunState.BLOCKED,
                AgentRunState.ABANDONED,
            }
            else record["started_at"]
        )
        ended_at = (
            timestamp
            if state
            in {
                AgentRunState.COMPLETED,
                AgentRunState.FAILED,
                AgentRunState.INTERRUPTED,
                AgentRunState.ABANDONED,
            }
            else None
        )
        with self._transaction():
            self._execute(
                """
                UPDATE runs
                SET state = ?, validation_status = ?, started_at = ?, ended_at = ?
                WHERE run_id = ?
                """,
                (
                    state.value,
                    validation_status or record["validation_status"],
                    started_at,
                    ended_at,
                    run_id,
                ),
            )

    def transition_publication(
        self,
        run_id: str,
        state: PublicationState,
    ) -> None:
        current = PublicationState(self.run(run_id)["publication_state"])
        validate_transition(current, state, PUBLICATION_TRANSITIONS)
        with self._transaction():
            self._execute(
                "UPDATE runs SET publication_state = ? WHERE run_id = ?",
                (state.value, run_id),
            )

    def enqueue(
        self,
        run_id: str,
        *,
        enqueued_at: str,
        run_when_ready: bool = False,
        wait_reason: str | None = None,
    ) -> int:
        run = self.run(run_id)
        validate_transition(
            AgentRunState(run["state"]),
            AgentRunState.QUEUED,
            AGENT_RUN_TRANSITIONS,
        )
        item = self.work_item(run["work_item_id"])
        validate_transition(
            WorkItemState(item["state"]),
            WorkItemState.QUEUED,
            WORK_ITEM_TRANSITIONS,
        )
        position = int(
            self._execute(
                "SELECT COALESCE(MAX(position), 0) + 1 FROM queue_entries "
                "WHERE state = 'queued'"
            ).fetchone()[0]
        )
        with self._transaction():
            self._execute(
                """
                INSERT INTO queue_entries (
                    run_id, position, state, run_when_ready,
                    wait_reason, enqueued_at, updated_at
                ) VALUES (?, ?, 'queued', ?, ?, ?, ?)
                """,
                (
                    run_id,
                    position,
                    int(run_when_ready),
                    wait_reason,
                    enqueued_at,
                    enqueued_at,
                ),
            )
            self._execute(
                "UPDATE runs SET state = ? WHERE run_id = ?",
                (AgentRunState.QUEUED.value, run_id),
            )
            self._execute(
                "UPDATE work_items SET state = ?, updated_at = ? "
                "WHERE work_item_id = ?",
                (
                    WorkItemState.QUEUED.value,
                    enqueued_at,
                    run["work_item_id"],
                ),
            )
        return position

    def queue(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self._execute(
                """
                SELECT q.*, r.work_item_id, r.provider_mode, r.requested_mode,
                       w.workflow_template_id
                FROM queue_entries q
                JOIN runs r ON r.run_id = q.run_id
                JOIN work_items w ON w.work_item_id = r.work_item_id
                WHERE q.state = 'queued'
                ORDER BY q.position, q.queue_entry_id
                """
            ).fetchall()
        ]

    def active_live_runs(self) -> list[dict[str, Any]]:
        active_states = tuple(
            state.value
            for state in (
                AgentRunState.PREFLIGHT,
                AgentRunState.STARTING_PROVIDER,
                AgentRunState.PLANNING,
                AgentRunState.RUNNING_READ,
                AgentRunState.WAITING_APPROVAL,
                AgentRunState.PREPARING_WORKTREE,
                AgentRunState.RUNNING_WRITE,
                AgentRunState.VALIDATING,
                AgentRunState.READY_FOR_REVIEW,
                AgentRunState.READY_FOR_REVIEW_WITH_FAILURES,
                AgentRunState.INTERRUPTING,
                AgentRunState.RECOVERY_REQUIRED,
            )
        )
        placeholders = ",".join("?" for _ in active_states)
        return [
            dict(row)
            for row in self._execute(
                f"SELECT * FROM runs WHERE provider_mode = 'live' "
                f"AND state IN ({placeholders}) ORDER BY created_at",
                active_states,
            ).fetchall()
        ]

    def reconcile_terminal_run(
        self,
        run_id: str,
        state: AgentRunState,
        *,
        ended_at: str,
    ) -> None:
        if state not in {
            AgentRunState.COMPLETED,
            AgentRunState.FAILED,
            AgentRunState.INTERRUPTED,
        }:
            raise ValueError("Reconciliation requires a terminal run state.")
        run = self.run(run_id)
        work_item_state = (
            WorkItemState.COMPLETED
            if state is AgentRunState.COMPLETED
            else WorkItemState.NEEDS_ATTENTION
        )
        validation_status = (
            "not_required"
            if state is AgentRunState.COMPLETED
            and run["validation_status"] == "not_run"
            else run["validation_status"]
        )
        with self._transaction():
            self._execute(
                """
                UPDATE runs
                SET state = ?, validation_status = ?, ended_at = ?
                WHERE run_id = ?
                """,
                (state.value, validation_status, ended_at, run_id),
            )
            self._execute(
                """
                UPDATE queue_entries
                SET state = 'stopped', wait_reason = NULL, updated_at = ?
                WHERE run_id = ? AND state IN ('queued', 'running')
                """,
                (ended_at, run_id),
            )
            self._execute(
                "UPDATE work_items SET state = ?, updated_at = ? "
                "WHERE work_item_id = ?",
                (work_item_state.value, ended_at, run["work_item_id"]),
            )

    def set_queue_wait_reason(
        self,
        run_id: str,
        *,
        wait_reason: str,
        updated_at: str,
    ) -> None:
        with self._transaction():
            cursor = self._execute(
                """
                UPDATE queue_entries
                SET wait_reason = ?, updated_at = ?
                WHERE run_id = ? AND state = 'queued'
                """,
                (wait_reason, updated_at, run_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Run is not queued: {run_id}")

    def claim_queued(self, run_id: str, *, started_at: str) -> dict[str, Any]:
        with self._transaction():
            row = self._execute(
                """
                SELECT q.state AS queue_state, r.*, w.state AS work_item_state
                FROM queue_entries q
                JOIN runs r ON r.run_id = q.run_id
                JOIN work_items w ON w.work_item_id = r.work_item_id
                WHERE q.run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if row is None or row["queue_state"] != "queued":
                raise KeyError(f"Run is not queued: {run_id}")
            if row["provider_mode"] == "live" and any(
                active["run_id"] != run_id for active in self.active_live_runs()
            ):
                raise RuntimeError("Another Live run already owns the worker.")
            validate_transition(
                AgentRunState(row["state"]),
                AgentRunState.PREFLIGHT,
                AGENT_RUN_TRANSITIONS,
            )
            validate_transition(
                WorkItemState(row["work_item_state"]),
                WorkItemState.ACTIVE,
                WORK_ITEM_TRANSITIONS,
            )
            self._execute(
                """
                UPDATE queue_entries
                SET state = 'running', wait_reason = NULL, updated_at = ?
                WHERE run_id = ?
                """,
                (started_at, run_id),
            )
            self._execute(
                "UPDATE runs SET state = ?, started_at = ? WHERE run_id = ?",
                (AgentRunState.PREFLIGHT.value, started_at, run_id),
            )
            self._execute(
                "UPDATE work_items SET state = ?, updated_at = ? "
                "WHERE work_item_id = ?",
                (WorkItemState.ACTIVE.value, started_at, row["work_item_id"]),
            )
        return self.run(run_id)

    def request_stop(self, run_id: str, *, requested_at: str) -> None:
        run = self.run(run_id)
        current = AgentRunState(run["state"])
        if current is AgentRunState.QUEUED:
            self.cancel_queued(run_id, updated_at=requested_at)
            return
        validate_transition(current, AgentRunState.INTERRUPTING, AGENT_RUN_TRANSITIONS)
        with self._transaction():
            self._execute(
                "UPDATE runs SET state = ? WHERE run_id = ?",
                (AgentRunState.INTERRUPTING.value, run_id),
            )
            self._execute(
                """
                UPDATE queue_entries
                SET state = 'stopped', updated_at = ?
                WHERE run_id = ? AND state = 'running'
                """,
                (requested_at, run_id),
            )
            self._execute(
                "UPDATE work_items SET state = ?, updated_at = ? "
                "WHERE work_item_id = ?",
                (
                    WorkItemState.NEEDS_ATTENTION.value,
                    requested_at,
                    run["work_item_id"],
                ),
            )

    def reorder_queue(self, run_ids: tuple[str, ...], *, updated_at: str) -> None:
        current = tuple(record["run_id"] for record in self.queue())
        if len(set(run_ids)) != len(run_ids) or set(run_ids) != set(current):
            raise ValueError("Queue reorder must include each queued run exactly once.")
        with self._transaction():
            for position, run_id in enumerate(run_ids, start=1):
                self._execute(
                    "UPDATE queue_entries SET position = ?, updated_at = ? "
                    "WHERE run_id = ? AND state = 'queued'",
                    (position, updated_at, run_id),
                )

    def cancel_queued(self, run_id: str, *, updated_at: str) -> None:
        with self._transaction():
            cursor = self._execute(
                "UPDATE queue_entries SET state = 'cancelled', updated_at = ? "
                "WHERE run_id = ? AND state = 'queued'",
                (updated_at, run_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Run is not queued: {run_id}")
            run = self.run(run_id)
            self._execute(
                "UPDATE runs SET state = ? WHERE run_id = ?",
                (AgentRunState.INTERRUPTED.value, run_id),
            )
            self._execute(
                "UPDATE work_items SET state = ?, updated_at = ? "
                "WHERE work_item_id = ?",
                (WorkItemState.NEEDS_ATTENTION.value, updated_at, run["work_item_id"]),
            )

    def append_evidence_link(self, link: EngineeringTaskLink) -> int:
        payload = _jsonable(link)
        previous = self._execute(
            "SELECT MAX(revision) FROM evidence_links WHERE link_id = ?",
            (link.link_id,),
        ).fetchone()[0]
        revision = int(previous or 0) + 1
        payload_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        with self._transaction():
            self._execute(
                """
                INSERT INTO evidence_links (
                    link_id, revision, work_item_id, meeting_id,
                    source_item_id, payload_json, payload_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link.link_id,
                    revision,
                    link.work_item_id,
                    link.meeting_id,
                    link.source_item_id,
                    payload_json,
                    digest,
                    link.updated_at,
                ),
            )
        return revision

    def evidence_link_history(self, link_id: str) -> list[dict[str, Any]]:
        return [
            {
                **json.loads(row["payload_json"]),
                "revision": row["revision"],
                "payload_sha256": row["payload_sha256"],
            }
            for row in self._execute(
                "SELECT * FROM evidence_links WHERE link_id = ? ORDER BY revision",
                (link_id,),
            ).fetchall()
        ]

    def store_session_grant(self, grant: RepositorySessionGrant) -> None:
        payload_json = json.dumps(_jsonable(grant), ensure_ascii=False, sort_keys=True)
        with self._transaction():
            self._execute(
                """
                INSERT INTO repository_session_grants (
                    grant_id, repository_id, actor_id, expires_at,
                    revoked_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    grant.grant_id,
                    grant.repository_id,
                    grant.actor_id,
                    grant.expires_at,
                    grant.revoked_at,
                    payload_json,
                ),
            )

    def revoke_repository_grants(
        self,
        repository_id: str,
        *,
        revoked_at: str,
    ) -> int:
        with self._transaction():
            cursor = self._execute(
                """
                UPDATE repository_session_grants
                SET revoked_at = ?
                WHERE repository_id = ? AND revoked_at IS NULL
                """,
                (revoked_at, repository_id),
            )
            return cursor.rowcount

    def create_recovery_record(
        self,
        *,
        recovery_id: str,
        run_id: str,
        status: str,
        reconciliation: Mapping[str, Any],
        created_at: str,
    ) -> None:
        with self._transaction():
            self._execute(
                """
                INSERT INTO recovery_records (
                    recovery_id, run_id, status, reconciliation_json,
                    created_at, resolved_at, resolution
                ) VALUES (?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    recovery_id,
                    run_id,
                    status,
                    json.dumps(_sanitize(reconciliation), ensure_ascii=False),
                    created_at,
                ),
            )

    def recovery_cards(self) -> list[dict[str, Any]]:
        cards = []
        for row in self._execute(
            """
            SELECT rr.*, r.state AS run_state, r.requested_mode, r.workspace_id
            FROM recovery_records rr
            JOIN runs r ON r.run_id = rr.run_id
            WHERE rr.resolved_at IS NULL
            ORDER BY rr.created_at
            """
        ).fetchall():
            card = dict(row)
            card["reconciliation"] = json.loads(
                card.pop("reconciliation_json")
            )
            card["actions"] = ("resume", "inspect", "abandon")
            cards.append(card)
        return cards

    def resolve_recovery(
        self,
        recovery_id: str,
        *,
        resolution: str,
        resolved_at: str,
    ) -> None:
        if resolution not in {"resume", "inspect", "abandon"}:
            raise ValueError("Recovery resolution must be resume, inspect, or abandon.")
        with self._transaction():
            cursor = self._execute(
                """
                UPDATE recovery_records
                SET resolved_at = ?, resolution = ?, status = 'resolved'
                WHERE recovery_id = ? AND resolved_at IS NULL
                """,
                (resolved_at, resolution, recovery_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Unknown or resolved recovery record: {recovery_id}")
            if resolution == "abandon":
                run_id = self._execute(
                    "SELECT run_id FROM recovery_records WHERE recovery_id = ?",
                    (recovery_id,),
                ).fetchone()[0]
                self._execute(
                    "UPDATE runs SET state = ?, ended_at = ? WHERE run_id = ?",
                    (AgentRunState.ABANDONED.value, resolved_at, run_id),
                )

    def index_artifact(self, artifact: Artifact) -> None:
        payload = _jsonable(artifact)
        with self._transaction():
            self._execute(
                """
                INSERT INTO artifact_index (
                    artifact_id, run_id, artifact_type, relative_path,
                    sha256, size_bytes, data_boundary_class, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(
                    payload[key]
                    for key in (
                        "artifact_id",
                        "run_id",
                        "artifact_type",
                        "relative_path",
                        "sha256",
                        "size_bytes",
                        "data_boundary_class",
                        "created_at",
                    )
                ),
            )

    def _repository_record(self, row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["allowed"] = bool(result["allowed"])
        result["allowed_remote_urls"] = json.loads(
            result.pop("allowed_remote_urls_json")
        )
        result["allowed_branch_prefixes"] = json.loads(
            result.pop("allowed_branch_prefixes_json")
        )
        return result

    def _migrate(self) -> None:
        version = int(self._connection.execute("PRAGMA user_version").fetchone()[0])
        if version > CATALOG_SCHEMA_VERSION:
            self.close()
            raise RuntimeError(
                f"Agent catalog schema {version} is newer than supported "
                f"{CATALOG_SCHEMA_VERSION}."
            )
        if version == CATALOG_SCHEMA_VERSION:
            return
        if self._preexisting:
            self.last_migration_backup = self._migration_backup(version)
        if version == 0:
            self._connection.executescript(
                """
                    BEGIN IMMEDIATE;
                    CREATE TABLE repositories (
                        repository_id TEXT PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        canonical_root TEXT NOT NULL UNIQUE,
                        root_fingerprint TEXT NOT NULL,
                        allowed INTEGER NOT NULL CHECK (allowed IN (0, 1)),
                        default_base_branch TEXT,
                        allowed_remote_urls_json TEXT NOT NULL,
                        allowed_branch_prefixes_json TEXT NOT NULL,
                        data_classification TEXT NOT NULL,
                        instruction_policy TEXT NOT NULL,
                        network_policy_id TEXT NOT NULL,
                        command_policy_id TEXT NOT NULL,
                        publication_policy_id TEXT NOT NULL,
                        retention_policy_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE work_items (
                        work_item_id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        title TEXT NOT NULL,
                        objective TEXT NOT NULL,
                        acceptance_criteria_json TEXT NOT NULL,
                        repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
                        workflow_template_id TEXT NOT NULL,
                        requested_mode TEXT NOT NULL,
                        requested_model_profile TEXT NOT NULL,
                        evidence_context_id TEXT,
                        created_by TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        state TEXT NOT NULL
                    );
                    CREATE INDEX work_items_repository_state
                        ON work_items(repository_id, state, updated_at);
                    CREATE TABLE runs (
                        run_id TEXT PRIMARY KEY,
                        work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
                        state TEXT NOT NULL,
                        provider_mode TEXT NOT NULL CHECK (provider_mode IN ('demo', 'live')),
                        requested_model_profile TEXT NOT NULL,
                        requested_mode TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        base_commit TEXT,
                        workspace_id TEXT,
                        resolved_model_id TEXT,
                        resolved_effort TEXT,
                        provider_version TEXT,
                        continuation_of_run_id TEXT REFERENCES runs(run_id),
                        publication_state TEXT NOT NULL,
                        validation_status TEXT NOT NULL,
                        started_at TEXT,
                        ended_at TEXT
                    );
                    CREATE INDEX runs_work_item_state
                        ON runs(work_item_id, state, created_at);
                    CREATE TABLE queue_entries (
                        queue_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT NOT NULL UNIQUE REFERENCES runs(run_id),
                        position INTEGER NOT NULL,
                        state TEXT NOT NULL,
                        run_when_ready INTEGER NOT NULL CHECK (run_when_ready IN (0, 1)),
                        wait_reason TEXT,
                        enqueued_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE UNIQUE INDEX queued_position
                        ON queue_entries(position) WHERE state = 'queued';
                    CREATE TABLE evidence_links (
                        link_id TEXT NOT NULL,
                        revision INTEGER NOT NULL,
                        work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
                        meeting_id TEXT NOT NULL,
                        source_item_id TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        payload_sha256 TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (link_id, revision)
                    );
                    CREATE TABLE repository_session_grants (
                        grant_id TEXT PRIMARY KEY,
                        repository_id TEXT NOT NULL REFERENCES repositories(repository_id),
                        actor_id TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        revoked_at TEXT,
                        payload_json TEXT NOT NULL
                    );
                    CREATE TABLE recovery_records (
                        recovery_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL REFERENCES runs(run_id),
                        status TEXT NOT NULL,
                        reconciliation_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        resolved_at TEXT,
                        resolution TEXT
                    );
                    CREATE TABLE artifact_index (
                        artifact_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL REFERENCES runs(run_id),
                        artifact_type TEXT NOT NULL,
                        relative_path TEXT NOT NULL,
                        sha256 TEXT NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        data_boundary_class TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE INDEX artifact_run_type
                        ON artifact_index(run_id, artifact_type);
                    PRAGMA user_version = 1;
                    COMMIT;
                    """
            )

    def _migration_backup(self, version: int) -> Path:
        base = self.path.with_name(f"{self.path.name}.schema-v{version}.backup")
        backup = base
        suffix = 1
        while backup.exists():
            backup = base.with_name(f"{base.name}.{suffix}")
            suffix += 1
        target = sqlite3.connect(backup)
        try:
            self._connection.backup(target)
        finally:
            target.close()
        return backup

    def _execute(
        self,
        statement: str,
        parameters: tuple[Any, ...] = (),
    ) -> sqlite3.Cursor:
        if self._connection is None:
            raise RuntimeError("Agent catalog is closed.")
        with self._lock:
            return self._connection.execute(statement, parameters)

    class _Transaction:
        def __init__(self, catalog: "AgentCatalog"):
            self.catalog = catalog

        def __enter__(self) -> None:
            self.catalog._lock.acquire()
            self.catalog._connection.execute("BEGIN IMMEDIATE")

        def __exit__(self, exc_type, _exc, _traceback) -> None:
            try:
                self.catalog._connection.execute(
                    "ROLLBACK" if exc_type else "COMMIT"
                )
            finally:
                self.catalog._lock.release()

    def _transaction(self) -> "AgentCatalog._Transaction":
        return self._Transaction(self)


class AgentStorageManager:
    def __init__(
        self,
        *,
        run_root: str | Path,
        worktree_root: str | Path,
        low_disk_threshold_bytes: int,
    ):
        self.run_root = Path(run_root).expanduser().resolve()
        self.worktree_root = Path(worktree_root).expanduser().resolve()
        self.low_disk_threshold_bytes = max(1, low_disk_threshold_bytes)

    def summary(self) -> dict[str, Any]:
        run_bytes = self._directory_size(self.run_root)
        worktree_bytes = self._directory_size(self.worktree_root)
        anchor = next(
            (
                path
                for path in (self.run_root, self.worktree_root)
                if path.exists()
            ),
            self.run_root.parent,
        )
        free_bytes = shutil.disk_usage(anchor).free
        return {
            "run_bytes": run_bytes,
            "worktree_bytes": worktree_bytes,
            "total_bytes": run_bytes + worktree_bytes,
            "free_bytes": free_bytes,
            "low_disk": free_bytes < self.low_disk_threshold_bytes,
            "automatic_deletion": False,
        }

    def cleanup_preview(self, targets: tuple[str | Path, ...]) -> dict[str, Any]:
        roots = (self.run_root, self.worktree_root)
        resolved: list[Path] = []
        for target in targets:
            path = Path(target).expanduser().resolve(strict=True)
            if not any(path == root or path.is_relative_to(root) for root in roots):
                raise ValueError("Cleanup target is outside Agent-owned storage.")
            if path in roots:
                raise ValueError("Cleanup preview requires a specific run or worktree.")
            resolved.append(path)
        return {
            "targets": tuple(str(path) for path in resolved),
            "bytes": sum(self._directory_size(path) for path in resolved),
            "requires_export_choice": True,
            "deleted": False,
        }

    @staticmethod
    def _directory_size(path: Path) -> int:
        if path.is_file():
            return path.stat().st_size
        if not path.exists():
            return 0
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
