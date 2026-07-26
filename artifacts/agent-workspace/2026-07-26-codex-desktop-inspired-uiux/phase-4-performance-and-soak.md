# Phase 4 — Performance, backpressure, and recovery evidence

Status: **CONFIRMED for deterministic native Qt integration scope**

The Agent Workspace now applies bounded loading and Qt model/view projection to
the scalable artifact paths covered in this phase:

- a 50 MiB command log loads a 64 KiB preview rather than the complete file;
- changed-file summaries use one `QAbstractListModel` and `QListView`;
- mutating work observes the low-storage activation gate while read-only work
  remains available;
- a 50-task native offscreen soak covers approval, stop, reconnect, recovery,
  recording, storage protection, persistence, and restart.

## Executed evidence

Command:

```bash
QT_QPA_PLATFORM=offscreen uv run python \
  scripts/run_agent_workspace_soak.py \
  --output artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/soak-report.json
```

Measured result:

| Check | Result |
| --- | ---: |
| Total deterministic tasks | 50 |
| Approval cycles | 10 |
| Stop/interruption cycles | 10 |
| Provider-failure/reconnect cycles | 30 |
| Explicit recovery cycles after restart | 10 |
| Persisted work items after restart | 50 |
| Total soak time | 7,353.791 ms |
| Three thread switches | 10.279 ms |
| Large-event projection | 0.466 ms |
| 50 MiB log preview | 0.029 ms |
| Bytes loaded from 50 MiB log | 65,536 |
| Content-free local audit events | 1,223 |

The soak report is
[`soak/soak-report.json`](soak/soak-report.json), SHA-256
`13e0dac76efc594bd4d0bd7004429ce744a6e7dffc0a32ee54d3ead63922f310`.
Its audit evidence is
[`soak/audit-evidence/audit-2026-07-26.jsonl`](soak/audit-evidence/audit-2026-07-26.jsonl),
SHA-256
`1672d4e46ecfef8a2d70ec20b726d37290babb6acc754bebd34b607c16165219`.

## Scope control

This phase confirms deterministic native Qt behavior with the Demo provider.
Live Codex compatibility remains covered by the existing fake app-server
integration tests and the separately retained workspace-write incident packet.
Human usability outcomes require the specified five-participant evaluation and
remain a separate validation layer.
