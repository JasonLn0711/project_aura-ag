# 2. Repository Map

## Assessment

**Confirmed.** The observed repository contains 508 source-controlled or visible worktree files. Entry points, tests, documentation, artifacts, and the Agent module remain separately inventoried.

## Required Coverage

- Directory purpose, entry points, source versus generated files, tests, documentation, artifacts, Agent additions, and ownership hotspots.

## Detailed Findings

### Directory ownership

**Confirmed.** `src/aura/` owns application services and native UI; `src/aura/agent/` owns the reversible Agent edge; `tests/` owns executable regression evidence; `docs/` owns durable design and operating guidance; `artifacts/` owns measured run and report packets; `scripts/` owns developer and release utilities. Exact file kind, size, digest, and tracked state are recorded in `../inventories/repository-files.csv`.

### Entry points and generated data

**Confirmed.** Console entry points are `aura`, `project-aura`, and `aura-evidence`; see `../inventories/entry-points.csv`. Python under `src/`, tests, and docs are source. Agent runs, architecture packets, distributions, caches, and session outputs are generated data with separate ownership.

### Hotspots

**Confirmed.** `MainWindow` composes major tabs, while `TranscriptionTab` remains the largest established workflow hotspot. The Agent module is intentionally outside that class. Static class ownership and line locations are in `../inventories/components.csv`.

## Evidence and Scope

Source commit: `3cddc5a8adee076baab829e8535c86e8f69b0861`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../inventories/repository-files.csv`, `components.csv`, and `entry-points.csv`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
