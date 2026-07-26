from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatch
import hashlib
from pathlib import Path
import re
import shlex
from typing import Mapping
from urllib.parse import urlparse, urlsplit, urlunsplit

from aura.redaction import (
    CREDENTIAL_PATTERNS,
    EMAIL_PATTERN,
    TAIWAN_NATIONAL_ID_PATTERN,
    TAIWAN_PHONE_PATTERN,
    redact_sensitive_text,
)


SENSITIVE_NAMES = {
    ".env",
    ".git-credentials",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "auth.json",
    "cookies",
    "cookies.sqlite",
    "credentials",
    "credentials.json",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
    "key4.db",
    "login data",
    "login.keychain-db",
    "logins.json",
}
SENSITIVE_PARTS = {
    ".aws",
    ".azure",
    ".codex",
    ".git",
    ".mozilla",
    ".ssh",
    "keychains",
    "keyrings",
    "secrets",
}
SENSITIVE_SEQUENCES = (
    (".config", "chromium"),
    (".config", "gcloud"),
    (".config", "google-chrome"),
    (".config", "microsoft-edge"),
    ("appdata", "local", "google", "chrome"),
    ("appdata", "local", "microsoft", "edge"),
    ("library", "application support", "google", "chrome"),
    ("library", "application support", "microsoft edge"),
)


def _inside(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def path_has_sensitive_component(path: str | Path) -> bool:
    parts = tuple(
        part.casefold()
        for part in str(path).replace("\\", "/").split("/")
        if part not in {"", "."}
    )
    atoms = {
        atom
        for part in parts
        for atom in re.split(r"[:=]", part)
        if atom
    }
    if atoms & SENSITIVE_NAMES or any(atom.startswith(".env.") for atom in atoms):
        return True
    if set(parts) & SENSITIVE_PARTS:
        return True
    return any(
        parts[index : index + len(sequence)] == sequence
        for sequence in SENSITIVE_SEQUENCES
        for index in range(len(parts) - len(sequence) + 1)
    )


def sanitize_remote_url(value: str) -> str:
    """Keep routing identity while removing URL-owned credentials and queries."""
    remote = str(value).strip()
    if "://" not in remote:
        match = re.fullmatch(r"([^@/]+)@([^:]+:.+)", remote)
        if match:
            return (
                remote
                if match.group(1) == "git"
                else redact_sensitive_text(match.group(2))
            )
        return redact_sensitive_text(remote)
    try:
        parsed = urlsplit(remote)
    except ValueError:
        return "[REDACTED_REMOTE]"
    hostname = parsed.hostname or ""
    try:
        parsed_port = parsed.port
    except ValueError:
        parsed_port = None
    port = f":{parsed_port}" if parsed_port is not None else ""
    username = "git@" if parsed.username == "git" and parsed.password is None else ""
    return redact_sensitive_text(urlunsplit(
        (
            parsed.scheme,
            f"{username}{hostname}{port}",
            parsed.path,
            "",
            "",
        )
    ))


class PathPolicy:
    def __init__(self, allowed_roots: tuple[Path, ...] | list[Path]):
        roots = tuple(Path(root).expanduser().resolve() for root in allowed_roots)
        self.allowed_roots = roots
        home = Path.home().resolve()
        self.sensitive_roots = (
            home / ".ssh",
            home / ".aws",
            home / ".azure",
            home / ".config" / "gcloud",
            home / ".codex" / "secrets",
        )

    def validate_repository(self, repository: str | Path) -> Path:
        path = Path(repository).expanduser().resolve(strict=True)
        if not path.is_dir():
            raise ValueError("Selected repository path is not a directory.")
        system_roots = {
            Path("/"),
            Path("/boot"),
            Path("/dev"),
            Path("/etc"),
            Path("/proc"),
            Path("/sys"),
            Path("/usr"),
            Path("/var"),
            Path.home().resolve(),
        }
        if path in system_roots:
            raise ValueError("Broad home and system roots cannot be repositories.")
        self._require_allowed(path)
        self._reject_sensitive(path)
        if not (path / ".git").exists():
            raise ValueError("Selected path is not a Git repository.")
        return path

    def validate_read(self, target: str | Path, repository: str | Path) -> Path:
        root = self.validate_repository(repository)
        path = Path(target).expanduser().resolve(strict=True)
        if not _inside(path, root):
            raise ValueError("Read path is outside the selected repository.")
        self._reject_sensitive(path)
        return path

    def validate_write(self, target: str | Path, worktree: str | Path) -> Path:
        root = Path(worktree).expanduser().resolve(strict=True)
        path = Path(target).expanduser().resolve(strict=False)
        if not _inside(path, root):
            raise ValueError("Write path is outside the isolated worktree.")
        self._reject_sensitive(path)
        return path

    def validate_worktree_root(self, root: str | Path) -> Path:
        path = Path(root).expanduser().resolve(strict=False)
        self._reject_sensitive(path)
        return path

    def _require_allowed(self, path: Path) -> None:
        if not any(_inside(path, root) for root in self.allowed_roots):
            raise ValueError("Repository path is outside the configured allowlist.")

    def _reject_sensitive(self, path: Path) -> None:
        if path_has_sensitive_component(path):
            raise ValueError("Sensitive credential paths are outside the Agent Workspace scope.")
        if any(_inside(path, sensitive) for sensitive in self.sensitive_roots):
            raise ValueError("Sensitive credential paths are outside the Agent Workspace scope.")


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    consequence: str
    reason: str
    risk_class: str = "R0"
    approval: str = "deny"


class CommandPolicy:
    _PROHIBITED = (
        re.compile(r"\bgit\s+(?:push|merge)\b", re.IGNORECASE),
        re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
        re.compile(r"\bgit\s+clean\b[^\\n]*\s-[a-z]*f", re.IGNORECASE),
        re.compile(r"\bgit\s+checkout\s+--\b", re.IGNORECASE),
        re.compile(r"\bgit\s+branch\s+-D\b"),
        re.compile(r"\b(?:kubectl|helm)\b", re.IGNORECASE),
        re.compile(r"\bterraform\s+(?:apply|destroy)\b", re.IGNORECASE),
        re.compile(r"\b(?:docker|podman)\s+push\b", re.IGNORECASE),
        re.compile(r"\b(?:npm|pnpm|yarn)\s+publish\b", re.IGNORECASE),
        re.compile(r"\b(?:twine\s+upload|gh\s+pr\s+create)\b", re.IGNORECASE),
        re.compile(r"\b(?:curl|wget|nc|ncat|ssh|scp|sftp)\b", re.IGNORECASE),
        re.compile(r"\bgit\s+(?:fetch|pull|clone)\b", re.IGNORECASE),
        re.compile(
            r"\b(?:pip|pip3|uv|npm|pnpm|yarn)\s+(?:install|add|sync|update)\b",
            re.IGNORECASE,
        ),
    )
    _SENSITIVE = re.compile(
        r"(?:^|[/\\\s])(?:\.ssh|\.aws|\.azure|\.codex[/\\](?:auth\.json|secrets)|"
        r"\.env|auth\.json|credentials(?:\.json)?|id_(?:dsa|ed25519|rsa))"
        r"(?:$|[/\\\s])",
        re.IGNORECASE,
    )
    _READ_ONLY_PREFIXES = (
        ("pwd",),
        ("ls",),
        ("rg",),
        ("grep",),
        ("head",),
        ("tail",),
        ("wc",),
        ("git", "status"),
        ("git", "diff"),
        ("git", "log"),
        ("git", "show"),
        ("git", "rev-parse"),
        ("git", "branch"),
        ("git", "ls-files"),
        ("git", "worktree", "list"),
    )
    _UNSAFE_OPTIONS = {
        "--delete",
        "--dereference-recursive",
        "--ext-diff",
        "--hidden",
        "--in-place",
        "--no-ignore",
        "--output",
        "--pre",
        "--pre-glob",
        "--recursive",
        "--textconv",
        "-R",
        "-delete",
        "-i",
        "-r",
    }

    def evaluate(self, command: str, *, safety_profile: str) -> PolicyDecision:
        if safety_profile not in {"read-only", "approved-worktree-write"}:
            return PolicyDecision(False, "prohibited", "The active safety profile cannot execute commands.")
        if not command.strip():
            return PolicyDecision(False, "prohibited", "An empty command cannot be approved.")
        if any(
            token in command
            for token in ("\n", "\r", "`", "$(", "&&", "||", ";", "|", ">", "<", "&")
        ):
            return PolicyDecision(
                False,
                "prohibited",
                "Shell interpolation or command chaining is outside the P0 command contract.",
            )
        if self._SENSITIVE.search(command):
            return PolicyDecision(
                False,
                "prohibited",
                "Credential and sensitive-path access is outside the Agent Workspace scope.",
            )
        if any(pattern.search(command) for pattern in self._PROHIBITED):
            return PolicyDecision(
                False,
                "prohibited",
                "Push, merge, release, and deployment are outside P0.",
            )
        try:
            argv = tuple(shlex.split(command, posix=True))
        except ValueError:
            return PolicyDecision(False, "prohibited", "The command could not be parsed safely.")
        if not argv:
            return PolicyDecision(False, "prohibited", "An empty command cannot be approved.")
        if any(path_has_sensitive_component(argument) for argument in argv[1:]):
            return PolicyDecision(
                False,
                "prohibited",
                "Credential and sensitive-path access is outside the Agent Workspace scope.",
            )
        if any(
            argument in self._UNSAFE_OPTIONS
            or argument.startswith(("--output=", "--pre=", "--pre-glob="))
            or re.fullmatch(r"-u{1,3}", argument)
            for argument in argv[1:]
        ):
            return PolicyDecision(
                False,
                "prohibited",
                "Execution hooks, recursive secret discovery, and write-capable options are outside the read contract.",
            )
        if any(
            argument.startswith(("/", "~", "../", "..\\"))
            or argument == ".."
            or "/../" in argument
            or "\\..\\" in argument
            or re.match(r"^[A-Za-z]:[\\/]", argument)
            for argument in argv[1:]
        ):
            return PolicyDecision(
                False,
                "prohibited",
                "Command paths must remain relative to the selected repository or worktree.",
            )
        if argv[:2] == ("git", "branch") and any(
            not argument.startswith("-") for argument in argv[2:]
        ):
            return PolicyDecision(
                False,
                "write",
                "Branch creation is outside the read-only command contract.",
            )
        read_only = any(argv[: len(prefix)] == prefix for prefix in self._READ_ONLY_PREFIXES)
        if safety_profile == "read-only" and not read_only:
            return PolicyDecision(
                False,
                "write",
                "Read-only mode accepts inspection commands only.",
            )
        return PolicyDecision(
            True,
            "read" if read_only else "write",
            "Command is inside the active P0 policy and still requires per-request approval.",
        )


@dataclass(frozen=True)
class TransferPreview:
    source_id: str
    classification: str
    original_length: int
    transmitted_length: int
    transmitted_text: str
    source_digest: str
    detections: tuple[str, ...]
    redaction_count: int
    allowed_to_transfer: bool = True
    blocked_categories: tuple[str, ...] = ()
    requires_confirmation: bool = True
    whole_document_confirmation_required: bool = False
    destination: str = "codex_app_server"
    estimated_utf8_bytes: int = 0


_TRANSFER_RULES = (
    *tuple(
        ("credential", pattern, "[REDACTED_CREDENTIAL]")
        for pattern in CREDENTIAL_PATTERNS
    ),
    (
        "email",
        EMAIL_PATTERN,
        "[REDACTED_EMAIL]",
    ),
    (
        "taiwan_phone",
        TAIWAN_PHONE_PATTERN,
        "[REDACTED_PHONE]",
    ),
    (
        "taiwan_national_id",
        TAIWAN_NATIONAL_ID_PATTERN,
        "[REDACTED_ID]",
    ),
)

_PRIVATE_BRAND_PATTERN = re.compile("vo" + "iss", re.IGNORECASE)


def neutralize_runtime_text(value: object) -> str:
    """Use product-neutral wording in runtime presentation and provider input."""

    return _PRIVATE_BRAND_PATTERN.sub("Project", str(value))


def build_transfer_preview(
    text: str,
    *,
    source_id: str,
    classification: str = "unknown",
) -> TransferPreview:
    if classification not in {
        "public",
        "internal",
        "internal_source",
        "confidential",
        "personal_data",
        "customer_confidential",
        "credential",
        "raw_audio",
        "local_audit",
        "restricted",
        "unknown",
    }:
        raise ValueError(f"Unsupported data classification: {classification}")
    transmitted = neutralize_runtime_text(text)
    detections: list[str] = []
    redaction_count = 0
    for label, pattern, replacement in _TRANSFER_RULES:
        transmitted, count = pattern.subn(replacement, transmitted)
        if count:
            detections.extend([label] * count)
            redaction_count += count
    return TransferPreview(
        source_id=source_id,
        classification=classification,
        original_length=len(text),
        transmitted_length=len(transmitted),
        transmitted_text=transmitted,
        source_digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        detections=tuple(detections),
        redaction_count=redaction_count,
        allowed_to_transfer="credential" not in detections,
        blocked_categories=("credential",) if "credential" in detections else (),
        requires_confirmation=classification != "public",
        estimated_utf8_bytes=len(transmitted.encode("utf-8")),
    )


class RiskClass(str, Enum):
    R0 = "R0"
    R1 = "R1"
    W1 = "W1"
    W2 = "W2"
    N1 = "N1"
    S1 = "S1"
    C1 = "C1"
    P1 = "P1"
    P2 = "P2"
    D1 = "D1"
    X1 = "X1"
    B1 = "B1"


class DataClass(str, Enum):
    PUBLIC = "public"
    INTERNAL_SOURCE = "internal_source"
    CONFIDENTIAL = "confidential"
    PERSONAL_DATA = "personal_data"
    CUSTOMER_CONFIDENTIAL = "customer_confidential"
    CREDENTIAL = "credential"
    RAW_AUDIO = "raw_audio"
    LOCAL_AUDIT = "local_audit"


@dataclass(frozen=True)
class CommandRequest:
    executable: str
    argv: tuple[str, ...]
    cwd: str
    shell: bool
    environment_names: tuple[str, ...]
    timeout_seconds: int
    network_required: bool = False
    network_destination: str | None = None
    expected_outputs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.executable or self.timeout_seconds < 1:
            raise ValueError("Command executable and positive timeout are required.")
        if any("=" in name for name in self.environment_names):
            raise ValueError("Command records environment names, never values.")


@dataclass(frozen=True)
class RepositoryPolicy:
    preset: str
    auto_risk_classes: frozenset[RiskClass]
    allowed_network_destinations: Mapping[str, tuple[str, ...]]
    allowed_branch_prefixes: tuple[str, ...] = ("aura-agent/",)
    protected_branches: tuple[str, ...] = ("main", "master")
    container_images: tuple[str, ...] = ()
    deny_patterns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.preset not in {"conservative", "standard", "team-ready", "custom"}:
            raise ValueError(f"Unsupported repository policy preset: {self.preset}")


@dataclass(frozen=True)
class PolicyContext:
    repository_root: Path
    worktree_root: Path | None
    mode: str
    repository_policy: RepositoryPolicy
    explicit_publish: bool = False
    target_branch: str | None = None
    default_branch: str | None = None
    remote_url: str | None = None
    recording_active: bool = False


class NetworkPolicy:
    def __init__(self, destinations: Mapping[str, tuple[str, ...]]):
        self.destinations = {
            purpose: tuple(values)
            for purpose, values in destinations.items()
        }

    def allows(self, destination: str, *, purpose: str) -> bool:
        parsed = urlparse(destination)
        hostname = (parsed.hostname or "").casefold()
        if not hostname:
            return False
        return any(
            hostname == allowed.casefold()
            or (
                allowed.startswith("*.")
                and hostname.endswith(allowed.removeprefix("*").casefold())
            )
            for allowed in self.destinations.get(purpose, ())
        )


class PolicyEngine:
    _SYSTEM_INSTALLERS = {
        "apt",
        "apt-get",
        "dnf",
        "pacman",
        "snap",
        "sudo",
        "yum",
        "zypper",
    }
    _PACKAGE_EXECUTABLES = {"pip", "pip3", "uv", "npm", "pnpm", "yarn"}
    _CONTAINER_EXECUTABLES = {"docker", "podman"}
    _NETWORK_EXECUTABLES = {
        "curl",
        "git",
        "gh",
        "nc",
        "ncat",
        "scp",
        "sftp",
        "ssh",
        "wget",
    }
    _BLOCKED_CONTAINER_ARGUMENTS = {
        "--privileged",
        "--network=host",
        "--pid=host",
        "/var/run/docker.sock",
    }

    def evaluate_command(
        self,
        request: CommandRequest,
        context: PolicyContext,
    ) -> PolicyDecision:
        executable = Path(request.executable).name.casefold()
        rendered = " ".join((request.executable, *request.argv))
        if any(fnmatch(rendered, pattern) for pattern in context.repository_policy.deny_patterns):
            return self._deny("A repository deny rule matched the command.")
        if executable in self._SYSTEM_INSTALLERS:
            return self._deny("System package installation and sudo are unavailable.")
        if request.shell or any(
            token in rendered
            for token in ("\n", "\r", "`", "$(", "&&", "||", ";", "|", ">", "<")
        ):
            return self._deny("Hidden shell composition is outside the execution contract.")
        if any(path_has_sensitive_component(argument) for argument in request.argv):
            return self._deny("Credential and sensitive paths are unavailable.")
        cwd = Path(request.cwd).expanduser().resolve(strict=True)
        repository = context.repository_root.expanduser().resolve(strict=True)
        worktree = (
            context.worktree_root.expanduser().resolve(strict=True)
            if context.worktree_root is not None
            else None
        )
        if context.mode in {"implement", "publish"}:
            if worktree is None or not _inside(cwd, worktree):
                return self._deny("Write-capable commands require the active worktree.")
        elif not _inside(cwd, repository):
            return self._deny("Read commands require the allowlisted repository.")

        if executable in self._CONTAINER_EXECUTABLES:
            if any(
                argument in self._BLOCKED_CONTAINER_ARGUMENTS
                or "docker.sock" in argument
                for argument in request.argv
            ):
                return self._deny(
                    "Privileged, host, and Docker-socket container access are unavailable."
                )
            return self._decision(
                RiskClass.C1,
                context,
                "Rootless container execution matches the declared mount and image policy.",
            )

        if executable in self._PACKAGE_EXECUTABLES and any(
            argument in {"add", "install", "sync", "update"}
            for argument in request.argv
        ):
            if context.recording_active:
                return PolicyDecision(
                    False,
                    "queued",
                    "Dependency work waits until recording and live ASR finish.",
                    RiskClass.S1.value,
                    "deferred",
                )
            return self._network_decision(
                RiskClass.S1,
                request,
                context,
                purpose="package_registry",
            )

        if executable == "git" and request.argv[:1] == ("push",):
            return self._publish_decision(request, context)
        if executable in {"gh"} and request.argv[:2] == ("pr", "create"):
            return self._publish_decision(request, context)
        if executable in self._NETWORK_EXECUTABLES and request.network_required:
            return self._network_decision(
                RiskClass.N1,
                request,
                context,
                purpose="official_documentation",
            )

        if executable == "rm":
            if any(argument in {"-rf", "-fr", "--recursive"} for argument in request.argv):
                return self._deny("Recursive destructive host commands are unavailable.")
            return self._decision(
                RiskClass.W2,
                context,
                "File deletion requires one run-scoped approval.",
                force_approval="once_per_run",
            )
        if executable == "git" and request.argv[:2] in {
            ("reset", "--hard"),
            ("clean", "-fdx"),
            ("merge", "--abort"),
        }:
            return self._deny("Destructive Git commands are unavailable.")

        risk = (
            RiskClass.R0
            if context.mode == "ask_explain"
            else RiskClass.W1
            if context.mode == "implement"
            else RiskClass.R1
        )
        return self._decision(
            risk,
            context,
            "Command is bounded by the active repository, mode, and sandbox.",
        )

    def _network_decision(
        self,
        risk: RiskClass,
        request: CommandRequest,
        context: PolicyContext,
        *,
        purpose: str,
    ) -> PolicyDecision:
        destination = request.network_destination
        if not destination or not NetworkPolicy(
            context.repository_policy.allowed_network_destinations
        ).allows(destination, purpose=purpose):
            return self._deny("The network destination is not approved for this purpose.")
        return self._decision(
            risk,
            context,
            "The destination matches the purpose-scoped repository policy.",
        )

    def _publish_decision(
        self,
        request: CommandRequest,
        context: PolicyContext,
    ) -> PolicyDecision:
        branch = context.target_branch or ""
        default_branch = context.default_branch or ""
        if (
            context.mode != "publish"
            or not context.explicit_publish
            or not any(
                branch.startswith(prefix)
                for prefix in context.repository_policy.allowed_branch_prefixes
            )
            or branch == default_branch
            or branch in context.repository_policy.protected_branches
            or any(argument in {"--force", "-f", "--force-with-lease"} for argument in request.argv)
        ):
            return self._deny(
                "Publish requires an explicit stage, allowed agent branch, and non-force target."
            )
        if context.remote_url not in {
            destination
            for values in context.repository_policy.allowed_network_destinations.values()
            for destination in values
        }:
            return self._deny("The publication remote is not allowlisted.")
        return self._decision(
            RiskClass.P2,
            context,
            "Explicit Publish scope matches the agent branch and remote.",
        )

    @staticmethod
    def _deny(reason: str) -> PolicyDecision:
        return PolicyDecision(False, "prohibited", reason, RiskClass.X1.value, "blocked")

    @staticmethod
    def _decision(
        risk: RiskClass,
        context: PolicyContext,
        reason: str,
        *,
        force_approval: str | None = None,
    ) -> PolicyDecision:
        approval = force_approval or (
            "auto"
            if risk in context.repository_policy.auto_risk_classes
            else "policy_or_user"
        )
        return PolicyDecision(
            approval == "auto",
            "read" if risk in {RiskClass.R0, RiskClass.R1} else "controlled",
            reason,
            risk.value,
            approval,
        )


@dataclass(frozen=True)
class InstructionTrustRecord:
    repository_id: str
    relative_path: str
    base_commit: str
    content_sha256: str
    approved_at: str


@dataclass(frozen=True)
class PromptInjectionFinding:
    source_alias: str
    attempted_effect: str
    control_outcome: str
    evidence_sha256: str


class InstructionTrustPolicy:
    _INJECTION_PATTERNS = (
        ("override_policy", re.compile(r"ignore (?:all |the )?(?:previous|system) instructions", re.I)),
        ("credential_request", re.compile(r"(?:send|print|read).{0,32}(?:token|password|credential)", re.I)),
        ("unapproved_network", re.compile(r"(?:curl|wget|upload).{0,80}https?://", re.I)),
        ("hidden_command", re.compile(r"(?:base64\s+-d|\beval\b|\bexec\b|\$\()", re.I)),
        ("disable_controls", re.compile(r"disable.{0,24}(?:test|security|sandbox|approval)", re.I)),
    )

    @staticmethod
    def approve(
        *,
        repository_id: str,
        repository: Path,
        instruction_file: Path,
        base_commit: str,
        approved_at: str,
        path_policy: PathPolicy,
    ) -> InstructionTrustRecord:
        path = path_policy.validate_read(instruction_file, repository)
        return InstructionTrustRecord(
            repository_id=repository_id,
            relative_path=path.relative_to(repository.resolve()).as_posix(),
            base_commit=base_commit,
            content_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            approved_at=approved_at,
        )

    @staticmethod
    def is_valid(
        record: InstructionTrustRecord,
        *,
        repository: Path,
        base_commit: str,
    ) -> bool:
        path = repository.resolve() / record.relative_path
        return (
            base_commit == record.base_commit
            and path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest()
            == record.content_sha256
        )

    @classmethod
    def scan_untrusted(
        cls,
        text: str,
        *,
        source_alias: str,
    ) -> tuple[PromptInjectionFinding, ...]:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return tuple(
            PromptInjectionFinding(
                source_alias=source_alias,
                attempted_effect=label,
                control_outcome="treated_as_untrusted_data_no_permission_granted",
                evidence_sha256=digest,
            )
            for label, pattern in cls._INJECTION_PATTERNS
            if pattern.search(text)
        )


class DataTransferGuard:
    def __init__(
        self,
        path_aliases: Mapping[str | Path, str] | None = None,
    ):
        self.path_aliases = tuple(
            (str(Path(path).expanduser().resolve()), alias)
            for path, alias in (path_aliases or {}).items()
        )

    def preview_text(
        self,
        text: str,
        *,
        source_id: str,
        classification: DataClass,
        content_kind: str = "selected_text",
        whole_document_confirmed: bool = False,
    ) -> TransferPreview:
        if classification in {DataClass.CREDENTIAL, DataClass.RAW_AUDIO}:
            return TransferPreview(
                source_id=source_id,
                classification=classification.value,
                original_length=len(text),
                transmitted_length=0,
                transmitted_text="",
                source_digest=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                detections=(classification.value,),
                redaction_count=0,
                allowed_to_transfer=False,
                blocked_categories=(classification.value,),
                requires_confirmation=False,
                estimated_utf8_bytes=0,
            )
        aliased = text
        for absolute, alias in self.path_aliases:
            aliased = aliased.replace(absolute, alias)
        preview = build_transfer_preview(
            aliased,
            source_id=source_id,
            classification=classification.value,
        )
        full_document = content_kind == "full_transcript"
        return TransferPreview(
            **{
                **preview.__dict__,
                "allowed_to_transfer": (
                    preview.allowed_to_transfer
                    and (not full_document or whole_document_confirmed)
                ),
                "whole_document_confirmation_required": (
                    full_document and not whole_document_confirmed
                ),
            }
        )

    @staticmethod
    def authorize(preview: TransferPreview, *, confirmed: bool) -> str:
        if not preview.allowed_to_transfer:
            raise PermissionError(
                "Transfer remains blocked by data classification or confirmation."
            )
        if preview.requires_confirmation and not confirmed:
            raise PermissionError("Transfer preview requires explicit confirmation.")
        return preview.transmitted_text
