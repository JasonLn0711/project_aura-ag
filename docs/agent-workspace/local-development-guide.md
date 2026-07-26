# Agent Workspace Local Development Guide

## Checkout and environment

```bash
git status --short --branch
uv sync --all-extras --frozen
```

Run AURA:

```bash
uv run aura
```

`uv run` selects the repository `.venv`; `source .venv/bin/activate` is not
required. If a developer intentionally activates the environment first, use
`aura` directly.

Open **AI Agent** for the offline Demo. Live mode additionally requires a
supported local Codex CLI:

```bash
codex --version
codex login
```

The desktop login button can initiate ChatGPT authorization without manual API
key entry.

## Focused validation

```bash
QT_QPA_PLATFORM=offscreen PYTHONWARNINGS=error::ResourceWarning \
  uv run python -m unittest \
  tests.test_agent_core \
  tests.test_agent_policy \
  tests.test_agent_persistence \
  tests.test_agent_demo \
  tests.test_agent_controller \
  tests.test_agent_integrations \
  tests.test_agent_codex_provider \
  tests.test_agent_ui \
  tests.test_agent_main_window \
  tests.test_agent_security \
  tests.test_agent_scheduler \
  tests.test_agent_publication \
  tests.test_agent_support \
  tests.test_agent_workspace_architecture \
  tests.test_agent_workspace_models \
  tests.test_agent_workspace_performance \
  tests.test_agent_workspace_redesign
```

Run the full application regression:

```bash
QT_QPA_PLATFORM=offscreen PYTHONWARNINGS=error::ResourceWarning uv run python \
  -m unittest discover -s tests
uv run python -m compileall -q src tests scripts
git diff --check
```

Run the release reliability and live-runtime gates:

```bash
QT_QPA_PLATFORM=offscreen uv run python \
  scripts/run_agent_stable_daily_soak.py \
  --repository . \
  --output artifacts/stable-daily-assurance \
  --runs 50

QT_QPA_PLATFORM=offscreen uv run python \
  scripts/run_agent_live_codex_smoke.py \
  --repository . \
  --output artifacts/stable-daily-assurance/live-codex
```

The soak is deterministic reliability evidence. The live script is the real
Codex app-server target-runtime minimum.

Run the redesigned native workspace soak:

```bash
QT_QPA_PLATFORM=offscreen uv run python \
  scripts/run_agent_workspace_soak.py \
  --output \
  artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/soak-report.json
```

This gate exercises 50 work items, 10 approvals, 10 interruptions, 30 provider
failure/reconnect paths, large events, recording/storage transitions, restart,
and 10 Recovery Cards. Its sibling `audit-evidence/` directory contains the
content-free hash-chain audit record.

Run the Live timeline Markdown, summary, activity, geometry, keyboard,
security, and recovery checks:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src:. uv run python -m unittest \
  tests.test_agent_timeline_markdown \
  tests.test_agent_codex_provider \
  tests.test_agent_ui \
  tests.test_agent_workspace_models
```

Capture the 22-state native matrix and performance packet:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src:. uv run python \
  scripts/capture_agent_timeline_markdown_screenshots.py \
  --output-dir \
  artifacts/agent-workspace/2026-07-26-live-timeline-markdown/after \
  --repository .

QT_QPA_PLATFORM=offscreen PYTHONPATH=src:. uv run python \
  scripts/benchmark_agent_timeline_markdown.py \
  --output-dir \
  artifacts/agent-workspace/2026-07-26-live-timeline-markdown/performance
```

The visual manifest records its source commit, geometry, content formats, item
counts, blank-item counts, and body/image digests. The benchmark records the
host/runtime, thresholds, timings, memory, cache, and maximum measured stall.

Verify the generated audit chain:

```bash
uv run python scripts/summarize_audit_events.py --format json \
  artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/audit-evidence
```

The command exits successfully only when `audit_integrity_pass` is true.
Each soak invocation uses a unique audit session identity, so repeated local
runs remain independently verifiable in the same dated JSONL file.

## Capture redesigned workspace states

Capture one native state at a declared geometry:

```bash
QT_QPA_PLATFORM=offscreen uv run python \
  scripts/capture_agent_workspace_screenshot.py \
  --repository . \
  --state waiting-approval \
  --width 1440 \
  --height 900 \
  --output \
  artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/after/waiting-approval-1440x900.png
```

Repeat for `no-repository`, `new-task`, `evidence-attached`, `running`,
`waiting-approval`, `completed-diff`, `recovery`, `recording`, and `settings`
at 1024×768, 1280×820, 1440×900, and 1920×1080. The screenshots use the real
Qt widgets with deterministic Demo data and activate no Live service.

## Generate an architecture package

Use the Report inspector export control, or:

```python
from pathlib import Path
from aura.agent.reporting import ArchitecturePackageGenerator

result = ArchitecturePackageGenerator(Path.cwd()).generate(Path("/approved/output"))
print(result.package_dir)
print(result.archive_path)
```

Review `validation/validation-report.md`,
`validation/missing-evidence.json`, `validation/checksums.sha256`, and
`package-manifest.json`.

Generate the package only from a clean committed source state. Commit the
resulting unique directory and sibling ZIP as a separate evidence change.

## Inspect run artifacts

The Run inspector shows the active artifact directory. Override its
cross-platform Qt application-data default with `AURA_AGENT_RUN_ROOT` for a
controlled validation packet.

## Cleanup

Application shutdown terminates Codex. Worktree cleanup is explicit: first
export any required patch and test evidence, then use the selected repository's
normal `git worktree remove <managed-path>` process. AURA never resets, stashes,
cleans, merges, pushes, or deletes source work automatically.
