# Project AURA v1.17.0 Release Validation

## Result

Status: `READY_FOR_PR`

The Ubuntu 24.04 release candidate completes the requested v1.17.0 feature,
privacy, anonymization, native-control, workflow, CUDA, local-LLM, and
reliability gates. The formal GitHub pull request, hosted CI, merge commit,
annotated tag, and release publication are the remaining activation steps.

The code candidate under test is commit `c331312357979857c700ff3395232bddcb3df36b`.
Documentation-only release preparation may advance the branch while this code
commit remains the validated implementation boundary.

## Runtime Validity

| Runtime or surface | Classification | Measured result |
| --- | --- | --- |
| AURA Breeze ASR 25 on CUDA | `valid_target_runtime` | 10 real runs over five public zh-TW clips |
| Meetily Breeze ASR 26 on CUDA | `valid_target_runtime` | 10 paired real runs over the same public clips |
| Pyannote speaker diarization on CUDA | `valid_target_runtime` | 2 real runs, 54 speaker turns |
| AURA splitter product pipeline | `valid_target_runtime` | 1 real 450-second run, 2 ordered WAV chunks |
| Local Ollama summary pipeline | `valid_target_runtime` | 1 complete `gemma4:e4b-it-qat` run, 9/9 fields valid |
| Codex app-server read-only turn | `valid_target_runtime` | 1 real turn, 0 approvals, unchanged checkout, clean process tree |
| Physical microphone capture | `valid_target_runtime` | 1 real 4.74-second mono capture with device state restored |
| Native Qt control matrix | `valid_target_runtime` | 36/36 reachable controls and state gates pass |
| Native workspace soak | `valid_deterministic_reliability_soak` | 50/50 tasks pass through production Qt and controller paths |
| Stable daily-use soak | `valid_deterministic_reliability_soak` | 50/50 runs pass through production Qt, catalog, and recovery paths |

The paired ASR decision uses the two zh-TW-capable runtimes. Parakeet remains
outside this zh-TW capability contract and therefore does not serve as a
release-blocking variant.

## Validation

- Full repository regression: 607/607 tests pass.
- Native Qt controls: 36 passed, 0 blocked, 0 harness errors.
- Native Qt latency: 18.132 ms ordinary maximum, 0.022 ms progress
  projection, and 194.035 ms visible heartbeat maximum.
- Workspace soak: 50 tasks, 10 approvals, 10 stops, 30 provider
  failure/reconnect cycles, 10 recovery cycles, and 1,323 content-free audit
  events.
- Workspace interaction latency: 18.173 ms repository/thread switch,
  8.574 ms large-event projection, and 0.031 ms for a bounded 64 KiB preview
  from a 50 MiB log.
- Stable daily-use soak: 40 completed runs, 10 interrupted runs, 5 provider
  restarts, 5 Recovery Card exercises, 12 workflows, and a 71.680 ms maximum
  UI heartbeat gap against the 500 ms gate.
- Public anonymization gate: working tree, registered worktrees, all local Git
  objects, and Git metadata pass with zero policy findings.
- Locked all-extras dependency audit: the previously classified single
  setuptools advisory is reproduced; the release publishes source plus the
  privacy-safe validation manifest and checksum asset, while the macOS
  activation path retains the advisory refresh gate.

## Privacy and Evidence Stewardship

This public packet contains aggregate counts, runtime classifications,
privacy-safe public-fixture descriptions, and repository-relative evidence
routes. Raw recordings, transcripts, provider identifiers, account details,
host identifiers, private paths, and detailed event traces remain in the
operator-controlled local evidence package.

The separately preserved legacy checkout, linked worktrees, dirty Partner
line, recovery bundle, and patch inventory remain private. Their retention
review is scheduled for 2026-08-27.

## Scope Controls

Ubuntu 24.04 x86_64 is the measured release platform. Native Windows and macOS
release-host execution, the five-participant usability study, and the
screen-reader field study remain separately activated validation paths.

## Decision

- Production default: Project AURA v1.17.0 on Ubuntu 24.04 after formal PR,
  hosted CI, merge, tag, and GitHub Release publication.
- Operational fallback: the deterministic Demo provider through the same
  native workspace and evidence contracts.
- Research candidate: target-host Windows/macOS validation and the
  five-participant usability study.
- Next optimization candidate: screen-reader field validation and measured
  background-service migration where future traces exceed the current
  responsiveness gates.
