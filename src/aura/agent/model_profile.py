from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from aura.agent.contracts import ProviderModel


EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max", "ultra")


@dataclass(frozen=True)
class ModelResolution:
    requested_profile: str
    model_id: str | None
    display_name: str | None
    reasoning_effort: str | None
    requires_fallback_approval: bool
    blocked_reason: str | None = None
    candidate_model_ids: tuple[str, ...] = ()
    max_wall_clock_minutes: int = 30
    max_turns: int = 12
    max_repair_loops: int = 2


PROFILE_BUDGETS = {
    "quick": (10, 6, 1),
    "standard": (30, 12, 2),
    "expert": (90, 24, 2),
    "sol-ultra": (90, 24, 2),
}


def _blocked(
    profile: str,
    models: tuple[ProviderModel, ...],
    reason: str,
) -> ModelResolution:
    wall_clock, turns, repairs = PROFILE_BUDGETS[profile]
    return ModelResolution(
        requested_profile=profile,
        model_id=None,
        display_name=None,
        reasoning_effort=None,
        requires_fallback_approval=True,
        blocked_reason=reason,
        candidate_model_ids=tuple(model.model_id for model in models),
        max_wall_clock_minutes=wall_clock,
        max_turns=turns,
        max_repair_loops=repairs,
    )


def _resolved(
    profile: str,
    model: ProviderModel,
    effort: str,
) -> ModelResolution:
    wall_clock, turns, repairs = PROFILE_BUDGETS[profile]
    return ModelResolution(
        requested_profile=profile,
        model_id=model.model_id,
        display_name=model.display_name,
        reasoning_effort=effort,
        requires_fallback_approval=False,
        candidate_model_ids=(model.model_id,),
        max_wall_clock_minutes=wall_clock,
        max_turns=turns,
        max_repair_loops=repairs,
    )


def resolve_model_profile(
    requested_profile: str,
    models: Iterable[ProviderModel],
) -> ModelResolution:
    profile = requested_profile.strip().lower()
    if profile not in PROFILE_BUDGETS:
        raise ValueError(f"Unknown model profile: {requested_profile}")
    available = tuple(models)
    if not available:
        return _blocked(profile, available, "The provider advertised no models.")

    if profile in {"expert", "sol-ultra"}:
        selected = next(
            (
                model
                for target in ("gpt-5.6-sol", "gpt-5.6")
                for model in available
                if model.model_id == target
            ),
            None,
        )
        if selected is None:
            return _blocked(
                profile,
                available,
                "The provider does not advertise gpt-5.6-sol or gpt-5.6.",
            )
        if "max" not in selected.supported_reasoning_efforts:
            return _blocked(
                profile,
                available,
                "Expert requires an advertised max reasoning effort.",
            )
        return _resolved(profile, selected, "max")

    selected = next((model for model in available if model.is_default), None)
    if selected is None:
        return _blocked(
            profile,
            available,
            "The provider did not identify a default model; choose a candidate explicitly.",
        )
    effort_preferences = (
        ("low", "medium")
        if profile == "quick"
        else ("medium", "high")
    )
    effort = next(
        (
            candidate
            for candidate in effort_preferences
            if candidate in selected.supported_reasoning_efforts
        ),
        None,
    )
    if effort is None:
        return _blocked(
            profile,
            available,
            f"The default model does not advertise a {profile} effort.",
        )
    return _resolved(profile, selected, effort)


def resolve_sol_ultra(models: Iterable[ProviderModel]) -> ModelResolution:
    return resolve_model_profile("sol-ultra", models)
