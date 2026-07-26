from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import datetime as dt
from dataclasses import dataclass
from pathlib import Path

from aura.agent.policy import PathPolicy, path_has_sensitive_component


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class WorktreeContext:
    path: Path
    repository: Path
    base_commit: str
    base_branch: str | None
    branch: str
    source_dirty: bool
    omitted_dirty_paths: tuple[str, ...]
    submodules: str
    lfs: str


class WorktreeManager:
    """Creates agent-branch worktrees without touching source checkout content."""

    def __init__(
        self,
        repository: str | Path,
        root: str | Path,
        path_policy: PathPolicy,
        *,
        minimum_free_bytes: int = 256 * 1024 * 1024,
    ):
        self.path_policy = path_policy
        self.repository = path_policy.validate_repository(repository)
        self.root = path_policy.validate_worktree_root(root)
        self.minimum_free_bytes = max(1, minimum_free_bytes)
        if self.root == self.repository or self.root.is_relative_to(self.repository):
            raise ValueError("Agent worktrees must live outside the source repository.")

    def create(
        self,
        run_id: str,
        *,
        base_ref: str = "HEAD",
        slug: str = "task",
    ) -> WorktreeContext:
        if not RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError("Run ID is not safe for a worktree path.")
        dirty_lines = tuple(
            line
            for line in self._git(
                "status",
                "--porcelain=v1",
                "--untracked-files=normal",
            ).splitlines()
            if line
        )
        base_commit = self._git("rev-parse", "--verify", f"{base_ref}^{{commit}}")
        branch = self._git_optional("symbolic-ref", "--quiet", "--short", "HEAD") or None
        agent_branch = self._available_branch(run_id, slug)
        repository_id = (
            f"{self.repository.name}-"
            f"{hashlib.sha256(str(self.repository).encode()).hexdigest()[:10]}"
        )
        target = self.root / repository_id / run_id
        if target.exists():
            raise FileExistsError(f"Agent worktree path already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(target.parent).free < self.minimum_free_bytes:
            raise OSError("The configured Agent worktree root has insufficient free space.")
        environment = os.environ.copy()
        environment["GIT_LFS_SKIP_SMUDGE"] = "1"
        self._git(
            "worktree",
            "add",
            "-b",
            agent_branch,
            str(target),
            base_commit,
            environment=environment,
        )
        resolved = target.resolve(strict=True)
        if resolved == self.repository or resolved.is_relative_to(self.repository):
            raise RuntimeError("Git created a worktree inside the source repository.")
        return WorktreeContext(
            path=resolved,
            repository=self.repository,
            base_commit=base_commit,
            base_branch=branch,
            branch=agent_branch,
            source_dirty=bool(dirty_lines),
            omitted_dirty_paths=tuple(line[3:] for line in dirty_lines),
            submodules="registered_only_no_recursive_update"
            if (self.repository / ".gitmodules").exists()
            else "not_declared",
            lfs="smudge_disabled_no_automatic_pull",
        )

    def _available_branch(self, run_id: str, slug: str) -> str:
        short_run_id = re.sub(r"[^a-z0-9]+", "", run_id.casefold())[-10:] or "run"
        safe_slug = re.sub(r"[^a-z0-9]+", "-", slug.casefold()).strip("-")[:32] or "task"
        prefix = dt.datetime.now().astimezone().strftime(
            f"aura-agent/%Y%m%d/{short_run_id}-{safe_slug}"
        )
        candidate = prefix
        suffix = 2
        while self._git_optional(
            "show-ref",
            "--verify",
            f"refs/heads/{candidate}",
        ):
            candidate = f"{prefix}-{suffix}"
            suffix += 1
        return candidate

    def export_patch(self, context: WorktreeContext, destination: str | Path) -> Path:
        if context.repository != self.repository:
            raise ValueError("Worktree context belongs to another repository.")
        worktree = context.path.resolve(strict=True)
        self.path_policy.validate_write(worktree, worktree)
        result = subprocess.run(
            ["git", "-C", str(worktree), "diff", "--binary", "--no-ext-diff", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode:
            raise RuntimeError(f"Git patch export failed: {result.stderr.strip()}")
        target = Path(destination).expanduser().resolve()
        if path_has_sensitive_component(target):
            raise ValueError("Patch export cannot use a sensitive path.")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(result.stdout, encoding="utf-8")
        os.replace(temporary, target)
        return target

    def _git(self, *arguments: str, environment=None) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repository), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        )
        if result.returncode:
            raise RuntimeError(
                f"Git command failed ({' '.join(arguments)}): {result.stderr.strip()}"
            )
        return result.stdout.strip()

    def _git_optional(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repository), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
