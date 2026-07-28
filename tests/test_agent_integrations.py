import csv
import getpass
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

from aura.agent.evidence import AuraEvidenceAdapter, FULL_TRANSCRIPT_CLAIM_ID
from aura.agent.persistence import AgentCatalog
from aura.agent.policy import PathPolicy, path_has_sensitive_component
from aura.agent.reporting import (
    CONFIDENCE,
    REPORTS,
    ArchitecturePackageGenerator,
    _copy_artifact,
    _redact_evidence_text,
)
from aura.agent.repository_registry import RepositoryRegistry
from aura.agent.worktree import WorktreeManager


class AuraEvidenceAdapterTests(unittest.TestCase):
    def test_local_audio_playback_rejects_manifest_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            session = root / "session"
            session.mkdir()
            outside = root / "outside.wav"
            outside.write_bytes(b"not audio")
            (session / "session.json").write_text(
                json.dumps({"audio_tracks": {"mixed": "../outside.wav"}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "outside the AURA session"):
                AuraEvidenceAdapter(session).local_audio_span(start_ms=0, end_ms=1)

    def test_only_fresh_confirmed_supported_actions_are_eligible(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            transcript_hash = hashlib.sha256(b"transcript").hexdigest()
            (session / "session.json").write_text(
                json.dumps(
                    {
                        "meeting_id": "meeting-1",
                        "transcript_sha256": transcript_hash,
                        "transcript_revision": 7,
                        "summary_status": "ready",
                        "created_at": "2026-07-25T10:00:00+08:00",
                    }
                ),
                encoding="utf-8",
            )
            (session / "segments.json").write_text(
                json.dumps(
                    {
                        "segments": [
                            {
                                "segment_id": "segment-1",
                                "text": "Create a bounded queue.",
                                "speaker": "Speaker 1",
                                "start_ms": 10,
                                "end_ms": 20,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (session / "summary.json").write_text(
                json.dumps(
                    {
                        "meeting_id": "meeting-1",
                        "transcript_sha256": transcript_hash,
                        "claims": [
                            {
                                "claim_id": "action-1",
                                "field": "action_items",
                                "text": "Bound the queue.",
                                "support_status": "supported",
                                "source_segment_ids": ["segment-1"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (session / "review_events.jsonl").write_text(
                json.dumps(
                    {
                        "event": "claim.confirmed",
                        "claim_id": "action-1",
                        "changes": {
                            "review_status": {
                                "from": "unreviewed",
                                "to": "confirmed",
                            }
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            adapter = AuraEvidenceAdapter(session)
            selection = adapter.select_confirmed_action("action-1")
            candidates = adapter.list_action_candidates()
            full_transcript = adapter.select_full_transcript()

            self.assertTrue(selection.eligible)
            self.assertFalse(selection.stale)
            self.assertEqual(selection.source_segment_ids, ("segment-1",))
            self.assertEqual(selection.snippets[0]["text"], "Create a bounded queue.")
            self.assertEqual(selection.transcript_revision, 7)
            self.assertEqual(selection.source_spans, ((10, 20),))
            self.assertEqual(selection.to_context().source_text, "Bound the queue.")
            self.assertEqual(selection.to_context().transcript_hash, transcript_hash)
            self.assertNotIn("audio", json.dumps(selection.to_dict()).lower())
            self.assertEqual(
                candidates[-1]["claim_id"],
                FULL_TRANSCRIPT_CLAIM_ID,
            )
            self.assertTrue(candidates[-1]["eligible"])
            self.assertEqual(
                full_transcript.transfer_scope,
                "full_transcript",
            )
            self.assertEqual(
                full_transcript.text,
                "Create a bounded queue.",
            )
            self.assertTrue(full_transcript.eligible)

    def test_stale_or_unsupported_action_is_an_explicit_delegation_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            (session / "session.json").write_text(
                json.dumps(
                    {
                        "meeting_id": "meeting-1",
                        "transcript_sha256": "current",
                        "summary_status": "invalidated",
                    }
                ),
                encoding="utf-8",
            )
            (session / "segments.json").write_text(
                json.dumps({"segments": []}),
                encoding="utf-8",
            )
            (session / "summary.json").write_text(
                json.dumps(
                    {
                        "meeting_id": "meeting-1",
                        "transcript_sha256": "stale",
                        "claims": [
                            {
                                "claim_id": "action-1",
                                "field": "action_items",
                                "text": "Unsafe action",
                                "support_status": "unsupported",
                                "source_segment_ids": ["missing"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            selection = AuraEvidenceAdapter(session).select_confirmed_action("action-1")

            self.assertFalse(selection.eligible)
            self.assertTrue(selection.stale)
            self.assertIn("transcript_hash_mismatch", selection.reasons)
            self.assertIn("support_status_unsupported", selection.reasons)


class WorktreeManagerTests(unittest.TestCase):
    def test_clean_repository_creates_agent_branch_isolated_worktree_and_patch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "source"
            worktrees = root / "worktrees"
            repository.mkdir()
            subprocess.run(["git", "init", "-q", repository], check=True)
            subprocess.run(
                ["git", "-C", repository, "config", "user.email", "test@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", repository, "config", "user.name", "AURA Test"],
                check=True,
            )
            (repository / "README.md").write_text("AURA\n", encoding="utf-8")
            subprocess.run(["git", "-C", repository, "add", "README.md"], check=True)
            subprocess.run(
                ["git", "-C", repository, "commit", "-qm", "baseline"],
                check=True,
            )
            manager = WorktreeManager(
                repository,
                worktrees,
                PathPolicy((root,)),
                minimum_free_bytes=1,
            )
            source_before = (repository / "README.md").read_bytes()

            context = manager.create("run-1")
            (context.path / "README.md").write_text("AURA Agent\n", encoding="utf-8")
            patch = manager.export_patch(context, root / "change.patch")

            self.assertTrue(context.path.is_dir())
            self.assertNotEqual(context.path, repository)
            self.assertTrue(context.branch.startswith("aura-agent/"))
            self.assertEqual(
                subprocess.run(
                    ["git", "-C", context.path, "branch", "--show-current"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip(),
                context.branch,
            )
            self.assertIn("-AURA", patch.read_text(encoding="utf-8"))
            self.assertIn("+AURA Agent", patch.read_text(encoding="utf-8"))
            self.assertEqual((repository / "README.md").read_bytes(), source_before)

    def test_dirty_repository_records_omitted_changes_without_touching_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "source"
            repository.mkdir()
            subprocess.run(["git", "init", "-q", repository], check=True)
            subprocess.run(
                ["git", "-C", repository, "config", "user.email", "test@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", repository, "config", "user.name", "AURA Test"],
                check=True,
            )
            (repository / "README.md").write_text("baseline\n", encoding="utf-8")
            subprocess.run(["git", "-C", repository, "add", "README.md"], check=True)
            subprocess.run(
                ["git", "-C", repository, "commit", "-qm", "baseline"],
                check=True,
            )
            (repository / "draft.txt").write_text("untracked", encoding="utf-8")
            manager = WorktreeManager(repository, root / "worktrees", PathPolicy((root,)))

            context = manager.create("run-1")

            self.assertTrue(context.source_dirty)
            self.assertEqual(context.omitted_dirty_paths, ("draft.txt",))
            self.assertFalse((context.path / "draft.txt").exists())
            self.assertEqual(
                (repository / "draft.txt").read_text(encoding="utf-8"),
                "untracked",
            )


class RepositoryRegistryTests(unittest.TestCase):
    def test_repository_add_is_explicit_hash_bound_and_portable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "source"
            repository.mkdir()
            subprocess.run(
                ["git", "init", "-q", "-b", "main", repository],
                check=True,
            )
            subprocess.run(
                ["git", "-C", repository, "config", "user.email", "test@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", repository, "config", "user.name", "AURA Test"],
                check=True,
            )
            (repository / "README.md").write_text("AURA\n", encoding="utf-8")
            (repository / "AGENTS.md").write_text(
                "Repository-local instructions.\n",
                encoding="utf-8",
            )
            (repository / "pyproject.toml").write_text(
                "[project]\nname='fixture'\nversion='0.1.0'\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "-C", repository, "add", "."], check=True)
            subprocess.run(
                ["git", "-C", repository, "commit", "-qm", "baseline"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    repository,
                    "remote",
                    "add",
                    "origin",
                    "ssh://example.invalid/aura.git",
                ],
                check=True,
            )

            with AgentCatalog(root / "catalog.sqlite3") as catalog:
                registry = RepositoryRegistry(catalog, PathPolicy((root,)))
                inspection = registry.inspect(repository)
                self.assertEqual(inspection.default_branch, "main")
                self.assertEqual(inspection.package_managers, ("python",))
                self.assertEqual(inspection.instruction_files[0][0], "AGENTS.md")
                self.assertEqual(len(inspection.instruction_files[0][1]), 64)
                profile = registry.confirm_add(
                    inspection,
                    now="2026-07-25T10:30:00+08:00",
                )
                self.assertTrue(catalog.repository(profile.repository_id)["allowed"])

                portable = registry.export_json(registry.portable_export())
                self.assertNotIn(str(repository), portable)
                self.assertIn(f"repo://{profile.repository_id}", portable)
                registry.remove(
                    profile.repository_id,
                    now="2026-07-25T10:31:00+08:00",
                )
                self.assertFalse(catalog.repository(profile.repository_id)["allowed"])


class ArchitecturePackageGeneratorTests(unittest.TestCase):
    def test_copied_text_artifacts_use_lf_on_every_platform(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.md"
            destination = root / "destination.md"
            source.write_bytes(b"first\r\nsecond\r\n")

            _copy_artifact(source, destination)

            self.assertEqual(destination.read_bytes(), b"first\nsecond\n")

    def test_redesign_reports_keep_required_order(self):
        self.assertEqual(
            REPORTS[16:],
            (
                ("17-ux-architecture", "UX Architecture and Interaction Grammar"),
                (
                    "18-state-matrix",
                    "State, Empty, Loading, Error, Approval, and Recovery Matrix",
                ),
                (
                    "19-accessibility-localization",
                    "Accessibility and Localization",
                ),
                (
                    "20-ui-performance",
                    "UI Performance, Virtualization, and Backpressure",
                ),
                (
                    "21-persistence-preferences",
                    "Persistence, Drafts, Preferences, and Schema Migration",
                ),
                (
                    "22-identity-permission-transfer",
                    "Identity, Account, Permission, and Data-Transfer UX",
                ),
                (
                    "23-prompt-injection-provenance",
                    "Prompt-Injection and Instruction-Provenance UX",
                ),
                (
                    "24-visual-usability-evidence",
                    "Visual Validation, Usability Evidence, and Before/After Screenshots",
                ),
                (
                    "25-release-readiness",
                    "Open Questions, Unknowns, Future Agent Operations Workbench Gates, and Release Readiness",
                ),
            ),
        )

    def test_in_repository_output_does_not_create_false_dirty_source(self):
        repository = Path(__file__).resolve().parents[1]
        baseline = subprocess.run(
            ["git", "status", "--short", "--untracked-files=normal"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        output = repository / f".aura-package-test-{uuid.uuid4().hex}"
        try:
            result = ArchitecturePackageGenerator(repository).generate(output)
            metadata = json.loads(
                (result.package_dir / "analysis-metadata.json").read_text()
            )
            self.assertEqual(metadata["source_dirty"], bool(baseline))
        finally:
            shutil.rmtree(output, ignore_errors=True)

    def test_package_has_all_reports_diagrams_inventories_and_valid_sboms(self):
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            result = ArchitecturePackageGenerator(repository).generate(Path(temporary))

            package = result.package_dir
            metadata = json.loads((package / "analysis-metadata.json").read_text())
            self.assertEqual(metadata["repository"], "project_aura-ag")
            self.assertEqual(len(list((package / "reports").glob("*.md"))), 25)
            self.assertGreaterEqual(
                len(list((package / "diagrams").glob("*.mmd"))),
                13,
            )
            self.assertGreaterEqual(len(list((package / "inventories").glob("*.csv"))), 18)
            source_adr_count = len(
                list((repository / "docs" / "agent-workspace" / "adr").glob("ADR-*.md"))
            )
            self.assertEqual(
                len(list((package / "adr").glob("ADR-*.md"))),
                source_adr_count,
            )
            self.assertTrue(
                (package / "screenshots" / "baseline-vs-redesign-1440x900.png").is_file()
            )
            self.assertTrue(
                (
                    package
                    / "screenshots"
                    / "transfer-review"
                    / "after"
                    / "04-credential-blocked.png"
                ).is_file()
            )
            self.assertTrue(
                (
                    package
                    / "validation"
                    / "transfer-review-visual-review.md"
                ).is_file()
            )
            checksum_file = (
                package
                / "validation"
                / "transfer-review-checksums.sha256"
            )
            for line in checksum_file.read_text(encoding="utf-8").splitlines():
                expected, relative = line.split(maxsplit=1)
                captured = (checksum_file.parent / relative).resolve()
                self.assertTrue(captured.is_file(), relative)
                self.assertEqual(
                    hashlib.sha256(captured.read_bytes()).hexdigest(),
                    expected,
                )
            transfer_flow = (
                package / "diagrams" / "07-data-transfer-flow.mmd"
            ).read_text(encoding="utf-8")
            self.assertIn("TransferReviewViewModel", transfer_flow)
            self.assertIn("demo_local_only", transfer_flow)
            transfer_report = (
                package
                / "reports"
                / "22-identity-permission-transfer.md"
            ).read_text(encoding="utf-8")
            self.assertIn("plain-language", transfer_report)
            self.assertIn("Repository authority", transfer_report)
            report_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted((package / "reports").glob("*.md"))
            )
            for label in CONFIDENCE:
                self.assertNotIn(f"**{label}.**", report_text)
            for relative in (
                "sbom/model-bom.json",
                "sbom/native-bom.json",
                "validation/compatibility-matrix.json",
                "validation/soak-report.md",
                "validation/ui-redesign-validation-report.md",
                "validation/ui-redesign-missing-evidence.md",
                "validation/ui-redesign-checksums.sha256",
                "artifacts/ui-redesign-soak-report.json",
                "artifacts/ui-redesign-audit-events.jsonl",
                "risk-register.csv",
                "controls.csv",
                "evidence-register.csv",
            ):
                self.assertTrue((package / relative).is_file(), relative)
            for path in package.rglob("*"):
                if path.suffix not in {".csv", ".md", ".mmd"}:
                    continue
                raw = path.read_bytes()
                lines = raw.splitlines()
                self.assertNotIn(b"\r", raw, path)
                self.assertFalse(
                    any(line.endswith((b" ", b"\t")) for line in lines),
                    path,
                )
            cyclone = json.loads((package / "sbom" / "cyclonedx.json").read_text())
            spdx = json.loads((package / "sbom" / "spdx.json").read_text())
            self.assertEqual(cyclone["bomFormat"], "CycloneDX")
            self.assertEqual(
                cyclone["metadata"]["component"]["name"],
                "project_aura-ag",
            )
            self.assertEqual(spdx["spdxVersion"], "SPDX-2.3")
            self.assertEqual(spdx["name"], "project_aura-ag-architecture-package")
            self.assertTrue(result.archive_path.is_file())
            validation = json.loads(
                (package / "validation" / "archive-validation.json").read_text()
            )
            self.assertEqual(validation["status"], "valid")
            command_results = (
                package / "validation" / "command-results.json"
            ).read_text(encoding="utf-8")
            self.assertNotIn(str(repository), command_results)
            self.assertNotIn(f"/home/{getpass.getuser()}", command_results)
            if platform.node():
                self.assertNotIn(
                    f"Host Name: {platform.node()}",
                    command_results,
                )
            self.assertNotIn(
                "/home/",
                (package / "reports" / "16-local-development.md").read_text(),
            )
            with (package / "inventories" / "events.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                self.assertGreater(len(list(csv.DictReader(handle))), 20)
            for report in (package / "reports").glob("*.md"):
                text = report.read_text(encoding="utf-8")
                self.assertIn("**CONFIRMED.**", text)
                self.assertIn("**PARTIALLY VERIFIED.**", text)
                self.assertIn("## Required Coverage", text)
                self.assertIn("## Detailed Findings", text)

            self.assertIn(
                "ready for operator review",
                (package / "reports" / "01-executive-summary.md").read_text(),
            )
            self.assertIn(
                "Cycles, imports, and hotspots",
                (package / "reports" / "09-dependency-graph.md").read_text(),
            )
            self.assertIn(
                "uv sync --all-extras --frozen",
                (package / "reports" / "16-local-development.md").read_text(),
            )
            with (package / "inventories" / "risks.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                risks = list(csv.DictReader(handle))
            self.assertTrue(risks)
            self.assertTrue(all(row["impact"] for row in risks))
            with (package / "inventories" / "repository-files.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                inventoried = {
                    row["path"] for row in csv.DictReader(handle)
                }
            visible = subprocess.run(
                [
                    "git",
                    "ls-files",
                    "--cached",
                    "--others",
                    "--exclude-standard",
                ],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
            expected = {
                relative
                for relative in visible
                if (repository / relative).is_file()
                and not path_has_sensitive_component(relative)
            }
            self.assertEqual(inventoried, expected)
            with (package / "inventories" / "native-dependencies.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                native = {row["dependency"] for row in csv.DictReader(handle)}
            self.assertTrue({"pulseaudio", "pipewire"}.issubset(native))
            for line in (
                package / "validation" / "checksums.sha256"
            ).read_text(encoding="utf-8").splitlines():
                expected, relative = line.split("  ", 1)
                self.assertEqual(
                    hashlib.sha256((package / relative).read_bytes()).hexdigest(),
                    expected,
                )

    def test_local_identifier_redaction_is_independent_of_host_tools(self):
        self.assertEqual(
            _redact_evidence_text("Cookie: workstation-id"),
            "Cookie: [REDACTED_LOCAL_ID]",
        )


if __name__ == "__main__":
    unittest.main()
