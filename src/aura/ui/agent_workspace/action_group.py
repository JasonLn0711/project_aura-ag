from __future__ import annotations

from typing import Any


class WorkspaceActionGroup:
    """Focused use-case group sharing one presentation context."""

    def __init__(self, view: Any) -> None:
        object.__setattr__(self, "_view", view)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_view"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, "_view"), name, value)
