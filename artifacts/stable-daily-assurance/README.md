# Project AURA Stable Daily-Use Release Assurance

This directory is the canonical bounded evidence packet for the v1.17.0 Agent
Workspace candidate.

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
