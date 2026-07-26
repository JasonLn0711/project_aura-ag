import os
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aura.agent.policy import PathPolicy
from aura.agent.publication import (
    PublicationBlocked,
    PublicationFailed,
    PublicationManager,
    build_pr_body,
)
from aura.agent.worktree import WorktreeManager


def git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", repository, *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class PublicationManagerTests(unittest.TestCase):
    def repository(self, root: Path):
        source = root / "source"
        remote = root / "remote.git"
        source.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", source], check=True)
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        git(source, "config", "user.email", "test@example.invalid")
        git(source, "config", "user.name", "AURA Test")
        (source / "README.md").write_text("baseline\n", encoding="utf-8")
        git(source, "add", "README.md")
        git(source, "commit", "-qm", "baseline")
        git(source, "remote", "add", "origin", str(remote))
        manager = WorktreeManager(
            source,
            root / "worktrees",
            PathPolicy((root,)),
            minimum_free_bytes=1,
        )
        return source, remote, manager.create("run-1234567890", slug="publish")

    def test_validated_commit_and_allowlisted_agent_branch_push_skip_local_hooks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, remote, context = self.repository(root)
            sentinel = root / "hook-ran"
            hook = source / ".git" / "hooks" / "pre-commit"
            hook.write_text(
                f"#!/bin/sh\nprintf unsafe > {sentinel}\nexit 1\n",
                encoding="utf-8",
            )
            os.chmod(hook, 0o755)
            (context.path / "README.md").write_text(
                "validated implementation\n",
                encoding="utf-8",
            )
            publication = PublicationManager(
                context,
                allowed_remote_urls=(str(remote),),
                explicit_publish=True,
            )

            committed = publication.commit(
                message="feat: validated agent change",
                run_id="run-1234567890",
                validation_status="passed",
            )
            pushed = publication.push("origin", validation_status="passed")

            self.assertFalse(sentinel.exists())
            self.assertEqual(committed.commit_sha, git(context.path, "rev-parse", "HEAD"))
            self.assertIn(
                "AURA-Run-ID: run-1234567890",
                git(context.path, "log", "-1", "--format=%B"),
            )
            self.assertEqual(pushed.remote_url, str(remote))
            self.assertIn(
                f"refs/heads/{context.branch}",
                git(remote, "show-ref"),
            )
            self.assertEqual(
                (source / "README.md").read_text(encoding="utf-8"),
                "baseline\n",
            )

    def test_publish_gates_validation_freshness_remote_and_credentials(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _source, remote, context = self.repository(root)
            (context.path / "feature.txt").write_text("safe\n", encoding="utf-8")
            stale = PublicationManager(
                context,
                allowed_remote_urls=(str(remote),),
                explicit_publish=True,
                evidence_required=True,
                evidence_freshness_check=lambda: False,
            )
            with self.assertRaisesRegex(PublicationBlocked, "freshness"):
                stale.commit(
                    message="feat: stale",
                    run_id="run-stale",
                    validation_status="passed",
                )

            (context.path / "feature.txt").write_text(
                "api_key=sk-abcdefghijklmnopqrstuv\n",
                encoding="utf-8",
            )
            secret = PublicationManager(
                context,
                allowed_remote_urls=(str(remote),),
                explicit_publish=True,
            )
            with self.assertRaisesRegex(PublicationBlocked, "credential-like"):
                secret.commit(
                    message="feat: unsafe",
                    run_id="run-secret",
                    validation_status="passed",
                )
            self.assertEqual(git(context.path, "rev-parse", "HEAD"), context.base_commit)

    def test_readiness_and_remote_allowlist_drive_contextual_publish_actions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _source, remote, context = self.repository(root)
            (context.path / "feature.txt").write_text("safe\n", encoding="utf-8")
            publication = PublicationManager(
                context,
                allowed_remote_urls=(str(remote),),
                explicit_publish=True,
            )

            self.assertEqual(
                publication.readiness(validation_status="passed"),
                (True, "ready"),
            )
            self.assertEqual(
                publication.readiness(validation_status="failed")[0],
                False,
            )
            self.assertTrue(publication.remote_allowed("origin"))
            self.assertFalse(publication.remote_allowed("../origin"))
            self.assertFalse(publication.remote_allowed("missing"))

            (context.path / "feature.txt").write_text(
                "api_key=sk-abcdefghijklmnopqrstuv\n",
                encoding="utf-8",
            )
            self.assertEqual(
                publication.readiness(validation_status="passed"),
                (False, "changed_file_secret_finding"),
            )

    def test_push_failure_retains_successful_local_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _source, _remote, context = self.repository(root)
            missing = root / "missing.git"
            git(context.path, "remote", "add", "broken", str(missing))
            (context.path / "README.md").write_text("local result\n", encoding="utf-8")
            publication = PublicationManager(
                context,
                allowed_remote_urls=(str(missing),),
                explicit_publish=True,
            )
            committed = publication.commit(
                message="feat: retained",
                run_id="run-retained",
                validation_status="passed",
            )

            with self.assertRaises(PublicationFailed) as captured:
                publication.push("broken", validation_status="passed")

            self.assertEqual(captured.exception.retained_commit, committed.commit_sha)
            self.assertEqual(git(context.path, "rev-parse", "HEAD"), committed.commit_sha)

    def test_pr_body_redacts_contact_data_and_uses_opaque_evidence_link(self):
        body = build_pr_body(
            objective="Deliver the queue for private@example.invalid.",
            validation=("Unit tests passed.",),
            risks=("Rollback uses the retained branch.",),
            run_id="run-opaque",
            evidence_reference="evidence-9d91",
        )

        self.assertNotIn("private@example.invalid", body)
        self.assertIn("[REDACTED_EMAIL]", body)
        self.assertIn("evidence-9d91", body)
        self.assertNotIn("meeting transcript", body.lower())
