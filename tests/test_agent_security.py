import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aura.agent.action_registry import ActionRegistry
from aura.agent.config import AgentConfig
from aura.agent.model_profile import resolve_sol_ultra
from aura.agent.persistence import AgentRunStore
from aura.agent.policy import CommandPolicy, PathPolicy
from aura.agent.reporting import ArchitecturePackageGenerator
from aura.audit import AuditRecorder, read_audit_events


class AgentSecurityTests(unittest.TestCase):
    def test_path_policy_rejects_parent_absolute_sensitive_and_write_escapes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            (repository / ".git").mkdir()
            outside = root / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            environment = repository / ".env"
            environment.write_text("SECRET=value", encoding="utf-8")
            environment_local = repository / ".env.local"
            environment_local.write_text("SECRET=value", encoding="utf-8")
            auth = repository / "auth.json"
            auth.write_text("{}", encoding="utf-8")
            git_config = repository / ".git" / "config"
            git_config.write_text("[remote \"origin\"]\n", encoding="utf-8")
            browser_login = repository / ".config" / "chromium" / "Default" / "Login Data"
            browser_login.parent.mkdir(parents=True)
            browser_login.write_text("credentials", encoding="utf-8")
            worktree = root / "worktree"
            worktree.mkdir()
            policy = PathPolicy((repository,))

            for target in (
                repository / ".." / "outside.txt",
                outside,
                environment,
                environment_local,
                auth,
                git_config,
                browser_login,
            ):
                with self.subTest(target=target):
                    with self.assertRaises(ValueError):
                        policy.validate_read(target, repository)
            with self.assertRaises(ValueError):
                policy.validate_write(outside, worktree)
            with self.assertRaises(ValueError):
                policy.validate_worktree_root(
                    Path.home() / ".codex" / "secrets" / "agent-worktrees"
                )

    def test_command_policy_blocks_network_secrets_writes_in_read_only_and_release_actions(self):
        policy = CommandPolicy()
        blocked = (
            ("head .env", "read-only"),
            ("head .env.local", "read-only"),
            ("head ~/.codex/auth.json", "read-only"),
            ("head .git/config", "read-only"),
            ("head '.config/chromium/Default/Login Data'", "read-only"),
            ("head .npmrc", "read-only"),
            ("touch result.txt", "read-only"),
            ("curl https://example.invalid", "approved-worktree-write"),
            ("git push origin main", "approved-worktree-write"),
            ("git reset --hard HEAD", "approved-worktree-write"),
            ("git clean -fd", "approved-worktree-write"),
            ("echo ok && deploy", "approved-worktree-write"),
            ("ls > result.txt", "read-only"),
            ("rg TODO | head", "read-only"),
            ("find . -delete", "read-only"),
            ("sed -i s/old/new/ README.md", "read-only"),
            ("git branch new-branch", "read-only"),
            ("rg --pre 'sh hook.sh' TODO", "read-only"),
            ("head /etc/passwd", "read-only"),
            ("tail ../outside.txt", "read-only"),
            ("rg token credentials.json", "read-only"),
            ("pwd", "danger-full-access"),
        )
        for command, profile in blocked:
            with self.subTest(command=command, profile=profile):
                self.assertFalse(
                    policy.evaluate(command, safety_profile=profile).allowed
                )

    def test_unknown_action_and_model_fallback_are_fail_closed(self):
        action = ActionRegistry().resolve("provider.unknown.consequential")
        self.assertFalse(action.enabled)
        resolution = resolve_sol_ultra([])
        self.assertTrue(resolution.requires_fallback_approval)
        self.assertIsNone(resolution.model_id)
        with patch.dict(
            os.environ,
            {"AURA_AGENT_DEFAULT_SAFETY_PROFILE": "approved-worktree-write"},
        ):
            with self.assertRaisesRegex(ValueError, "read-only"):
                AgentConfig.from_environment(
                    repository_hint=Path(__file__).resolve().parents[1]
                )

    def test_agent_environment_defaults_to_live_mode(self):
        with patch.dict(os.environ, {}, clear=True):
            config = AgentConfig.from_environment(
                repository_hint=Path(__file__).resolve().parents[1]
            )

        self.assertEqual(config.default_mode, "live")

    def test_malformed_report_output_and_existing_package_collision_do_not_overwrite(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            output_file = Path(temporary) / "not-a-directory"
            output_file.write_text("preserve", encoding="utf-8")
            with self.assertRaises(OSError):
                ArchitecturePackageGenerator(repository).generate(output_file)
            self.assertEqual(output_file.read_text(encoding="utf-8"), "preserve")
            sensitive = Path(temporary) / ".codex" / "secrets"
            with self.assertRaisesRegex(ValueError, "sensitive"):
                ArchitecturePackageGenerator(repository).generate(sensitive / "reports")
            with self.assertRaisesRegex(ValueError, "sensitive"):
                AgentRunStore(sensitive / "runs")
            self.assertFalse(sensitive.exists())

            failed_root = Path(temporary) / "failed-package"
            with patch.object(
                ArchitecturePackageGenerator,
                "_validate_archive",
                side_effect=OSError("simulated archive failure"),
            ):
                with self.assertRaises(OSError):
                    ArchitecturePackageGenerator(repository).generate(failed_root)
            partial = next(
                path
                for path in failed_root.iterdir()
                if path.is_dir()
            )
            archive_status = json.loads(
                (partial / "validation" / "archive-validation.json").read_text()
            )
            self.assertEqual(archive_status["status"], "invalid")
            self.assertFalse(
                archive_status["validated_after_final_archive_creation"]
            )
            self.assertIn(
                "INVALID",
                (partial / "validation" / "validation-report.md").read_text(),
            )

    def test_secret_looking_audit_details_are_redacted(self):
        with tempfile.TemporaryDirectory() as temporary:
            recorder = AuditRecorder(temporary, retention_days=0)
            recorder.record(
                "agent.command_started",
                category="agent.workspace",
                workflow="agent",
                details={
                    "command": (
                        "curl -H 'Authorization: Bearer "
                        "sk-abcdefghijklmnopqrstuv' https://example.invalid "
                        + "ghp_"
                        + ("b" * 36)
                        + " 0912-345-678 A123456789"
                    ),
                    "operator": "private@example.invalid",
                },
            )
            events, issues = read_audit_events([temporary])
            self.assertEqual(issues, [])
            serialized = json.dumps(events[0]["details"])
            self.assertNotIn("sk-abcdefghijklmnopqrstuv", serialized)
            self.assertNotIn("private@example.invalid", serialized)
            self.assertNotIn("ghp_", serialized)
            self.assertNotIn("0912-345-678", serialized)
            self.assertNotIn("A123456789", serialized)
            self.assertIn("REDACTED", serialized)


if __name__ == "__main__":
    unittest.main()
