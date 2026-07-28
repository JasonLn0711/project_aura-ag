# Project AURA: Local Desktop Audio Assistant

<p>
  <img alt="Maintained repository status" src="https://img.shields.io/badge/Status-Maintained-brightgreen?logo=github">
  <img alt="Continuous integration status" src="https://github.com/JasonLn0711/project_aura-ag/actions/workflows/ci.yml/badge.svg">
  <img alt="Python 3.10 or newer" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python">
  <img alt="faster-whisper ASR engine" src="https://img.shields.io/badge/ASR-faster--whisper-orange">
  <img alt="PyQt6 desktop interface" src="https://img.shields.io/badge/UI-PyQt6-9cf">
  <img alt="MIT license" src="https://img.shields.io/badge/License-MIT-yellow.svg">
</p>

*Repository indicators summarize maintenance, CI, runtime, ASR, UI, and license status.*

<!--
README FORMAT CONTRACT

Keep the rendered sections in this exact order:
1. Product Purpose
2. Project Status
3. Latest Update
4. Core Capabilities
5. Architecture and Ownership
6. Evidence-First Session Contract
7. Desktop Workflow
8. Installation
9. Configuration Defaults
10. Feature Behavior
11. Session Artifacts and Data Layout
12. Validation and Evidence
13. Development and Testing
14. Windows Runtime Path
15. Release and Versioning
16. Troubleshooting
17. Documentation Map
18. Repository Data Stewardship
19. License

Keep all rendered README copy in English. Place an explanatory caption
immediately after every screenshot, diagram, or illustration. Preserve
operational depth while routing dated history to GitHub Releases, design
detail to docs/, and measured runtime packets to artifacts/.

Preserve the Refactor Version, Latest Published Tag, Next Release Candidate
rows and the Latest Update heading because scripts/bump_version.py updates
them during release preparation.
-->

Project AURA is a local desktop audio assistant for professional meetings,
lectures, and review-intensive transcription workflows. It brings recording,
RTX/CUDA speech recognition, Traditional Chinese transcript preparation,
human review, local structured summaries, and evidence export into one
recoverable workflow.

![Project AURA transcription workspace with CUDA status, waveform, Traditional Chinese transcript, and review controls](./img/transcription-workspace-v1.14.0.png)

*Figure 1. The transcription workspace keeps capture controls, CUDA readiness, waveform feedback, Traditional Chinese transcript review, output actions, and the local activity log in one operator view.*

![Project AURA AI Agent workspace after a completed repository task, with repository history, the reviewable result, and the next-prompt composer](./img/agent-workspace-completed-v1.17.0.png)

*Figure 2. The AI Agent workspace presents a completed repository task in context: repository-scoped history stays visible beside the reviewable conversation, completion result, execution environment, and composer for the next prompt.*

## Product Purpose

AURA turns audio into a durable, reviewable meeting record. The application
keeps audio, transcript states, summary claims, and review events connected
through one session identity so operators can move from capture to confirmed
actions with a visible evidence path.

The active product flow is:

```text
Live capture or media import
        |
        v
Breeze ASR on RTX/CUDA
        |
        v
Traditional Chinese punctuation and glossary correction
        |
        v
Timestamped human review
        |
        v
Local Gemma 4 structured summary
        |
        v
Source-linked claims, exports, and evidence search
```

Use this repository for:

- the maintained PyQt6 desktop application;
- reusable audio, ASR, review, summary, diagnostics, and evidence services;
- regression tests and platform smoke checks;
- release packaging and semantic version automation;
- public runtime evidence with source manifests and measured event traces;
- architecture, product strategy, governance, and platform documentation.

## Project Status

| Field | Value |
| --- | --- |
| Project Name | Project AURA / Ultimate Audio Assistant |
| Refactor Version | `1.17.0` |
| Latest Published Tag | `v1.17.0` |
| Next Release Candidate | `v1.17.0` |
| Release State | `v1.17.0` is the published Ubuntu stable daily-use release with the intent-first native Agent Workspace; automated regression, responsive visual, native controls, live runtimes, and both 50-task reliability gates pass, with target-host and field-study packages retained as the next validation layers |
| Primary Platform | Ubuntu 22.04 / 24.04 desktop |
| Python Runtime | Python 3.10+ |
| ASR Model | `SoybeanMilk/faster-whisper-Breeze-ASR-25` |
| ASR Runtime | NVIDIA RTX/CUDA with `int8` compute |
| Summary Runtime | Local Ollama `gemma4:e4b-it-qat` with reasoning enabled |
| Desktop UI | PyQt6 |
| Project Lead | Jason Chia-Sheng Lin, National Yang Ming Chiao Tung University |
| License | MIT |

### Start here: choose a runtime path

| Runtime path | Recommended use | Current evidence |
| --- | --- | --- |
| Ubuntu 24.04 desktop | Full AURA operation, Agent development, and release validation | Primary measured platform; the current 608-test full regression and native 50-task workspace soak pass |
| Windows with WSL2 Ubuntu 24.04 | Linux-aligned development and the fastest Windows path to the Agent Workspace | Supported implementation path; target-host AURA release execution is `unavailable_not_passed` |
| Native Windows | Portable onboarding and native Windows release work | Packaging and source paths exist; v1.17.0 target-host execution is `unavailable_not_passed` |
| macOS | Source portability and future release-host work | Cross-platform code paths exist; v1.17.0 target-host execution is `unavailable_not_passed` |

Windows developers can follow the complete
[WSL2 Ubuntu 24.04 path](#wsl2-ubuntu-2404-development-path) or the
[native Windows path](#native-windows-portable-onboarding). Runtime evidence
and remaining host gates are tracked in the
[Agent Workspace redesign acceptance ledger](docs/agent-workspace/ux-redesign/11-acceptance-status.md).

### Release lineage

| Release | Contribution |
| --- | --- |
| `v1.17.0` | Published Ubuntu stable daily-use Agent Workspace with twelve workflows, four modes, durable queue/catalog, resource governance, dynamic quality profiles, explicit Publish, recovery/support tooling, and 25-report assurance |
| `v1.16.0` candidate | Native Agent Workspace P0, evidence-gated Demo and Live operation, architecture-package generation, and the WSL2 Ubuntu 24.04 implementation path |
| `v1.15.0` preserved source baseline | Durable meeting sessions, crash recovery, timestamped transcript review, source-linked summary claims, and rebuildable local evidence search |
| `v1.14.0` | Operator-focused workspace, content-free local audit events, runtime diagnostics, integrity checks, and synchronized version automation |
| `v1.13.0` | Windows onboarding, portable packaging, RTX diagnostics, output policy, scheduling, and broader artifact visibility |
| `v1.12.0` | Structured transcript artifacts, progress telemetry, audio-quality controls, and modular transcription services |

GitHub Releases owns the durable release chronology. The sections below
describe the current product contract and link each capability to its
canonical design or evidence source.

## Latest Update — v1.17.0 (2026-07-28)

Project AURA v1.17.0 advances the native Agent Workspace to one intent-first
repository/thread surface while retaining the complete evidence-first meeting
workflow and stable daily-use safety contract.

![Project AURA native Agent Workspace with repository threads, one centered composer, three suggestions, and contextual controls](./artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/after/new-task-1440x900.png)

*Figure 3. The redesigned native workspace makes repository identity, task history, one intent composer, and the send path immediately visible while evidence, environment, and artifact detail remain contextual.*

### Readable Live timeline

Live user and Aura narrative now renders through the installed native Qt
Markdown path with natural wrapping, dynamic row height, resize reflow,
explicit expansion, raw/display copy, safe resource handling, and confirmed
HTTPS link actions. Technical output retains code, plain-text, diff, or
structured treatment.

Provider summaries reconcile empty completion safely: a non-empty delta stays
visible, and an empty-only summary creates no card. One stable
`工作進度` digest groups observable command and tool lifecycles while failures,
approval gates, and terminal outcomes remain visible. Canonical events retain
their complete sequence for audit and recovery.

The final validation includes 82 timeline-focused tests within the current
608-test full regression, 22
native states with zero blank projected items, and a bounded performance packet
whose maximum measured GUI-thread stall is 55.351 ms. The complete issue,
72-row acceptance ledger, security contract, and evidence are in the
[Live timeline record](docs/agent-workspace/timeline-markdown/issue-and-resolution.md)
and [evidence packet](artifacts/agent-workspace/2026-07-26-live-timeline-markdown/).

### Continuous task conversations

One WorkItem now owns the complete visible conversation until the operator
selects **新增任務**. A second Prompt creates a continuation AgentRun under the
same WorkItem, resumes the established Codex provider thread, and appends its
user, reasoning-summary, activity, and response rows after the earlier turns.
The explicit new-task action clears the visible conversation and starts the
next WorkItem.

Codex thinking and execution status is mounted inside the composer directly
above the editor. The compact status row communicates the current phase and
indeterminate activity without creating a separate desktop window, while the
timeline remains the durable source for plans, tool activity, approvals, and
answers.

![Project AURA Agent Workspace with Codex thinking and execution status embedded above the task composer](./artifacts/agent-workspace/2026-07-26-conversation-continuity/screenshots/01-inline-codex-status.png)

*The inline activity row keeps attention, progress, approval, and the next Prompt inside one workspace while the current task conversation remains visible.*

The verified Live minimum completed two real `gpt-5.6-sol` turns on the same
provider thread, observed both expected replies, retained an unchanged
checkout, and closed the Codex process tree. The full
[issue and resolution](docs/agent-workspace/conversation-continuity/issue-and-resolution.md)
and [evidence packet](artifacts/agent-workspace/2026-07-26-conversation-continuity/)
connect the original screenshot, visual correction, regression, Live trace,
and content-free audit events.

### Stable daily-use Agent Workspace

| Architecture layer | Implemented contract | Evidence status |
| --- | --- | --- |
| Product surface | Repository/thread navigation, one intent-first composer, three suggestions, four modes, persistent per-thread drafts, contextual inspectors, Environment, and category-based Settings | Native Qt interaction tests plus 36 state/viewport captures pass |
| Durable work | WorkItems, AgentRuns, evidence links, repository profiles/grants, SQLite WAL queue/catalog, Recovery Cards, storage preview, and support bundles | Migration, restart, recovery, and redaction tests pass |
| Runtime | One provider-neutral contract shared by deterministic Demo and compatible Codex app-server Live operation | 50-run deterministic soak passes; one real Live turn is `valid_target_runtime` |
| Resource ownership | Exactly one Live run; recording/live-ASR, storage, CPU, and memory gates queue protected work | Ten stops, 30 provider failure/reconnect cycles, ten Recovery Cards, and pressure exercises pass |
| Repository lifecycle | Explicit allowlist, canonical paths, isolated worktrees, freshness checks, and explicit Publish for commit/push/PR | Source checkout remains unchanged; force/default branch, merge, and deploy stay unavailable |
| Data and trust | Classification, minimization, redaction, plain-language exact-payload review, document confirmation, instruction provenance, request-scoped approvals | Credentials/raw audio have no transfer path; security, transfer-review, and support-bundle tests pass |
| Evidence | 25 reports, 23 Mermaid diagrams, 37 ADRs, four BOMs, risks, controls, 36 redesign captures, 22 timeline captures, soak/live records, checksums, and validated ZIP | Canonical assurance is under `artifacts/agent-workspace/` and `artifacts/repository-architecture/` |

Quick, Standard, and Expert resolve from the live catalog. The v1.17.0 live
minimum used Quick, resolved `gpt-5.6-sol` with `low` effort, observed the exact
expected response, requested no approval, changed no tracked file, and left no
Codex process. The approved-worktree follow-up also completed as
`valid_target_runtime` with the stable thread contract and an isolated
`workspaceWrite` turn policy.

The Ubuntu 24.04 gate passes the current 608-test full regression. The native
50-task workspace soak exercises ten approval cycles, ten stop cycles, 30
provider failure/reconnect cycles, ten Recovery Cards, recording/storage
transitions, and restart persistence. It retains 1,323 content-free audit
events with hash-chain integrity `PASS`.

The redesign captures nine states at 1024×768, 1280×820, 1440×900, and
1920×1080. Repository/thread switching measures 18.173 ms, a large event
projection measures 8.574 ms, and the 50 MiB log path loads a bounded 64 KiB
preview in 0.031 ms. The five-participant task study and complete background execution for
remaining legacy Git/SQLite/report/media/provider UI actions remain explicit
validation gates.

The dependency scan retains one classified residual:
`CVE-2026-59890`, a macOS source-distribution Unicode-normalization issue in
setuptools. The active Ubuntu runtime does not build or publish source
distributions; PyTorch currently constrains the patched setuptools version out
of the lock. macOS activation carries the refresh gate. Windows and macOS
remain `unavailable_not_passed`.

See the
[final implementation report](docs/agent-workspace/final-implementation-report.md),
[redesign acceptance ledger](docs/agent-workspace/ux-redesign/11-acceptance-status.md),
[usability result](docs/agent-workspace/ux-redesign/12-usability-evaluation-results.md),
[UI validation packet](artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/),
[release assurance](artifacts/stable-daily-assurance/), and
[architecture packages](artifacts/repository-architecture/) for claim-level
evidence.

#### v1.17.0 validation

- Full regression: 608 tests pass.
- Native workspace soak: 50/50 tasks pass the deterministic integrity gate.
- Content-free audit: 1,323 events pass hash-chain verification.
- Native control matrix: 36/36 reachable controls and state gates pass with
  0 blocked controls and 0 harness errors.
- Stable daily-use soak: 50/50 runs pass with 40 completed, 10 interrupted,
  5 restarts, 5 Recovery Card exercises, and a 71.680 ms maximum heartbeat gap.
- Responsive visual evidence: 36/36 final state captures exist at the declared geometries.
- Real Codex minimum: `LIVE_MINIMUM_COMPLETED`.
- Redesign acceptance: 90 `CONFIRMED`, 3 `PARTIALLY VERIFIED`, 1 `NOT VERIFIED`.
- Release platform: Ubuntu 24.04 passed; Windows/macOS
  `unavailable_not_passed`.

### Preserved v1.15.0 scope — 2026-07-23

Project AURA v1.15.0 establishes the evidence-first local meeting workflow.
Each recording or import creates one canonical session that connects audio,
transcript revisions, structured summary claims, and human review. This scope
and its evidence remain assigned to v1.15.0.

#### Durable meeting sessions

- Multi-source capture writes mixed, system, and microphone PCM journals as
  sources become available.
- Capture journals flush every second and reach an `fsync` checkpoint every
  five seconds.
- Atomic `session.json` updates preserve meeting identity, runtime state,
  artifact locators, and recovery guidance.
- Startup discovery presents recoverable sessions to the operator.
- Recovery reconstructs review-ready WAV evidence from the durable PCM
  journal and records the recovery acknowledgement.
- Recording and media import share the same transcript preparation and
  evidence model.

#### Reviewable transcript and claims

- Live ASR provides provisional feedback while durable audio remains the source
  for the final timestamped pass.
- Transcript segments progress through `provisional`, `final`, and `confirmed`
  states.
- Operators can edit text, rename speakers across the meeting, navigate review
  signals, and open the matching audio span.
- Transcript edits append review events and activate summary invalidation
  before the revised canonical transcript is saved.
- Decisions and action items retain stable claim identity, source segment IDs,
  support status, and review status.
- Confirmed actions emerge from current source evidence and human review.

#### Local structured summary runtime

- Summary generation receives the prepared corrected transcript from the
  current session.
- Nine field extractors run as one parallel application batch:
  `meeting_topic`, `participants`, `executive_summary`, `key_points`,
  `decisions`, `action_items`, `open_questions`, `risks`, and `next_steps`.
- Each field uses a dedicated prompt, an explicit JSON shape, Python
  validation, and one format-repair path.
- Python merges the validated fields and renders deterministic Markdown.
- The supported runner is local Ollama `gemma4:e4b-it-qat` through
  `/api/chat`, with `think=true`, `format=json`, `num_ctx=32768`,
  `num_predict=1536`, and `temperature=0`.
- Reasoning remains ephemeral runtime data; validated final content becomes the
  summary artifact.
- The local server starts with loopback binding, cloud access inactive, one
  server-side parallel sequence, Flash Attention, and q8 KV cache.

#### v1.15.0 release validation

The v1.15.0 runtime correction passed `398` regression tests. Its live local
LLM packet records 12 real model calls, including one complete nine-field
product pipeline. All nine final fields passed schema validation while AURA
ASR remained resident on the same 16 GB GPU.

The next validation layer uses a paired reviewed meeting corpus to measure
summary quality, source support, human correction time, queue time, and peak
VRAM. The complete product direction and activation gates live in
[`docs/aura-llm-agent-product-strategy.md`](docs/aura-llm-agent-product-strategy.md).

## Core Capabilities

| Capability | Current operating scope |
| --- | --- |
| Live recording | Captures system audio, microphone audio, or a balanced mixed stream through PulseAudio/PipeWire sources |
| Durable capture | Writes append-only PCM journals and atomic session state for recovery and final audio reconstruction |
| Scheduled recording | Arms a wall-clock start time and an optional wall-clock stop time through the standard recording path |
| Media import | Processes common FFmpeg audio and video containers through a visible, cancellable queue |
| GPU-only ASR | Runs Breeze ASR 25 through `faster-whisper` on the activated RTX/CUDA runtime |
| Traditional Chinese punctuation | Applies local model-backed punctuation when activated and deterministic full-width cleanup as the always-available preparation layer |
| Domain glossary correction | Uses conservative RapidFuzz thresholds and records each accepted correction |
| Transcript review | Supports timestamped edits, speaker renaming, review signals, audio-span playback, and revision-aware confirmation |
| Speaker diarization | Adds optional imported-file speaker labels through `pyannote.audio` |
| Local summary | Extracts nine structured meeting fields with local Gemma 4 and renders stable JSON and Markdown |
| Claim review | Connects decisions and actions to source segments, support status, review status, and append-only review events |
| Evidence search | Rebuilds a local SQLite FTS5 index for meetings, segments, and confirmed actions |
| Audio preparation | Provides FFmpeg normalization, bounded denoise presets, level protection, and progress telemetry |
| Meeting-distance modes | Offers `off`, `normal`, `far-speaker`, and `rescue-offline` policies with explicit activation paths |
| Track Splitter | Finds natural pause points around a target duration and exports ordered media chunks |
| Runtime Diagnostics | Reports GPU, CUDA, ASR model, FFmpeg, audio device, disk capacity, and output-path readiness |
| First Launch Check | Presents readiness gates and direct setup actions in the desktop UI |
| Local audit trail | Records content-free app and workflow events with redaction, retention, owner permissions, and hash-chain integrity |
| Native Agent Workspace | Runs offline deterministic assurance or a read-only Codex app-server turn through typed Qt cards, explicit approvals, evidence freshness, isolated worktrees, durable run artifacts, and validated architecture-package export |
| Windows onboarding | Provides check/start wrappers, diagnostic reports, hosted CI, RTX smoke scripts, and portable release packaging |

## Architecture and Ownership

The codebase keeps testable product logic outside Qt widgets and gives each
runtime concern one clear owner.

```text
project_aura/
├── pyproject.toml                  # package and dependency contract
├── Makefile                       # setup, check, build, and version commands
├── Start-AURA.* / Check-AURA.*    # Windows onboarding entry points
├── config/
│   └── domain_glossary.yaml        # conservative ASR correction terms
├── src/
│   ├── aura/
│   │   ├── asr/                    # transcription and punctuation services
│   │   ├── audio/                  # capture, denoise, export, and splitting
│   │   ├── diarization/            # optional speaker labeling
│   │   ├── llm/                    # local summary runtime integration
│   │   ├── system/                 # CUDA, paths, diagnostics, and updates
│   │   ├── agent/                  # provider contracts, controller, safety, persistence, worktrees, and reports
│   │   ├── ui/                     # PyQt6 widgets and interaction wiring
│   │   ├── audit.py                # content-free local audit events
│   │   ├── evidence_search.py      # rebuildable SQLite FTS5 index
│   │   ├── review.py               # transcript review and revision state
│   │   └── scheduling.py           # wall-clock scheduling rules
│   ├── asr_postprocess/            # glossary correction package
│   └── summary/                    # schemas, prompts, validation, rendering
├── scripts/                        # diagnostics, evaluation, and release tools
├── tests/                          # standard-library regression suite
├── docs/                           # design, setup, strategy, and roadmaps
├── artifacts/                      # measured public runtime evidence
└── img/                            # semantic product screenshots
```

### Module ownership

- `src/aura/settings.py` owns inspectable runtime defaults.
- `src/aura/asr/` owns file and live transcription behavior.
- `src/aura/audio/` owns source discovery, capture, mixing, denoise, export,
  recording durability, and media splitting.
- `src/aura/diarization/` owns speaker-model activation and timestamp overlap
  assignment.
- `src/aura/llm/` and `src/summary/` own local summary runtime, field schemas,
  validation, and deterministic rendering.
- `src/aura/review.py` owns transcript states, revisions, review events, and
  summary invalidation.
- `src/aura/evidence_search.py` owns rebuildable cross-meeting retrieval.
- `src/aura/agent/` owns provider-neutral events, deterministic Demo and Codex
  adapters, state, approvals, path policy, isolated worktrees, run artifacts,
  and architecture-package generation.
- `src/aura/system/` owns platform facts and readiness checks shared by the UI
  and command-line diagnostics.
- `src/aura/ui/` owns presentation, signals, and operator interaction.

The architecture rule is simple: behavior that can be verified independently
from Qt belongs in a service module with a focused regression check.

## Evidence-First Session Contract

### One meeting identity

Every recording or import receives one `meeting_id`. The corresponding
`session.json` acts as the artifact locator for audio, transcript segments,
summary claims, review events, and exported files. Each downstream stage reuses
the same identity.

### Durable audio source

The capture loop appends PCM frames to `.capture/` journals for the mixed
stream and each active source. Final WAV files are reconstructed from these
journals. Delivery formats such as M4A and MP3 are produced from the preserved
audio source, while the mixed WAV anchors transcript review and timestamp
playback.

### Transcript states and revisions

Live recognition supports operator awareness through provisional text. The
durable audio pass creates final timestamped segments. Human edits and
confirmation create revision-aware review events. Confidence, speaker
assignment, and overlap signals help operators prioritize attention.

### Source-linked summary claims

The structured summary records decisions and action items as claims with source
segment IDs. Each claim carries support and review state. Transcript revisions
activate a fresh summary evidence identity so confirmation always maps to the
current source.

### Rebuildable local retrieval

Canonical session artifacts remain the source of truth. `aura-evidence rebuild`
creates an atomic SQLite FTS5 derivative for fast local search. Query commands
open the index in read-only mode, and index replacement begins after schema and
version validation.

The current tool surface focuses on review and retrieval:

- meeting search;
- segment search;
- audio-span lookup;
- confirmed action retrieval.

External action connectors form a separately activated work package after a
real consumer, repeated operational demand, item-level approval, and audit
evidence establish the value.

## Desktop Workflow

### Transcription workspace

1. Open **Settings** and select the capture source, output policy, meeting
   distance mode, denoise profile, speaker labeling, and summary options.
2. Run **First Launch Check** to confirm GPU, CUDA, FFmpeg, audio devices,
   output capacity, ASR model, and local summary readiness.
3. Complete the meeting notice and consent confirmation.
4. Select **Start Recording** for live capture or **Import Media** for file
   transcription.
5. Follow waveform, status, transcript, progress, and activity feedback in the
   primary workspace.
6. Review timestamped segments, correct text, rename speakers, and open source
   audio spans.
7. Select **Summarize Transcript** or activate the post-ASR summary option.
8. Review source-linked decisions and actions, then export the required
   transcript and evidence formats.
9. Select **Open Output Folder** to inspect the complete session package.

### Settings and Runtime Diagnostics

![Project AURA Settings panel with audio, scheduling, summary, output, model, and diagnostics controls](./img/advanced-settings-v1.14.0.png)

*Figure 4. The Settings panel groups audio preparation, capture policy, scheduling, local summary, output location, model controls, and Runtime Diagnostics so operators can activate each capability from one workspace.*

Runtime Diagnostics reports:

- GPU identity and CUDA runtime readiness;
- ASR model load state and compute type;
- FFmpeg availability;
- input and output audio devices;
- selected output path and available disk capacity;
- local Ollama command, server, and model-tag readiness;
- speaker-diarization token readiness when that feature is selected.

The First Launch Check pairs each activation gate with focused setup guidance,
report copy, setup-folder access, and retry actions.

### Track Splitter

![Project AURA Track Splitter with source, output, target duration, tolerance, progress, and processing details](./img/track-splitter-v1.14.0.png)

*Figure 5. Track Splitter presents the complete source-to-output sequence and keeps duration targets, tolerance, progress, and processing details visible during long media jobs.*

The Track Splitter workflow:

1. Select an audio or video source.
2. Select the output directory.
3. Set the target segment length and tolerance.
4. Start processing.
5. Review ordered chunks created near natural pauses.

### AI Agent workspace

The third native tab uses one repository/thread workspace for General and
Evidence-Backed tasks. Start by typing in the centered composer. Three optional
suggestions provide feature, bug, and meeting-evidence entry points; the
complete registry remains available through intent inference and slash
commands. `Ctrl+K` opens or closes repository and task-thread search.

The sidebar groups threads by repository and shows Needs Attention only when
work requires a decision. The normalized timeline coalesces plans, narrative,
commands, changes, tests, reports, and failures through Qt model/view.
User and Aura narrative uses native Markdown with natural wrapping; one stable
work-progress digest groups observable lifecycle updates while command details
remain available through explicit disclosure.
Evidence, repository-file, and existing-artifact references appear as compact
removable context chips. Environment details open on demand, and
Evidence/Diff/Tests/Report/Run inspectors reserve no width until their actual
artifacts exist. Run Details also provides the sanitized diagnostic export.
Live is the startup default: AURA starts the Codex provider,
reads the current ChatGPT account, discovers compatible models, and presents a
ready composer before the first prompt. Provider thread and turn identities are
created automatically when that prompt is sent, so every external identity
corresponds to a real audited interaction. Demo remains available from the
Control Panel. Demo and Live share the same presentation pipeline,
request-scoped approvals, interruption, durable evidence, and Recovery Cards.
Subsequent Prompts remain in the same visible WorkItem conversation and resume
its Codex provider thread. **新增任務** is the explicit boundary that clears the
timeline and begins the next task. During an active turn, one compact status row
above the editor keeps Codex thinking, execution, approval, and stop feedback
inside the main workspace.

Live presents one structured Taiwan Traditional Chinese review before external
AI transfer: what will be sent, recognized sensitive-information handling,
what remains outside the initial payload, and the exact transformed text.
Technical metadata stays available through progressive disclosure, while
Repository permissions remain in execution settings and scoped approvals.
Demo states that content stays local and starts without representing an
external-transfer approval.

Live launches the compatible Codex app-server through supervised `QProcess`
JSONL stdio. ChatGPT login remains provider-managed. Quick, Standard, and
Expert resolve dynamically with no silent fallback. Read-only and
network-disabled operation form the default; implementation starts in an
isolated Git worktree. Commit, push, and PR creation activate only in Publish
after freshness, validation, secret, branch, remote, and hook checks. The
complete operating contract is in the
[Agent Workspace guide](docs/agent-workspace/README.md).

## Installation

### Recommended Linux runtime

- Ubuntu 22.04 or 24.04 desktop
- Python 3.10 or newer
- NVIDIA RTX GPU with an activated CUDA runtime
- PulseAudio or PipeWire with PulseAudio compatibility
- FFmpeg, PortAudio development headers, and Python development headers
- `uv` for the repository Make targets

Install system packages:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg portaudio19-dev python3-dev
```

### Quick start with uv

Run these commands once from the repository root to prepare the standard
application profile, including the model-backed Traditional Chinese
punctuation path, and launch AURA:

```bash
make setup-app
uv run aura
```

For later launches from an already synchronized checkout, the launch command
is simply:

```bash
uv run aura
```

`uv run` automatically selects the repository's `.venv`; activating it with
`source .venv/bin/activate` first is unnecessary. When using a manually
activated environment, run `aura` directly instead of combining activation
with `uv run`.

After the first launch, use **First Launch Check** to review GPU, CUDA, audio,
FFmpeg, local-summary, and Agent readiness. Offline Demo remains available
while optional model or Codex activation is in progress.

`pyproject.toml` and `uv.lock` form the dependency contract for local setup,
CI, and release builds.

### Pip environment

Use this path when intentionally managing the virtual environment with
standard `venv` and pip instead of `uv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[punctuation]"
aura
```

The package exposes three entry points:

- `aura`
- `project-aura`
- `aura-evidence`

### Complete development environment

```bash
make setup-dev
uv run aura
```

For a lockfile-frozen checkout with every optional dependency group:

```bash
uv sync --all-extras --frozen
uv run aura
```

This profile installs every declared optional dependency group for development,
testing, evaluation, diarization, punctuation, and model research.

### Local meeting summary

Install Ollama, activate the local service, and pull the supported model:

```bash
ollama pull gemma4:e4b-it-qat
```

AURA verifies `http://localhost:11434/api/tags`, starts the local service when
the command is available, checks the exact model tag, and presents model-pull
actions through the desktop UI.

### Speaker diarization

```bash
python -m pip install -e ".[diarization]"
export HUGGINGFACE_TOKEN=hf_your_token_here
```

Accept the Hugging Face terms for
`pyannote/speaker-diarization-community-1`, then provide
`HUGGINGFACE_TOKEN`, `HF_TOKEN`, or an `AURA_HF_TOKEN_FILE` path through the
local secret environment.

## Configuration Defaults

| Setting | Default |
| --- | --- |
| Sample rate | `16000 Hz` |
| Audio frame | `30 ms` / `480 samples` |
| WebRTC VAD level | `3` |
| ASR model | `SoybeanMilk/faster-whisper-Breeze-ASR-25` |
| ASR device | `cuda` |
| ASR compute type | `int8` |
| ASR beam size | `5` |
| Language | `zh` |
| Target volume | `-20 dBFS` |
| Live capture source | System audio and microphone |
| Live maximum segment | `16.0 seconds` |
| Live energy gate | `1000.0 RMS` |
| Recording delivery format | `M4A / AAC-LC 96k` |
| Meeting distance mode | `off` |
| Denoise preset | `off` |
| Speaker diarization | Operator-activated; imported media; `2-6` speakers |
| Traditional Chinese punctuation | Active |
| Local summary | Operator-activated |
| Splitter target | `40 minutes` |
| Splitter tolerance | `5 minutes` |
| Agent mode | `Live`; Offline `Demo` remains available |
| Agent quality profile | `standard`; Quick, Standard, and Expert resolve dynamically |
| Agent safety profile | `read-only` |
| Agent network | Disabled |
| Agent concurrency | One active Live run; additional work remains queued |
| Agent approval | Request-scoped `Approve once`, `Reject`, or `Stop run` |
| Agent retention | Manual; no automatic deletion |

### Runtime environment variables

| Variable | Purpose |
| --- | --- |
| `AURA_RUNTIME_DIR` | Location for transient normalized WAV files and live transcript backup |
| `AURA_AUDIT_DIR` | Local audit-event directory |
| `AURA_AUDIT_ENABLED` | Audit-event activation control |
| `AURA_AUDIT_RETENTION_DAYS` | Local audit retention period; default `90` days |
| `HUGGINGFACE_TOKEN` / `HF_TOKEN` | Speaker-diarization model access |
| `AURA_HF_TOKEN_FILE` | Local file path that supplies the diarization token |
| `AURA_CLEARVOICE_PYTHON` | Python runtime for the separately activated ClearVoice evaluation path |
| `AURA_AGENT_RUN_ROOT` | Durable per-run Agent artifacts |
| `AURA_AGENT_WORKTREE_ROOT` | Approved detached Git worktrees |
| `AURA_AGENT_ALLOWED_ROOTS` | Platform-separated allowlist of selectable repository roots |
| `AURA_CODEX_EXECUTABLE` | Explicit local Codex CLI path |
| `AURA_CODEX_STARTUP_TIMEOUT_SECONDS` | Codex child-process startup bound |
| `AURA_CODEX_REQUEST_TIMEOUT_SECONDS` | Per-request JSONL response bound |
| `AURA_CODEX_MAX_MESSAGE_BYTES` | Provider message-size trust boundary |
| `AURA_AGENT_DEFAULT_MODE` | Startup mode; defaults to `live`, with `demo` available |
| `AURA_AGENT_DEFAULT_PROFILE` | `quick`, `standard`, or `expert` |
| `AURA_AGENT_DEMO_SPEED_MS` | Deterministic Demo playback interval |
| `AURA_AGENT_RETENTION_DAYS` | Reserved horizon; this release keeps cleanup manual |
| `AURA_AGENT_REPORT_OUTPUT_ROOT` | Suggested architecture-package export root |

The default transient runtime directory is:

```text
/tmp/project_aura/
```

Set a dedicated path when the runtime needs a different temporary storage
location:

```bash
export AURA_RUNTIME_DIR=/path/to/runtime
```

## Feature Behavior

### GPU-only ASR

AURA ASR runs on the CUDA execution contract. The settings layer, model loader,
file pipeline, live queue, runtime report, and smoke scripts share the same
device requirement. Runtime activation stops at a clear product-facing gate
when CUDA libraries or the ASR model require attention.

The file-transcription prompt guides the recognizer toward a professional
Traditional Chinese meeting record with full-width punctuation that follows
the speaker's tone. The Settings panel provides an editable prompt for each
workflow.

### Live capture and audio preservation

- Capture source choices include system audio, microphone, and a mixed stream.
- PulseAudio/PipeWire discovery resolves the default sink monitor and
  microphone source.
- Active-source RMS balancing applies bounded gain and mix headroom.
- The live queue records segment duration, ASR elapsed time, real-time factor,
  queue size, and backlog.
- The inactivity safeguard closes a live recording after 20 continuous minutes
  of speech inactivity and trims the trailing inactive frames.
- Recorded delivery audio uses M4A/AAC by default, with MP3 as an available
  compatibility format.

### Traditional Chinese punctuation and glossary correction

The punctuation layer recognizes Traditional Chinese transcript content and
applies readable full-width punctuation. The model-backed path uses
`p208p2002/zh-wiki-punctuation-restore`. The deterministic preparation path
normalizes punctuation width, spacing, duplicates, and sentence endings.

Glossary correction runs after ASR and before summary generation. RapidFuzz
matches terms against `config/domain_glossary.yaml` with category-specific
confidence thresholds. Each accepted change appears in the correction log,
while raw ASR text remains available for comparison.

### Speaker diarization

Speaker diarization is an imported-media capability. The pipeline:

1. prepares the source audio;
2. runs Breeze ASR;
3. runs `pyannote/speaker-diarization-community-1`;
4. maps each transcript segment to the speaker turn with the greatest timestamp
   overlap;
5. emits labels such as `SPEAKER_00` and `SPEAKER_01`;
6. presents speaker labels for operator review and meeting-wide renaming.

Equal minimum and maximum speaker counts activate an exact speaker count.
Different values activate the configured speaker range.

### Local structured summary

The summary pipeline receives the corrected transcript associated with the
current session. Its source of truth is structured JSON. Deterministic Markdown
rendering creates stable meeting notes for review, GitHub, Notion, Google Docs,
and email handoff.

The direct script path supports repeatable summary generation:

```bash
PYTHONPATH=src uv run python scripts/generate_meeting_summary.py \
  --transcript path/to/meeting_corrected.txt \
  --output-md reports/meeting_summary.md \
  --output-json reports/meeting_summary.json
```

The validated generation contract is:

| Parameter | Value |
| --- | --- |
| Base model | `google/gemma-4-E4B-it` |
| Ollama model tag | `gemma4:e4b-it-qat` |
| Endpoint | Local `/api/chat` |
| Reasoning | `think=true` |
| Context window | `32768` |
| Generation budget | `1536` |
| Temperature | `0` |
| Server parallelism | `1` |

vLLM is the next throughput candidate. Its implementation gate opens when
paired measurements demonstrate sustained concurrent demand or an agreed
queue-time, latency, throughput, or VRAM advantage.

### Denoise and meeting-distance modes

The desktop UI offers four meeting-distance policies:

- `off`: direct capture and preparation;
- `normal`: lightweight meeting-room preparation;
- `far-speaker`: stronger VAD bridging, bounded segment gain, and the medium
  preparation floor;
- `rescue-offline`: an imported-media evaluation path for ClearVoice or
  ClearerVoice.

The built-in denoise presets are `off`, `light`, and `medium`. Short buffers use
adaptive FFT and hop sizes. Silent buffers remain intact. DeepFilterNet3 and
ClearVoice stay in separate environments so the primary NumPy 2 application
contract remains stable.

Promotion of a new default begins with a fixed, reference-backed far-field
corpus and measured transcript quality. See
[`docs/denoise_upgrade_plan.md`](docs/denoise_upgrade_plan.md).

### Runtime diagnostics and local audit

The runtime report centralizes platform facts for command-line tools, ASR
activation guidance, and the desktop UI. The local audit system records
content-free lifecycle, UI, model, recording, import, summary, splitter, and
diagnostic events.

Audit stewardship includes:

- transcript, summary, audio, prompt, credential, and path redaction;
- stable lowercase event identifiers;
- per-session sequence numbers;
- SHA-256 hash-chain integrity;
- owner-focused local permissions;
- configurable retention;
- Markdown and JSON analysis reports;
- workflow completion, latency, repeated-action, and anomaly review signals.

Canonical design:
[`docs/audit-event-system-design.md`](docs/audit-event-system-design.md).

### Track Splitter

Track Splitter decodes the source through FFmpeg/pydub, locates silence near
the configured target duration, exports ordered chunks, and reports progress.
MP3 exports reuse the source bitrate when the media metadata provides it.

## Session Artifacts and Data Layout

### Output location policy

Settings provides three output policies:

- **Same folder as source/recording** keeps artifacts beside the selected
  source or recording package.
- **Project outputs/transcripts folder** stores artifacts under
  `outputs/transcripts/`.
- **Custom folder** sends session artifacts to an operator-selected location.

### Canonical session package

A completed workflow can contain a canonical session directory:

```text
{base}_session/
├── session.json
├── .capture/
│   ├── mixed.pcm
│   ├── system.pcm
│   └── microphone.pcm
├── {recording}.wav
├── {recording}_system.wav
├── {recording}_microphone.wav
├── prepared_transcript.json
├── segments.json
├── summary.json
└── review_events.jsonl
```

Operator-facing transcript and telemetry artifacts remain beside the session
directory under the selected output policy:

```text
{base}_raw.txt
{base}_corrected.txt
{base}_summary.txt
{base}_final.txt
{base}_correction_log.json
{base}_processing_metrics.json
{base}_event_log.json
{base}_runtime.log
review exports in JSON, Markdown, SRT, or VTT
```

The exact set reflects the selected capture sources and activated processing
features. `session.json` records the authoritative artifact locators.

### Agent run package

Agent execution uses a separate canonical run directory:

```text
<agent-run-root>/<run-id>/
├── run.json
├── context.json
├── events.jsonl
├── approvals.jsonl
├── provider.json
├── evidence.json
├── commands.jsonl
├── file-changes.json
├── diff.patch
├── tests.json
├── report-manifest.json
└── export/
```

Normalized events and approvals are append-only; JSON snapshots use atomic
replacement; terminal metadata records artifact digests. Agent packages
describe an Agent run and never replace canonical AURA meeting artifacts.
The sibling SQLite WAL catalog owns WorkItems, AgentRuns, evidence links,
repository profiles/grants, artifacts, drafts, queue order, and recovery state.
Schema changes use backup-first migration and integrity validation.

### Evidence search commands

```bash
aura-evidence rebuild outputs/transcripts outputs/aura-evidence.sqlite3
aura-evidence search-meetings outputs/aura-evidence.sqlite3 "acceptance"
aura-evidence search-segments outputs/aura-evidence.sqlite3 "organization name"
aura-evidence confirmed-actions outputs/aura-evidence.sqlite3
```

The rebuild command writes an atomic derivative from canonical session
artifacts. Meeting, segment, and confirmed-action queries use read-only index
connections.

## Validation and Evidence

### Current evidence summary

| Evidence layer | Result |
| --- | --- |
| v1.17.0 release regression | Current `608`-test full repository regression passes on Ubuntu 24.04 |
| Live timeline readability | `82` focused tests, `22/22` native states, zero blank items, 72-row acceptance mapping, and bounded performance gate pass |
| Native Agent Workspace validation | Architecture, domain, queue, Demo, Codex, Qt, policy, persistence, publication, security, recovery, reporting, accessibility, model/view scale, and migration checks pass |
| Native workspace soak | `50/50` tasks pass; 10 approvals, 10 stops, 30 provider failure/reconnect cycles, 10 Recovery Cards, and 1,323 integrity-verified audit events |
| Native control matrix | `36/36` reachable controls and state gates pass; ordinary interaction, progress projection, and visible-heartbeat gates remain within their release thresholds |
| Stable daily-use soak | `50/50` runs pass; 40 completed, 10 interrupted, 5 restarts, 5 Recovery Card exercises, and 12 workflows retain artifact and catalog integrity |
| v1.17.0 Agent Live minimum | One real Codex app-server turn is `valid_target_runtime`; Quick resolves `gpt-5.6-sol` with `low` effort, expected reply observed, no approval, unchanged checkout, clean process tree |
| v1.17.0 conversation continuity Live minimum | Two real Codex turns are `valid_target_runtime`; both expected replies are observed on one resumed provider thread with unchanged checkout and a clean process tree |
| v1.17.0 workspace-write Live minimum | One real approved-worktree turn is `valid_target_runtime`; the stable thread contract, scoped turn policy, unchanged checkout, and clean process shutdown pass |
| v1.17.0 architecture package | 25 reports, 23 Mermaid diagrams, machine-readable inventories, 37 ADRs, four BOMs, risks, screenshots, soak/live evidence, checksums, missing-evidence register, and validated ZIP |
| Dependency assurance | Compatible vulnerable packages upgraded; one macOS sdist advisory classified Low residual for the Ubuntu runtime |
| Redesign acceptance ledger | 94 rows: 90 `CONFIRMED`, 3 `PARTIALLY VERIFIED`, 1 `NOT VERIFIED`; Windows/macOS are `unavailable_not_passed` |
| AURA ASR live minimum | 10 real CUDA/int8 transcriptions over five public Common Voice 24 zh-TW clips |
| Paired ASR runtime | AURA Breeze ASR 25 and Meetily Breeze ASR 26 each classify as `valid_target_runtime` |
| Local LLM live minimum | 12 real calls, including one complete nine-field product pipeline |
| LLM schema validity | 9 of 9 final product fields pass schema validation |
| Target-host scope | Ubuntu 24.04 is measured; Windows and macOS release-host execution remain `unavailable_not_passed` |

### GPU-only ASR packet

[`artifacts/asr-benchmark/2026-07-13-common-voice24-minimum/`](artifacts/asr-benchmark/2026-07-13-common-voice24-minimum/)
contains:

- five public Common Voice 24 zh-TW clips with reference text;
- 20 real transcriptions across the paired AURA and Meetily paths;
- request summaries and run configuration;
- event traces and error logs;
- GPU telemetry;
- latency analysis;
- runtime validity classification;
- source manifest and final decision report.

The clean-speech minimum validates the paired GPU execution contract.
Long-form, far-field, overlapping, and noisy meeting speech form the next
comparison layer.

Audit event:
[`docs/audit-events/2026-07-14-gpu-only-asr-live-benchmark/audit-event.md`](docs/audit-events/2026-07-14-gpu-only-asr-live-benchmark/audit-event.md).

### Local Gemma 4 packet

[`artifacts/llm-runtime/2026-07-23-ollama-gemma4-e4b-qat-minimum/`](artifacts/llm-runtime/2026-07-23-ollama-gemma4-e4b-qat-minimum/)
contains:

- the exact Ollama and model configuration;
- 12 real model requests;
- a complete nine-field AURA summary run;
- request summaries and event traces;
- GPU telemetry with AURA ASR resident;
- schema and runtime validity reports;
- latency, analysis, source manifest, and final product decision.

This packet validates local execution, reasoning/content separation,
structured completion, and shared-GPU operation. The paired reviewed corpus
adds product-quality and human-effort evidence.

## Development and Testing

### Run the complete check

```bash
make check
```

This command compiles source and tests, then runs the standard-library
regression suite.

Equivalent commands:

```bash
QT_QPA_PLATFORM=offscreen PYTHONWARNINGS=error::ResourceWarning \
  uv run python -m unittest discover -s tests
uv run python -m compileall -q src tests scripts
```

### Focused release checks

```bash
PYTHONPATH=src python -m unittest -q \
  tests.test_versioning \
  tests.test_bump_version

uv run python scripts/check_public_anonymization.py
uv run python scripts/check_public_anonymization.py --all-worktrees
```

The first command validates the active checkout. The second validates every
registered worktree before publication while preserving each worktree's own
branch and uncommitted state.

Historical stewardship diagnostics:

```bash
uv run python scripts/check_public_anonymization.py \
  --all-worktrees --git-objects --git-metadata
```

This broader command validates the published replacement lineage at zero
findings after the authorized history activation. It remains read-only.
Existing local clones that retain earlier refs, reflogs, or unreachable objects
continue to report those retained recovery objects until their owner activates
the separate local-cleanup path.

Stable daily-use release gates:

```bash
QT_QPA_PLATFORM=offscreen uv run python \
  scripts/run_agent_stable_daily_soak.py \
  --repository . --output artifacts/stable-daily-assurance --runs 50

QT_QPA_PLATFORM=offscreen uv run python \
  scripts/run_agent_live_codex_smoke.py \
  --repository . --output artifacts/stable-daily-assurance/live-codex
```

### Coverage areas

The regression suite covers:

- file import preparation, formatting, cleanup, queueing, and cancellation;
- durable recording journals, checkpoints, recovery, and partial audio
  preservation;
- session identity, transcript revisions, review events, and stale-summary
  invalidation;
- source-linked decisions, actions, claim review, and confirmed-action search;
- SQLite schema validation, atomic rebuild, read-only queries, and path
  containment;
- CUDA activation, model loading, runtime diagnostics, and report formatting;
- live capture source discovery, RMS mixing, VAD, inactivity safeguards, and
  telemetry;
- M4A and MP3 export, normalization, limiter behavior, and FFmpeg progress;
- punctuation, glossary correction, correction logs, and artifact naming;
- speaker diarization timestamps and speaker-count policy;
- local Gemma prompts, schemas, reasoning contract, output validation, and UI
  runtime integration;
- denoise presets, meeting-distance modes, and evaluation gates;
- scheduled recording calculations;
- Track Splitter selection, ordering, export, and progress;
- audit redaction, integrity, retention, reporting, and workflow analysis;
- Agent event ordering, reducer transitions, deterministic branches, evidence
  freshness, transfer redaction, path and command policy, workflow/domain
  transitions, SQLite WAL migration, durable queue, recording resource
  governance, worktree isolation, explicit publication, fake and real Codex
  JSONL transport, compatibility/model discovery, approvals, interruption,
  native Qt rendering, recovery, support bundles, SBOMs, screenshots,
  checksums, soak evidence, and archive validation;
- Windows-hosted setup, packaging layout, and RTX smoke contracts.

### Build artifacts

```bash
make build
```

The build uses `uv build` to produce a source distribution and wheel from the
package metadata.

## Windows Runtime Path

Windows users can choose WSL2 for the Linux-aligned development contract or
the native Windows package for platform-specific onboarding and release work.
These paths share the AURA source while retaining separate host evidence.

### WSL2 Ubuntu 24.04 development path

WSL2 is the recommended Windows development path for reproducing AURA's
verified Linux architecture and v1.17.0 Agent Workspace contract. It provides
a real Ubuntu 24.04 userspace with WSLg GUI and audio integration while
preserving native Windows as its own release target.

#### 1. Install WSL2 and Ubuntu 24.04

Use Windows 11 or a supported Windows 10 release with hardware virtualization
enabled. Open PowerShell as Administrator:

```powershell
wsl --install Ubuntu-24.04
wsl --update
wsl --list --verbose
```

Restart Windows when requested, open Ubuntu 24.04, and create the Linux user
account. The distribution should report WSL version `2`; convert it only when
the final command reports version `1`:

```powershell
wsl --set-version Ubuntu-24.04 2
```

#### 2. Install and launch AURA inside Ubuntu

Keep the checkout in the WSL Linux filesystem, such as `~/src`, for Linux
filesystem semantics and performance:

```bash
sudo apt-get update
sudo apt-get install -y \
  ffmpeg git portaudio19-dev pulseaudio-utils python3-dev python3-venv

mkdir -p ~/src
cd ~/src
git clone https://github.com/JasonLn0711/project_aura-ag.git
cd project_aura-ag

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[punctuation]"
aura
```

WSLg presents the PyQt6 window on the Windows desktop. Live prepares the Codex
provider automatically when the AI Agent tab opens. Media import and Offline
Demo remain deterministic local paths while provider activation is in progress.

#### 3. Activate and verify the Agent Workspace

Live is the default Agent mode and requires a supported local Codex CLI plus
provider-managed ChatGPT sign-in:

```bash
codex --version
codex login
aura
```

When the existing Codex account is already signed in, AURA automatically reads
the account, discovers the compatible model profile, and focuses the composer.
When sign-in is required, complete it once in the desktop surface; AURA then
refreshes account and model readiness automatically. The first prompt creates
the provider thread and turn identities as part of the audited Live run.

The stable daily-use adapter evidence baseline is `codex-cli 0.145.0`. When the installed
version differs, follow the
[Codex compatibility refresh](docs/agent-workspace/codex-provider-guide.md#compatibility-refresh)
before treating a Live run as release evidence. The desktop remains useful in
Offline Demo while provider activation is in progress.

Run the repository checks and then one read-only Live turn:

```bash
QT_QPA_PLATFORM=offscreen PYTHONWARNINGS=error::ResourceWarning \
  uv run python -m unittest discover -s tests
uv run python -m compileall -q src tests scripts
git diff --check
```

The first Live validation keeps the source checkout unchanged, network access
disabled, and approvals empty. Activate isolated-worktree writing only for a
separately approved rehearsal.

#### 4. Validate GPU, audio, and device boundaries

Full Breeze ASR requires NVIDIA CUDA visibility. Install the current NVIDIA
driver on Windows and use its WSL CUDA support; keep the Linux display driver
outside the WSL distribution.

```bash
nvidia-smi
pactl info
pactl list short sources
```

WSLg supplies the GUI and PulseAudio-compatible input/output bridge. Actual
microphone names, system-monitor sources, and USB devices depend on the host,
so record a short sample and inspect the source list before a live meeting.
Use Microsoft's `usbipd-win` path when a required USB device is not exposed to
WSL. Media import remains the stable first validation path.

Official platform references:

- [Microsoft: Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install)
- [Canonical: Install Ubuntu 24.04 on WSL2](https://documentation.ubuntu.com/wsl/stable/howto/install-ubuntu-wsl2/)
- [Microsoft: Run Linux GUI apps with WSLg](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps)
- [Microsoft: WSLg GUI and audio integration](https://github.com/microsoft/wslg)
- [Microsoft: WSL filesystem guidance](https://learn.microsoft.com/en-us/windows/wsl/filesystems)
- [Microsoft: Connect USB devices to WSL](https://learn.microsoft.com/en-us/windows/wsl/connect-usb)
- [NVIDIA: CUDA on WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)
- [OpenAI: Codex CLI setup and Windows support](https://help.openai.com/en/articles/11096431)

Completing this path produces WSL2 evidence. Native Windows packaging,
filesystem behavior, and device integration remain the native Windows
validation contract.

### Native Windows portable onboarding

1. Install or update the NVIDIA driver.
2. Extract `aura-windows-portable-v<version>.zip`.
3. Run `Check-AURA.bat`.
4. Review `diagnostic_report.txt`.
5. Run `Start-AURA.bat`.

The wrappers prepare `.venv`, install dependencies, verify FFmpeg and NVIDIA
visibility, run the shared RTX/CUDA diagnostics, and launch the same PyQt6
application used by Linux.

### Native Windows developer validation

```powershell
nvidia-smi
python scripts/runtime_report.py
python scripts/windows_gpu_smoke.py
python scripts/windows_asr_artifact_smoke.py
```

The Windows path includes:

- hosted GitHub Actions for compile, unit, PyQt import, runtime report, and
  portable packaging;
- a gated self-hosted RTX lane for real model-load and ASR artifact smoke;
- root-level PowerShell and batch entry points;
- a versioned portable ZIP builder;
- platform-specific setup and activation guidance.

Detailed guides:

- [`docs/windows_setup.md`](docs/windows_setup.md)
- [`docs/windows_native_roadmap.md`](docs/windows_native_roadmap.md)
- [`docs/windows_known_issues.md`](docs/windows_known_issues.md)

## Release and Versioning

Project AURA uses semantic versioning. Package versions use
`MAJOR.MINOR.PATCH`; Git tags and GitHub Releases use `vMAJOR.MINOR.PATCH`.

Prepare a version:

```bash
make bump-version BUMP=patch RELEASE_DATE=YYYY-MM-DD
make check
make build
```

The version helper synchronizes:

- `pyproject.toml`;
- `src/aura/metadata.py`;
- `uv.lock`;
- the README `Refactor Version` row;
- the README `Next Release Candidate` row;
- the README `Latest Update` heading.

`Latest Published Tag` records the release tag that currently exists. The
candidate row records the package version preparing for its next annotated tag
and GitHub Release.

The complete release contract is documented in
[`docs/versioning.md`](docs/versioning.md).

## Troubleshooting

### GPU memory pressure

- Keep ASR compute type at `int8`.
- Close other GPU-intensive applications before long recordings.
- Use Runtime Diagnostics to review device state and model readiness.
- AURA releases model references and clears available CUDA cache during
  lifecycle cleanup.

### CUDA activation

- Run `nvidia-smi`.
- Run `python scripts/runtime_report.py`.
- Confirm CUDA, cuBLAS, cuDNN, `ctranslate2`, and `faster-whisper` readiness.
- Refresh the environment with `uv sync` after dependency updates.

### Audio source discovery

- Confirm microphone and output devices in system settings.
- Confirm the PulseAudio/PipeWire compatibility service.
- Inspect sources with:

```bash
pactl info
pactl list short sources
```

- Runtime status and event logs record the selected source and active capture
  path.

### Local summary activation

- Confirm `ollama` is available on `PATH`.
- Confirm the loopback service at `http://localhost:11434`.
- Confirm the exact model tag:

```bash
ollama list
ollama pull gemma4:e4b-it-qat
```

- Retry First Launch Check after the service and model become ready.

### Speaker diarization activation

- Install the `diarization` extra.
- Accept the model terms for
  `pyannote/speaker-diarization-community-1`.
- Provide `HUGGINGFACE_TOKEN`, `HF_TOKEN`, or `AURA_HF_TOKEN_FILE`.
- Run Runtime Diagnostics to confirm token and model readiness.

### Long media and output size

- Keep FFmpeg visible on `PATH`.
- Select an output location with at least 1 GiB of available capacity.
- Use Track Splitter for delivery-sized media chunks.
- Review processing metrics for normalization stages, elapsed time, and export
  paths.

### Agent provider and policy

- Continue in Demo when Codex is unavailable or signed out.
- Use the Login and Run inspectors for provider-managed authorization and
  redacted protocol diagnostics.
- Confirm the selected repository is inside `AURA_AGENT_ALLOWED_ROOTS`.
- Complete the data-boundary preview before a Live turn.
- Resolve a blocked Quick, Standard, or Expert profile through refreshed discovery or an
  explicit future fallback decision; AURA never silently downgrades.
- Review dirty omitted changes and select a safe source strategy before
  approved-worktree activation.
- Use Recovery Cards for explicit Resume, Inspect, or Abandon after restart.
- Use Publish only after validation, freshness, secret, branch, remote, and
  hook gates pass.
- Review [Agent troubleshooting](docs/agent-workspace/troubleshooting.md) for
  process, protocol, worktree, test, report, and recovery paths.
- For clipped narrative, blank summary cards, or repeated exit-zero activity,
  verify the checkout includes
  [ADR-037](docs/agent-workspace/adr/ADR-037-native-markdown-timeline-and-activity-digest.md)
  and run the focused timeline validation in the
  [local development guide](docs/agent-workspace/local-development-guide.md).

## Documentation Map

| Document | Purpose |
| --- | --- |
| [`docs/architecture_decisions.md`](docs/architecture_decisions.md) | Module ownership, GPU execution, session identity, evidence, output, and platform decisions |
| [`docs/agent-workspace/README.md`](docs/agent-workspace/README.md) | Native Agent operation, architecture, Codex provider, login, data boundary, security, Demo, validation, and rollback |
| [`docs/agent-workspace/transfer-review/current-state.md`](docs/agent-workspace/transfer-review/current-state.md) | Plain-language AI transfer-review baseline, structured native implementation, Demo/Live behavior, copy, interaction states, and visual evidence |
| [`docs/agent-workspace/transfer-review/acceptance-status.md`](docs/agent-workspace/transfer-review/acceptance-status.md) | Current 42-row transfer-review UX, interaction, security, architecture, and quality evidence |
| [`docs/agent-workspace/timeline-markdown/issue-and-resolution.md`](docs/agent-workspace/timeline-markdown/issue-and-resolution.md) | Live timeline Markdown, wrapping, empty-summary reconciliation, activity digest, safety, recovery, and field-validation record |
| [`docs/agent-workspace/timeline-markdown/acceptance-status.md`](docs/agent-workspace/timeline-markdown/acceptance-status.md) | Current 72-row timeline Markdown, layout, summary, activity, UX, and architecture evidence |
| [`docs/agent-workspace/conversation-continuity/issue-and-resolution.md`](docs/agent-workspace/conversation-continuity/issue-and-resolution.md) | Same-task multi-turn continuity, provider-thread resume, explicit new-task boundary, inline Codex activity, regression, Live evidence, and rollback |
| [`docs/privacy/public-anonymization-policy.md`](docs/privacy/public-anonymization-policy.md) | Public identity labels, archive and visual scope, regression gate, evidence path, and separately authorized history stewardship |
| [`docs/audit-events/2026-07-26-public-anonymization/audit-event.md`](docs/audit-events/2026-07-26-public-anonymization/audit-event.md) | Public anonymization inventory, corrective controls, machine event, validation, publication scope, and next stewardship gate |
| [`docs/agent-workspace/local-development-guide.md`](docs/agent-workspace/local-development-guide.md) | Agent checkout, focused tests, architecture-package generation, artifact inspection, and cleanup |
| [`docs/agent-workspace/final-implementation-report.md`](docs/agent-workspace/final-implementation-report.md) | Implemented scope, measured evidence, runtime validity, host gates, and release recommendation |
| [`docs/agent-workspace/ux-redesign/11-acceptance-status.md`](docs/agent-workspace/ux-redesign/11-acceptance-status.md) | Current 94-row UX, architecture, quality, and regression acceptance evidence |
| [`docs/agent-workspace/ux-redesign/12-usability-evaluation-results.md`](docs/agent-workspace/ux-redesign/12-usability-evaluation-results.md) | Automated interaction evidence and the five-participant usability activation gate |
| [`docs/audit-events/2026-07-26-agent-workspace-empty-state-microcopy/audit-event.md`](docs/audit-events/2026-07-26-agent-workspace-empty-state-microcopy/audit-event.md) | Empty-state microcopy issue, source preservation, root cause, implementation, visual evidence, regression, and machine audit lineage |
| [`docs/audit-events/2026-07-26-agent-workspace-transfer-review/audit-event.md`](docs/audit-events/2026-07-26-agent-workspace-transfer-review/audit-event.md) | Plain-language AI transfer-review issue, root cause, Live/Demo contract correction, validation, and machine audit lineage |
| [`docs/audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md`](docs/audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md) | Complete `thread/start` incident, root-cause correction, Live verification, and audit lineage |
| [`docs/audit-events/2026-07-26-agent-workspace-conversation-continuity/audit-event.md`](docs/audit-events/2026-07-26-agent-workspace-conversation-continuity/audit-event.md) | Conversation-retention and detached-status-window issue, root-cause correction, visual evidence, Live verification, and machine audit lineage |
| [`artifacts/agent-workspace/2026-07-26-conversation-continuity/`](artifacts/agent-workspace/2026-07-26-conversation-continuity/) | Original symptom, accepted screenshots, two-turn Live trace, focused/full validation, checksums, and content-free audit evidence |
| [`artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/`](artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/) | Before/after visuals, responsive states, performance, soak, checksums, and content-free audit evidence |
| [`artifacts/stable-daily-assurance/v1.17.0-2026-07-28/`](artifacts/stable-daily-assurance/v1.17.0-2026-07-28/) | v1.17.0 Ubuntu runtime validity, native controls, reliability soaks, privacy validation, and publication activation status |
| [`docs/aura-llm-agent-product-strategy.md`](docs/aura-llm-agent-product-strategy.md) | Product positioning, public pain evidence, local summary strategy, and Agent activation gates |
| [`docs/audit-event-system-design.md`](docs/audit-event-system-design.md) | Audit schema, privacy, integrity, retention, analysis, and operator controls |
| [`docs/asr_postprocess_fuzzy_glossary.md`](docs/asr_postprocess_fuzzy_glossary.md) | Glossary correction thresholds, artifacts, and validation path |
| [`docs/denoise_upgrade_plan.md`](docs/denoise_upgrade_plan.md) | Far-field corpus, denoise candidates, evaluation metrics, and promotion gate |
| [`docs/first-principles-aura-meetily-review.md`](docs/first-principles-aura-meetily-review.md) | Cross-repository product ownership and capability migration evidence |
| [`docs/refactor_plan.md`](docs/refactor_plan.md) | Refactor phases, module boundaries, and acceptance checks |
| [`docs/versioning.md`](docs/versioning.md) | Semantic version synchronization, checks, builds, tags, and releases |
| [`docs/windows_setup.md`](docs/windows_setup.md) | Windows environment preparation and RTX validation |
| [`docs/windows_native_roadmap.md`](docs/windows_native_roadmap.md) | Windows runtime and portable release direction |
| [`docs/windows_known_issues.md`](docs/windows_known_issues.md) | Platform activation guidance and tracked validation layers |

## Repository Data Stewardship

- Application source, tests, small stable fixtures, documentation, and public
  evidence packets belong in version control.
- Private recordings and transcripts belong in the operator-selected output
  location, `outputs/`, or a dedicated data repository.
- `tests/fixtures/` carries small, stable samples that directly support
  regression checks.
- `artifacts/` carries public, source-described, reproducible runtime evidence.
- `.record/`, local virtual environments, build products, transient runtime
  files, and private operator data stay within their designated local storage.
- Audit events remain content-free and apply redaction, local permissions,
  retention, and integrity controls.
- Credentials remain in local environment or secret-store paths.
- Public identity labels follow the
  [repository anonymization policy](docs/privacy/public-anonymization-policy.md)
  and its executable publication gate.

## License

Project AURA is available under the [MIT License](./LICENSE).

Copyright (c) 2026 Jason Chia-Sheng Lin.
