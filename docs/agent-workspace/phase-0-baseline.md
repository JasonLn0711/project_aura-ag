# Stable Daily Agent Workspace Phase 0 Baseline

**Recorded:** 2026-07-25 (Asia/Taipei)

**Status:** IMPLEMENTATION_BASELINE_CONFIRMED

## Binding source

- Goal prompt:
  `/home/jnclaw/Downloads/PROJECT_AURA_STABLE_DAILY_AGENT_CODEX_GOAL_PROMPT.md`
- Prompt size: 2,648 lines / 88,310 bytes
- Prompt SHA-256:
  `710206fcdf90cf93256a78ee12164abefd889d05fb201b9de6ecd10911c60acd`
- Supplied architecture source commit:
  `93fd7587ae628104e0fa23581204d92ee085e3ce`
- Implementation-start commit:
  `b19c00d3703a2aafd5316407acb8e67aecd42929`
- Implementation branch:
  `aura-agent/20260725/stable-daily-workspace`
- Isolated implementation worktree:
  `/home/jnclaw/every_on_git_jnclaw/project_aura-stable-daily`

The filename named by the goal prompt,
`repository-technical-architecture-package-project_aura-ag-20260725-221128-393521.zip`,
was not present under `/home/jnclaw` at implementation start. The repository
contains an earlier package named
`repository-technical-architecture-package-project_aura-ag-20260725-213848-256779.zip`;
its metadata binds it to commit
`368118ec79291bd94f62af4633131afe5fc202f9` and a dirty source checkout.
It is retained as historical evidence and is not represented as the missing
supplied package. Commit `93fd7587ae628104e0fa23581204d92ee085e3ce`
therefore supplies the authoritative architecture-source comparison.

## Repository state

The source checkout at
`/home/jnclaw/every_on_git_jnclaw/project_aura-ag` was on `main` at
`b19c00d3703a2aafd5316407acb8e67aecd42929`, matching `origin/main`.
Its pre-existing user-owned working-tree state was:

```text
 D .github/workflows/ci.yml
 D .github/workflows/windows.yml
?? sys
```

The `sys` file was approximately 6.99 MB. These paths remain outside this
implementation branch and worktree.

## Drift from the architecture source commit

The implementation-start tree differs from `93fd7587` in five files:

| Path | Classification |
| --- | --- |
| `README.md` | Release-facing documentation expansion |
| `docs/agent-workspace/README.md` | Documentation routing |
| `pyproject.toml` | Version synchronization |
| `src/aura/metadata.py` | Version synchronization |
| `uv.lock` | Version synchronization |

The drift contains 245 insertions and 24 deletions. Agent runtime source files
do not differ across this range. The current version is `v1.16.0`.

## Environment

- Operating system: Ubuntu 24.04.4 LTS
- Kernel: Linux 7.0.0-28, x86_64
- Python: 3.12.3
- Codex CLI: 0.145.0
- Agent UI: native PyQt6
- Package environment: frozen `uv.lock`

## Existing architecture seam

Confirmed from the implementation-start tree:

- `MainWindow` owns the native tab integration seam.
- Existing transcription, recording, summary, evidence-search, and splitter
  workflows remain outside the Agent subsystem.
- `AuditRecorder` supplies the existing sanitized audit seam.
- Canonical meeting artifacts remain filesystem-owned.
- `EvidenceSearch` supplies read-only meeting, segment, confirmed-action, and
  audio-span queries.
- Agent P0 already supplies typed events, reducer state, per-run JSON/JSONL
  evidence, deterministic Demo fixtures, a stdio Codex adapter, an isolated
  worktree helper, evidence transfer preview, and trusted native renderers.
- The stable-daily release extends these seams with a durable task catalog,
  queue, policy-scoped workflows, resource protection, recovery, publication,
  and a low-density task UI.

## Test baseline

The frozen environment was checked without changing repository source:

```bash
uv sync --all-extras --frozen
```

Result:

```text
Checked 139 packages in 1ms
```

The complete implementation-start suite was then executed:

```bash
QT_QPA_PLATFORM=offscreen \
  uv run python -W error::ResourceWarning \
  -m unittest discover -s tests -v
```

Result:

```text
Ran 451 tests in 11.093s
OK
```

The simulated audio-capture failure log came from its dedicated recovery test
and did not fail the suite.

## Codex compatibility baseline

- Executable: the configured `codex` found on `PATH`
- Installed version: `codex-cli 0.145.0`
- Transport: JSONL over stdio
- Required handshake: `initialize`, then `initialized`
- Authentication owner: Codex / ChatGPT login
- AURA credential storage: none
- Current generated v2 schema SHA-256:
  `16d8024fb52dfb10eb7a2c8a0768812a32d7e2a693d4e65a3831be6ea7bc2b1e`

The installed schema includes thread start/resume/list/read, turn
start/interrupt/steer, account methods, model discovery, command and file
approval requests, and session-scoped command approval. Live activation still
requires the product preflight and a no-side-effect probe; schema presence alone
is preflight evidence rather than a live-run result.

## Phase 0 release gates

| Gate | Result |
| --- | --- |
| Goal prompt captured and hashed | PASS |
| Architecture source commit available | PASS |
| Exact named architecture ZIP available | MISSING_INPUT |
| Drift classified | PASS |
| Dirty user work isolated | PASS |
| Dedicated branch and worktree | PASS |
| Frozen dependency check | PASS |
| Complete baseline regression | PASS |
| Installed Codex version recorded | PASS |
| Current app-server schema generated and hashed | PASS |
| Windows live validation | NOT VERIFIED |
| macOS live validation | NOT VERIFIED |

Ubuntu 24.04 is the declared release-validation platform. Other platforms
remain explicit validation gates and are never counted as passes.
