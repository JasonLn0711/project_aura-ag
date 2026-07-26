# 17. Testing and Quality Strategy

## Assessment

**Confirmed.** The current test inventory contains 484 discovered test functions. Unit, JSON-RPC, UI, integration, regression, security, and Demo snapshot layers form the P0 quality path.

## Required Coverage

- Unit, contract, integration, security, Demo snapshot, offscreen Qt, full regression, package, and platform validation layers.

## Detailed Findings

### Quality layers

**Confirmed.** Static discovery recorded 484 test functions. The suite covers service units, event/reducer contracts, policies, persistence, Demo snapshots, real Git worktree isolation, fake JSONL process integration, provider mapping, security boundaries, offscreen Qt UI, MainWindow integration, packaged resources, versioning, and established AURA regression behavior.

**Partially Verified.** The architecture generator inventories tests but does not convert source discovery into a pass claim. Executed counts belong in the release validation packet. Cross-platform native UI, audio, GPU, and process checks remain target-host quality gates.

## Evidence and Scope

Source commit: `44f266970c5c28999314d347de73f86ca52048fa`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../inventories/tests.csv` and `../validation/validation-report.md`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
