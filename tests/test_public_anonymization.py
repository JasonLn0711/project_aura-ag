import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_public_anonymization import (
    scan_git_metadata,
    scan_git_objects,
    scan_registered_worktrees,
    scan_repository,
)


class PublicAnonymizationTests(unittest.TestCase):
    def init_repository(self, repository: Path) -> None:
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

    def commit(self, repository: Path, message: str) -> None:
        subprocess.run(["git", "add", "-A"], cwd=repository, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", message],
            cwd=repository,
            check=True,
        )

    def test_publishable_repository_has_no_sensitive_labels(self):
        repository = Path(__file__).resolve().parents[1]

        self.assertEqual(scan_repository(repository), [])

    def test_deleted_tracked_file_is_not_scanned(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            self.init_repository(repository)
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
            self.init_repository(repository)
            (repository / "tracked.txt").write_text("clean", encoding="utf-8")
            self.commit(repository, "test fixture")
            subprocess.run(
                ["git", "worktree", "add", "-q", "-b", "side", side],
                cwd=repository,
                check=True,
            )
            (side / "finding.txt").write_bytes(b"M" + b"ax")

            findings = scan_registered_worktrees(repository)

            self.assertEqual(len(findings), 1)
            self.assertIn("finding.txt", findings[0])

    def test_git_object_scan_finds_labels_removed_from_current_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            self.init_repository(repository)
            tracked = repository / "tracked.txt"
            tracked.write_bytes(b"M" + b"ax")
            self.commit(repository, "sensitive fixture")
            tracked.write_text("clean", encoding="utf-8")
            self.commit(repository, "clean fixture")

            self.assertEqual(scan_repository(repository), [])
            self.assertTrue(scan_git_objects(repository))

    def test_git_metadata_scan_finds_sensitive_ref_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            self.init_repository(repository)
            (repository / "tracked.txt").write_text("clean", encoding="utf-8")
            self.commit(repository, "clean fixture")
            label = (b"M" + b"ax").decode()
            subprocess.run(
                ["git", "branch", f"feature/{label}"],
                cwd=repository,
                check=True,
            )

            self.assertTrue(scan_git_metadata(repository))


if __name__ == "__main__":
    unittest.main()
