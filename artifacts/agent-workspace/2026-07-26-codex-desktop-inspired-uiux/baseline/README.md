# Agent Workspace UI Redesign Baseline Evidence

**Captured:** 2026-07-26 (Asia/Taipei)
**Commit:** `9b54c36064c7869d5b752ba03646ff9ed57cfaa9`
**State:** New task / empty thread
**Platform:** Ubuntu 24.04, PyQt6 offscreen

## Capture command

Each image was captured with the repository's native Qt screenshot harness:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=src \
  /home/jnclaw/every_on_git_jnclaw/project_aura-ag/.venv/bin/python \
  scripts/capture_agent_workspace_screenshot.py \
  --repository /home/jnclaw/every_on_git_jnclaw/project_aura-agent-uiux-expert \
  --output <target> \
  --width <width> \
  --height <height>
```

The harness uses the real `AgentWorkspaceTab` and deterministic Demo
configuration. The Phase 2 capture harness will also load the production AURA
QSS so visual comparison represents the released theme.

## Files and checksums

| File | SHA-256 |
| --- | --- |
| `agent-empty-1024x768.png` | `b03eb4c23028f6797141eb5cd3e88bcf2357d0c2aa675694b8db5fc750e1e603` |
| `agent-empty-1280x820.png` | `9051fb97a7b7aca2514b01ceddaa63706a46ceb4b299e3f85fa6e2770cb71793` |
| `agent-empty-1440x900.png` | `9bbe91559e94a7039e78779433d4c7f09ca631029fa59ab77aa00014614c0c58` |
| `agent-empty-1920x1080.png` | `0bf7ae0d94f595ae80348f66f82313fecc9578b8a7a5090a1dc3a1da4df965dc` |

## Widget-tree summary at 1280×820

```text
AgentWorkspaceTab 1280×820
├── agentHeader 1264×34
├── agentMainSplitter 1264×464
│   ├── TaskRail 240×464
│   ├── agentTaskThread 1020×464
│   └── DynamicArtifactInspector hidden, nominal 380×464
└── agentComposer 1264×292
```

The empty thread contains two primary task-path buttons and four workflow
buttons. The composer contains an editable workflow combo, one task editor,
three selector controls, transfer/phase labels, and a separate send button.

## Baseline validation

Focused:

```text
Ran 13 tests in 2.318s
OK
```

Complete frozen suite:

```text
Ran 486 tests in 27.926s
OK
```

These are pre-change behavior baselines. Usability, accessibility, scale, and
visual improvement remain implementation validation gates.
