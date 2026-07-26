# 20. Open Questions, Unknowns, and Release Gates

## Assessment

**Confirmed.** Target-platform runtime evidence, immutable model identity, native BOM completeness, hosted multi-user isolation, and future write-back remain separately activated validation work packages.

## Required Coverage

- Platform verification, immutable model identity, native BOM completeness, hosted isolation, write-back, and provider drift remain explicit release gates.

## Detailed Findings

### Active release gates

**Unknown.** Complete Windows and macOS execution evidence is not present. **Partially Verified.** Native tools and provider-hosted model identities are observed rather than immutably bound. **Confirmed.** The P0 is local single-user; hosted tenancy requires a separate identity and threat-model work package.

### Future activation paths

**Confirmed.** Network-enabled execution, API-key billing, automatic write-back, push/merge/deployment, dynamic renderers, and concurrent Live runs remain outside the active P0 contract. Provider-schema refresh, a target-OS matrix, native/model manifests, and a user-approved Live worktree rehearsal are the next validation steps. Machine-readable gates are in `../validation/missing-evidence.json` and `../inventories/risks.csv`.

## Evidence and Scope

Source commit: `44f266970c5c28999314d347de73f86ca52048fa`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../validation/missing-evidence.json`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
