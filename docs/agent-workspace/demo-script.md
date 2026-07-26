# Repository Assurance Demo Script

## Setup

1. Launch Project AURA.
2. Open **AI Agent**.
3. Select **Environment** and confirm `DEMO` with `本機 Demo`.
4. Select **Technical Architecture Package** and enable the repository fixture
   through the Demo controls.
5. Choose `Approval`, speed `1x`, `4x`, or `Instant`.
6. Confirm the visible local-only notice:
   `Demo 模式：內容只在本機模擬，不會傳到外部 AI。`
7. Optionally choose **查看模擬內容**, close the non-blocking inspection, and
   start. Demo does not request external-transfer approval.
8. Confirm the Demo execution policy when the selected scenario requests it.

## Complete scenario

Observe:

1. provider readiness;
2. sanitized repository and architecture context;
3. explicit preflight, context, and planning phases;
4. R-001, R-002, and R-003 evidence links;
5. R-002 selected as the bounded remediation;
6. an approval card for a simulated isolated worktree;
7. **Approve once** as the request-scoped action;
8. simulated command lifecycle;
9. a realistic bounded-queue patch in Diff;
10. exact deterministic tests: 8 passed, 0 failed, 0 skipped;
11. twenty-five report sections;
12. `ready_with_limitations` validation;
13. validated evidence ZIP export;
14. `demo_completed` terminal outcome.

Evidence, Diff, Tests, Report, and Run inspectors appear as their artifacts
arrive. Pause and resume preserve event order. Reset clears only the visible
Demo playback state and never removes Live or AURA artifacts.

## Required branches

Replay each branch:

| Branch | Expected terminal |
| --- | --- |
| Approval | `completed` |
| Rejection | `completed` with plan retained and remediation inactive |
| Stop during planning | `interrupted` in planning |
| Stop during command | `interrupted` in running |
| Provider failure | `failed` |
| Test failure | `failed`; remediation remains unverified |
| Report validation failure | `failed`; partial report state retained |

All branches use production DTOs, reducer, renderers, approvals, persistence,
and inspectors. No branch reports completion from missing output.
