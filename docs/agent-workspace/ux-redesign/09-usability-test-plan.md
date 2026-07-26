# Agent Workspace Usability Test Plan

**Status:** READY FOR EXECUTION
**Result claim:** No usability result is claimed until this protocol is run.

## Objective

Determine whether a first-time operator can begin from intent, distinguish
general and evidence-backed work, locate attention and artifacts, return to
recent work, and inspect execution context without understanding provider
protocol or settings structure.

## Participants

Target five internal participants:

- at least two familiar with Git repositories;
- at least two unfamiliar with the Agent Workspace;
- at least one who regularly uses a CJK input method;
- no participant receives implementation details before the session.

If fewer than five participate, results are reported as partial evidence and
the 4-of-5 acceptance target remains open.

## Environment

- Ubuntu 24.04 desktop
- production-equivalent AURA theme
- 1280×820 primary test viewport
- one 1024×768 constrained-layout pass
- deterministic Demo data for repeatability
- one configured repository with recent, queued, attention, completed, and
  evidence-backed fixture threads
- no credentials, private meeting content, or raw audio in captured material

## Moderator protocol

1. State that this is a product test, not a participant test.
2. Ask the participant to think aloud.
3. Give only the task objective.
4. Record the first action, time, wrong clicks, backtracks, and help requests.
5. Provide help only after the participant declares they cannot continue.
6. After each task, record confidence from 1 to 5.
7. After all tasks, run the five-second comprehension check.

## Tasks

### T-01 — Start a general repository question

Prompt:

> 請詢問這個 Repository 的啟動方式，以及主要入口在哪裡。

Success:

- composer found;
- question sent;
- no General/Evidence workflow selection required;
- read-only scope understood.

### T-02 — Create a feature task

Prompt:

> 請建立一項功能任務：在設定頁加入鍵盤快捷鍵說明。

Success:

- intent entered;
- Implement scope recognized;
- isolated-worktree meaning understood;
- task started or reaches the expected confirmation.

### T-03 — Attach a confirmed meeting action

Prompt:

> 將已確認的「補上操作手冊」會議 Action 加入任務，並在傳送前確認來源。

Success:

- Evidence Context Picker found;
- eligible item selected;
- source preview understood;
- attachment recognized as context;
- transfer preview reached before provider submission.

### T-04 — Find a task waiting for approval

Prompt:

> 找到目前需要你確認的任務，說明核准後會發生什麼事。

Success:

- Needs Attention found;
- approval opened;
- consequence explained correctly;
- offered decisions identified.

### T-05 — Review a diff and tests

Prompt:

> 找到剛完成的修改，查看它的 Diff 與 Tests。

Success:

- correct completed thread opened;
- both artifacts reached within two actions each;
- actual artifact status distinguished from unavailable content.

### T-06 — Return to a recent task

Prompt:

> 回到剛才詢問啟動方式的任務，繼續補上一句問題。

Success:

- recent thread reopened within two actions;
- draft or follow-up composer used;
- current thread identity remains clear.

### T-07 — Find account, model, and worktree details

Prompt:

> 找到目前的 ChatGPT 帳戶狀態、實際模型，以及是否正在隔離 Worktree 執行。

Success:

- environment surface found within two actions;
- all three values located;
- normal settings traversal not required.

## Five-second comprehension check

Show the new-task state for five seconds, then hide it. Ask the participant to
identify:

1. selected repository;
2. input location;
3. send action;
4. meeting-context action;
5. task history location.

Target: at least four of five participants identify at least four of the five
items.

## General versus evidence-backed check

Ask:

> 一般 Repository 任務與加入會議證據的任務，有什麼差別？

Successful explanation includes:

- both use the same task/thread surface;
- evidence-backed work has an attached confirmed source;
- attachment stays local until transfer preview and confirmation;
- evidence does not itself grant write or publication authority.

Target: correct explanation from at least four of five participants.

## Measures

For every task record:

| Measure | Recording rule |
| --- | --- |
| Completion | complete, complete with help, incomplete |
| Time to first action | seconds from prompt end to first meaningful action |
| Completion time | seconds to success or stop |
| Wrong clicks | action not advancing the task |
| Backtracks | explicit return after entering the wrong surface |
| Help | count and exact moderator cue |
| Confidence | 1–5 after task |
| Notes | participant language and observed confusion |

## Acceptance thresholds

- Each critical task: at least 4 of 5 complete without help.
- T-04, T-05, T-06, and T-07: target surface reached within two actions.
- Five-second comprehension: at least 4 of 5 identify at least 4 of 5 items.
- General/evidence understanding: at least 4 of 5 explain the distinction.
- Median confidence: at least 4 of 5-scale.
- No repeated critical misunderstanding of send, approval consequence,
  evidence transfer, or publication authority.

## Evidence handling

Retain:

- anonymized participant IDs;
- task-level metric table;
- moderator notes;
- screenshot or screen recording only with explicit participant consent;
- issue list linked to acceptance criteria;
- changes made after the study;
- retest result.

Private participant data and raw recording remain outside repository artifacts.
The repository receives only consent-safe aggregate results.

## Reporting template

| Participant | T-01 | T-02 | T-03 | T-04 | T-05 | T-06 | T-07 | Median confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P-01 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| P-02 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| P-03 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| P-04 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| P-05 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |

The table remains `NOT RUN` until real sessions occur.
