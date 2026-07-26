# Stable Daily-Use Soak Report

Status: **PASS**

Runtime classification: `valid_deterministic_reliability_soak`

This gate exercised the production native Qt workspace, controller, deterministic provider adapter, per-run evidence store, SQLite catalog, queue transitions, resource governor, shutdown, and Recovery Cards.

## Live Counts

- Representative runs: 50
- Completed runs: 40
- Interrupted runs: 10
- Provider/application restarts: 5
- Recovery Card exercises: 5
- Distinct workflows: 11

## Reliability Results

- Maximum UI heartbeat gap: 67.054 ms (gate: under 500 ms)
- Catalog integrity: ok
- Tracked checkout unchanged: true
- Out-of-bound write findings: 0
- Orphan process findings in this deterministic provider soak: 0
- Storage-pressure decision: `queue`
- Recording/live-ASR pressure decision: `queue`
- Per-run artifact integrity: 50/50 valid

## Scope Control

This is valid deterministic reliability evidence for the AURA production contracts. It is distinct from live Codex inference evidence; the release packet records the real Codex minimum and process-tree shutdown test separately.
