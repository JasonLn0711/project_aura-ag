from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from importlib.resources import files
from typing import Any


VERSION_PATTERN = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")


@dataclass(frozen=True)
class CodexCompatibility:
    installed_version: str | None
    status: str
    reason: str
    manifest: dict[str, Any]

    @property
    def live_allowed(self) -> bool:
        return self.status == "compatible"


def compatibility_manifest() -> dict[str, Any]:
    resource = files("aura.agent.providers").joinpath("codex_compatibility.json")
    value = json.loads(resource.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("Unsupported Codex compatibility manifest.")
    return value


def _version(value: str) -> tuple[int, int, int] | None:
    match = VERSION_PATTERN.search(value)
    return tuple(map(int, match.groups())) if match else None


def assess_version(version_output: str) -> CodexCompatibility:
    manifest = compatibility_manifest()
    observed = _version(version_output)
    minimum = _version(str(manifest["minimum_cli_version"]))
    maximum = _version(str(manifest["maximum_cli_version_exclusive"]))
    if observed is None or minimum is None or maximum is None:
        return CodexCompatibility(
            installed_version=None,
            status="incompatible",
            reason="Codex version output could not be validated.",
            manifest=manifest,
        )
    installed = ".".join(map(str, observed))
    if not minimum <= observed < maximum:
        return CodexCompatibility(
            installed_version=installed,
            status="incompatible",
            reason=(
                "Installed Codex is outside the tested compatibility range "
                f"{manifest['minimum_cli_version']}–"
                f"<{manifest['maximum_cli_version_exclusive']}."
            ),
            manifest=manifest,
        )
    return CodexCompatibility(
        installed_version=installed,
        status="version_compatible",
        reason="Installed Codex is inside the tested compatibility range.",
        manifest=manifest,
    )


def discover_version(program: str, *, timeout_seconds: float = 5.0) -> CodexCompatibility:
    try:
        result = subprocess.run(
            [program, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        manifest = compatibility_manifest()
        return CodexCompatibility(
            installed_version=None,
            status="incompatible",
            reason=f"Codex version discovery failed: {type(exc).__name__}.",
            manifest=manifest,
        )
    if result.returncode:
        manifest = compatibility_manifest()
        return CodexCompatibility(
            installed_version=None,
            status="incompatible",
            reason="Codex version discovery returned a non-zero exit status.",
            manifest=manifest,
        )
    return assess_version(result.stdout or result.stderr)
