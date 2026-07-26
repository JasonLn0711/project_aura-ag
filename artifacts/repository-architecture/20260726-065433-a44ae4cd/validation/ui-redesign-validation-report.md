# Native Agent Workspace Validation Report

**Executed:** 2026-07-26 (Asia/Taipei)
**Soak code checkpoint:** `43eab8361ad22de45a9d98f4ad52a6f8d0a9a9f9`
**Final clean-source regression checkpoint:** `6d2b137c60049cb7e8951882e8b8ace9b2d854b0`

## Result

**CONFIRMED:** The implemented native workspace, migration compatibility,
four-resolution state set, bounded model/view presentation, content-free
audit, and deterministic reliability soak satisfy their executed gates.

**PARTIALLY VERIFIED:** The typed facade owns core run intentions and the new
presentation paths meet their measured latency targets. Some legacy
catalog/Git/report/media/provider actions still require full migration to
background application-service execution.

**NOT VERIFIED:** The required five-participant usability study and
assistive-technology field review were not executed.

## Executed commands

```bash
QT_QPA_PLATFORM=offscreen \
  uv run python -m unittest discover -s tests -v

uv run python -m compileall -q src tests scripts
git diff --check

QT_QPA_PLATFORM=offscreen \
  uv run python scripts/run_agent_workspace_soak.py \
  --output artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/soak-report.json

uv run python scripts/summarize_audit_events.py --format json \
  artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/audit-evidence
```

## Results

| Check | Executed result |
| --- | --- |
| Full regression | 520 tests in 32.393 seconds; `OK` |
| Compile | `src`, `tests`, `scripts`; `PASS` |
| Diff whitespace | `PASS` |
| Native soak | 50 tasks in 7.328 seconds; `PASS` |
| Audit integrity | 1,223 events; `PASS` |
| Screen geometries | 36/36 individual final captures match declared width/height |
| Visual comparison | Combined baseline and redesign image inspected |
| Performance | 12.348ms switch; 0.488ms event; 0.028ms bounded 50 MiB preview |

Expected diagnostic output:

- upstream `webrtcvad` warns that `pkg_resources` is deprecated;
- the Qt offscreen plugin reports unsupported native window capabilities;
- the audio recovery test deliberately emits its device-disconnection
  traceback and passes.

These messages have passing owning tests and do not alter the result.

## Checksums

- soak report:
  `b23dcc9aa2deb437114da057dee2e063679063ea8cc5dc4625ce221ef4f6b337`;
- content-free audit:
  `87dd6cd6473195d6fa2c152ac74d082e68650fa0b8c956458722c97de652258c`;
- combined visual comparison:
  `3247dbf3aa1b0f12d4f4cc90609bbee77fa1955f4984b468e2705536fc9d52a6`.

The complete manifest is [`checksums.sha256`](checksums.sha256).
