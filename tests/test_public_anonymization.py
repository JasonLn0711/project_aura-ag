import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_public_anonymization import (
    scan_registered_worktrees,
    scan_repository,
)


class PublicAnonymizationTests(unittest.TestCase):
    def test_publishable_repository_has_no_sensitive_labels(self):
        repository = Path(__file__).resolve().parents[1]

        self.assertEqual(scan_repository(repository), [])

    def test_deleted_tracked_file_is_not_scanned(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            removed = repository / "removed.txt"
            removed.write_text("clean", encoding="utf-8")
            subprocess.run(["git", "add", "removed.txt"], cwd=repository, check=True)
            removed.unlink()

            self.assertEqual(scan_repository(repository), [])

    def test_registered_worktree_scan_covers_side_worktrees(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "main"
            side = root / "side"
            repository.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Anonymization Test"],
                cwd=repository,
                check=True,
            )
            (repository / "tracked.txt").write_text("clean", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "test fixture"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "worktree", "add", "-q", "-b", "side", side],
                cwd=repository,
                check=True,
            )
            (side / "finding.txt").write_bytes(b"M" + b"ax")

            findings = scan_registered_worktrees(repository)

            self.assertEqual(len(findings), 1)
            self.assertIn("finding.txt", findings[0])


if __name__ == "__main__":
    unittest.main()
