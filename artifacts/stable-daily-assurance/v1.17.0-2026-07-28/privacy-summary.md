# Project AURA v1.17.0 Privacy Validation

## Result

Status: `PASS`

The executable public-anonymization policy passes across the release
candidate's working tree, every registered worktree, all reachable local Git
objects, and Git metadata with zero findings.

## Public Evidence Scope

The public release carries aggregate validation counts, runtime
classifications, public-fixture descriptions, source commit and tag
provenance, and repository-relative evidence locators. This gives operators
and maintainers a durable verification path while preserving the local
evidence boundary.

## Protected Local Scope

Operator recordings and transcripts, provider and account identifiers, host
identifiers, private filesystem paths, raw event traces, credentials, the
legacy checkout, linked worktrees, the dirty Partner line, and recovery
patches remain in the private operator-controlled package.

The private recovery package has an explicit retention review on 2026-08-27.
Review is an operator stewardship checkpoint and does not schedule automatic
deletion.

## Verification

```bash
.venv/bin/python scripts/check_public_anonymization.py \
  --all-worktrees \
  --git-objects \
  --git-metadata
```

The gate reports:

```text
Public anonymization check passed for 1 registered worktrees, all local Git objects, Git metadata.
```

