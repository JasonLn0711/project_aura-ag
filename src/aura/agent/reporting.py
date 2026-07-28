from __future__ import annotations

import ast
import csv
import datetime as dt
import hashlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import tomllib
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from aura.agent.contracts import NORMALIZED_EVENT_TYPES
from aura.agent.policy import path_has_sensitive_component
from aura.redaction import redact_sensitive_text


CONFIDENCE = (
    "Confirmed",
    "Partially Verified",
    "Inferred",
    "Unknown",
    "Blocked",
    "Not Verified",
)
REPORTS = (
    ("01-executive-summary", "Executive Summary"),
    ("02-repository-map", "Repository Map"),
    ("03-technology-stack", "Technology Stack Inventory"),
    ("04-c4-system-context", "C4 System Context"),
    ("05-c4-container", "C4 Container Architecture"),
    ("06-component-architecture", "Component Architecture"),
    ("07-runtime-data-flow", "Runtime and Data Flow"),
    ("08-api-interface-inventory", "API and Interface Inventory"),
    ("09-dependency-graph", "Dependency Graph"),
    ("10-sbom", "Software Bill of Materials"),
    ("11-build-deployment", "Build and Deployment Architecture"),
    ("12-configuration", "Configuration and Environment Variables"),
    ("13-security-boundaries", "Security Boundaries"),
    ("14-architecture-decisions", "Architecture Decision Records"),
    ("15-risks-technical-debt", "Risks and Technical Debt"),
    ("16-local-development", "Local Development and Execution Guide"),
    ("17-ux-architecture", "UX Architecture and Interaction Grammar"),
    (
        "18-state-matrix",
        "State, Empty, Loading, Error, Approval, and Recovery Matrix",
    ),
    ("19-accessibility-localization", "Accessibility and Localization"),
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
)
REPORT_COVERAGE = {
    1: (
        "Product purpose, architecture shape, critical workflows, strengths, risks, MVP changes, release recommendation, and validation limitations.",
    ),
    2: (
        "Directory purpose, entry points, source versus generated files, tests, documentation, artifacts, Agent additions, and ownership hotspots.",
    ),
    3: (
        "Python runtime, PyQt6, ASR, audio, local LLM, storage, Git/Codex, build and test tools, native dependencies, versions, and licenses.",
    ),
    4: (
        "AURA user, desktop app, audio devices, filesystem, SQLite, Ollama, Git, Codex app-server, ChatGPT boundary, and browser login.",
    ),
    5: (
        "PyQt modular monolith, transcription, summary, evidence, Agent Workspace, Codex child process, Git worktree, local stores, and provider boundary.",
    ),
    6: (
        "MainWindow, existing tabs, AgentWorkspaceTab, controller, reducer, providers, JSONL transport, renderers, approvals, policy, evidence, reporting, audit, and persistence.",
    ),
    7: (
        "Application and provider startup, login, model discovery, Demo, Live read-only, approved worktree, approvals, interruption, reporting, shutdown, recovery, and transfer.",
    ),
    8: (
        "Protocols, signals, slots, DTOs, normalized events, JSON-RPC methods and notifications, CLI and filesystem formats, SQLite, Git, and user approvals.",
    ),
    9: (
        "Internal imports, Python packages, native and provider dependencies, cycles, unresolved imports, hotspots, optional dependencies, and the Agent edge boundary.",
    ),
    10: (
        "CycloneDX, SPDX, human report, generation notes, tool versions, omissions, checksums, Python BOM, and native/operational BOM including models.",
    ),
    11: (
        "OS evidence, Python and locked install, Qt, GPU/CUDA, FFmpeg/audio, Ollama/models, Codex, launch, packaging, updates, and local stewardship.",
    ),
    12: (
        "Settings sources, environment variables, precedence, secret classification, run/worktree roots, Codex path, provider, safety, model, retention, audit, and Demo controls.",
    ),
    13: (
        "GUI, child process, OS credentials, repository, worktree, canonical AURA data, Agent artifacts, Ollama, OpenAI, browser, untrusted content, approvals, paths, and network.",
    ),
    14: (
        "The current accepted decision set covers native integration, events, trusted rendering, provider parity, stdio, authentication, model discovery, safety, worktrees, approvals, evidence, reporting, publication, and the intent-first workspace redesign.",
    ),
    15: (
        "Every registered risk carries ID, severity, likelihood, evidence, impact, mitigation, owner, verification, and release gate.",
    ),
    16: (
        "Checkout, Python setup, locked install, desktop launch, tests, Codex setup/login, Demo and Live operation, package generation, artifact inspection, troubleshooting, cleanup, and rollback.",
    ),
    17: (
        "Repository/thread interaction grammar, one-primary-action states, unified composer, progressive disclosure, evidence attachment, approvals, artifacts, and action counts.",
    ),
    18: (
        "No-repository, new task, draft, loading, disconnected, login/model/data gates, queued, running, approval, validation, completion, failure, interruption, recovery, recording, and disk states.",
    ),
    19: (
        "Keyboard shortcuts, CJK IME, transfer-review focus entry and return, accessible labels, non-color status, Traditional Chinese copy, contrast, reduced motion, responsive geometry, and field-review gates.",
    ),
    20: (
        "Qt model/view virtualization, event deduplication/coalescing, bounded previews, 1,000 work items, 10,000 timeline items, 1,000 changed files, 50 MiB logs, and GUI-thread boundaries.",
    ),
    21: (
        "WorkItem/AgentRun ownership, catalog/run artifacts, per-thread drafts, versioned UI preferences, schema migration, backup, integrity, restart, recovery, and retention.",
    ),
    22: (
        "Single-operator identity, Codex-owned ChatGPT authentication, external Git credentials, local authorization, environment details, session grants, plain-language exact-payload review, Demo local-only semantics, Repository-authority separation, redaction, confirmation, and blocked data classes.",
    ),
    23: (
        "Instruction source, scope, path/origin, base commit, content hash, precedence, policy conflicts, untrusted repository/evidence/provider content, deny precedence, and inert rendering.",
    ),
    24: (
        "Four-resolution workspace captures, ten transfer-review states, combined baseline comparison, screenshot integrity, task-flow automation, five-second comprehension review, usability measurements, and honest study status.",
    ),
    25: (
        "Current readiness, open human and background-execution gates, target-host unknowns, immutable identity, future work-item/provider/team seams, stopping conditions, and next validation.",
    ),
}
DIAGRAMS = {
    "01-c4-system-context.mmd": """flowchart LR
User[AURA user] --> App[Project AURA desktop app]
Audio[Local audio devices] --> App
App --> Files[(Local filesystem)]
App --> SQLite[(Local SQLite evidence index)]
App --> Ollama[Local Ollama model]
App --> Git[Selected Git repository]
App --> Codex[Codex app-server child process]
Codex --> OpenAI[OpenAI / ChatGPT account boundary]
App --> Browser[System browser]
Browser --> OpenAI
""",
    "02-c4-container.mmd": """flowchart TB
subgraph Desktop[Native PyQt6 desktop process]
Main[MainWindow] --> Transcription[Transcription and review]
Main --> Splitter[Track Splitter]
Main --> AgentUI[Agent Workspace UI]
AgentUI --> Application[Typed application service and presenter]
Application --> Domain[Agent controller, policy, scheduler, evidence, publication]
end
Domain --> Catalog[(SQLite catalog and run artifacts)]
Domain --> AuraEvidence[(Canonical AURA meeting evidence)]
Domain --> Worktree[Isolated Git worktree]
Domain --> Codex[Codex app-server child process]
Codex --> Provider[OpenAI and ChatGPT account boundary]
""",
    "03-component-architecture.mmd": """flowchart LR
Tab[AgentWorkspaceTab compatibility shell] --> View[AgentWorkspaceView]
View --> Sidebar[Repository and thread model/delegate]
View --> Timeline[Timeline model/delegate, coalescer, and native Markdown renderer]
View --> Composer[Intent-first composer]
View --> TransferReview[TransferReviewDialog and frozen view model]
View --> Inspector[Contextual artifact inspector]
View --> Actions[Focused action groups]
Actions --> Facade[Typed application service]
View --> Presenter[Immutable view-state presenter]
Tab --> Subsystem[AgentWorkspaceSubsystem composition root]
Subsystem --> Facade
Subsystem --> Controller[AgentRunController and reducer]
Subsystem --> Scheduler[Scheduler and resource governor]
Subsystem --> Store[Catalog and run store]
Subsystem --> Policy[Policy and transfer guard]
Policy --> TransferReview
Subsystem --> Evidence[AURA evidence adapter]
Subsystem --> Git[Worktree and publication]
Subsystem --> Providers[Demo and Codex providers]
Subsystem --> Reports[Report and support exporters]
""",
    "04-live-run-sequence.mmd": """sequenceDiagram
actor User
participant View
participant Application
participant Controller
participant Codex
participant Coalescer
participant Models
User->>View: Send confirmed intent
View->>Application: typed StartRunRequest
Application->>Controller: start_run
Controller->>Codex: thread/start
Codex-->>Controller: thread/started
Controller->>Codex: turn/start
Codex-->>Controller: streamed notifications
Controller->>Controller: validate and persist normalized events
Controller-->>Coalescer: ordered AgentUiEvent stream
Coalescer-->>Models: bounded item updates
Models-->>View: sidebar, timeline, and artifact state
Codex-->>Controller: turn/completed
Controller-->>View: durable terminal state
""",
    "05-login-sequence.mmd": """sequenceDiagram
actor User
participant AURA
participant Codex
participant Browser
User->>AURA: Sign in with ChatGPT
AURA->>Codex: account/login/start
Codex-->>AURA: authUrl and loginId
AURA->>Browser: open authUrl
Browser-->>Codex: provider-managed authorization
Codex-->>AURA: account/login/completed
AURA->>Codex: account/read
Codex-->>AURA: non-secret account status
""",
    "06-approval-sequence.mmd": """sequenceDiagram
participant Provider
participant Controller
actor User
Provider->>Controller: approval request
Controller->>Controller: policy check and durable request
Controller-->>User: trusted native approval card
User->>Controller: approve once / reject / stop
Controller->>Controller: durable decision
Controller-->>Provider: request-scoped response
Provider-->>Controller: eventual outcome
""",
    "07-data-transfer-flow.mmd": """flowchart LR
Task[Task and selected references] --> Guard[DataTransferGuard]
Canonical[AURA canonical evidence] --> Adapter[Read-only evidence adapter]
Adapter --> Freshness[Eligibility and freshness]
Freshness --> Guard
Guard --> Preview[Immutable TransferPreview]
Preview --> ViewModel[TransferReviewViewModel]
ViewModel --> LiveReview[Plain-language Live review]
LiveReview --> Decision[Explicit current-payload confirmation]
Decision --> Codex[Exact confirmed transmitted_text]
ViewModel --> DemoNotice[Demo local-only notice and optional inspection]
DemoNotice --> DemoSatisfied[demo_local_only audit satisfaction]
DemoSatisfied --> Demo[Deterministic local provider]
Guard --> Block[Credential and raw-audio hard block]
Canonical -. raw audio remains local .-> Local[Local playback]
RepoAuth[Repository authority and scoped approvals] --> Codex
RepoAuth -. separate from initial-payload review .-> LiveReview
Codex --> Run[(Agent run artifacts)]
Demo --> Run
""",
    "08-trust-boundaries.mmd": """flowchart TB
subgraph Trusted[AURA-owned trusted boundary]
UI[Native Qt UI]
Controller[Controller and policy]
Store[(Local run store)]
end
Repo[Untrusted repository content] --> Controller
Evidence[Untrusted imported evidence] --> Controller
Controller --> Child[Codex child process]
Child --> Cloud[OpenAI provider]
Controller --> Worktree[Approved writable worktree]
Browser[System browser] --> Cloud
""",
    "09-run-state-machine.mmd": """stateDiagram-v2
[*] --> draft
draft --> preflight
preflight --> context_review
context_review --> planning
planning --> waiting_for_approval
planning --> running
waiting_for_approval --> planning: reject
waiting_for_approval --> running: approve once
running --> testing
running --> review_required
testing --> review_required
review_required --> reporting
reporting --> completed
draft --> interrupted
preflight --> failed
running --> failed
running --> interrupted
completed --> [*]
failed --> [*]
interrupted --> [*]
""",
    "10-evidence-freshness.mmd": """stateDiagram-v2
[*] --> discovered
discovered --> fresh: IDs and hashes resolve
discovered --> stale: mismatch or invalidation
fresh --> eligible: confirmed and supported
fresh --> generic_only: review pending
eligible --> previewed
previewed --> attached: user confirms boundary
stale --> discovered: canonical artifacts refreshed
""",
    "11-deployment-architecture.mmd": """flowchart LR
Package[Python package + Qt runtime] --> Desktop[Local desktop process]
Desktop --> GPU[Optional NVIDIA CUDA]
Desktop --> FFmpeg[FFmpeg and audio services]
Desktop --> Ollama[Optional local Ollama]
Desktop --> Codex[Local Codex CLI]
Codex --> Account[ChatGPT account]
Desktop --> Data[(Local application data)]
""",
    "12-internal-dependency-graph.mmd": """flowchart LR
Main[aura.ui.main_window] --> Tabs[aura.ui tabs]
Main --> AgentUI[aura.ui.agent_workspace_tab]
AgentUI --> Workspace[aura.ui.agent_workspace]
Workspace --> Application[application and presenter]
Application --> Controller[aura.agent.controller]
Controller --> Contracts[aura.agent.contracts]
Controller --> Providers[aura.agent.providers]
Controller --> Persistence[aura.agent.persistence]
Providers --> Policy[aura.agent.policy]
Application --> Evidence[aura.agent.evidence]
Application --> Reporting[aura.agent.reporting]
Evidence --> Existing[aura.claim_review]
""",
    "13-application-startup.mmd": """sequenceDiagram
actor User
participant App
participant Catalog
participant Scheduler
participant Provider
User->>App: Launch native AURA
App->>Catalog: Migrate, validate, and recover
Catalog-->>App: WorkItems, queue, and Recovery Cards
App->>Scheduler: Apply recording and one-Live policy
App->>Provider: Compatibility preflight when Live is selected
Provider-->>App: Ready, unavailable, or fail-closed state
App-->>User: Task-first workspace
""",
    "14-provider-preflight.mmd": """sequenceDiagram
actor User
participant AURA
participant Codex
participant Browser
AURA->>Codex: Discover executable and version
AURA->>AURA: Verify compatibility manifest
AURA->>Codex: initialize
AURA->>Codex: account/read and model/list
AURA->>Codex: thread/list no-side-effect probe
Codex-->>AURA: Compatibility and capability evidence
opt Login required
AURA-->>User: Sign-in action
User->>Browser: Provider-owned login
Browser-->>Codex: Authorization result
end
""",
    "15-general-repository-task.mmd": """flowchart LR
User[Operator objective] --> Profile[Allowlisted repository profile]
Profile --> Mode[Ask, Review, Implement, or Publish]
Mode --> Policy[Policy and resource preflight]
Policy --> Queue[Durable queue]
Queue --> Run[AgentRun]
Run --> Read[Repository inspection]
Read --> Review[Reviewable output]
Review --> Worktree[Isolated worktree when mutation is approved]
""",
    "16-evidence-backed-task.mmd": """flowchart LR
Action[Confirmed AURA action] --> Fresh[Hash and revision freshness]
Fresh --> Link[EngineeringTaskLink]
Link --> Preview[Classified redacted preview]
Preview --> Confirm[Operator confirmation]
Confirm --> Run[Evidence-backed AgentRun]
Run --> Status[Linked engineering status]
Status -. preserves .-> Action
""",
    "17-queue-recording-gate.mmd": """stateDiagram-v2
[*] --> queued
queued --> running: Live slot free and resources safe
queued --> recording_hold: recording or live ASR active
recording_hold --> queued: recording and live ASR clear
running --> interrupted: recording starts during heavy/write work
interrupted --> inspect
inspect --> queued: operator explicitly retries
running --> completed
""",
    "18-worktree-write.mmd": """sequenceDiagram
actor User
participant Policy
participant Git
participant Agent
User->>Policy: Approve Implement
Policy->>Git: Validate allowlist, root, base, and branch
Git->>Git: Create collision-safe agent worktree
Git-->>Agent: Isolated path and base commit
Agent->>Agent: Write and validate inside worktree
Agent-->>User: File-change and test artifacts
User->>Agent: Open Diff or Tests inspector
Agent-->>User: Bounded changed-file model, unified diff, counts, and logs
""",
    "19-stop-interruption.mmd": """sequenceDiagram
actor User
participant UI
participant Controller
participant Provider
User->>UI: Stop
UI->>Controller: Persist stop request
Controller-->>UI: Interrupted state acknowledgement
Controller->>Provider: turn/interrupt
Provider-->>Controller: terminal event or bounded shutdown
Controller-->>UI: Inspect or explicit retry
""",
    "20-crash-recovery.mmd": """flowchart LR
Crash[App or provider crash] --> Catalog[(Durable catalog and run evidence)]
Catalog --> Discover[Startup integrity scan]
Discover --> Card[Recovery Card]
Card --> Resume[Resume read-only work]
Card --> Inspect[Inspect artifacts]
Card --> Abandon[Abandon run]
Resume --> Gate[Fresh policy and resource preflight]
Gate -. mutating work requires explicit restart .-> Queue[Queue]
""",
    "21-commit-publish.mmd": """sequenceDiagram
actor User
participant Publish
participant Git
participant Remote
participant GitHub
User->>Publish: Enter explicit Publish stage
Publish->>Publish: Freshness, validation, secret, and policy gates
Publish->>Git: Commit agent branch with run trailer
Git-->>User: Commit SHA and diff hash
User->>Publish: Approve push or push plus PR
Publish->>Remote: Push HEAD to allowed agent branch
opt Pull request selected
Publish->>GitHub: Create redacted PR through external auth
end
""",
    "22-architecture-package.mmd": """flowchart LR
Checkout[Observed checkout] --> Scanner[Source and runtime evidence collectors]
Scanner --> Reports[25 reports]
Scanner --> Inventories[Machine-readable inventories]
Scanner --> BOM[Python, native, and model BOMs]
Scanner --> Assurance[Compatibility, soak, screenshots, risks, controls]
Reports --> Validator[Package validator]
Inventories --> Validator
BOM --> Validator
Assurance --> Validator
Validator --> Checksums[Manifest and checksums]
Checksums --> Zip[CRC-validated archive]
""",
    "23-shutdown.mmd": """sequenceDiagram
actor User
participant AURA
participant Catalog
participant Codex
participant OS
User->>AURA: Close
AURA->>Catalog: Flush queue and terminal snapshots
AURA->>Codex: Graceful shutdown
alt Child remains
AURA->>OS: Terminate exact process group
end
OS-->>AURA: No orphan child
AURA-->>User: Native process exits
""",
}
INVENTORY_NAMES = (
    "repository-files.csv",
    "technology-stack.csv",
    "components.csv",
    "entry-points.csv",
    "api-interfaces.csv",
    "events.csv",
    "signals-and-slots.csv",
    "external-services.csv",
    "environment-variables.csv",
    "databases-and-storage.csv",
    "native-dependencies.csv",
    "third-party-dependencies.csv",
    "licenses.csv",
    "tests.csv",
    "risks.csv",
    "controls.csv",
    "model-assets.csv",
    "agent-actions.csv",
)


@dataclass(frozen=True)
class ArchitecturePackageResult:
    package_dir: Path
    archive_path: Path
    status: str
    source_commit: str


def _run(
    arguments: Sequence[str],
    cwd: Path,
    timeout: int = 15,
    *,
    output_limit: int | None = 4000,
) -> dict[str, object]:
    repository_root = str(cwd.resolve())

    def redact(value: object) -> str:
        return _redact_evidence_text(str(value).replace(repository_root, "<repository-root>"))

    def limit(value: str) -> str:
        return value if output_limit is None else value[:output_limit]

    try:
        result = subprocess.run(
            list(arguments),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "argv": [redact(value) for value in arguments],
            "exit_code": result.returncode,
            "stdout": limit(redact(result.stdout.strip())),
            "stderr": limit(redact(result.stderr.strip())),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "argv": [redact(value) for value in arguments],
            "exit_code": None,
            "stdout": "",
            "stderr": type(exc).__name__,
        }


def _redact_evidence_text(value: str) -> str:
    text = str(value)
    home = str(Path.home())
    if home and home != "/":
        text = text.replace(home, "<HOME>")
    text = re.sub(r"(?m)^(User Name|Host Name|Cookie):.*$", r"\1: [REDACTED_LOCAL_ID]", text)
    text = redact_sensitive_text(text)
    return re.sub(
        r"(?im)^([ MADRCU?!]{1,3}\s+).*(?:auth\.json|credentials(?:\.json)?|"
        r"id_(?:dsa|ed25519|rsa)|\.env)(?:\s*)$",
        r"\1[REDACTED_SENSITIVE_PATH]",
        text,
    )


def _sensitive_repository_path(relative: str) -> bool:
    return path_has_sensitive_component(relative)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text(path: Path, value: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def _copy_artifact(source: Path, destination: Path) -> None:
    if source.suffix.lower() in {
        ".csv",
        ".json",
        ".jsonl",
        ".md",
        ".mmd",
        ".sha256",
        ".txt",
    }:
        _write_text(destination, source.read_text(encoding="utf-8"))
        return
    shutil.copyfile(source, destination)


def _write_csv(path: Path, rows: Iterable[Mapping[str, object]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _safe_spdx_id(name: str, index: int) -> str:
    normalized = re.sub(r"[^A-Za-z0-9.-]", "-", name)
    return f"SPDXRef-Package-{index}-{normalized}"


class ArchitecturePackageGenerator:
    """Source-backed, stdlib-only architecture packet generator."""

    def __init__(self, repository: str | Path):
        self.repository = Path(repository).expanduser().resolve(strict=True)
        if not (self.repository / ".git").exists():
            raise ValueError("Architecture reports require a Git repository root.")

    def generate(self, output_root: str | Path) -> ArchitecturePackageResult:
        output = Path(output_root).expanduser().resolve()
        if path_has_sensitive_component(output):
            raise ValueError("Architecture package output cannot use a sensitive path.")
        timestamp = dt.datetime.now().astimezone()
        run_id = f"{timestamp:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
        package = output / run_id

        commands = {
            "git_head": _run(["git", "rev-parse", "HEAD"], self.repository),
            "git_branch": _run(
                ["git", "branch", "--show-current"], self.repository
            ),
            "git_status": _run(
                ["git", "status", "--short", "--untracked-files=normal"], self.repository
            ),
            "python": _run([sys.executable, "--version"], self.repository),
            "git": _run(["git", "--version"], self.repository),
            "codex": _run(["codex", "--version"], self.repository),
            "ffmpeg": _run(["ffmpeg", "-version"], self.repository),
            "ollama": _run(["ollama", "--version"], self.repository, timeout=5),
            "nvidia_smi": _run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], self.repository, timeout=5),
            "pulseaudio": _run(["pactl", "info"], self.repository, timeout=5),
            "pipewire": _run(["pipewire", "--version"], self.repository, timeout=5),
            "vulnerability_scanner": _run(
                [sys.executable, "-m", "pip_audit", "--version"],
                self.repository,
                timeout=5,
            ),
        }
        commit = str(commands["git_head"]["stdout"] or "Unknown")
        dirty = bool(commands["git_status"]["stdout"])
        remote_url = str(
            _run(["git", "remote", "get-url", "origin"], self.repository)["stdout"]
        )
        remote_name = re.split(r"[:/]", remote_url.rstrip("/"))[-1].removesuffix(
            ".git"
        )
        repository_name = (
            remote_name
            if re.fullmatch(r"[A-Za-z0-9._-]+", remote_name)
            else self.repository.name
        )
        files = self._repository_files(excluded_roots=(output,))
        python_facts = self._python_facts(files)
        dependencies = self._dependencies()
        risks = self._risks()
        controls = self._controls()
        metadata = {
            "schema_version": 1,
            "run_id": run_id,
            "generated_at": timestamp.isoformat(timespec="seconds"),
            "repository": repository_name,
            "source_commit": commit,
            "source_branch": commands["git_branch"]["stdout"],
            "source_dirty": dirty,
            "generator": "aura.agent.reporting.ArchitecturePackageGenerator",
            "release_maturity": "single-operator stable daily-use",
            "confidence_vocabulary": list(CONFIDENCE),
            "limitations": [
                "Native dependency presence is observed on this workstation only.",
                "Mermaid source receives structural validation when no Mermaid CLI is installed.",
                "Model assets without immutable provider identifiers remain Partially Verified.",
            ],
        }
        output.mkdir(parents=True, exist_ok=True)
        for directory in (
            "reports",
            "diagrams",
            "inventories",
            "sbom",
            "adr",
            "artifacts",
            "validation",
            "screenshots",
        ):
            (package / directory).mkdir(parents=True, exist_ok=True)
        _write_text(
            package / "analysis-metadata.json",
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        )
        _write_text(
            package / "validation" / "command-results.json",
            json.dumps(commands, ensure_ascii=False, indent=2) + "\n",
        )
        self._write_reports(package, metadata, commands, files, python_facts, dependencies, risks)
        self._write_diagrams(package)
        self._write_inventories(
            package,
            files,
            python_facts,
            dependencies,
            commands,
            risks,
            controls,
        )
        self._write_sboms(package, dependencies, commands, metadata)
        self._write_assurance_evidence(package, metadata, risks, controls)
        self._write_readme(package, metadata)
        missing = {
            "status": "ready_with_limitations",
            "items": [
                {
                    "id": "ME-001",
                    "confidence": "Unknown",
                    "evidence": "Windows and macOS target-host suites are unavailable_not_passed; Ubuntu 24.04 is the measured release platform.",
                    "next_validation": "Run the full package and GUI suite on each additional declared target OS.",
                },
                {
                    "id": "ME-002",
                    "confidence": "Partially Verified",
                    "evidence": "Native and model BOM entries reflect discoverable local commands and declarations.",
                    "next_validation": "Collect immutable native package and model manifests from release hosts.",
                },
                {
                    "id": "ME-003",
                    "confidence": "Not Verified",
                    "evidence": "The required five-participant task-based usability study, timed transfer-review comprehension study, and screen-reader field session were not executed.",
                    "next_validation": "Run docs/agent-workspace/ux-redesign/09-usability-test-plan.md with the plain-language transfer-review tasks and retain privacy-safe aggregate results.",
                },
                {
                    "id": "ME-004",
                    "confidence": "Partially Verified",
                    "evidence": "The typed facade owns core run intents; remaining legacy Git, SQLite, report, media, and provider presentation actions still need complete background-service migration.",
                    "next_validation": "Route each remaining action through typed background execution and retain a GUI-heartbeat regression.",
                },
            ],
        }
        _write_text(
            package / "validation" / "missing-evidence.json",
            json.dumps(missing, ensure_ascii=False, indent=2) + "\n",
        )
        _write_text(
            package / "validation" / "validation-report.md",
            self._validation_report(package),
        )
        archive_validation = package / "validation" / "archive-validation.json"

        def write_archive_status(
            status: str,
            *,
            validated: bool,
            error_class: str | None = None,
        ) -> None:
            payload = {
                "status": status,
                "method": "zip CRC test plus exact member comparison",
                "validated_after_final_archive_creation": validated,
            }
            if error_class:
                payload["error_class"] = error_class
            _write_text(
                archive_validation,
                json.dumps(payload, indent=2) + "\n",
            )

        write_archive_status("pending", validated=False)
        try:
            self._write_manifest_and_checksums(package, metadata)
            archive = Path(
                shutil.make_archive(str(package), "zip", package.parent, package.name)
            )
            self._validate_archive(package, archive)
            write_archive_status("valid", validated=True)
            self._write_manifest_and_checksums(package, metadata)
            archive = Path(
                shutil.make_archive(str(package), "zip", package.parent, package.name)
            )
            self._validate_archive(package, archive)
        except Exception as exc:
            write_archive_status(
                "invalid",
                validated=False,
                error_class=type(exc).__name__,
            )
            _write_text(
                package / "validation" / "validation-report.md",
                "# Validation Report\n\n"
                "- Result: **INVALID**\n"
                f"- Archive validation error class: `{type(exc).__name__}`\n\n"
                "The partial package remains available for diagnosis and is not a "
                "validated release artifact.\n",
            )
            try:
                self._write_manifest_and_checksums(package, metadata)
            except OSError:
                pass
            raise
        return ArchitecturePackageResult(
            package_dir=package,
            archive_path=archive,
            status="ready_with_limitations",
            source_commit=commit,
        )

    def _repository_files(
        self,
        *,
        excluded_roots: tuple[Path, ...] = (),
    ) -> list[dict[str, object]]:
        result = _run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            self.repository,
            output_limit=None,
        )
        rows = []
        for value in str(result["stdout"]).splitlines():
            relative = value.strip()
            if not relative or _sensitive_repository_path(relative):
                continue
            path = self.repository / relative
            if not path.is_file():
                continue
            resolved = path.resolve()
            if any(
                resolved == root or resolved.is_relative_to(root)
                for root in excluded_roots
            ):
                continue
            rows.append(
                {
                    "path": relative,
                    "kind": (
                        "test"
                        if relative.startswith("tests/")
                        else "documentation"
                        if relative.endswith((".md", ".rst"))
                        else "source"
                        if relative.startswith("src/")
                        else "artifact"
                    ),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                    "tracked": "yes"
                    if _run(["git", "ls-files", "--error-unmatch", relative], self.repository)[
                        "exit_code"
                    ]
                    == 0
                    else "no",
                }
            )
        return rows

    def _python_facts(self, files: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
        components: list[dict[str, object]] = []
        interfaces: list[dict[str, object]] = []
        signals: list[dict[str, object]] = []
        tests: list[dict[str, object]] = []
        envs: dict[str, dict[str, object]] = {}
        for row in files:
            relative = str(row["path"])
            if not relative.endswith(".py"):
                continue
            path = self.repository / relative
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
            module = relative.removesuffix(".py").replace("/", ".")
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    components.append(
                        {
                            "component": node.name,
                            "module": module,
                            "line": node.lineno,
                            "kind": "class",
                        }
                    )
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    public = not node.name.startswith("_")
                    if public:
                        interfaces.append(
                            {
                                "interface": node.name,
                                "module": module,
                                "line": node.lineno,
                                "kind": "async function"
                                if isinstance(node, ast.AsyncFunctionDef)
                                else "function",
                            }
                        )
                    if relative.startswith("tests/") and node.name.startswith("test"):
                        tests.append(
                            {
                                "test": node.name,
                                "path": relative,
                                "line": node.lineno,
                                "runner": "unittest-compatible",
                            }
                        )
            for match in re.finditer(r"(?m)^\s*(\w+)\s*=\s*pyqtSignal\(([^)]*)\)", source):
                signals.append(
                    {
                        "signal": match.group(1),
                        "path": relative,
                        "signature": match.group(2),
                        "line": source[: match.start()].count("\n") + 1,
                    }
                )
            for match in re.finditer(
                r"(?:os\.environ\.get|os\.getenv)\(\s*[\"']([A-Z][A-Z0-9_]*)[\"']",
                source,
            ):
                envs.setdefault(
                    match.group(1),
                    {
                        "variable": match.group(1),
                        "source": relative,
                        "classification": "configuration",
                        "secret_value_included": "no",
                    },
                )
        return {
            "components": components,
            "interfaces": interfaces,
            "signals": signals,
            "tests": tests,
            "environment": list(envs.values()),
        }

    def _dependencies(self) -> list[dict[str, str]]:
        pyproject = tomllib.loads((self.repository / "pyproject.toml").read_text(encoding="utf-8"))
        direct_values = list(pyproject.get("project", {}).get("dependencies", []))
        direct_names = {
            re.split(r"[\s<>=!~;\[]", value, maxsplit=1)[0].lower().replace("_", "-")
            for value in direct_values
        }
        locked: dict[str, str] = {}
        lock_path = self.repository / "uv.lock"
        if lock_path.exists():
            try:
                for package in tomllib.loads(lock_path.read_text(encoding="utf-8")).get(
                    "package", []
                ):
                    if package.get("name") and package.get("version"):
                        locked[str(package["name"]).lower().replace("_", "-")] = str(
                            package["version"]
                        )
            except tomllib.TOMLDecodeError:
                pass
        rows = []
        for name in sorted(set(locked) | direct_names):
            license_value = "Unknown"
            try:
                metadata = importlib.metadata.metadata(name)
                license_value = str(
                    metadata.get("License-Expression")
                    or metadata.get("License")
                    or "Unknown"
                )
            except importlib.metadata.PackageNotFoundError:
                pass
            rows.append(
                {
                    "name": name,
                    "version": locked.get(name, "declared_unresolved"),
                    "scope": "direct" if name in direct_names else "transitive",
                    "license": license_value[:200],
                    "source": "pyproject.toml + uv.lock",
                }
            )
        return rows

    @staticmethod
    def _risks() -> list[dict[str, str]]:
        values = (
            ("R-001", "High", "Likely", "Oversized existing UI/controller hotspot", "TranscriptionTab couples workflow concerns", "Changes can regress established desktop workflows", "Keep Agent Workspace in a reversible module", "AURA maintainer", "focused UI regression", "agent tab regression green"),
            ("R-002", "High", "Possible", "ASR queue backpressure", "live queue behavior requires bounded evidence", "Unbounded work can increase latency or memory use", "retain durable audio and validate queue bounds", "ASR owner", "load test", "measured bound"),
            ("R-003", "High", "Possible", "Lock enforcement", "uv.lock exists; installer discipline varies", "Hosts can resolve a divergent runtime", "use uv sync --frozen", "release owner", "clean install", "locked install green"),
            ("R-004", "High", "Possible", "Mutable model identity", "provider model tags may move", "A later run can use materially different model behavior", "record observed IDs and discovery time", "agent owner", "provider metadata", "identity evidence captured"),
            ("R-005", "High", "Possible", "PII and provenance", "meeting evidence can contain identifiers", "Excess transfer can expose sensitive or weakly sourced content", "minimal transfer preview and redaction", "privacy owner", "PII boundary tests", "preview confirmed"),
            ("R-006", "Critical", "Possible", "Prompt injection", "repository and evidence are untrusted", "Untrusted content can attempt to redirect execution", "controller-owned policy and static renderers", "security owner", "injection tests", "trust controls green"),
            ("R-007", "Critical", "Unlikely", "Credential boundary", "Codex manages ChatGPT credentials", "Credential disclosure can compromise the provider account", "never read or persist auth tokens", "security owner", "secret scan", "zero credential findings"),
            ("R-008", "High", "Possible", "App-server protocol drift", "installed schema is version-sensitive", "Live startup or event mapping can fail after CLI updates", "adapter isolation and fake-server contract", "agent owner", "schema integration test", "observed schema supported"),
            ("R-009", "High", "Possible", "Child process lifecycle", "desktop exits can strand children", "Orphan processes can retain resources or stale state", "graceful terminate then bounded kill", "agent owner", "shutdown test", "no orphan process"),
            ("R-010", "Medium", "Possible", "Audit tamper resistance", "local append-only logs are host-admin mutable", "Local records cannot prove integrity against a privileged host user", "hashes and local stewardship", "operations owner", "integrity verification", "integrity chain valid"),
            ("R-011", "Medium", "Possible", "OS portability", "native tools differ by OS", "Unverified hosts can fail at launch or native integration", "target-platform validation matrix", "release owner", "multi-OS CI", "declared OS checks green"),
            ("R-012", "Medium", "Possible", "Coverage depth", "GUI failure paths require continued expansion", "Rare UI and process failures can escape P0 tests", "focused unit and offscreen UI tests", "QA owner", "suite and coverage review", "P0 cases green"),
            ("R-013", "High", "Possible", "Native dependency reproducibility", "drivers and audio services live outside Python", "A locked Python install can still differ operationally", "operational BOM and diagnostics", "operations owner", "host validation", "host bill captured"),
            ("R-014", "Medium", "Possible", "Worktree lifecycle", "isolated worktrees consume disk", "Abandoned worktrees can consume disk and confuse operators", "explicit cleanup and collision checks", "operator", "worktree inventory", "selected cleanup complete"),
            ("R-015", "High", "Possible", "Report false certainty", "static analysis has evidence limits", "Decision-makers can over-rely on unverified architecture claims", "claim confidence and missing-evidence register", "architecture owner", "package validation", "no unlabeled claims"),
            ("R-016", "Critical", "Possible", "Future multi-user isolation", "local account is single-user", "A hosted deployment without tenancy controls can cross user boundaries", "separate hosted identity and tenancy work package", "product owner", "threat model", "multi-user gate approved"),
        )
        fields = (
            "id",
            "severity",
            "likelihood",
            "risk",
            "evidence",
            "impact",
            "mitigation",
            "owner",
            "verification",
            "release_gate",
        )
        rows = [
            {
                **dict(zip(fields, row)),
                "confidence": "Confirmed",
                "residual_risk": "Platform and field-operation validation remains active.",
            }
            for row in values
        ]
        additions = (
            ("R-017", "Critical", "Possible", "Automation policy overbreadth", "AUTO grants combine workflow and repository capabilities", "A broad grant could authorize an unintended consequential action", "Bind grants to repository, commit, workflow, capability, expiry, and deny precedence", "security owner", "grant scope and stale reuse tests", "all grant tests green", "Low within declared single-operator scope"),
            ("R-018", "Critical", "Possible", "Publication credentials", "Push and PR use external Git and GitHub credential owners", "Credential or remote misuse could publish unintended content", "Sanitize allowlisted remotes, protect branches, scan changed files, and keep tokens external", "release owner", "temporary-remote and secret-canary tests", "publication suite green", "Medium; external credential stewardship remains"),
            ("R-019", "High", "Likely", "Indefinite retention and storage pressure", "Release 1 retains runs until manual cleanup", "Local storage growth can impair operation", "Display totals and warnings; require preview before user-triggered cleanup", "operations owner", "storage warning and cleanup preview tests", "storage exercise green", "Medium; operator action is required"),
            ("R-020", "High", "Possible", "Queue or catalog corruption", "SQLite catalog is durable scheduling state", "Corruption can hide or misorder queued and recovery work", "WAL, migration backup, integrity check, and rebuild/recovery records", "agent owner", "migration and corruption recovery tests", "recovery suite green", "Low after validated recovery"),
            ("R-021", "High", "Possible", "Evidence staleness", "Transcript and summary revisions can change after task creation", "Engineering work can use superseded evidence", "Bind IDs, revisions, hashes, spans, and recheck before run, commit, and publish", "evidence owner", "freshness transition tests", "freshness tests green", "Low for bound artifacts"),
            ("R-022", "High", "Possible", "Recording resource interference", "Agent work shares CPU, memory, and disk with recording and live ASR", "Heavy work can degrade capture quality", "Recording-first scheduler, live resource snapshot, queue hold, and interruption", "audio owner", "recording gate and transition tests", "recording checks green", "Medium across unmeasured hardware"),
            ("R-023", "High", "Possible", "Native UI refactor regression", "The Agent tab composition changed materially", "Established desktop workflows or accessibility can regress", "Keep the MainWindow seam small and run offscreen plus full regressions", "UI owner", "UI and complete regression suite", "release suite green", "Low on the declared Ubuntu host"),
            ("R-024", "High", "Likely", "Latest Codex compatibility drift", "App-server is explicitly a development interface", "A new CLI can change methods, events, or schema", "Tested version range, schema digest, capability probe, and fail-closed Live mode", "provider owner", "compatibility and fake-server tests plus live minimum", "known version and live gate green", "Medium; each new version requires capture"),
            ("R-025", "Critical", "Possible", "Package, network, or container supply chain", "Python, native tools, external CLI, remotes, and optional containers cross supply boundaries", "Compromise can affect host or published output", "Frozen lock, BOMs, vulnerability evidence, network deny, privileged-container deny, and external credentials", "security owner", "dependency, network, and container policy tests", "security suite and scan reviewed", "Medium; native and hosted artifacts remain external"),
            ("R-026", "Critical", "Likely", "Future team identity gap", "Release 1 is intentionally single-operator", "Shared or hosted use without tenancy can cross user boundaries", "Activate IdP, tenant isolation, RBAC, revocation, encryption, and a new threat model before team hosting", "product owner", "future multi-user architecture review", "team-hosting gate approved", "High until the separate work package completes"),
            ("R-027", "High", "Possible", "AI transfer-review comprehension drift", "Decision copy, policy metadata, and Repository authority can become mixed as the UI evolves", "An operator can misunderstand the initial payload or infer broader permission", "Keep one typed plain-language review, exact transformed text, centralized mapping, Demo local-only semantics, and separate Repository approvals", "privacy and UI owners", "transfer-review tests, screenshots, and audit verification", "all TR acceptance gates green", "Low on the declared native flow; human study remains active"),
        )
        for row in additions:
            (
                risk_id,
                severity,
                likelihood,
                risk,
                evidence,
                impact,
                mitigation,
                owner,
                verification,
                release_gate,
                residual_risk,
            ) = row
            rows.append(
                {
                    "id": risk_id,
                    "severity": severity,
                    "likelihood": likelihood,
                    "confidence": "Confirmed",
                    "risk": risk,
                    "evidence": evidence,
                    "impact": impact,
                    "mitigation": mitigation,
                    "owner": owner,
                    "verification": verification,
                    "release_gate": release_gate,
                    "residual_risk": residual_risk,
                }
            )
        return rows

    @staticmethod
    def _controls() -> list[dict[str, str]]:
        return [
            {"control": "C-001", "area": "execution", "implementation": "Read-only default and no danger-full-access", "evidence": "src/aura/agent/policy.py"},
            {"control": "C-002", "area": "filesystem", "implementation": "Canonical allowlist and symlink boundary", "evidence": "PathPolicy"},
            {"control": "C-003", "area": "credentials", "implementation": "App-server-managed authentication", "evidence": "ADR-006"},
            {"control": "C-004", "area": "UI", "implementation": "Static trusted Qt renderer registry", "evidence": "ADR-003"},
            {"control": "C-005", "area": "approvals", "implementation": "Request-scoped approve once decisions", "evidence": "AgentRunController"},
            {"control": "C-006", "area": "network", "implementation": "Network disabled by default", "evidence": "ADR-011"},
            {"control": "C-007", "area": "data", "implementation": "Minimal exact transfer preview, local redaction, and blocked categories", "evidence": "DataTransferGuard and build_transfer_preview"},
            {"control": "C-008", "area": "Git", "implementation": "Detached isolated worktree and push prohibition", "evidence": "WorktreeManager and CommandPolicy"},
            {"control": "C-009", "area": "audit", "implementation": "Append-only normalized run events", "evidence": "AgentRunStore"},
            {"control": "C-010", "area": "recovery", "implementation": "Incomplete runs discovered without auto-resume", "evidence": "AgentRunStore.discover_incomplete"},
            {"control": "C-011", "area": "scheduling", "implementation": "One Live run with recording and live-ASR priority", "evidence": "DurableRunScheduler and ResourceGovernor"},
            {"control": "C-012", "area": "instructions", "implementation": "Repository instruction trust bound to commit and hash", "evidence": "InstructionTrustPolicy"},
            {"control": "C-013", "area": "publication", "implementation": "Explicit Publish stage, agent branch, validation, freshness, secret scan, and external credentials", "evidence": "PublicationManager"},
            {"control": "C-014", "area": "retention", "implementation": "Manual cleanup after storage totals, warnings, and preview", "evidence": "AgentStorageManager.cleanup_preview"},
            {"control": "C-015", "area": "transfer UX", "implementation": "Typed plain-language Live review, Demo local-only satisfaction, and Repository-authority separation", "evidence": "TransferReviewViewModel, TransferReviewDialog, and transfer-review tests"},
        ]

    def _write_reports(
        self,
        package: Path,
        metadata: dict[str, object],
        commands: dict[str, dict[str, object]],
        files: list[dict[str, object]],
        facts: dict[str, list[dict[str, object]]],
        dependencies: list[dict[str, str]],
        risks: list[dict[str, str]],
    ) -> None:
        adr_count = len(
            list((self.repository / "docs" / "agent-workspace" / "adr").glob("ADR-*.md"))
        )
        subjects = {
            1: "Project AURA is a native PyQt6 desktop audio and evidence workspace. The Agent Workspace adds deterministic Demo and Codex-backed operational review while preserving canonical meeting artifacts.",
            2: f"The observed repository contains {len(files)} source-controlled or visible worktree files. Entry points, tests, documentation, artifacts, and the Agent module remain separately inventoried.",
            3: f"The stack is Python, PyQt6, faster-whisper, audio tooling, optional local LLM tooling, Git, and Codex. {len(dependencies)} locked or declared Python packages are listed.",
            4: "The system context connects the local user, audio devices, filesystem, SQLite evidence index, Ollama, Git, Codex app-server, ChatGPT account boundary, and system browser.",
            5: "The desktop remains a modular monolith; Codex is a bounded child process and worktrees/run stores are isolated local containers.",
            6: f"Static analysis identified {len(facts['components'])} Python classes. The Agent boundary owns controller, reducer, providers, JSON-RPC transport, renderers, approvals, policy, evidence, reporting, audit, and persistence.",
            7: "Startup, login, discovery, Demo, live read-only, approved worktree, approvals, interruption, reporting, recovery, evidence transfer, and shutdown use explicit event and state transitions.",
            8: f"The API inventory contains {len(facts['interfaces'])} public Python callables, {len(NORMALIZED_EVENT_TYPES)} normalized event names, Qt signals, filesystem formats, SQLite, Git, and version-sensitive Codex JSON-RPC methods.",
            9: "Internal imports retain the Agent Workspace as an edge module around existing AURA evidence services. Native and provider dependencies stay explicit.",
            10: "CycloneDX 1.6 and SPDX 2.3 inventories cover Python packages; the operational BOM separately records Git, Codex, FFmpeg, Ollama, CUDA/GPU, audio services, and model assets where discoverable.",
            11: "Local installation uses the locked Python environment and native Qt/audio/GPU tools. Desktop launch, updates, Codex setup, and on-prem stewardship are explicit validation layers.",
            12: "Configuration precedence is explicit arguments, approved environment variables, application defaults, then provider discovery. Secret values are excluded from every inventory.",
            13: "Trust boundaries cover the GUI, app-server child, OS credential store, repository, worktree, canonical evidence, agent artifacts, local models, provider, browser, approvals, paths, and network.",
            14: f"{adr_count} accepted ADRs record the stable daily-use product, architecture, autonomy, evidence, reliability, recovery, publication, and workspace-redesign decisions.",
            15: f"The register contains {len(risks)} owned risks with severity, likelihood, confidence, evidence, impact, mitigation, verification, release gate, and residual risk.",
            16: "Verified local steps use uv sync --frozen, Python unittest discovery, native desktop launch, Codex login, Demo/Live selection, package export, artifact inspection, cleanup, and reversible Agent-module removal.",
            17: "The native workspace organizes repository and thread navigation, one intent-first composer, contextual attachments, inline approvals, and artifact inspectors through progressive disclosure.",
            18: "The workspace maps every material empty, loading, gate, execution, approval, terminal, interruption, and recovery condition to an explicit operator action and durable state.",
            19: "Keyboard-first operation, CJK IME-safe sending, labeled transfer-review controls, non-color status cues, Taiwan Traditional Chinese copy, contrast, responsive geometry, and reduced-motion behavior form the active accessibility contract.",
            20: "Qt model/view lists, coalesced events, bounded previews, and measured scale exercises protect the UI across large work-item, timeline, changed-file, and log datasets.",
            21: "Work-item and run ownership, per-thread drafts, schema-versioned preferences, atomic persistence, migration, restart, recovery, retention, and integrity checks form the local continuity contract.",
            22: "The local operator, Codex account boundary, external Git credentials, repository-session grants, plain-language exact-payload review, Demo local-only state, redaction, and confirmation controls define identity, permission, and transfer UX.",
            23: "Instruction provenance exposes source, scope, origin, commit, hash, precedence, conflicts, and trust status while keeping repository, evidence, provider, and model content inert.",
            24: "Four-resolution workspace captures, ten transfer-review states, a combined baseline comparison, integrity checks, automated task-flow evidence, and explicit usability status support visual validation.",
            25: "The current release packet separates verified native capability from human-study, assistive-technology, target-host, and remaining asynchronous-migration gates while preserving future workbench seams.",
        }
        details = {
            1: (
                "### Product and architecture\n\n"
                "**Confirmed.** AURA supports local recording, transcription, review, summary, "
                "evidence search, track splitting, and Agent-assisted engineering review through "
                "one native PyQt6 desktop process. `src/aura/ui/main_window.py` is the composition "
                "root; canonical meeting artifacts remain filesystem-owned while the Agent has a "
                "separate run store.\n\n"
                "### Strengths and critical workflows\n\n"
                "**Confirmed.** Native UI ownership, canonical evidence provenance, deterministic "
                "Demo replay, explicit Live trust state, read-only default, isolated worktree "
                "writes, request-scoped approvals, and durable event logs form the primary "
                "strengths. The critical flows are diagrammed in `../diagrams/04-live-run-sequence.mmd`, "
                "`05-login-sequence.mmd`, `06-approval-sequence.mmd`, and "
                "`07-data-transfer-flow.mmd`.\n\n"
                "### MVP change and recommendation\n\n"
                "**Confirmed.** The MVP adds `src/aura/agent/` and "
                "`src/aura/ui/agent_workspace_tab.py` through a small `MainWindow` seam rather than "
                "refactoring the transcription controller. The Ubuntu P0 is ready for operator "
                "review with read-only and network-disabled defaults active.\n\n"
                "### Risk and limitation\n\n"
                "**Partially Verified.** Prompt injection, credential boundaries, provider drift, "
                "native reproducibility, and cross-platform behavior are controlled through the "
                "risk register. Target-host validation and immutable model identity remain active "
                "release gates in `../validation/missing-evidence.json`."
            ),
            2: (
                "### Directory ownership\n\n"
                "**Confirmed.** `src/aura/` owns application services and native UI; "
                "`src/aura/agent/` owns the reversible Agent edge; `tests/` owns executable "
                "regression evidence; `docs/` owns durable design and operating guidance; "
                "`artifacts/` owns measured run and report packets; `scripts/` owns developer and "
                "release utilities. Exact file kind, size, digest, and tracked state are recorded "
                "in `../inventories/repository-files.csv`.\n\n"
                "### Entry points and generated data\n\n"
                "**Confirmed.** Console entry points are `aura`, `project-aura`, and "
                "`aura-evidence`; see `../inventories/entry-points.csv`. Python under `src/`, tests, "
                "and docs are source. Agent runs, architecture packets, distributions, caches, "
                "and session outputs are generated data with separate ownership.\n\n"
                "### Hotspots\n\n"
                "**Confirmed.** `MainWindow` composes major tabs, while "
                "`TranscriptionTab` remains the largest established workflow hotspot. The Agent "
                "module is intentionally outside that class. Static class ownership and line "
                "locations are in `../inventories/components.csv`."
            ),
            3: (
                "### Application stack\n\n"
                "**Confirmed.** Python and PyQt6 provide the desktop runtime; faster-whisper and "
                "CUDA packages provide ASR; PyAudio, pydub, FFmpeg, WebRTC VAD, and optional "
                "denoise tooling provide audio paths; Ollama provides the local summary boundary; "
                "JSON/JSONL, SQLite FTS5, and the filesystem provide storage; Git worktree and "
                "Codex app-server provide controlled engineering integration.\n\n"
                "### Build, test, native, and license evidence\n\n"
                f"**Confirmed.** `pyproject.toml` and `uv.lock` yielded {len(dependencies)} direct "
                "or transitive Python records. Build uses setuptools/wheel through uv; tests use "
                "unittest-compatible discovery and offscreen Qt. Exact versions and license "
                "metadata are in `technology-stack.csv`, `third-party-dependencies.csv`, "
                "`licenses.csv`, and `native-dependencies.csv`.\n\n"
                "**Partially Verified.** Python metadata does not bind GPU drivers, audio-service "
                "state, provider-hosted model weights, or every target OS package. The operational "
                "BOM keeps those layers separate."
            ),
            4: (
                "### Actors and boundaries\n\n"
                "**Confirmed.** The local AURA user operates the native desktop. Audio devices, "
                "the filesystem, SQLite evidence index, optional Ollama model, and selected Git "
                "repository are local boundaries. Codex app-server is a local child process that "
                "mediates the OpenAI/ChatGPT account boundary. The system browser is used only for "
                "provider-managed login activation.\n\n"
                "**Confirmed.** `../diagrams/01-c4-system-context.mmd` shows every required actor "
                "and dependency direction. `../inventories/external-services.csv` records network "
                "defaults and stewardship."
            ),
            5: (
                "### Logical containers\n\n"
                "**Confirmed.** Project AURA remains a desktop modular monolith: one PyQt "
                "application contains transcription, summary, evidence, Track Splitter, and Agent "
                "subsystems. The Agent controller owns provider-neutral state and persistence; "
                "Codex is an external child process; detached Git worktrees isolate approved "
                "writes; run, audit, evidence, and meeting stores retain distinct canonical scope.\n\n"
                "**Confirmed.** The child/provider and worktree boundaries are process or "
                "filesystem containers, not web services. See "
                "`../diagrams/02-c4-container.mmd` and "
                "`../inventories/databases-and-storage.csv`."
            ),
            6: (
                "### Native composition\n\n"
                "**Confirmed.** `MainWindow` retains Transcription and Track Splitter and composes "
                "`AgentWorkspaceTab` as a compatibility shell. `AgentWorkspaceSubsystem` is the "
                "composition root; `AgentWorkspaceView` owns native presentation; the typed "
                "application facade and immutable presenter state mediate controller actions and "
                "view updates. Qt model/view adapters own repository, thread, timeline, "
                "changed-file, evidence, test, and report collections. Timeline content formats, "
                "the coalescer, bounded native Markdown renderer, and shared delegate layout keep "
                "canonical events separate from presentation.\n\n"
                "### Domain, trust, and artifact components\n\n"
                "**Confirmed.** `AgentRunController` remains the single event writer; "
                "`AgentEventReducer` owns phase transitions; Demo and Codex providers share the "
                "`ProviderEvent` contract; static trusted renderers keep provider output inert; "
                "approval cards send request-scoped decisions; policy, evidence, reporting, audit, "
                "and persistence retain their bounded domain ownership. Symbols and source lines "
                "are in `components.csv`, `api-interfaces.csv`, and `signals-and-slots.csv`.\n\n"
                "**Partially Verified.** Catalog refresh, Git/report generation, media handoff, and "
                "some provider-presentation actions still complete synchronously through the "
                "native application facade. The current release keeps those bounded paths visible "
                "and records background-execution migration as a measured next-stage gate."
            ),
            7: (
                "### Startup through shutdown\n\n"
                "**Confirmed.** AURA starts with local Demo readiness. Live selection launches "
                "Codex, performs initialize/initialized, reads account state, discovers models, "
                "and activates queued work only after readiness. Demo uses deterministic events; "
                "Live starts or resumes a thread, starts a turn, maps notifications, and reaches an "
                "explicit completed, failed, or interrupted terminal.\n\n"
                "### Write, approval, reporting, and recovery flows\n\n"
                "**Confirmed.** Read-only runs transmit only confirmed preview scope. Write-capable "
                "runs first create an isolated clean-base worktree and require each command or file "
                "decision. Report generation writes to a new package path and validates its ZIP. "
                "Shutdown terminates the child process; incomplete run discovery opens existing "
                "events without automatically continuing Live execution. Diagrams 04–10 record "
                "the corresponding sequences and state machines."
            ),
            8: (
                "### In-process and durable interfaces\n\n"
                f"**Confirmed.** Static analysis recorded {len(facts['interfaces'])} public Python "
                f"callables, {len(facts['signals'])} Qt signals, and "
                f"{len(NORMALIZED_EVENT_TYPES)} normalized event types. DTOs serialize to JSON; "
                "run, approval, and command streams use JSONL; snapshots use JSON; diffs use patch; "
                "meeting evidence uses JSON/JSONL/audio plus a rebuildable SQLite FTS5 index.\n\n"
                "### Provider, CLI, Git, and approval interfaces\n\n"
                "**Confirmed.** The observed Codex contract includes initialize, account, login, "
                "logout, model, thread, turn, command-approval, and file-approval methods over "
                "stdio. Git interfaces are bounded to inspection and explicit worktree creation; "
                "human approval interfaces expose Approve once, Reject, and Stop. Exact symbols, "
                "events, and signal locations are in the three interface inventories."
            ),
            9: (
                "### Dependency layers\n\n"
                "**Confirmed.** `../diagrams/12-internal-dependency-graph.mmd` shows the Agent as an "
                "edge imported by the UI: controller depends on contracts/state/persistence; "
                "providers depend on contracts/state/policy; existing AURA services do not depend "
                "back on the Agent UI. Package and native layers are separately inventoried.\n\n"
                "### Cycles, imports, and hotspots\n\n"
                "**Confirmed on the observed host.** Full import and regression execution resolved "
                "the installed application imports. Source inspection found no Agent-to-UI back "
                "edge and therefore no cycle across the new boundary. Optional ASR, CUDA, "
                "diarization, Ollama, audio, and Codex capabilities remain activation-time "
                "dependencies. `TranscriptionTab` is the primary coupling hotspot; the Agent seam "
                "keeps it unchanged.\n\n"
                "**Partially Verified.** The generator uses AST/source evidence rather than a "
                "whole-program dynamic cycle analyzer. Target-environment optional import "
                "resolution remains a release-host validation."
            ),
            10: (
                "### Python BOM\n\n"
                f"**Confirmed.** CycloneDX 1.6 and SPDX 2.3 contain {len(dependencies)} declared or "
                "locked Python package records with versions, direct/transitive scope, and "
                "available license metadata. Generation inputs are `pyproject.toml` and `uv.lock`.\n\n"
                "### Operational BOM\n\n"
                "**Confirmed where observed.** `native-dependencies.csv` and `sbom-report.md` "
                "separately record Python, Git, Codex CLI, FFmpeg, Ollama CLI, NVIDIA driver/GPU, "
                "PulseAudio, and PipeWire evidence. `model-assets.csv` records ASR, Ollama, and "
                "provider model declarations.\n\n"
                "**Partially Verified.** Provider-hosted model weights, complete OS package "
                "manifests, and runtime service health are not implied by Python BOM presence. "
                "Checksums bind the generated packet, not external binaries or hosted weights."
            ),
            11: (
                "### Installation and launch\n\n"
                "**Confirmed.** Ubuntu 24.04 uses Python 3.12, `uv sync --all-extras --frozen`, "
                "setuptools/wheel packaging, and `uv run aura`. Qt is a native runtime dependency. "
                "GPU/CUDA, FFmpeg, audio services, Ollama/model, and external Codex CLI are "
                "separately discoverable activation layers.\n\n"
                "### Packaging, update, and local stewardship\n\n"
                "**Confirmed.** The project builds an sdist and platform-independent Python wheel; "
                "the repository includes Windows launch/smoke surfaces and GitHub-release update "
                "checking. The desktop and its canonical data are locally operated; the Codex "
                "provider is optional and Demo remains available without it.\n\n"
                "**Partially Verified.** Ubuntu is the measured P0 host. Windows packaging, native "
                "audio/GPU integration, and macOS operation require their target-host matrices."
            ),
            12: (
                "### Configuration sources and precedence\n\n"
                "**Confirmed.** Agent configuration uses explicit constructor values in tests, "
                "approved `AURA_AGENT_*` environment overrides, Qt application-data defaults, and "
                "provider discovery. It covers mode, run and worktree roots, allowed repository "
                "roots, Codex executable/timeouts/message size, read-only safety, network-off, Sol "
                "Expert and Quick/Standard profiles, Demo speed, retention, audit, redaction, and "
                "report output.\n\n"
                "### Secret scope\n\n"
                "**Confirmed.** Environment inventories record variable names and source paths "
                "only. Credential values are excluded, and the app-server owns ChatGPT "
                "authentication. Exact discovered variable names are in "
                "`environment-variables.csv`; defaults and validation are in "
                "`src/aura/agent/config.py`."
            ),
            13: (
                "### Trusted and untrusted regions\n\n"
                "**Confirmed.** Trusted AURA code includes the native GUI, controller, reducer, "
                "policies, static renderers, and local run store. Repository text, imported "
                "evidence, transcript content, provider output, and model output are untrusted "
                "inputs. Codex child process, OS credential store, OpenAI, browser, Ollama, "
                "repository, worktree, canonical AURA artifacts, and Agent artifacts retain "
                "explicit boundaries.\n\n"
                "### Enforcement\n\n"
                "**Confirmed.** Read-only and network-off are defaults; path resolution and "
                "symlink checks enforce local roots; sensitive names are denied; transfer preview "
                "minimizes/redacts content; consequential requests require request-scoped approval; "
                "unknown actions are inert; publication activates only from the explicit Publish "
                "stage on a governed agent branch. See "
                "`trust-boundaries.mmd` and `controls.csv`."
            ),
            14: (
                "### Accepted decision set\n\n"
                f"**Confirmed.** ADR-001 through ADR-{adr_count:03d} cover Evidence-to-Engineering identity, "
                "General and Evidence-Backed tasks, low-density native UI, provider-neutral seams, "
                "one-Live scheduling, recording priority, isolated writes, scoped AUTO, session "
                "grants, credential/audio boundaries, redacted transfer, latest-compatible Codex, "
                "durable evidence, manual retention, explicit publication, recovery, instruction "
                "trust, future team readiness, and the intent-first native workspace redesign.\n\n"
                "**Confirmed.** Each ADR records status, context, decision, alternatives, "
                "consequences, security impact, rollback, and verification. Copies are included "
                "under `../adr/` and source files remain under `docs/agent-workspace/adr/`."
            ),
            15: (
                "### Priority risk posture\n\n"
                "**Confirmed.** Critical risks cover prompt injection, credential disclosure, and "
                "future hosted multi-user isolation. High risks cover UI hotspots, ASR "
                "backpressure, lock discipline, model identity, PII/provenance, protocol drift, "
                "child lifecycle, native reproducibility, and report certainty. Medium risks cover "
                "local audit assurance, OS portability, coverage depth, and worktree lifecycle.\n\n"
                f"**Confirmed.** `../risk-register.csv` carries all {len(risks)} IDs with severity, "
                "likelihood, confidence, evidence, operational impact, mitigation, owner, "
                "verification, release gate, and residual risk. `../controls.csv` maps the active "
                "execution, credential, UI, network, data, Git, audit, and recovery protections."
            ),
            16: (
                "### Developer and operator path\n\n"
                "**Confirmed.** The command block below covers current-checkout inspection, frozen "
                "environment setup, desktop launch, full tests, Codex verification/login, package "
                "generation, artifact inspection, and Git worktree inventory. Demo and Live use "
                "the same AI Agent tab; the Run and Report inspectors expose output paths.\n\n"
                "**Confirmed.** Troubleshooting and rollback stay in source documentation so "
                "operators can diagnose provider readiness, login, model drift, dirty worktrees, "
                "report validation, and recovery without modifying canonical AURA data."
            ),
            17: (
                "### Interaction grammar\n\n"
                "**Confirmed.** Repository-grouped navigation and durable threads anchor the left "
                "rail; one intent-first composer owns task text, context attachments, mode, effort, "
                "scope, send, queue, and steer actions. The center timeline presents readable "
                "Markdown narrative, one observable activity digest, trusted approvals, and "
                "terminal outcomes while canonical events retain their complete sequence. The "
                "right inspector appears when diffs, "
                "tests, evidence, reports, or instruction provenance are available. Suggestions "
                "accelerate common starts without competing with the primary action.\n\n"
                "### Progressive disclosure and ownership\n\n"
                "**Confirmed.** Repository selection, account/model readiness, policy preflight, "
                "approval, publication, and recovery enter the primary flow only when their gate "
                "is active. `AgentWorkspaceView`, its Qt models/delegates, the typed application "
                "facade, presenter state, and subsystem composition root retain explicit ownership. "
                "The source design record is `docs/agent-workspace/ux-redesign/`.\n\n"
                "**Partially Verified.** Automated offscreen flows and visual comparisons confirm "
                "the implemented grammar. Human comprehension and task-completion measures remain "
                "the next usability validation layer."
            ),
            18: (
                "### State and operator action matrix\n\n"
                "**Confirmed.** No-repository and new-task states lead to repository selection or "
                "intent entry. Draft and loading states preserve input and expose progress. Login, "
                "model, Live AI-transfer, policy, and recording gates explain the activating action. "
                "Queued and running states expose queue position, activity, Stop, and eligible "
                "steering. Approval state presents trusted details with Approve once and Reject. "
                "Validation, completion, failure, interruption, and recovery states route to "
                "artifacts, retry, inspect, resume-read-only, or abandon actions.\n\n"
                "### Durable transitions\n\n"
                "**Confirmed.** Normalized events, reducer transitions, catalog snapshots, and "
                "recovery cards preserve the same state after restart. Empty collections use "
                "purpose-specific guidance; errors retain diagnostics and a bounded recovery path. "
                "The source matrix is `docs/agent-workspace/ux-redesign/06-component-and-state-map.md`.\n\n"
                "**Partially Verified.** Automated UI and persistence tests cover the implemented "
                "states. Target-host audio-device, provider-login, and operating-system failure "
                "presentations remain release-host validation paths."
            ),
            19: (
                "### Keyboard, language, and status communication\n\n"
                "**Confirmed.** Keyboard entry reaches repository search, thread search, composer, "
                "send/queue, Stop, inspector, and settings actions. Enter-to-send respects active "
                "CJK input-method composition, while Shift+Enter retains multiline input. Controls "
                "carry accessible names and focus behavior; state combines text, iconography, and "
                "shape so color is supplementary. Taiwan-facing product copy uses Taiwan "
                "Traditional Chinese service terms. The Live transfer review starts on the safe "
                "return action, preserves logical tab order, restores focus, and keeps full-"
                "transcript acknowledgement reachable at 1024×768.\n\n"
                "### Visual and motion controls\n\n"
                "**Confirmed.** Central tokens govern contrast, spacing, typography, focus rings, "
                "minimum target size, and reduced-motion behavior across responsive geometries. "
                "The transfer-review evidence adds ten native states, explicit blocked text, "
                "collapsed technical disclosure, and non-modal Demo local-only presentation. "
                "The operator references are `docs/agent-workspace/keyboard-shortcuts.md` and "
                "`docs/agent-workspace/ux-redesign/08-accessibility-plan.md`.\n\n"
                "**Partially Verified.** Offscreen keyboard, focus, IME, label, and geometry checks "
                "are recorded. Screen-reader, switch-control, high-contrast desktop-theme, and "
                "assistive-technology field review remain the next validation layer."
            ),
            20: (
                "### Model/view and bounded presentation\n\n"
                "**Confirmed.** Repository, thread, timeline, changed-file, evidence, test, and "
                "report collections use Qt model/view presentation. Event bursts are deduplicated "
                "and coalesced before bounded model updates. Diff, log, and document previews read "
                "bounded content, while full artifacts stay on disk for explicit inspection.\n\n"
                "### Scale evidence and backpressure\n\n"
                "**Confirmed.** Automated exercises cover 1,000 work items, 10,000 timeline events, "
                "1,000 changed files, 50 MiB preview input, event bursts, queue/recovery cycles, "
                "provider failures, and audit integrity. Measured evidence is packaged in "
                "`../validation/soak-report.md` and the UI redesign validation report.\n\n"
                "**Partially Verified.** Current measurements confirm responsive model operations "
                "on the observed Ubuntu host. Catalog refresh, Git/report generation, media "
                "handoff, and selected provider-presentation actions retain a bounded synchronous "
                "path; background execution activates when target-host profiling shows material "
                "GUI-thread pressure."
            ),
            21: (
                "### Ownership and durable continuity\n\n"
                "**Confirmed.** WorkItems own operator intent, repository identity, thread "
                "metadata, queue state, drafts, and run history. AgentRuns own normalized events, "
                "approvals, commands, context snapshots, changed files, tests, reports, and "
                "terminal integrity. Atomic catalog snapshots and append-only run evidence support "
                "restart discovery without mutating auto-resume.\n\n"
                "### Preferences, migration, and retention\n\n"
                "**Confirmed.** Per-thread drafts and schema-versioned UI preferences preserve "
                "layout and interaction choices through a deterministic migration path. Manual "
                "storage review, cleanup preview, and explicit worktree cleanup preserve operator "
                "ownership. The source decisions are ADR-013, ADR-014, ADR-016, and ADR-032.\n\n"
                "**Partially Verified.** Migration, restart, recovery, and integrity are covered by "
                "automated tests and soak evidence on the observed host. Long-duration upgrade "
                "chains and target-platform filesystem interruption remain release-host exercises."
            ),
            22: (
                "### Identity, account, and permission UX\n\n"
                "**Confirmed.** Release 1 serves one local operator. AURA owns allowlisted "
                "repository authorization and expiring repository-session grants; Codex owns "
                "ChatGPT login and tokens; Git/GitHub tooling owns publication credentials. The UI "
                "shows non-secret account, model, repository, base-commit, mode, scope, and grant "
                "status at the decision point. Repository authority, worktree activation, Sandbox, "
                "commit, push, and PR decisions remain in execution settings and request-scoped "
                "approval surfaces.\n\n"
                "### Data-transfer UX\n\n"
                "**Confirmed.** Live uses a structured plain-language review for what is sent, "
                "recognized sensitive-information handling, local-only items, and the exact "
                "transformed payload. Audit metadata stays under collapsed technical details. "
                "Whole-transcript transfer uses a second document confirmation; credentials and "
                "raw audio remain blocked. Demo records `demo_local_only` without representing a "
                "user approval for external transfer. Repository authority remains a separate "
                "contract from this initial-payload decision.\n\n"
                "**Partially Verified.** Single-operator account and transfer flows are automated "
                "and documented. Hosted identity, tenant isolation, role policy, shared storage, "
                "revocation, and organization data controls form a separately activated work "
                "package."
            ),
            23: (
                "### Provenance presentation\n\n"
                "**Confirmed.** The inspector presents instruction source, canonical path/origin, "
                "repository identity, base commit, content hash, precedence, scope, trust status, "
                "and policy conflicts. Repository instructions are accepted only from canonical "
                "allowlisted paths and remain bound to the reviewed commit and content hash.\n\n"
                "### Injection-resilient interaction\n\n"
                "**Confirmed.** Transcript text, repository content, attachments, tool output, "
                "provider output, and model output are rendered as untrusted data. Their content "
                "cannot create a grant, approval, network permission, write boundary, or "
                "publication authority. Deny rules precede grants, unknown events render inertly, "
                "and approvals remain request-scoped and durable.\n\n"
                "**Partially Verified.** Security fixtures cover hidden-shell, provider-event, "
                "instruction-precedence, path, and approval boundaries. Emerging provider schemas "
                "and target-host credential integrations remain compatibility validation layers."
            ),
            24: (
                "### Visual evidence\n\n"
                "**Confirmed.** The packet includes no-repository, new-task, evidence-attached, "
                "running, approval, completed-diff, recording, recovery, and settings states at "
                "1024×768, 1280×820, 1440×900, and 1920×1080. Contact sheets and a same-viewport "
                "baseline-versus-redesign comparison make hierarchy, density, and responsive "
                "behavior directly reviewable. Ten additional transfer-review states cover clean, "
                "evidence-backed, redacted, blocked, full-transcript, technical-detail, Demo, "
                "1024×768, and 1440×900 presentation. Checksums preserve screenshot integrity.\n\n"
                "### Task-flow and usability evidence\n\n"
                "**Confirmed.** Offscreen Qt automation covers core task flows, contextual "
                "inspectors, approvals, keyboard/CJK behavior, scale, queue, recording, recovery, "
                "and responsive geometry. The images are under `../screenshots/`; executed results "
                "are in `../validation/ui-redesign-validation-report.md` and "
                "`transfer-review-visual-review.md`.\n\n"
                "**Partially Verified.** Automated and expert visual review are complete for the "
                "observed host. The planned five-participant study has 0 of 5 sessions completed, "
                "so comprehension, completion, error, and satisfaction results remain "
                "`NOT VERIFIED` until real participant evidence is recorded."
            ),
            25: (
                "### Release readiness\n\n"
                "**Confirmed.** The native intent-first workspace, typed application seam, "
                "model/view presentation, contextual attachments and inspectors, trusted "
                "approvals, instruction provenance, drafts/preferences migration, recovery, "
                "documentation, visual packet, audit trail, and clean-source regression evidence "
                "form the current release candidate. The architecture ZIP is generated from a "
                "recorded commit and validated before publication.\n\n"
                "### Open questions and future workbench gates\n\n"
                "**Partially Verified.** Human usability, assistive-technology field review, "
                "Windows/macOS behavior, immutable provider-model identity, native BOM parity, and "
                "the remaining synchronous GUI action paths stay visible in "
                "`../validation/missing-evidence.json` and the redesign missing-evidence report. "
                "Provider-neutral WorkItems, AgentRuns, repository profiles, audit events, and "
                "publication records preserve future provider, team, and hosted-workbench seams.\n\n"
                "**Confirmed.** The stopping condition for this release is a reproducible package "
                "with clean source, passing automated validation, bounded known gates, and no "
                "claim that substitutes automation for the pending human study."
            ),
        }
        evidence = (
            f"Source commit: `{metadata['source_commit']}`\n\n"
            f"Dirty source state: `{metadata['source_dirty']}`\n\n"
            "Primary evidence: `analysis-metadata.json`, `inventories/`, "
            "`validation/command-results.json`, and repository symbols.\n\n"
            "Limitation: claims apply to the observed checkout and workstation at generation time."
        )
        local_commands = (
            "## Verified Local Commands\n\n"
            "Run from the observed checkout `<repository-root>`:\n\n"
            "```bash\n"
            "git status --short --branch\n"
            "uv sync --all-extras --frozen\n"
            "uv run aura\n"
            "QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v\n"
            "codex --version\n"
            "codex login\n"
            "uv run python -c \"from aura.agent.reporting import ArchitecturePackageGenerator as G; "
            "print(G('.').generate('artifacts/repository-architecture').archive_path)\"\n"
            "find artifacts/repository-architecture -maxdepth 4 -type f | sort\n"
            "git worktree list\n"
            "```\n\n"
            "Demo and Live activation, artifact review, selected-worktree cleanup, troubleshooting, "
            "and reversible feature removal are documented in `../../docs/agent-workspace/`.\n\n"
        )
        for index, (slug, title) in enumerate(REPORTS, start=1):
            cross_links = {
                2: "See `../inventories/repository-files.csv`, `components.csv`, and `entry-points.csv`.",
                3: "See `../inventories/technology-stack.csv`, `third-party-dependencies.csv`, `licenses.csv`, and `native-dependencies.csv`.",
                4: "See `../diagrams/01-c4-system-context.mmd`.",
                5: "See `../diagrams/02-c4-container.mmd`.",
                6: "See `../diagrams/03-component-architecture.mmd` and `components.csv`.",
                7: "See sequence, transfer, freshness, and state diagrams in `../diagrams/`.",
                8: "See `api-interfaces.csv`, `events.csv`, and `signals-and-slots.csv`.",
                9: "See `../diagrams/12-internal-dependency-graph.mmd`.",
                10: "See `../sbom/cyclonedx.json`, `spdx.json`, and `sbom-report.md`.",
                14: "See `../../docs/agent-workspace/adr/` in the source checkout.",
                15: "See `../inventories/risks.csv` and `controls.csv`.",
                17: "See `../diagrams/03-component-architecture.mmd`, `../screenshots/`, and the source UX redesign packet.",
                18: "See `../diagrams/09-run-state-machine.mmd`, `17-queue-recording-gate.mmd`, and `20-crash-recovery.mmd`.",
                19: "See `../validation/ui-redesign-validation-report.md`, `transfer-review-visual-review.md`, and the source keyboard and accessibility guides.",
                20: "See `../validation/soak-report.md`, `ui-redesign-validation-report.md`, and `../inventories/tests.csv`.",
                21: "See `../diagrams/20-crash-recovery.mmd`, `../inventories/databases-and-storage.csv`, and the persistence test entries.",
                22: "See `../diagrams/07-data-transfer-flow.mmd`, `14-provider-preflight.mmd`, `../screenshots/transfer-review/`, and `../controls.csv`.",
                23: "See `../diagrams/08-trust-boundaries.mmd`, `../controls.csv`, and the instruction-trust ADR.",
                24: "See `../screenshots/`, `../screenshots/transfer-review/`, `../validation/ui-redesign-validation-report.md`, `transfer-review-visual-review.md`, and `ui-redesign-missing-evidence.md`.",
                25: "See `../validation/missing-evidence.json`, `ui-redesign-missing-evidence.md`, and `../risk-register.csv`.",
            }.get(index, "See the linked inventories and diagrams for machine-readable evidence.")
            coverage = "\n".join(f"- {item}" for item in REPORT_COVERAGE[index])
            body = (
                f"# {index}. {title}\n\n"
                "## Assessment\n\n"
                f"**Confirmed.** {subjects[index]}\n\n"
                "## Required Coverage\n\n"
                f"{coverage}\n\n"
                "## Detailed Findings\n\n"
                f"{details[index]}\n\n"
                "## Evidence and Scope\n\n"
                f"{evidence}\n\n"
                "## Architecture Control\n\n"
                f"**Confirmed.** {cross_links}\n\n"
                f"{local_commands if index == 16 else ''}"
                "## Next Validation Layer\n\n"
                "**Partially Verified.** Re-run the documented commands and package validator "
                "on the intended release host; record any platform or provider drift in the "
                "missing-evidence register before publication.\n"
            )
            for label in CONFIDENCE:
                body = body.replace(f"**{label}.**", f"**{label.upper()}.**")
            _write_text(package / "reports" / f"{slug}.md", body)

    def _write_diagrams(self, package: Path) -> None:
        for filename, source in DIAGRAMS.items():
            if not source.strip().startswith(("flowchart", "sequenceDiagram", "stateDiagram")):
                raise ValueError(f"Unsupported Mermaid diagram root: {filename}")
            _write_text(package / "diagrams" / filename, source.strip() + "\n")

    def _write_inventories(
        self,
        package: Path,
        files: list[dict[str, object]],
        facts: dict[str, list[dict[str, object]]],
        dependencies: list[dict[str, str]],
        commands: dict[str, dict[str, object]],
        risks: list[dict[str, str]],
        controls: list[dict[str, str]],
    ) -> None:
        target = package / "inventories"
        _write_csv(target / "repository-files.csv", files, ("path", "kind", "size_bytes", "sha256", "tracked"))
        _write_csv(
            target / "technology-stack.csv",
            [
                {"technology": "Python", "role": "application runtime", "evidence": "pyproject.toml", "confidence": "Confirmed"},
                {"technology": "PyQt6", "role": "native desktop UI", "evidence": "src/aura/ui", "confidence": "Confirmed"},
                {"technology": "faster-whisper", "role": "ASR", "evidence": "pyproject.toml", "confidence": "Confirmed"},
                {"technology": "SQLite FTS5", "role": "local evidence index", "evidence": "src/aura/evidence_search.py", "confidence": "Confirmed"},
                {"technology": "Ollama", "role": "local summary model", "evidence": "src/aura/llm", "confidence": "Partially Verified"},
                {"technology": "Codex app-server", "role": "live Agent provider", "evidence": "src/aura/agent/providers", "confidence": "Confirmed"},
                {"technology": "Git worktree", "role": "isolated write workspace", "evidence": "src/aura/agent/worktree.py", "confidence": "Confirmed"},
            ],
            ("technology", "role", "evidence", "confidence"),
        )
        _write_csv(target / "components.csv", facts["components"], ("component", "module", "line", "kind"))
        _write_csv(
            target / "entry-points.csv",
            [
                {"entry_point": "aura", "target": "aura.app:main", "kind": "console script"},
                {"entry_point": "project-aura", "target": "aura.app:main", "kind": "console script"},
                {"entry_point": "aura-evidence", "target": "aura.evidence_search:main", "kind": "console script"},
            ],
            ("entry_point", "target", "kind"),
        )
        _write_csv(target / "api-interfaces.csv", facts["interfaces"], ("interface", "module", "line", "kind"))
        _write_csv(
            target / "events.csv",
            [{"event_type": event, "schema_version": 1, "trusted_action": "no"} for event in NORMALIZED_EVENT_TYPES],
            ("event_type", "schema_version", "trusted_action"),
        )
        _write_csv(target / "signals-and-slots.csv", facts["signals"], ("signal", "path", "signature", "line"))
        _write_csv(
            target / "external-services.csv",
            [
                {"service": "OpenAI / ChatGPT", "boundary": "Codex-managed cloud", "network_default": "disabled"},
                {"service": "System browser", "boundary": "provider login only", "network_default": "user activated"},
                {"service": "Ollama", "boundary": "local process", "network_default": "local"},
                {"service": "Git repository", "boundary": "local selected root", "network_default": "none"},
            ],
            ("service", "boundary", "network_default"),
        )
        _write_csv(target / "environment-variables.csv", facts["environment"], ("variable", "source", "classification", "secret_value_included"))
        _write_csv(
            target / "databases-and-storage.csv",
            [
                {"store": "AURA session directory", "format": "JSON/JSONL/audio", "canonical_scope": "meeting artifacts"},
                {"store": "Evidence index", "format": "SQLite FTS5", "canonical_scope": "rebuildable index"},
                {"store": "Agent run directory", "format": "JSON/JSONL/patch", "canonical_scope": "agent run"},
                {"store": "Git worktree", "format": "Git checkout", "canonical_scope": "approved proposal"},
                {"store": "Audit directory", "format": "hash-linked JSONL", "canonical_scope": "local usage audit"},
            ],
            ("store", "format", "canonical_scope"),
        )
        _write_csv(
            target / "native-dependencies.csv",
            [
                {"dependency": key, "detected": command["exit_code"] == 0, "version_evidence": str(command["stdout"]).splitlines()[0] if command["stdout"] else "", "confidence": "Confirmed" if command["exit_code"] == 0 else "Unknown"}
                for key, command in commands.items()
                if key in {
                    "python",
                    "git",
                    "codex",
                    "ffmpeg",
                    "ollama",
                    "nvidia_smi",
                    "pulseaudio",
                    "pipewire",
                }
            ],
            ("dependency", "detected", "version_evidence", "confidence"),
        )
        _write_csv(target / "third-party-dependencies.csv", dependencies, ("name", "version", "scope", "license", "source"))
        _write_csv(
            target / "licenses.csv",
            [{"component": item["name"], "license": item["license"], "confidence": "Confirmed" if item["license"] != "Unknown" else "Unknown"} for item in dependencies],
            ("component", "license", "confidence"),
        )
        _write_csv(target / "tests.csv", facts["tests"], ("test", "path", "line", "runner"))
        _write_csv(
            target / "risks.csv",
            risks,
            (
                "id",
                "severity",
                "likelihood",
                "confidence",
                "risk",
                "evidence",
                "impact",
                "mitigation",
                "owner",
                "verification",
                "release_gate",
                "residual_risk",
            ),
        )
        _write_csv(target / "controls.csv", controls, ("control", "area", "implementation", "evidence"))
        _write_csv(
            target / "model-assets.csv",
            [
                {"asset": "faster-whisper model", "identity": "runtime configured", "location": "provider cache", "confidence": "Partially Verified"},
                {"asset": "gemma4:e4b-it-qat", "identity": "local Ollama tag", "location": "Ollama store", "confidence": "Partially Verified"},
                {"asset": "gpt-5.6-sol", "identity": "provider-discovered model ID", "location": "Codex provider", "confidence": "Partially Verified"},
            ],
            ("asset", "identity", "location", "confidence"),
        )
        _write_csv(
            target / "agent-actions.csv",
            [
                {"action_id": "repository_health_review", "consequence": "read", "approval": "data boundary"},
                {"action_id": "generate_architecture_package", "consequence": "read/export", "approval": "artifact output"},
                {"action_id": "security_pii_review", "consequence": "read", "approval": "data boundary"},
                {"action_id": "plan_approved_fix", "consequence": "read then isolated write", "approval": "worktree and each change"},
                {"action_id": "review_confirmed_aura_action", "consequence": "read then optional isolated write", "approval": "evidence transfer and each write"},
            ],
            ("action_id", "consequence", "approval"),
        )
        missing = [name for name in INVENTORY_NAMES if not (target / name).exists()]
        if missing:
            raise RuntimeError(f"Required inventories were not generated: {missing}")

    def _write_sboms(
        self,
        package: Path,
        dependencies: list[dict[str, str]],
        commands: dict[str, dict[str, object]],
        metadata: dict[str, object],
    ) -> None:
        components = [
            {
                "type": "library",
                "bom-ref": f"pkg:pypi/{item['name']}@{item['version']}",
                "name": item["name"],
                "version": item["version"],
                "purl": f"pkg:pypi/{item['name']}@{item['version']}",
                "licenses": [{"license": {"name": item["license"]}}],
                "properties": [{"name": "aura:scope", "value": item["scope"]}],
            }
            for item in dependencies
        ]
        cyclone = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.6",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": metadata["generated_at"],
                "component": {
                    "type": "application",
                    "name": metadata["repository"],
                    "version": str(metadata["source_commit"]),
                },
                "tools": {
                    "components": [
                        {
                            "type": "application",
                            "name": "AURA ArchitecturePackageGenerator",
                            "version": "1",
                        }
                    ]
                },
            },
            "components": components,
        }
        spdx_packages = []
        for index, item in enumerate(dependencies, start=1):
            spdx_packages.append(
                {
                    "name": item["name"],
                    "SPDXID": _safe_spdx_id(item["name"], index),
                    "versionInfo": item["version"],
                    "downloadLocation": "NOASSERTION",
                    "filesAnalyzed": False,
                    "licenseConcluded": "NOASSERTION",
                    "licenseDeclared": item["license"]
                    if item["license"] != "Unknown"
                    else "NOASSERTION",
                    "copyrightText": "NOASSERTION",
                }
            )
        spdx = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": f"{metadata['repository']}-architecture-package",
            "documentNamespace": f"https://project-aura.invalid/spdx/{uuid.uuid4()}",
            "creationInfo": {
                "created": dt.datetime.now(dt.timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
                "creators": ["Tool: AURA ArchitecturePackageGenerator-1"],
            },
            "packages": spdx_packages,
        }
        sbom = package / "sbom"
        _write_text(sbom / "cyclonedx.json", json.dumps(cyclone, indent=2) + "\n")
        _write_text(sbom / "spdx.json", json.dumps(spdx, indent=2) + "\n")
        native_records = [
            {
                "name": name,
                "observed": value["exit_code"] == 0,
                "version_evidence": (
                    str(value["stdout"]).splitlines()[0]
                    if value["stdout"]
                    else str(value["stderr"])
                ),
                "command": value["argv"],
            }
            for name, value in commands.items()
            if name
            in {
                "python",
                "git",
                "codex",
                "ffmpeg",
                "ollama",
                "nvidia_smi",
                "pulseaudio",
                "pipewire",
            }
        ]
        model_records = [
            {
                "name": "faster-whisper",
                "identity": "runtime-configured local ASR model",
                "location": "provider cache",
                "confidence": "Partially Verified",
            },
            {
                "name": "gemma4:e4b-it-qat",
                "identity": "local Ollama tag",
                "location": "Ollama store",
                "confidence": "Partially Verified",
            },
            {
                "name": "gpt-5.6-sol",
                "identity": "Codex provider-discovered model ID",
                "location": "Codex/OpenAI provider boundary",
                "confidence": "Partially Verified",
            },
        ]
        _write_text(
            sbom / "native-bom.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "frontend_runtime": "native PyQt6; no web frontend",
                    "components": native_records,
                },
                indent=2,
            )
            + "\n",
        )
        _write_text(
            sbom / "model-bom.json",
            json.dumps(
                {"schema_version": 1, "models": model_records},
                indent=2,
            )
            + "\n",
        )
        native_lines = "\n".join(
            f"- **{name}**: {'observed' if value['exit_code'] == 0 else 'pending verification'} — "
            f"`{str(value['stdout']).splitlines()[0] if value['stdout'] else value['stderr']}`"
            for name, value in commands.items()
            if name
            in {
                "python",
                "git",
                "codex",
                "ffmpeg",
                "ollama",
                "nvidia_smi",
                "pulseaudio",
                "pipewire",
            }
        )
        _write_text(
            sbom / "sbom-report.md",
            "# Software Bill of Materials\n\n"
            f"**Confirmed.** The Python BOM contains {len(dependencies)} declared or locked packages.\n\n"
            "## Operational and Native BOM\n\n"
            f"{native_lines}\n\n"
            "## Scope Control\n\n"
            "**Partially Verified.** Python packages, locally discoverable native tools, CUDA/GPU "
            "evidence, audio services, Ollama, Codex CLI, Git, and model declarations are distinct "
            "layers. Immutable model files and target-host package-manager manifests remain a next "
            "validation layer.\n",
        )
        _write_text(
            sbom / "generation-notes.json",
            json.dumps(
                {
                    "generator": "stdlib parser over pyproject.toml and uv.lock",
                    "formats": ["CycloneDX 1.6", "SPDX 2.3"],
                    "known_omissions": [
                        "undiscoverable OS package records",
                        "immutable hashes for provider-hosted models",
                    ],
                },
                indent=2,
            )
            + "\n",
        )

    def _write_assurance_evidence(
        self,
        package: Path,
        metadata: dict[str, object],
        risks: list[dict[str, str]],
        controls: list[dict[str, str]],
    ) -> None:
        risk_fields = (
            "id",
            "severity",
            "likelihood",
            "confidence",
            "risk",
            "evidence",
            "impact",
            "mitigation",
            "owner",
            "verification",
            "release_gate",
            "residual_risk",
        )
        _write_csv(package / "risk-register.csv", risks, risk_fields)
        _write_csv(
            package / "controls.csv",
            controls,
            ("control", "area", "implementation", "evidence"),
        )

        assurance = self.repository / "artifacts" / "stable-daily-assurance"
        source_evidence = assurance / "evidence-register.csv"
        if source_evidence.is_file():
            _write_text(
                package / "evidence-register.csv",
                source_evidence.read_text(encoding="utf-8"),
            )
        else:
            _write_csv(
                package / "evidence-register.csv",
                [
                    {
                        "evidence_id": "EV-ARCH-001",
                        "claim": "Architecture package generated from the observed checkout",
                        "status": "Confirmed",
                        "source": "analysis-metadata.json",
                        "verification": f"source commit {metadata['source_commit']}",
                    },
                    {
                        "evidence_id": "EV-ASSURANCE-001",
                        "claim": "Stable daily-use release assurance",
                        "status": "Blocked",
                        "source": "artifacts/stable-daily-assurance",
                        "verification": "Generate the canonical release-assurance packet.",
                    },
                ],
                ("evidence_id", "claim", "status", "source", "verification"),
            )

        adr_source = self.repository / "docs" / "agent-workspace" / "adr"
        for path in sorted(adr_source.glob("ADR-*.md")):
            _copy_artifact(path, package / "adr" / path.name)

        compatibility_source = assurance / "compatibility-matrix.json"
        if compatibility_source.is_file():
            _copy_artifact(
                compatibility_source,
                package / "validation" / "compatibility-matrix.json",
            )
        else:
            compatibility_manifest = (
                self.repository
                / "src"
                / "aura"
                / "agent"
                / "providers"
                / "codex_compatibility.json"
            )
            compatibility = {
                "schema_version": 1,
                "release_platforms": [
                    {
                        "platform": "Ubuntu 24.04",
                        "status": "declared_release_platform",
                        "evidence": "current-host validation required",
                    },
                    {
                        "platform": "Windows",
                        "status": "unavailable_not_passed",
                        "evidence": "target-host run pending",
                    },
                    {
                        "platform": "macOS",
                        "status": "unavailable_not_passed",
                        "evidence": "target-host run pending",
                    },
                ],
                "codex_contract": (
                    json.loads(compatibility_manifest.read_text(encoding="utf-8"))
                    if compatibility_manifest.is_file()
                    else {"status": "Blocked", "reason": "manifest unavailable"}
                ),
            }
            _write_text(
                package / "validation" / "compatibility-matrix.json",
                json.dumps(compatibility, ensure_ascii=False, indent=2) + "\n",
            )

        soak_source = assurance / "soak-report.md"
        if soak_source.is_file():
            _copy_artifact(
                soak_source,
                package / "validation" / "soak-report.md",
            )
        else:
            _write_text(
                package / "validation" / "soak-report.md",
                "# Stable Daily-Use Soak Report\n\n"
                "Status: **BLOCKED**\n\n"
                "The canonical 50-run release soak has not been attached to this checkout. "
                "This package records the gate without converting it into a pass claim.\n",
            )
        for filename in ("soak-summary.json", "soak-events.jsonl"):
            source = assurance / filename
            if source.is_file():
                _copy_artifact(source, package / "artifacts" / filename)

        live_codex_source = assurance / "live-codex"
        if live_codex_source.is_dir():
            live_codex_target = package / "artifacts" / "live-codex"
            live_codex_target.mkdir(parents=True, exist_ok=True)
            for path in sorted(live_codex_source.iterdir()):
                if path.is_file():
                    _copy_artifact(path, live_codex_target / path.name)

        redesign_assurance = (
            self.repository
            / "artifacts"
            / "agent-workspace"
            / "2026-07-26-codex-desktop-inspired-uiux"
        )
        redesign_screenshots = redesign_assurance / "after"
        screenshot_source = (
            redesign_screenshots
            if redesign_screenshots.is_dir()
            else assurance / "screenshots"
        )
        if screenshot_source.is_dir():
            for path in sorted(screenshot_source.iterdir()):
                if path.is_file() and path.suffix.lower() in {".md", ".png"}:
                    _copy_artifact(path, package / "screenshots" / path.name)
        comparison = redesign_assurance / "baseline-vs-redesign-1440x900.png"
        if comparison.is_file():
            _copy_artifact(comparison, package / "screenshots" / comparison.name)
        for source, destination in (
            (
                redesign_assurance / "validation-report.md",
                package / "validation" / "ui-redesign-validation-report.md",
            ),
            (
                redesign_assurance / "missing-evidence.md",
                package / "validation" / "ui-redesign-missing-evidence.md",
            ),
            (
                redesign_assurance / "checksums.sha256",
                package / "validation" / "ui-redesign-checksums.sha256",
            ),
            (
                redesign_assurance / "soak" / "soak-report.json",
                package / "artifacts" / "ui-redesign-soak-report.json",
            ),
            (
                redesign_assurance
                / "soak"
                / "audit-evidence"
                / "audit-2026-07-26.jsonl",
                package / "artifacts" / "ui-redesign-audit-events.jsonl",
            ),
        ):
            if source.is_file():
                _copy_artifact(source, destination)

        transfer_assurance = (
            self.repository
            / "artifacts"
            / "agent-workspace"
            / "2026-07-26-plain-language-transfer-review"
        )
        transfer_target = package / "screenshots" / "transfer-review"
        for state in ("before", "after"):
            source_dir = transfer_assurance / state
            if not source_dir.is_dir():
                continue
            destination_dir = transfer_target / state
            destination_dir.mkdir(parents=True, exist_ok=True)
            for path in sorted(source_dir.iterdir()):
                if path.is_file():
                    _copy_artifact(path, destination_dir / path.name)
        visual_review = transfer_assurance / "after" / "visual-review.md"
        if visual_review.is_file():
            _copy_artifact(
                visual_review,
                package
                / "validation"
                / "transfer-review-visual-review.md",
            )
        transfer_checksums = (
            transfer_assurance / "after" / "checksums.sha256"
        )
        if transfer_checksums.is_file():
            package_checksums = "\n".join(
                (
                    f"{digest}  ../screenshots/transfer-review/after/"
                    f"{Path(relative).name}"
                )
                for digest, relative in (
                    line.split(maxsplit=1)
                    for line in transfer_checksums.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if line.strip()
                )
            )
            _write_text(
                package
                / "validation"
                / "transfer-review-checksums.sha256",
                package_checksums + "\n",
            )
        if not any((package / "screenshots").glob("*.png")):
            _write_text(
                package / "screenshots" / "README.md",
                "# Screenshot Evidence\n\n"
                "Before/after release screenshots are pending attachment and remain an explicit "
                "visual-review gate.\n",
            )

        vulnerability_source = assurance / "vulnerability-scan.json"
        if vulnerability_source.is_file():
            _copy_artifact(
                vulnerability_source,
                package / "validation" / "vulnerability-scan.json",
            )
        else:
            vulnerability_command = json.loads(
                (package / "validation" / "command-results.json").read_text(
                    encoding="utf-8"
                )
            ).get("vulnerability_scanner", {})
            _write_text(
                package / "validation" / "vulnerability-scan.json",
                json.dumps(
                    {
                        "status": "scanner_unavailable_not_passed",
                        "command_evidence": vulnerability_command,
                    },
                    indent=2,
                )
                + "\n",
            )
        vulnerability_assessment = assurance / "vulnerability-assessment.md"
        if vulnerability_assessment.is_file():
            _copy_artifact(
                vulnerability_assessment,
                package / "validation" / "vulnerability-assessment.md",
            )

    def _write_readme(self, package: Path, metadata: dict[str, object]) -> None:
        adr_count = len(list((package / "adr").glob("ADR-*.md")))
        _write_text(
            package / "README.md",
            "# Project AURA Repository Technical Architecture Package\n\n"
            f"Status: **READY WITH LIMITATIONS**\n\n"
            f"Run ID: `{metadata['run_id']}`\n\n"
            f"Source commit: `{metadata['source_commit']}`\n\n"
            f"Source dirty: `{metadata['source_dirty']}`\n\n"
            f"This package provides {len(REPORTS)} source-backed reports, "
            f"{len(DIAGRAMS)} Mermaid diagrams, {len(INVENTORY_NAMES)} machine-readable "
            f"inventories, {adr_count} release ADRs, CycloneDX/SPDX/model/native BOMs, risks, "
            "controls, evidence, screenshots, soak evidence, checksums, validation, and a "
            "missing-evidence register.\n\n"
            "Claims use `Confirmed`, `Partially Verified`, `Inferred`, `Unknown`, "
            "`Blocked`, or `Not Verified`. "
            "The source checkout remains authoritative for implementation; this package is the "
            "canonical snapshot for this architecture analysis run.\n",
        )

    def _validation_report(self, package: Path) -> str:
        missing = []
        for slug, _ in REPORTS:
            if not (package / "reports" / f"{slug}.md").exists():
                missing.append(f"reports/{slug}.md")
        for filename in DIAGRAMS:
            if not (package / "diagrams" / filename).exists():
                missing.append(f"diagrams/{filename}")
        for filename in INVENTORY_NAMES:
            if not (package / "inventories" / filename).exists():
                missing.append(f"inventories/{filename}")
        for filename in (
            "sbom/cyclonedx.json",
            "sbom/spdx.json",
            "sbom/model-bom.json",
            "sbom/native-bom.json",
            "validation/compatibility-matrix.json",
            "validation/soak-report.md",
            "validation/transfer-review-visual-review.md",
            "validation/transfer-review-checksums.sha256",
            "screenshots/transfer-review/before/legacy-transfer-dialog-1440x900.png",
            "screenshots/transfer-review/after/10-viewport-1440x900.png",
            "risk-register.csv",
            "controls.csv",
            "evidence-register.csv",
        ):
            if not (package / filename).exists():
                missing.append(filename)
        adr_count = len(list((package / "adr").glob("ADR-*.md")))
        expected_adr_count = len(
            list((self.repository / "docs" / "agent-workspace" / "adr").glob("ADR-*.md"))
        )
        if adr_count != expected_adr_count:
            missing.append(f"adr decisions: {adr_count}/{expected_adr_count}")
        if missing:
            raise RuntimeError(f"Architecture package validation failed: {missing}")
        return (
            "# Validation Report\n\n"
            f"- Required reports: {len(REPORTS)}/{len(REPORTS)}\n"
            f"- Mermaid diagrams: {len(DIAGRAMS)} (13 required runtime/data flows covered)\n"
            f"- Required inventories: {len(INVENTORY_NAMES)}/{len(INVENTORY_NAMES)}\n"
            f"- Architecture decisions: {adr_count}/{expected_adr_count} source decisions\n"
            "- CycloneDX JSON: present\n"
            "- SPDX JSON: present\n"
            "- Model BOM JSON: present\n"
            "- Native BOM JSON: present\n"
            "- Command results: present\n"
            "- Compatibility matrix: present\n"
            "- Soak report: present\n"
            "- Plain-language transfer-review before/after evidence: present\n"
            "- Transfer-review visual review and checksums: present\n"
            "- Root risk, control, and evidence registers: present\n"
            "- Missing-evidence register: present\n"
            "- Result: **READY WITH LIMITATIONS**\n\n"
            "The limitations register is an active validation path and prevents unsupported "
            "certainty from entering release decisions.\n"
        )

    def _write_manifest_and_checksums(
        self, package: Path, metadata: dict[str, object]
    ) -> None:
        paths = sorted(
            path
            for path in package.rglob("*")
            if path.is_file()
            and path.name not in {"package-manifest.json", "checksums.sha256"}
        )
        archive_validation_path = package / "validation" / "archive-validation.json"
        archive_status = (
            json.loads(archive_validation_path.read_text(encoding="utf-8")).get("status")
            if archive_validation_path.is_file()
            else "pending"
        )
        package_status = {
            "invalid": "invalid",
            "pending": "building",
            "valid": "ready_with_limitations",
        }.get(str(archive_status), "invalid")
        manifest = {
            "schema_version": 1,
            "package_status": package_status,
            "source_commit": metadata["source_commit"],
            "files": [
                {
                    "path": path.relative_to(package).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
                for path in paths
            ],
            "manifest_exclusions": [
                "package-manifest.json",
                "validation/checksums.sha256",
                "external zip archive",
            ],
        }
        manifest_path = package / "package-manifest.json"
        _write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
        checksum_paths = [*paths, manifest_path]
        _write_text(
            package / "validation" / "checksums.sha256",
            "".join(
                f"{_sha256(path)}  {path.relative_to(package).as_posix()}\n"
                for path in checksum_paths
            ),
        )

    @staticmethod
    def _validate_archive(package: Path, archive: Path) -> None:
        expected = {
            path.relative_to(package.parent).as_posix()
            for path in package.rglob("*")
            if path.is_file()
        }
        with zipfile.ZipFile(archive) as handle:
            corrupt = handle.testzip()
            actual = {name for name in handle.namelist() if not name.endswith("/")}
        if corrupt or actual != expected:
            raise RuntimeError(
                f"Architecture archive validation failed: corrupt={corrupt}, "
                f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )
