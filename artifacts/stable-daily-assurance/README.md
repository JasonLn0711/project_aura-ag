# Project AURA Stable Daily-Use Release Assurance

This directory indexes the canonical bounded evidence packets for Project
AURA's stable daily-use release path.

| Release evidence | Status | Source |
| --- | --- | --- |
| v1.17.0 Ubuntu release validation | `LIVE_FULL_COMPLETED` | [`v1.17.0-2026-07-28/`](v1.17.0-2026-07-28/) |
| Preserved Agent Workspace pre-release baseline | `CONFIRMED` | The files and directories at this level |

The dated v1.17.0 packet connects the current 608-test regression, native
control matrix, CUDA and local-runtime evidence, two reliability soaks,
privacy validation, and the published PR, hosted CI, merge, annotated tag, and
GitHub Release evidence. The top-level baseline remains preserved for
historical claim lineage.

| Evidence | Result | Source |
| --- | --- | --- |
| Native UI | Task-first visual review passes at 1440×900 and 1024×768 | [`screenshots/`](screenshots/) |
| Deterministic reliability | 50/50 runs pass, including 10 interruptions, 5 restarts, and 5 Recovery Cards | [`soak-report.md`](soak-report.md) |
| Live provider | `LIVE_MINIMUM_COMPLETED`, `valid_target_runtime` | [`live-codex/runtime-validity-report.md`](live-codex/runtime-validity-report.md) |
| Dependencies | `PASS_WITH_CLASSIFIED_RESIDUAL` | [`vulnerability-assessment.md`](vulnerability-assessment.md) |
| Compatibility | Ubuntu measured; Windows/macOS `unavailable_not_passed` | [`compatibility-matrix.json`](compatibility-matrix.json) |
| Claim routes | Source-backed release claims and verification paths | [`evidence-register.csv`](evidence-register.csv) |

The deterministic soak uses the production Qt/controller/catalog paths with the
Demo provider and is reliability evidence rather than live inference. The
sanitized Live packet records one real Codex app-server turn. Neither packet
contains credentials, private account identifiers, raw audio, or private
transcript text.
