# 24. Permission, Network, Dependency, Container, and Publication Governance

## Assessment

**Confirmed.** Operating modes and repository-session grants are bounded by deny-first filesystem, command, network, dependency, container, branch, and publication controls.

## Required Coverage

- Operating modes, scoped AUTO grants, command/network/package/container controls, supply-chain evidence, worktree publication, protected branches, and deployment boundary.

## Detailed Findings

### Governed autonomy

**Confirmed.** Ask is read-only, Review writes Agent artifacts, Implement writes inside an isolated worktree, and Publish requires its own explicit stage. Repository-session grants are repository, commit, workflow, capability, and expiry scoped; deny rules govern sensitive paths, sudo/system packages, hidden shell, network, privileged containers, default branches, force push, merge, and deployment.

### Supply chain and publication

**Partially Verified.** Frozen Python resolution, SBOMs, native/model BOMs, Codex compatibility capture, changed-file secret scanning, disabled repository hooks, sanitized allowlisted remotes, external credentials, and redacted PR bodies form the active chain. The vulnerability scanner result and target-host native manifests remain explicit evidence in command results and missing-evidence.

## Evidence and Scope

Source commit: `3cddc5a8adee076baab829e8535c86e8f69b0861`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../controls.csv`, `../risk-register.csv`, and `../sbom/`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
