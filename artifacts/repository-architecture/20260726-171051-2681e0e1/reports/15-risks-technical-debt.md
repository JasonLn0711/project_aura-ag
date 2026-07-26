# 15. Risks and Technical Debt

## Assessment

**CONFIRMED.** The register contains 27 owned risks with severity, likelihood, confidence, evidence, impact, mitigation, verification, release gate, and residual risk.

## Required Coverage

- Every registered risk carries ID, severity, likelihood, evidence, impact, mitigation, owner, verification, and release gate.

## Detailed Findings

### Priority risk posture

**CONFIRMED.** Critical risks cover prompt injection, credential disclosure, and future hosted multi-user isolation. High risks cover UI hotspots, ASR backpressure, lock discipline, model identity, PII/provenance, protocol drift, child lifecycle, native reproducibility, and report certainty. Medium risks cover local audit assurance, OS portability, coverage depth, and worktree lifecycle.

**CONFIRMED.** `../risk-register.csv` carries all 27 IDs with severity, likelihood, confidence, evidence, operational impact, mitigation, owner, verification, release gate, and residual risk. `../controls.csv` maps the active execution, credential, UI, network, data, Git, audit, and recovery protections.

## Evidence and Scope

Source commit: `fdc0e4f659bacb2c895d65a0df87801deb20d241`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../inventories/risks.csv` and `controls.csv`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
