from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentUiPreferences:
    selected_repository_id: str | None = None
    selected_thread_id: str | None = None
    sidebar_width: int = 264
    sidebar_collapsed: bool = False
    inspector_width: int = 420
    last_artifact: str | None = None
    enter_sends: bool = True
    reduced_motion: bool = False
    reduced_transparency: bool = False
    recent_workflows: tuple[str, ...] = ()
    thread_drafts: tuple[tuple[str, str], ...] = ()
    pinned_thread_ids: tuple[str, ...] = ()
    deleted_thread_ids: tuple[str, ...] = ()


class AgentUiPreferenceStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.last_error: str | None = None

    def load(self) -> AgentUiPreferences:
        self.last_error = None
        if not self.path.exists():
            return AgentUiPreferences()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("schema_version") not in {1, 2}:
                raise ValueError("Unsupported Agent UI preference schema.")
            allowed = AgentUiPreferences.__dataclass_fields__.keys()
            values = {key: payload[key] for key in allowed if key in payload}
            values["recent_workflows"] = tuple(
                values.get("recent_workflows", ())
            )
            values["thread_drafts"] = tuple(
                (str(key), str(value))
                for key, value in values.get("thread_drafts", ())
            )
            values["pinned_thread_ids"] = tuple(
                str(value)
                for value in values.get("pinned_thread_ids", ())
            )
            values["deleted_thread_ids"] = tuple(
                str(value)
                for value in values.get("deleted_thread_ids", ())
            )
            return AgentUiPreferences(**values)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            self.last_error = str(error)
            return AgentUiPreferences()

    def save(self, preferences: AgentUiPreferences) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": 2, **asdict(preferences)}
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(payload, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
