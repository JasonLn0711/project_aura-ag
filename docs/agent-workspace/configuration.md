# Agent Workspace Configuration

## Precedence

Configuration precedence is:

1. constructor values used by tests or an embedding application;
2. documented environment overrides;
3. `AgentConfig` safe defaults;
4. provider discovery for account, model, effort, and version.

Values are typed and validated before use. Secret values do not belong in
these settings.

## Defaults

| Key | Default |
| --- | --- |
| `agent.enabled` | `true` |
| `agent.default_mode` | `live` |
| `agent.default_profile` | `standard` |
| `agent.default_safety_profile` | `read-only` |
| `agent.network_access_default` | `false` |
| `agent.one_live_run_only` | `true` |
| `agent.redaction_enabled` | `true` |
| `agent.audit_enabled` | existing AURA audit setting |
| `agent.demo_speed` | `300 ms/event` |
| `agent.retention_days` | `0`; retain until the operator deletes |
| Codex startup timeout | `10 seconds` |
| Codex request timeout | `30 seconds` |
| Codex message limit | `8 MiB` |

Run, worktree, and report roots use Qt `AppDataLocation` unless overridden.

## Environment overrides

| Variable | Purpose |
| --- | --- |
| `AURA_AGENT_DEFAULT_MODE` | `live` by default; set `demo` for deterministic local playback |
| `AURA_AGENT_RUN_ROOT` | Durable per-run directories |
| `AURA_AGENT_WORKTREE_ROOT` | Detached approved worktrees |
| `AURA_AGENT_ALLOWED_ROOTS` | `os.pathsep`-separated repository roots |
| `AURA_CODEX_EXECUTABLE` | Explicit Codex executable |
| `AURA_CODEX_STARTUP_TIMEOUT_SECONDS` | Process startup bound |
| `AURA_CODEX_REQUEST_TIMEOUT_SECONDS` | Per-request bound |
| `AURA_CODEX_MAX_MESSAGE_BYTES` | JSONL trust-boundary limit |
| `AURA_AGENT_DEFAULT_PROFILE` | `quick`, `standard`, or `expert` |
| `AURA_AGENT_DEFAULT_SAFETY_PROFILE` | Must remain `read-only`; approved worktree write activates per run |
| `AURA_AGENT_DEMO_SPEED_MS` | Deterministic playback interval |
| `AURA_AGENT_RETENTION_DAYS` | Reserved retention horizon; this release performs no automatic deletion |
| `AURA_AGENT_REPORT_OUTPUT_ROOT` | Suggested package-export root |

Allowed roots must exist. The stable daily-use contract requires a
network-disabled default, active redaction, and exactly one Live run.

Live startup performs provider initialization, compatibility probing, account
read, and model discovery automatically. A completed provider-managed login
triggers another account read and moves the same page to ready without an app
restart. Provider thread and turn IDs are execution identities, so AURA creates
them only when the first prompt starts a real audited run.

The workspace retains Agent run artifacts until the operator deletes them. The typed
retention value reserves a future activation path and never triggers automatic
cleanup in this release.
