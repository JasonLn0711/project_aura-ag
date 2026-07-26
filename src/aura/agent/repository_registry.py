from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from aura.agent.contracts import RepositoryProfile
from aura.agent.persistence import AgentCatalog
from aura.agent.policy import PathPolicy, sanitize_remote_url


@dataclass(frozen=True)
class RepositoryInspection:
    canonical_root: Path
    repository_id: str
    display_name: str
    root_fingerprint: str
    current_branch: str | None
    default_branch: str | None
    head_commit: str
    dirty_paths: tuple[str, ...]
    remote_urls: tuple[str, ...]
    submodules: str
    lfs: str
    package_managers: tuple[str, ...]
    instruction_files: tuple[tuple[str, str], ...]
    trust_summary: tuple[str, ...]


class RepositoryRegistry:
    def __init__(
        self,
        catalog: AgentCatalog,
        path_policy: PathPolicy,
    ):
        self.catalog = catalog
        self.path_policy = path_policy

    def inspect(self, candidate: str | Path) -> RepositoryInspection:
        root = self.path_policy.validate_repository(candidate)
        stat = root.stat()
        fingerprint_source = (
            f"{root}\0{stat.st_dev}\0{stat.st_ino}".encode("utf-8")
        )
        root_fingerprint = hashlib.sha256(fingerprint_source).hexdigest()
        repository_id = (
            f"{root.name.lower().replace(' ', '-')}-"
            f"{root_fingerprint[:12]}"
        )
        current_branch = self._git_optional(
            root,
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
        )
        default_branch = self._default_branch(root, current_branch)
        remotes = tuple(
            sanitize_remote_url(line)
            for line in self._git_optional(
                root,
                "remote",
                "get-url",
                "--all",
                "origin",
            ).splitlines()
            if line
        )
        dirty_paths = tuple(
            line[3:]
            for line in self._git(root, "status", "--porcelain=v1").splitlines()
            if len(line) > 3
        )
        instruction_files = tuple(
            (
                relative,
                hashlib.sha256((root / relative).read_bytes()).hexdigest(),
            )
            for relative in (
                "AGENTS.md",
                "CLAUDE.md",
                "GEMINI.md",
                ".github/copilot-instructions.md",
            )
            if (root / relative).is_file()
        )
        package_managers = tuple(
            manager
            for manager, markers in (
                ("uv", ("uv.lock",)),
                ("python", ("pyproject.toml", "requirements.txt")),
                ("npm", ("package-lock.json",)),
                ("pnpm", ("pnpm-lock.yaml",)),
                ("yarn", ("yarn.lock",)),
                ("cargo", ("Cargo.lock",)),
                ("go", ("go.mod",)),
            )
            if any((root / marker).exists() for marker in markers)
        )
        lfs = (
            "declared_smudge_disabled_by_agent"
            if (root / ".gitattributes").is_file()
            and "filter=lfs"
            in (root / ".gitattributes").read_text(
                encoding="utf-8",
                errors="replace",
            )
            else "not_declared"
        )
        submodules = (
            "registered_no_automatic_update"
            if (root / ".gitmodules").is_file()
            else "not_declared"
        )
        trust_summary = (
            f"Git repository at repo://{repository_id}",
            f"Base commit {self._git(root, 'rev-parse', 'HEAD')}",
            f"{len(dirty_paths)} dirty path(s) omitted from write worktrees",
            f"{len(instruction_files)} instruction file(s) require hash-bound trust",
            "Git hooks are never executed during inspection",
        )
        return RepositoryInspection(
            canonical_root=root,
            repository_id=repository_id,
            display_name=root.name,
            root_fingerprint=root_fingerprint,
            current_branch=current_branch or None,
            default_branch=default_branch,
            head_commit=self._git(root, "rev-parse", "HEAD"),
            dirty_paths=dirty_paths,
            remote_urls=remotes,
            submodules=submodules,
            lfs=lfs,
            package_managers=package_managers,
            instruction_files=instruction_files,
            trust_summary=trust_summary,
        )

    def confirm_add(
        self,
        inspection: RepositoryInspection,
        *,
        preset: str = "standard",
        now: str | None = None,
    ) -> RepositoryProfile:
        if preset not in {"conservative", "standard", "team-ready", "custom"}:
            raise ValueError(f"Unsupported repository policy preset: {preset}")
        current = now or dt.datetime.now().astimezone().isoformat(
            timespec="milliseconds"
        )
        profile = RepositoryProfile(
            repository_id=inspection.repository_id,
            display_name=inspection.display_name,
            canonical_root=str(inspection.canonical_root),
            root_fingerprint=inspection.root_fingerprint,
            allowed=True,
            default_base_branch=inspection.default_branch,
            allowed_remote_urls=inspection.remote_urls,
            allowed_branch_prefixes=("aura-agent/",),
            data_classification="internal_source",
            instruction_policy="approve_hash_bound",
            network_policy_id=f"network-{preset}",
            command_policy_id=f"command-{preset}",
            publication_policy_id=f"publication-{preset}",
            retention_policy_id="manual",
            created_at=current,
            updated_at=current,
        )
        self.catalog.register_repository(profile)
        return profile

    def remove(
        self,
        repository_id: str,
        *,
        now: str | None = None,
    ) -> None:
        self.catalog.set_repository_allowed(
            repository_id,
            allowed=False,
            updated_at=now
            or dt.datetime.now().astimezone().isoformat(timespec="milliseconds"),
        )

    def portable_export(self) -> dict[str, object]:
        repositories = []
        for record in self.catalog.repositories():
            repositories.append(
                {
                    "repository_id": record["repository_id"],
                    "display_name": record["display_name"],
                    "path_alias": f"repo://{record['repository_id']}",
                    "root_fingerprint": record["root_fingerprint"],
                    "allowed": record["allowed"],
                    "default_base_branch": record["default_base_branch"],
                    "allowed_remote_urls": record["allowed_remote_urls"],
                    "allowed_branch_prefixes": record["allowed_branch_prefixes"],
                    "data_classification": record["data_classification"],
                    "instruction_policy": record["instruction_policy"],
                    "network_policy_id": record["network_policy_id"],
                    "command_policy_id": record["command_policy_id"],
                    "publication_policy_id": record["publication_policy_id"],
                    "retention_policy_id": record["retention_policy_id"],
                }
            )
        return {
            "schema_version": 1,
            "repositories": repositories,
            "credentials": None,
            "requires_path_remap_on_import": True,
        }

    @staticmethod
    def export_json(payload: dict[str, object]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)

    @staticmethod
    def _git(root: Path, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), "-c", "core.hooksPath=/dev/null", *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode:
            raise RuntimeError(
                f"Git repository inspection failed: {result.stderr.strip()}"
            )
        return result.stdout.strip()

    @classmethod
    def _git_optional(cls, root: Path, *arguments: str) -> str:
        try:
            return cls._git(root, *arguments)
        except RuntimeError:
            return ""

    @classmethod
    def _default_branch(
        cls,
        root: Path,
        current_branch: str,
    ) -> str | None:
        origin_head = cls._git_optional(
            root,
            "symbolic-ref",
            "--quiet",
            "--short",
            "refs/remotes/origin/HEAD",
        )
        if origin_head.startswith("origin/"):
            return origin_head.removeprefix("origin/")
        for candidate in ("main", "master"):
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "core.hooksPath=/dev/null",
                    "show-ref",
                    "--verify",
                    "--quiet",
                    f"refs/heads/{candidate}",
                ],
                check=False,
            )
            if result.returncode == 0:
                return candidate
        return current_branch or None
