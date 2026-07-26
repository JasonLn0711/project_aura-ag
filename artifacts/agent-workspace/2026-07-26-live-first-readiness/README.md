# Live-First Agent Readiness Evidence

## Status

`LIVE_MINIMUM_COMPLETED`

This packet validates the corrected Live-first path on Ubuntu 24.04:

- Codex app-server starts through the supported JSONL stdio transport;
- the existing ChatGPT account is discovered as signed in;
- `gpt-5.6-sol` resolves without silent fallback;
- a real read-only turn creates provider thread and turn identities;
- the expected model reply is observed;
- no approval is requested;
- the tracked checkout remains unchanged;
- the provider process tree closes cleanly.

The live minimum ran after the production catalog reconciled the previously
stale completed Run and released the Live worker.

## Runtime summary

| Field | Result |
| --- | --- |
| Runtime classification | `valid_target_runtime` |
| Codex CLI | `0.145.0` |
| Compatibility | `compatible` |
| Account | `signed_in` / `chatgpt` |
| Safety | `read-only` |
| Network | Disabled |
| Model | `gpt-5.6-sol` |
| Effort | `low` |
| Expected reply | Observed |
| Unexpected approval | `false` |
| Tracked checkout changed | `false` |
| Process tree clean | `true` |
| Event count | `34` |
| Preflight | `0.241 seconds` |
| Turn | `5.936 seconds` |
| Total | `6.199 seconds` |

## Files

| File | Purpose |
| --- | --- |
| [Runtime validity](live-read-only-minimum/runtime-validity-report.md) | Target-runtime classification and safety result |
| [Live summary](live-read-only-minimum/live-run-summary.json) | Machine-readable bounded runtime evidence |
| [Request summary](live-read-only-minimum/request-summary.jsonl) | Content-free request scope |
| [Event trace](live-read-only-minimum/event-trace.jsonl) | Sanitized lifecycle, provider, thread, turn, and completion events |
| [Error log](live-read-only-minimum/error-log.jsonl) | Empty error stream for this successful run |
| [Latency](live-read-only-minimum/latency-report.md) | Measured provider and turn duration |
| [Failure analysis](live-read-only-minimum/failure-analysis.md) | Observed failure status and broader fault-path boundary |

## Regression evidence

Focused Agent regression:

```text
71 tests passed
```

Full repository regression:

```text
594 tests passed
```

## Data boundary

The request contained a synthetic sentinel instruction. The packet stores
opaque hashes for provider identities, captures no credential values, and
transfers no raw audio. Canonical local audit evidence retains the content-free
catalog reconciliation event.
