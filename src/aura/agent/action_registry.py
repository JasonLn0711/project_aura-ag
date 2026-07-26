from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ActionHandler = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class RegisteredAction:
    action_id: str
    label: str
    consequence: str
    handler: ActionHandler | None
    enabled: bool = True


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, RegisteredAction] = {}

    def register(self, action: RegisteredAction) -> None:
        if action.action_id in self._actions:
            raise ValueError(f"Action is already registered: {action.action_id}")
        if action.consequence not in {"read", "write", "external", "destructive"}:
            raise ValueError(f"Unsupported action consequence: {action.consequence}")
        self._actions[action.action_id] = action

    def resolve(self, action_id: str) -> RegisteredAction:
        return self._actions.get(
            action_id,
            RegisteredAction(
                action_id=action_id,
                label="Unavailable action",
                consequence="unknown",
                handler=None,
                enabled=False,
            ),
        )

    def invoke(self, action_id: str, context: dict[str, Any]) -> None:
        action = self.resolve(action_id)
        if not action.enabled or action.handler is None:
            raise ValueError(f"Action is not available: {action_id}")
        action.handler(context)
