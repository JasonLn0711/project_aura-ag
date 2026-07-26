from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from aura.agent.policy import path_has_sensitive_component, sanitize_remote_url
from aura.agent.worktree import WorktreeContext
from aura.redaction import CREDENTIAL_PATTERNS, redact_sensitive_text


AGENT_BRANCH = re.compile(r"^aura-agent/\d{8}/[a-z0-9][a-z0-9-]*$")
REMOTE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


class PublicationBlocked(RuntimeError):
    pass


class PublicationFailed(RuntimeError):
    def __init__(self, message: str, *, retained_commit: str | None = None):
        super().__init__(message)
        self.retained_commit = retained_commit


@dataclass(frozen=True)
class PublicationEvidence:
    branch: str
    base_commit: str
    commit_sha: str | None
    diff_sha256: str | None
    remote_name: str | None
    remote_url: str | None
    pull_request_url: str | None
    secret_fingerprints: tuple[str, ...]


def build_pr_body(
    *,
    objective: str,
    validation: tuple[str, ...],
    risks: tuple[str, ...],
    run_id: str,
    evidence_reference: str | None = None,
) -> str:
    safe_objective = redact_sensitive_text(objective)
    safe_validation = tuple(redact_sensitive_text(item) for item in validation)
    safe_risks = tuple(redact_sensitive_text(item) for item in risks)
    lines = [
        "## Objective",
        safe_objective,
        "",
        "## Validation",
        *(f"- {item}" for item in safe_validation),
        "",
        "## Risks and stewardship",
        *(f"- {item}" for item in safe_risks),
        "",
        "## AURA linkage",
        f"- Run: `{run_id}`",
    ]
    if evidence_reference:
        lines.append(f"- Evidence: `{evidence_reference}` (opaque local reference)")
    return "\n".join(lines).rstrip() + "\n"


class PublicationManager:
    """Explicit agent-branch commit, push, and PR lifecycle."""

    def __init__(
        self,
        context: WorktreeContext,
        *,
        allowed_remote_urls: tuple[str, ...],
        explicit_publish: bool,
        evidence_required: bool = False,
        evidence_freshness_check: Callable[[], bool] | None = None,
    ):
        self.context = context
        self.worktree = context.path.resolve(strict=True)
        self.allowed_remote_urls = allowed_remote_urls
        self.explicit_publish = explicit_publish
        self.evidence_required = evidence_required
        self.evidence_freshness_check = evidence_freshness_check
        self._commit_sha: str | None = None
        self._diff_sha256: str | None = None
        self._secret_fingerprints: tuple[str, ...] = ()
        self._verify_branch()

    def commit(
        self,
        *,
        message: str,
        run_id: str,
        validation_status: str,
    ) -> PublicationEvidence:
        self._preflight(validation_status=validation_status)
        findings = self._scan_changed_files()
        self._secret_fingerprints = tuple(
            sorted({fingerprint for _path, fingerprint in findings})
        )
        if findings:
            raise PublicationBlocked(
                "Commit blocked because changed files contain credential-like content."
            )
        self._git("add", "-A")
        staged = self._git("diff", "--cached", "--binary", "--no-ext-diff")
        if not staged:
            raise PublicationBlocked("No implementation changes are staged.")
        self._diff_sha256 = hashlib.sha256(staged.encode("utf-8")).hexdigest()
        safe_message = " ".join(message.split()).strip()
        if not safe_message:
            raise ValueError("Commit message is required.")
        self._git(
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgSign=false",
            "commit",
            "--no-verify",
            "-m",
            safe_message,
            "-m",
            f"AURA-Run-ID: {run_id}",
        )
        self._commit_sha = self._git("rev-parse", "HEAD")
        return self.evidence()

    def readiness(self, *, validation_status: str) -> tuple[bool, str]:
        try:
            self._preflight(validation_status=validation_status)
            if self._scan_changed_files():
                return False, "changed_file_secret_finding"
        except (OSError, RuntimeError, ValueError) as error:
            return False, str(error)
        return True, "ready"

    def remote_allowed(self, remote_name: str) -> bool:
        if not REMOTE_NAME.fullmatch(remote_name):
            return False
        try:
            remote_url = sanitize_remote_url(
                self._git("remote", "get-url", remote_name)
            )
        except RuntimeError:
            return False
        return remote_url in {
            sanitize_remote_url(value) for value in self.allowed_remote_urls
        }

    def push(self, remote_name: str, *, validation_status: str) -> PublicationEvidence:
        self._preflight(validation_status=validation_status)
        if self._commit_sha is None:
            self._commit_sha = self._git("rev-parse", "HEAD")
        if not REMOTE_NAME.fullmatch(remote_name):
            raise PublicationBlocked("Remote name is outside the publication contract.")
        remote_url = sanitize_remote_url(
            self._git("remote", "get-url", remote_name)
        )
        if remote_url not in {
            sanitize_remote_url(value) for value in self.allowed_remote_urls
        }:
            raise PublicationBlocked("Publication remote is not allowlisted.")
        if self._scan_changed_files():
            raise PublicationBlocked("Push blocked by a changed-file secret scan.")
        try:
            self._git(
                "-c",
                "core.hooksPath=/dev/null",
                "push",
                "--porcelain",
                "--no-verify",
                remote_name,
                f"HEAD:refs/heads/{self.context.branch}",
                timeout=120,
            )
        except RuntimeError as exc:
            raise PublicationFailed(
                "Agent-branch push failed; the local implementation commit is retained.",
                retained_commit=self._commit_sha,
            ) from exc
        return self.evidence(remote_name=remote_name, remote_url=remote_url)

    def open_pull_request(
        self,
        *,
        remote_name: str,
        base_branch: str,
        title: str,
        body: str,
        validation_status: str,
    ) -> PublicationEvidence:
        published = self.push(remote_name, validation_status=validation_status)
        gh = shutil.which("gh")
        if gh is None:
            raise PublicationFailed(
                "GitHub CLI is unavailable; the pushed agent branch is retained.",
                retained_commit=self._commit_sha,
            )
        if base_branch in {"main", "master"}:
            target = base_branch
        elif not re.fullmatch(r"[A-Za-z0-9._/-]+", base_branch):
            raise PublicationBlocked("Pull-request base branch is invalid.")
        else:
            target = base_branch
        with tempfile.TemporaryDirectory(prefix="aura-pr-") as temporary:
            body_file = Path(temporary) / "body.md"
            body_file.write_text(redact_sensitive_text(body), encoding="utf-8")
            os.chmod(body_file, 0o600)
            result = subprocess.run(
                [
                    gh,
                    "pr",
                    "create",
                    "--head",
                    self.context.branch,
                    "--base",
                    target,
                    "--title",
                    " ".join(title.split()),
                    "--body-file",
                    str(body_file),
                ],
                cwd=self.worktree,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
        if result.returncode:
            raise PublicationFailed(
                "Pull-request creation failed; the pushed agent branch is retained.",
                retained_commit=self._commit_sha,
            )
        match = re.search(r"https://\S+", result.stdout)
        return PublicationEvidence(
            **{
                **published.__dict__,
                "pull_request_url": match.group(0) if match else None,
            }
        )

    def evidence(
        self,
        *,
        remote_name: str | None = None,
        remote_url: str | None = None,
    ) -> PublicationEvidence:
        return PublicationEvidence(
            branch=self.context.branch,
            base_commit=self.context.base_commit,
            commit_sha=self._commit_sha,
            diff_sha256=self._diff_sha256,
            remote_name=remote_name,
            remote_url=remote_url,
            pull_request_url=None,
            secret_fingerprints=self._secret_fingerprints,
        )

    def _preflight(self, *, validation_status: str) -> None:
        if not self.explicit_publish:
            raise PublicationBlocked("Publication requires the explicit Publish stage.")
        self._verify_branch()
        if validation_status != "passed":
            raise PublicationBlocked("Required validation must pass before publication.")
        if self.evidence_required and (
            self.evidence_freshness_check is None
            or not self.evidence_freshness_check()
        ):
            raise PublicationBlocked(
                "Evidence freshness must be revalidated before publication."
            )

    def _verify_branch(self) -> None:
        if not AGENT_BRANCH.fullmatch(self.context.branch):
            raise PublicationBlocked("Publication is limited to an AURA agent branch.")
        current = self._git("branch", "--show-current")
        if current != self.context.branch or current in {"main", "master"}:
            raise PublicationBlocked("The active worktree is not on its agent branch.")

    def _scan_changed_files(self) -> tuple[tuple[str, str], ...]:
        paths = set(
            self._git(
                "diff",
                "--name-only",
                self.context.base_commit,
                "HEAD",
            ).splitlines()
        )
        for line in self._git(
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
        ).splitlines():
            relative = line[3:].split(" -> ")[-1]
            if relative:
                paths.add(relative)
        findings: list[tuple[str, str]] = []
        for relative in sorted(paths):
            path = (self.worktree / relative).resolve(strict=False)
            if (
                path != self.worktree
                and not path.is_relative_to(self.worktree)
            ) or path_has_sensitive_component(path):
                findings.append((relative, hashlib.sha256(relative.encode()).hexdigest()))
                continue
            if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
                continue
            text = path.read_bytes().decode("utf-8", errors="ignore")
            if any(pattern.search(text) for pattern in CREDENTIAL_PATTERNS):
                findings.append(
                    (
                        relative,
                        hashlib.sha256(
                            f"credential:{relative}".encode("utf-8")
                        ).hexdigest(),
                    )
                )
        return tuple(findings)

    def _git(self, *arguments: str, timeout: int = 30) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.worktree), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode:
            raise RuntimeError(
                f"Git publication step failed: {arguments[0] if arguments else 'git'}."
            )
        return result.stdout.strip()
