from __future__ import annotations

from typing import Protocol

from aura.agent.contracts import ProviderModel


class AgentProvider(Protocol):
    provider_id: str

    def start(self) -> None: ...

    def shutdown(self) -> None: ...

    def list_models(self) -> tuple[ProviderModel, ...]: ...

    def interrupt_turn(self, thread_id: str, turn_id: str) -> None: ...

    def resolve_approval(self, request_id: str, decision: str) -> None: ...
