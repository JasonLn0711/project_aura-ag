import os
import unittest
from dataclasses import replace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from aura.agent.contracts import AgentUiEvent
from aura.agent.providers.codex_app_server import extract_reasoning_summary_text
from aura.ui.agent_workspace.coalescer import TimelineCoalescer
from aura.ui.agent_workspace.coalescer import ProjectionChange
from aura.ui.agent_workspace.markdown_renderer import (
    DenyResourceTextDocument,
    MarkdownLinkPolicy,
    MarkdownRenderer,
)
from aura.ui.agent_workspace.timeline import TimelineModel, TimelineRole
from aura.ui.agent_workspace.view_state import TimelineContentFormat
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QStyleOptionViewItem
from aura.ui.agent_workspace.timeline_view import ThreadTimelineView
from aura.ui.agent_workspace.view_state import TimelineItemViewState


def event(sequence: int, event_type: str, payload: dict) -> AgentUiEvent:
    return AgentUiEvent.create(
        run_id="run-markdown",
        event_type=event_type,
        sequence=sequence,
        source="fixture",
        severity="info",
        payload=payload,
        created_at=f"2026-07-26T17:40:{sequence % 60:02d}+08:00",
        event_id=f"event-{sequence}",
    )


class TimelineContentFormatTests(unittest.TestCase):
    def test_projection_declares_markdown_and_technical_formats(self):
        coalescer = TimelineCoalescer()

        coalescer.consume(
            event(
                1,
                "message.user",
                {"item_id": "user-1", "text": "**檢查** `git status`"},
            )
        )
        coalescer.consume(
            event(
                2,
                "command.output.delta",
                {"command_id": "command-1", "text": "* raw stdout"},
            )
        )

        self.assertEqual(
            coalescer.items[0].content_format,
            TimelineContentFormat.MARKDOWN,
        )
        self.assertEqual(
            coalescer.items[1].content_format,
            TimelineContentFormat.STRUCTURED,
        )
        self.assertEqual(coalescer.items[1].details[0].output, "* raw stdout")

    def test_every_timeline_family_has_an_explicit_safe_format(self):
        cases = (
            ("message.user", {"item_id": "u", "text": "hello"}, TimelineContentFormat.MARKDOWN),
            (
                "message.assistant.completed",
                {"item_id": "a", "text": "hello"},
                TimelineContentFormat.MARKDOWN,
            ),
            (
                "reasoning.summary.completed",
                {"item_id": "s", "summary": "summary"},
                TimelineContentFormat.MARKDOWN,
            ),
            ("plan.updated", {"text": "plan"}, TimelineContentFormat.MARKDOWN),
            ("diff.updated", {"text": "+line"}, TimelineContentFormat.DIFF),
            (
                "test.completed",
                {"passed": 1, "failed": 0, "skipped": 0},
                TimelineContentFormat.STRUCTURED,
            ),
            (
                "report.ready",
                {"section_count": 1},
                TimelineContentFormat.STRUCTURED,
            ),
            (
                "provider.protocol_error",
                {},
                TimelineContentFormat.STRUCTURED,
            ),
        )

        for event_type, payload, expected in cases:
            with self.subTest(event_type=event_type):
                coalescer = TimelineCoalescer()
                coalescer.consume(event(1, event_type, payload))
                self.assertEqual(coalescer.items[-1].content_format, expected)


class ProviderSummaryNormalizationTests(unittest.TestCase):
    def test_summary_extractor_accepts_display_shapes_and_fails_closed(self):
        self.assertEqual(
            extract_reasoning_summary_text(
                {"summary": ["先確認工作樹。", "接著執行測試。"]}
            ),
            "先確認工作樹。\n\n接著執行測試。",
        )
        self.assertEqual(
            extract_reasoning_summary_text({"summary": "單段摘要"}),
            "單段摘要",
        )
        self.assertEqual(
            extract_reasoning_summary_text(
                {
                    "summary": [
                        {"type": "summary_text", "text": "第一段"},
                        {"type": "summary_text", "text": "第二段"},
                    ]
                }
            ),
            "第一段\n\n第二段",
        )
        self.assertEqual(
            extract_reasoning_summary_text(
                {"summary": [{"unexpected": "SECRET_VALUE"}]}
            ),
            "",
        )
        self.assertNotIn(
            "sk-live-secret",
            extract_reasoning_summary_text(
                {"summary": "Token: sk-live-secret"}
            ),
        )


class SummaryProjectionTests(unittest.TestCase):
    def test_empty_completion_retains_delta_and_empty_only_creates_no_row(self):
        coalescer = TimelineCoalescer()

        coalescer.consume(
            event(
                1,
                "reasoning.summary.delta",
                {"item_id": "summary-1", "text": "先確認工作樹。"},
            )
        )
        coalescer.consume(
            event(
                2,
                "reasoning.summary.completed",
                {"item_id": "summary-1", "summary": "   \n"},
            )
        )
        empty_change = coalescer.consume(
            event(
                3,
                "reasoning.summary.completed",
                {"item_id": "summary-2", "summary": ""},
            )
        )

        self.assertEqual(len(coalescer.items), 1)
        self.assertEqual(coalescer.items[0].title, "處理摘要")
        self.assertEqual(coalescer.items[0].body, "先確認工作樹。")
        self.assertEqual(coalescer.items[0].status, "completed")
        self.assertEqual(
            coalescer.items[0].content_format,
            TimelineContentFormat.MARKDOWN,
        )
        self.assertEqual(empty_change, ())

    def test_completed_only_summary_is_visible_without_python_repr(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "reasoning.summary.completed",
                {
                    "item_id": "summary-1",
                    "summary": "已完成 **事件模型** 檢查。",
                },
            )
        )

        self.assertEqual(len(coalescer.items), 1)
        self.assertEqual(
            coalescer.items[0].body,
            "已完成 **事件模型** 檢查。",
        )
        self.assertNotIn("{", coalescer.items[0].body)


class PlanAndLifecycleCopyTests(unittest.TestCase):
    def test_plan_statuses_and_fixed_steps_use_taiwan_copy(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "plan.updated",
                {
                    "steps": [
                        {
                            "status": "completed",
                            "step": "Validate context and policy",
                        },
                        {
                            "status": "in_progress",
                            "step": "Run the read-only provider turn",
                        },
                        {
                            "status": "pending",
                            "step": "Provider-authored next step",
                        },
                    ]
                },
            )
        )

        plan = coalescer.items[0]
        self.assertEqual(plan.title, "執行計畫")
        self.assertIn("**已完成：** 確認專案內容與執行設定", plan.body)
        self.assertIn("**進行中：** 執行唯讀檢查", plan.body)
        self.assertIn("**接下來：** Provider-authored next step", plan.body)
        self.assertEqual(plan.content_format, TimelineContentFormat.MARKDOWN)

    def test_provider_and_context_lifecycle_never_expose_raw_updated(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(event(1, "provider.starting", {}))
        starting = "\n".join(
            f"{item.title}\n{item.body}" for item in coalescer.items
        )
        coalescer.consume(event(2, "provider.model_list.updated", {}))
        coalescer.consume(
            event(
                3,
                "context.snapshot",
                {"repository": "/repo"},
            )
        )

        visible = "\n".join(
            f"{item.title}\n{item.body}" for item in coalescer.items
        )
        self.assertIn("正在連線 Codex", starting)
        self.assertIn("Codex 已就緒", visible)
        self.assertIn("專案內容已準備完成", visible)
        self.assertNotIn("updated", visible)
        self.assertNotIn("Repository Context", visible)

    def test_run_file_report_and_outcome_copy_never_exposes_raw_enums(self):
        coalescer = TimelineCoalescer()
        lifecycle = (
            ("run.started", {}),
            ("run.phase_changed", {"phase": "context_review"}),
            ("run.phase_changed", {"phase": "planning"}),
            ("run.phase_changed", {"phase": "running"}),
            (
                "file_change.completed",
                {"file_change_id": "files-1", "paths": ["src/a.py"]},
            ),
            ("report.section_ready", {"section_total": 2}),
            ("report.validation_completed", {"status": "completed"}),
            ("report.ready", {"section_count": 2}),
            ("run.completed", {"outcome": "live_turn_completed"}),
        )
        for sequence, (event_type, payload) in enumerate(lifecycle, start=1):
            coalescer.consume(event(sequence, event_type, payload))

        visible = "\n".join(
            f"{item.title}\n{item.body}" for item in coalescer.items
        )
        for raw_value in (
            "started",
            "context_review",
            "planning",
            "running",
            "completed",
            "sections ready",
            "Validation:",
            "Report ready",
            "live_turn_completed",
        ):
            self.assertNotIn(raw_value, visible)
        self.assertIn("工作進度", visible)
        self.assertIn("1 個檔案已完成更新", visible)
        self.assertIn("架構報告已完成", visible)
        self.assertIn("成果已可供覆核", visible)

    def test_empty_message_plan_and_orphan_output_create_no_cards(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "message.assistant.completed",
                {"item_id": "assistant-empty", "text": " \n"},
            )
        )
        coalescer.consume(event(2, "plan.updated", {"text": "\n"}))
        coalescer.consume(
            event(
                3,
                "command.output.delta",
                {"command_id": "orphan", "text": " \n"},
            )
        )

        self.assertEqual(coalescer.items, [])


class ActivityDigestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_command_lifecycle_updates_one_progress_row_with_details(self):
        coalescer = TimelineCoalescer()
        lifecycle = (
            (
                "command.started",
                {
                    "command_id": "git-status",
                    "command": "git status --short",
                    "cwd": "/repo",
                },
            ),
            (
                "command.output.delta",
                {
                    "command_id": "git-status",
                    "text": " M src/a.py\n",
                },
            ),
            (
                "command.completed",
                {
                    "command_id": "git-status",
                    "command": "git status --short",
                    "cwd": "/repo",
                    "exit_code": 0,
                    "duration_ms": 25,
                    "output": " M src/a.py\n",
                },
            ),
            (
                "command.started",
                {
                    "command_id": "tests",
                    "command": "python -m pytest -q",
                    "cwd": "/repo",
                },
            ),
            (
                "command.completed",
                {
                    "command_id": "tests",
                    "command": "python -m pytest -q",
                    "cwd": "/repo",
                    "exit_code": 2,
                    "duration_ms": 1400,
                    "output": "collection error",
                },
            ),
        )
        for sequence, (event_type, payload) in enumerate(lifecycle, start=1):
            coalescer.consume(event(sequence, event_type, payload))

        self.assertEqual(len(coalescer.items), 1)
        progress = coalescer.items[0]
        self.assertEqual(progress.stable_id, "progress:run-markdown")
        self.assertEqual(progress.kind, "progress")
        self.assertEqual(progress.title, "工作進度")
        self.assertEqual(
            progress.content_format,
            TimelineContentFormat.STRUCTURED,
        )
        self.assertEqual(progress.detail_count, 2)
        self.assertTrue(progress.details_available)
        self.assertIn("1 項檢查未完成", progress.body)
        self.assertNotIn("exit 0", progress.body)
        self.assertNotIn("git status --short", progress.body)
        self.assertEqual(progress.details[0].label, "檢查 Git 工作區狀態")
        self.assertEqual(progress.details[0].status, "completed")
        self.assertEqual(progress.details[1].label, "執行測試")
        self.assertEqual(progress.details[1].status, "failed")
        self.assertEqual(progress.details[1].exit_code, 2)
        self.assertIn("collection error", progress.details[1].output)

    def test_legal_search_no_match_and_unknown_command_use_conservative_copy(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "command.completed",
                {
                    "command_id": "search",
                    "command": "rg missing src",
                    "exit_code": 1,
                },
            )
        )
        self.assertEqual(coalescer.items[0].severity, "info")
        coalescer.consume(
            event(
                2,
                "command.completed",
                {
                    "command_id": "unknown",
                    "command": "custom-inspector --safe",
                    "exit_code": 0,
                },
            )
        )

        progress = coalescer.items[0]
        self.assertEqual(progress.details[0].status, "completed")
        self.assertEqual(progress.details[0].label, "搜尋程式碼")
        self.assertEqual(progress.details[1].label, "執行唯讀檢查")
        self.assertEqual(progress.details[1].status, "completed")

    def test_expanded_progress_copy_contains_bounded_technical_details(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "command.completed",
                {
                    "command_id": "tests",
                    "command": "python -m pytest -q",
                    "cwd": "/repo",
                    "exit_code": 2,
                    "duration_ms": 1400,
                    "output": "collection error",
                },
            )
        )
        view = ThreadTimelineView()
        view.resize(520, 480)
        view.timeline_model.replace_items(coalescer.items)
        view.setCurrentIndex(view.timeline_model.index(0, 0))
        view.show()
        self.app.processEvents()

        QTest.keyClick(view, Qt.Key.Key_Return)
        view.copy_selected(raw=False)
        copied = self.app.clipboard().text()

        self.assertIn("執行測試", copied)
        self.assertIn("狀態：未完成", copied)
        self.assertIn("命令：python -m pytest -q", copied)
        self.assertIn("工作目錄：/repo", copied)
        self.assertIn("耗時：1.4 秒", copied)
        self.assertIn("結束代碼：2", copied)
        self.assertIn("collection error", copied)
        view.close()

    def test_approval_and_terminal_events_update_progress_and_keep_cards(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "command.started",
                {
                    "command_id": "status",
                    "command": "git status --short",
                },
            )
        )
        coalescer.consume(
            event(
                2,
                "approval.requested",
                {
                    "approval_id": "approval-1",
                    "reason": "Confirm inspection.",
                },
            )
        )

        progress = next(
            item for item in coalescer.items if item.kind == "progress"
        )
        self.assertIn("需要你確認", progress.body)
        self.assertTrue(
            any(item.kind == "approval" for item in coalescer.items)
        )

        coalescer.consume(
            event(
                3,
                "approval.resolved",
                {
                    "approval_id": "approval-1",
                    "decision": "approved_once",
                },
            )
        )
        coalescer.consume(
            event(4, "run.completed", {"outcome": "live_turn_completed"})
        )

        progress = next(
            item for item in coalescer.items if item.kind == "progress"
        )
        self.assertIn("檢視完成", progress.body)
        self.assertEqual(progress.status, "completed")
        self.assertTrue(
            any(item.kind == "outcome" for item in coalescer.items)
        )

    def test_out_of_order_duplicate_and_recovery_projection_are_equivalent(self):
        events = (
            event(
                1,
                "command.started",
                {
                    "command_id": "status",
                    "command": "git status --short",
                    "cwd": "/repo",
                },
            ),
            event(
                2,
                "command.output.delta",
                {"command_id": "status", "text": " M src/a.py\n"},
            ),
            event(
                3,
                "command.completed",
                {
                    "command_id": "status",
                    "command": "git status --short",
                    "cwd": "/repo",
                    "exit_code": 0,
                    "duration_ms": 20,
                },
            ),
            event(4, "run.completed", {"outcome": "live_turn_completed"}),
        )
        sequential = TimelineCoalescer()
        for item in events:
            sequential.consume(item)

        replayed = TimelineCoalescer()
        for item in (events[1], events[0], events[3], events[2], events[3]):
            replayed.consume(item)

        self.assertEqual(replayed.items, sequential.items)
        self.assertEqual(replayed.activity_digest, sequential.activity_digest)

    def test_file_change_completion_closes_existing_tool_detail(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "tool.output.delta",
                {
                    "item_id": "file-change-1",
                    "tool": "fileChange",
                    "text": "prepared patch",
                },
            )
        )
        coalescer.consume(
            event(
                2,
                "file_change.completed",
                {
                    "file_change_id": "file-change-1",
                    "changes": [{"path": "src/a.py"}],
                },
            )
        )

        progress = next(
            item for item in coalescer.items if item.kind == "progress"
        )
        self.assertEqual(progress.details[0].status, "completed")
        self.assertEqual(progress.details[0].label, "準備檔案變更")
        self.assertIn("已完成 1 項檢查", progress.body)


class MarkdownRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_native_renderer_preserves_source_and_projects_readable_markdown(self):
        source = """## 建議順序

1. 先確認 **事件資料模型**。
2. 再執行 `pytest`。

> 結果由你確認。

| 狀態 | 數量 |
| --- | ---: |
| 完成 | 7 |

- [ ] 待確認

[文件](https://example.com/docs)
"""
        result = MarkdownRenderer(max_cache_entries=8).render(
            stable_id="assistant-1",
            source=source,
            content_format=TimelineContentFormat.MARKDOWN,
            width_px=420,
            font=self.app.font(),
            palette=self.app.palette(),
        )

        self.assertEqual(result.raw_source, source)
        self.assertIn("建議順序", result.plain_text)
        self.assertIn("事件資料模型", result.plain_text)
        self.assertIn("pytest", result.plain_text)
        self.assertNotIn("**", result.plain_text)
        self.assertNotIn("`", result.plain_text)
        self.assertEqual(result.links, ("https://example.com/docs",))
        self.assertGreater(result.full_height, 100)

    def test_untrusted_html_resources_and_links_remain_inert(self):
        source = """<script>approve()</script>
<iframe src="file:///etc/passwd">system</iframe>

![遠端](https://example.com/a.png)
![本機](file:///etc/passwd)
![資料](data:image/png;base64,AAAA)

[安全文件](https://example.com/docs)
[腳本](javascript:approve())
[檔案](file:///etc/passwd)
[內部偽裝](repo://trusted/path)

- [ ] Approve
"""
        result = MarkdownRenderer(max_cache_entries=8).render(
            stable_id="assistant-security",
            source=source,
            content_format=TimelineContentFormat.MARKDOWN,
            width_px=420,
            font=self.app.font(),
            palette=self.app.palette(),
        )

        self.assertIn("[圖片：遠端]", result.plain_text)
        self.assertIn("[圖片：本機]", result.plain_text)
        self.assertIn("[圖片：資料]", result.plain_text)
        self.assertNotIn("\ufffc", result.plain_text)
        self.assertNotIn("<script>", result.document.toHtml())
        self.assertEqual(result.document.blocked_resources, [])
        self.assertEqual(
            MarkdownLinkPolicy.describe("https://example.com/docs"),
            "example.com — https://example.com/docs",
        )
        for destination in (
            "javascript:approve()",
            "data:text/plain,approve",
            "file:///etc/passwd",
            "repo://trusted/path",
            "https://user:password@example.com/private",
        ):
            self.assertIsNone(MarkdownLinkPolicy.describe(destination))

    def test_supported_and_partial_markdown_matrix_fails_safe(self):
        source = """# Heading

Paragraph one.

Paragraph two with **bold**, *italic*, ~~strike~~, `inline`, 中文標點，and emoji 🧭.

- unordered
  - nested
1. ordered

```python
print("code")
```

> quote

```mermaid
graph TD; A-->B
```

**unfinished
```python
unfinished(
"""
        result = MarkdownRenderer(max_cache_entries=4).render(
            stable_id="matrix",
            source=source,
            content_format=TimelineContentFormat.MARKDOWN,
            width_px=260,
            font=self.app.font(),
            palette=self.app.palette(),
        )

        for text in (
            "Heading",
            "Paragraph one.",
            "Paragraph two",
            "nested",
            "ordered",
            "print",
            "quote",
            "graph TD",
            "unfinished",
            "中文標點",
            "🧭",
        ):
            self.assertIn(text, result.plain_text)
        self.assertEqual(result.raw_source, source)
        self.assertFalse(result.render_failed)

    def test_renderer_failure_uses_plain_source_without_exception_content(self):
        renderer = MarkdownRenderer(max_cache_entries=2)
        source = "**still visible**"
        with patch.object(
            DenyResourceTextDocument,
            "setMarkdown",
            side_effect=RuntimeError("secret parser diagnostic"),
        ):
            result = renderer.render(
                stable_id="fallback",
                source=source,
                content_format=TimelineContentFormat.MARKDOWN,
                width_px=240,
                font=self.app.font(),
                palette=self.app.palette(),
            )

        self.assertTrue(result.render_failed)
        self.assertEqual(result.raw_source, source)
        self.assertEqual(result.plain_text, source)
        self.assertNotIn("secret parser diagnostic", result.plain_text)

    def test_cache_is_bounded_and_key_never_contains_source_text(self):
        renderer = MarkdownRenderer(max_cache_entries=2)
        for index in range(3):
            renderer.render(
                stable_id=f"item-{index}",
                source=f"private-source-{index}",
                content_format=TimelineContentFormat.MARKDOWN,
                width_px=240,
                font=self.app.font(),
                palette=self.app.palette(),
            )
        renderer.render(
            stable_id="item-2",
            source="private-source-2",
            content_format=TimelineContentFormat.MARKDOWN,
            width_px=240,
            font=self.app.font(),
            palette=self.app.palette(),
        )

        self.assertEqual(renderer.cache_size, 2)
        self.assertEqual(renderer.cache_hits, 1)
        for key in renderer._cache:
            self.assertNotIn("private-source", repr(key))

    def test_long_code_and_wide_table_stay_within_document_width(self):
        renderer = MarkdownRenderer(max_cache_entries=4)
        for stable_id, source in (
            ("code", "```\n" + "x" * 500 + "\n```"),
            (
                "table",
                "| value |\n| --- |\n| " + "寬" * 300 + " |",
            ),
            ("plain", "a" * 500),
        ):
            with self.subTest(stable_id=stable_id):
                result = renderer.render(
                    stable_id=stable_id,
                    source=source,
                    content_format=TimelineContentFormat.MARKDOWN,
                    width_px=300,
                    font=self.app.font(),
                    palette=self.app.palette(),
                )
                self.assertLessEqual(result.full_size.width(), 301)
                self.assertGreater(result.full_height, 30)

    def test_collapsed_height_never_slices_through_a_table_frame(self):
        result = MarkdownRenderer(max_cache_entries=2).render(
            stable_id="collapsed-table",
            source=(
                "## Result\n\n"
                + "Readable paragraph. " * 8
                + "\n\n| field | value |\n| --- | --- |\n"
                "| one | alpha |\n| two | beta |\n| three | gamma |"
            ),
            content_format=TimelineContentFormat.MARKDOWN,
            width_px=360,
            font=self.app.font(),
            palette=self.app.palette(),
            max_collapsed_lines=7,
        )
        iterator = result.document.rootFrame().begin()
        table = None
        while not iterator.atEnd() and table is None:
            table = iterator.currentFrame()
            iterator += 1

        self.assertIsNotNone(table)
        table_rect = result.document.documentLayout().frameBoundingRect(table)
        self.assertTrue(result.collapsed)
        self.assertLessEqual(result.visible_height, table_rect.top())


class TimelineGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_markdown_row_height_reflows_with_available_width(self):
        view = ThreadTimelineView()
        view.resize(720, 500)
        view.timeline_model.replace_items(
            (
                TimelineItemViewState(
                    stable_id="assistant-wrap",
                    kind="assistant",
                    title="Aura，回覆",
                    body=(
                        "## 檢查結果\n\n"
                        + "這是一段需要依照可用寬度自然換行的台灣繁體中文內容。" * 8
                        + "\n\n1. 保留原始段落。\n2. 依寬度重新排版。"
                    ),
                    created_at="2026-07-26T17:41:00+08:00",
                    content_format=TimelineContentFormat.MARKDOWN,
                    presentation_tier="primary",
                    max_collapsed_lines=None,
                    raw_source_available=True,
                ),
            )
        )
        index = view.timeline_model.index(0, 0)
        delegate = view.itemDelegate()

        wide = QStyleOptionViewItem()
        wide.font = view.font()
        wide.palette = view.palette()
        wide.rect = QRect(0, 0, 680, 1000)
        narrow = QStyleOptionViewItem(wide)
        narrow.rect = QRect(0, 0, 340, 1000)

        wide_height = delegate.sizeHint(wide, index).height()
        narrow_height = delegate.sizeHint(narrow, index).height()

        self.assertGreater(wide_height, 64)
        self.assertGreater(narrow_height, wide_height)
        self.assertEqual(
            view.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.assertEqual(view.accessibleName(), "任務對話與工作進度")

    def test_keyboard_expands_and_copies_display_or_raw_markdown(self):
        view = ThreadTimelineView()
        view.resize(420, 480)
        original = TimelineItemViewState(
            stable_id="assistant-expand",
            kind="assistant",
            title="Aura，回覆",
            body="## 結果\n\n" + "**已完成** 檢查。\n\n" * 12,
            created_at="2026-07-26T17:42:00+08:00",
            content_format=TimelineContentFormat.MARKDOWN,
            presentation_tier="primary",
            max_collapsed_lines=3,
            raw_source_available=True,
        )
        view.timeline_model.replace_items((original,))
        index = view.timeline_model.index(0, 0)
        view.setCurrentIndex(index)
        view.show()
        self.app.processEvents()

        option = QStyleOptionViewItem()
        option.font = view.font()
        option.palette = view.palette()
        option.rect = QRect(0, 0, 380, 1000)
        collapsed_height = view.itemDelegate().sizeHint(option, index).height()

        QTest.keyClick(view, Qt.Key.Key_Return)
        expanded_height = view.itemDelegate().sizeHint(option, index).height()
        self.assertTrue(view.timeline_model.item_at(0).expanded)
        self.assertGreater(expanded_height, collapsed_height)

        QTest.keyClick(
            view,
            Qt.Key.Key_C,
            Qt.KeyboardModifier.ControlModifier,
        )
        display_copy = self.app.clipboard().text()
        self.assertIn("已完成", display_copy)
        self.assertNotIn("**", display_copy)

        QTest.keyClick(
            view,
            Qt.Key.Key_C,
            Qt.KeyboardModifier.ControlModifier
            | Qt.KeyboardModifier.ShiftModifier,
        )
        self.assertEqual(self.app.clipboard().text(), original.body)

        QTest.keyClick(view, Qt.Key.Key_Space)
        self.assertFalse(view.timeline_model.item_at(0).expanded)
        view.close()

    def test_selected_item_opens_one_recycled_selectable_full_viewer(self):
        view = ThreadTimelineView()
        item = TimelineItemViewState(
            stable_id="assistant-selectable",
            kind="assistant",
            title="Aura",
            body="## 結果\n\n**已完成** `pytest`。\n\n" + "全文。" * 100,
            created_at="2026-07-26T17:42:00+08:00",
            content_format=TimelineContentFormat.MARKDOWN,
            max_collapsed_lines=2,
            raw_source_available=True,
        )
        view.timeline_model.replace_items((item,))
        view.setCurrentIndex(view.timeline_model.index(0, 0))

        self.assertTrue(view.open_selected_text_viewer())
        first_viewer = view._text_viewer
        self.assertTrue(first_viewer.isVisible())
        self.assertIn("已完成", view._text_viewer_edit.toPlainText())
        self.assertNotIn("**", view._text_viewer_edit.toPlainText())
        self.assertNotIn("`", view._text_viewer_edit.toPlainText())
        self.assertIsNone(view.indexWidget(view.timeline_model.index(0, 0)))

        self.assertTrue(view.open_selected_text_viewer())
        self.assertIs(view._text_viewer, first_viewer)
        view._text_viewer.reject()
        view.close()

    def test_escape_collapses_and_delta_update_preserves_expansion(self):
        view = ThreadTimelineView()
        original = TimelineItemViewState(
            stable_id="assistant-expand",
            kind="assistant",
            title="Aura",
            body="## Result\n\n" + "Long paragraph. " * 30,
            created_at="2026-07-26T17:42:00+08:00",
            content_format=TimelineContentFormat.MARKDOWN,
            max_collapsed_lines=2,
        )
        view.timeline_model.replace_items((original,))
        view.setCurrentIndex(view.timeline_model.index(0, 0))
        view.timeline_model.set_expanded(0, True)
        view.timeline_model.apply_changes(
            (
                ProjectionChange(
                    "update",
                    0,
                    replace(original, body=original.body + " Final."),
                ),
            )
        )
        self.assertTrue(view.timeline_model.item_at(0).expanded)

        QTest.keyClick(view, Qt.Key.Key_Escape)
        self.assertFalse(view.timeline_model.item_at(0).expanded)
        self.assertTrue(view.hasFocus() or view.focusPolicy() != Qt.FocusPolicy.NoFocus)

    def test_accessible_item_text_uses_role_names_without_raw_markdown_symbols(self):
        model = TimelineModel()
        model.replace_items(
            (
                TimelineItemViewState(
                    stable_id="assistant-accessible",
                    kind="assistant",
                    title="Aura",
                    body="**已完成** `pytest`。",
                    created_at="2026-07-26T17:42:00+08:00",
                    content_format=TimelineContentFormat.MARKDOWN,
                ),
            )
        )

        accessible = model.data(
            model.index(0, 0),
            Qt.ItemDataRole.AccessibleTextRole,
        )
        self.assertIn("Aura，回覆", accessible)
        self.assertIn("已完成", accessible)
        self.assertNotIn("**", accessible)
        self.assertNotIn("`", accessible)

    def test_font_scaling_increases_height_without_horizontal_scroll(self):
        view = ThreadTimelineView()
        view.timeline_model.replace_items(
            (
                TimelineItemViewState(
                    stable_id="scaled",
                    kind="assistant",
                    title="Aura",
                    body="## 結果\n\n" + "可讀內容。" * 80,
                    created_at="2026-07-26T17:42:00+08:00",
                    content_format=TimelineContentFormat.MARKDOWN,
                ),
            )
        )
        index = view.timeline_model.index(0, 0)
        option = QStyleOptionViewItem()
        option.font = view.font()
        option.palette = view.palette()
        option.rect = QRect(0, 0, 480, 1000)
        normal = view.itemDelegate().sizeHint(option, index).height()

        scaled = QStyleOptionViewItem(option)
        scaled.font = option.font
        scaled.font.setPointSizeF(option.font.pointSizeF() * 2)
        doubled = view.itemDelegate().sizeHint(scaled, index).height()

        self.assertGreater(doubled, normal)
        self.assertEqual(
            view.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

    def test_view_emits_only_policy_checked_link_requests(self):
        view = ThreadTimelineView()
        requested = []
        view.external_link_requested.connect(
            lambda destination, description: requested.append(
                (destination, description)
            )
        )

        self.assertTrue(
            view.request_external_link("https://example.com/docs")
        )
        for destination in (
            "javascript:approve()",
            "data:text/plain,approve",
            "file:///etc/passwd",
            "repo://trusted/path",
        ):
            self.assertFalse(view.request_external_link(destination))

        self.assertEqual(
            requested,
            [
                (
                    "https://example.com/docs",
                    "example.com — https://example.com/docs",
                )
            ],
        )

    def test_new_content_follows_only_when_reader_is_near_bottom(self):
        view = ThreadTimelineView()
        view.resize(420, 220)
        items = tuple(
            TimelineItemViewState(
                stable_id=f"item-{index}",
                kind="assistant",
                title="Aura，回覆",
                body=("第 " + str(index) + " 項內容。" * 20),
                created_at="2026-07-26T17:43:00+08:00",
                content_format=TimelineContentFormat.MARKDOWN,
            )
            for index in range(20)
        )
        view.timeline_model.replace_items(items)
        view.show()
        self.app.processEvents()
        view.scrollToBottom()
        self.app.processEvents()

        appended = TimelineItemViewState(
            stable_id="item-20",
            kind="assistant",
            title="Aura，回覆",
            body="底部更新。",
            created_at="2026-07-26T17:43:20+08:00",
            content_format=TimelineContentFormat.MARKDOWN,
        )
        view.queue_changes(
            (ProjectionChange("append", 20, appended),),
            flush_immediately=True,
        )
        self.app.processEvents()
        self.assertEqual(
            view.verticalScrollBar().value(),
            view.verticalScrollBar().maximum(),
        )

        view.verticalScrollBar().setValue(0)
        second = TimelineItemViewState(
            stable_id="item-21",
            kind="assistant",
            title="Aura，回覆",
            body="閱讀期間的新內容。",
            created_at="2026-07-26T17:43:21+08:00",
            content_format=TimelineContentFormat.MARKDOWN,
        )
        view.queue_changes(
            (ProjectionChange("append", 21, second),),
            flush_immediately=True,
        )
        self.app.processEvents()

        self.assertEqual(view.verticalScrollBar().value(), 0)
        self.assertTrue(view.new_content_button.isVisibleTo(view))
        view.new_content_button.click()
        self.app.processEvents()
        self.assertEqual(
            view.verticalScrollBar().value(),
            view.verticalScrollBar().maximum(),
        )
        self.assertFalse(view.new_content_button.isVisible())
        view.close()

    def test_one_thousand_streaming_changes_are_throttled_into_one_row(self):
        view = ThreadTimelineView()
        coalescer = TimelineCoalescer()
        for sequence in range(1, 1001):
            changes = coalescer.consume(
                event(
                    sequence,
                    "message.assistant.delta",
                    {"item_id": "assistant-stream", "text": "字"},
                )
            )
            view.queue_changes(changes, flush_immediately=False)

        self.assertTrue(view._render_timer.isActive())
        self.assertEqual(view.timeline_model.rowCount(), 0)
        QTest.qWait(70)
        self.app.processEvents()

        self.assertEqual(view.timeline_model.rowCount(), 1)
        self.assertEqual(
            len(view.timeline_model.item_at(0).body),
            1000,
        )


if __name__ == "__main__":
    unittest.main()
