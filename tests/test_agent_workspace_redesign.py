import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QListWidget,
    QStackedWidget,
    QToolButton,
    QTreeView,
)

from aura.ui.agent_workspace.agent_composer import AgentComposer
from aura.ui.agent_workspace.artifact_inspector import ArtifactInspector
from aura.ui.agent_workspace.evidence_picker import (
    EvidenceCandidateModel,
    EvidenceContextPicker,
)
from aura.ui.agent_workspace.settings import AgentSettingsDialog
from aura.ui.agent_workspace.sidebar import RepositoryThreadModel
from aura.ui.agent_workspace.sidebar_view import WorkspaceSidebar
from aura.ui.agent_workspace.text_controls import (
    ElidedLabel,
    ElidingPushButton,
)
from aura.ui.agent_workspace.timeline import TimelineModel
from aura.ui.agent_workspace.timeline_view import (
    ThreadTimelineView,
    TimelineDelegate,
)
from aura.ui.agent_workspace_components import EnvironmentDialog


class AgentWorkspaceRedesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_sidebar_and_timeline_use_native_model_view(self):
        sidebar = WorkspaceSidebar()
        self.assertIsInstance(sidebar.tree, QTreeView)
        self.assertIsInstance(sidebar.model, RepositoryThreadModel)
        self.assertFalse(sidebar.tree.uniformRowHeights())
        sidebar.set_records(
            (
                {
                    "repository_id": "repo-1",
                    "display_name": "Repository with a long display name",
                },
            ),
            (
                {
                    "work_item_id": "work-1",
                    "repository_id": "repo-1",
                    "title": "A long task title that remains on one line",
                    "state": "draft",
                    "relative_time": "2 分鐘前",
                },
            ),
        )
        sidebar.resize(268, 600)
        sidebar.show()
        self.app.processEvents()
        repository = sidebar.model.index(0, 0)
        group = sidebar.model.index(0, 0, repository)
        thread = sidebar.model.index(0, 0, group)
        self.assertEqual(sidebar.tree.visualRect(repository).height(), 30)
        self.assertEqual(sidebar.tree.visualRect(thread).height(), 46)

        timeline = ThreadTimelineView()
        self.assertIsInstance(timeline.model(), TimelineModel)
        self.assertIsNotNone(timeline.itemDelegate())
        self.assertEqual(len(timeline.findChildren(QListWidget)), 0)

    def test_timeline_uses_subtle_odd_row_backgrounds(self):
        self.assertEqual(
            TimelineDelegate.background_for_row(0).name(),
            "#20262d",
        )
        self.assertIsNone(TimelineDelegate.background_for_row(1))

    def test_environment_tabs_fit_content_without_scroll_arrows(self):
        dialog = EnvironmentDialog()
        dialog.resize(680, 460)
        dialog.show()
        self.app.processEvents()
        tab_bar = dialog.tabs.tabBar()

        self.assertFalse(tab_bar.expanding())
        self.assertTrue(tab_bar.usesScrollButtons())
        self.assertLessEqual(
            sum(tab_bar.tabRect(index).width() for index in range(tab_bar.count())),
            dialog.tabs.width(),
        )
        self.assertFalse(
            any(button.isVisible() for button in tab_bar.findChildren(QToolButton))
        )

        private_name = "VO" + "ISS"
        dialog.update_sections(
            {"repository": f"Legacy {private_name} repository"}
        )
        self.assertNotIn(
            private_name.casefold(),
            dialog.sections["repository"].toPlainText().casefold(),
        )

    def test_collapsed_sidebar_keeps_a_stable_expand_control(self):
        sidebar = WorkspaceSidebar()
        sidebar.resize(268, 600)
        sidebar.show()
        self.app.processEvents()

        sidebar.toggle_collapsed()
        self.app.processEvents()

        self.assertTrue(sidebar._collapsed)
        self.assertFalse(sidebar.title_label.isVisibleTo(sidebar))
        self.assertTrue(sidebar.collapse_button.isVisibleTo(sidebar))
        self.assertGreaterEqual(sidebar.collapse_button.width(), 32)
        self.assertLessEqual(sidebar.collapse_button.y(), 12)
        self.assertFalse(sidebar.collapse_button.icon().isNull())
        self.assertIn("展開", sidebar.collapse_button.toolTip())

        sidebar.collapse_button.click()
        self.app.processEvents()
        self.assertFalse(sidebar._collapsed)
        self.assertTrue(sidebar.title_label.isVisibleTo(sidebar))

    def test_single_line_controls_elide_without_losing_full_text(self):
        text = "Repository with a very long name that exceeds the available width"
        label = ElidedLabel(text)
        label.resize(140, 30)
        label.show()
        button = ElidingPushButton(text)
        button.resize(160, 34)
        button.show()
        self.app.processEvents()

        self.assertNotEqual(label.display_text(), text)
        self.assertEqual(label.text(), text)
        self.assertEqual(label.toolTip(), text)
        self.assertNotEqual(button.display_text(), text)
        self.assertEqual(button.full_text, text)
        self.assertEqual(button.toolTip(), text)

        composer = AgentComposer()
        composer.resize(520, 220)
        composer.set_context_chips((text,))
        composer.show()
        self.app.processEvents()
        context_button = composer._context_buttons[0]
        self.assertGreaterEqual(context_button.width(), 96)
        self.assertNotEqual(context_button.text(), "")
        self.assertEqual(context_button.full_text, text)

    def test_composer_has_one_intent_editor_three_suggestions_and_two_selectors(self):
        composer = AgentComposer()

        self.assertEqual(len(composer.suggestion_buttons), 3)
        self.assertEqual(
            [button.text() for button in composer.suggestion_buttons],
            ["做新功能", "修正問題", "從會議建立任務"],
        )
        self.assertEqual(composer.editor.placeholderText(), "Ask our AI agent…")
        self.assertTrue(composer.editor.accessibleName())
        self.assertTrue(composer.send_button.accessibleName())
        self.assertTrue(composer.send_button.toolTip())
        self.assertTrue(composer.operating_mode.isVisibleTo(composer))
        self.assertTrue(composer.model_profile.isVisibleTo(composer))
        self.assertFalse(hasattr(composer, "workflow_combo"))
        self.assertFalse(hasattr(composer, "validation_profile"))

        composer.set_blocked_reason("先選擇 Repository")
        self.assertEqual(composer.blocked_reason.text(), "先選擇 Repository")
        composer.set_running(True)
        self.assertTrue(composer.stop_button.isVisibleTo(composer))
        self.assertTrue(composer.follow_up_behavior.isVisibleTo(composer))

    def test_context_chip_can_preview_and_remove_with_accessible_controls(self):
        composer = AgentComposer()
        previewed = []
        removed = []
        composer.context_preview_requested.connect(previewed.append)
        composer.context_remove_requested.connect(removed.append)
        composer.set_context_chips(("檔案：README.md",))

        composer._context_buttons[0].click()
        remove = composer._context_widgets[0].findChild(QToolButton)
        self.assertIsNotNone(remove)
        remove.click()

        self.assertEqual(previewed, [0])
        self.assertEqual(removed, [0])
        self.assertTrue(remove.accessibleName())
        self.assertTrue(remove.toolTip())

    def test_inspector_is_dynamic_and_settings_use_category_navigation(self):
        inspector = ArtifactInspector()
        page = QStackedWidget()
        inspector.register_page("diff", "Diff", page)

        self.assertTrue(inspector.isHidden())
        self.assertEqual(inspector.count(), 0)
        inspector.show_artifact("diff")
        self.assertEqual(inspector.available_artifacts(), ("diff",))

        settings = AgentSettingsDialog()
        self.assertIsInstance(settings.categories, QListWidget)
        self.assertIsInstance(settings.pages, QStackedWidget)
        self.assertEqual(settings.pages.count(), 8)
        self.assertTrue(settings.categories.item(7).isHidden())
        settings.advanced_toggle.setChecked(True)
        self.assertFalse(settings.categories.item(7).isHidden())

    def test_icon_only_controls_expose_accessible_names_and_tooltips(self):
        composer = AgentComposer()
        controls = (
            composer.context_button,
            composer.send_button,
            composer.stop_button,
        )
        for control in controls:
            with self.subTest(control=control.objectName()):
                self.assertTrue(control.accessibleName())
                self.assertTrue(control.toolTip())
        self.assertEqual(
            composer.editor.focusPolicy(),
            Qt.FocusPolicy.StrongFocus,
        )

    def test_evidence_picker_defaults_to_eligible_confirmed_supported_items(self):
        model = EvidenceCandidateModel()
        model.set_candidates(
            (
                {
                    "claim_id": "eligible",
                    "text": "Ship the verified action",
                    "review_status": "confirmed",
                    "support_status": "supported",
                    "eligible": True,
                },
                {
                    "claim_id": "stale",
                    "text": "Old action",
                    "review_status": "confirmed",
                    "support_status": "supported",
                    "eligible": False,
                },
            )
        )

        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(
            model.data(model.index(0, 0), Qt.ItemDataRole.UserRole),
            "eligible",
        )
        model.set_show_all(True)
        self.assertEqual(model.rowCount(), 2)
        model.set_query("Old")
        self.assertEqual(model.rowCount(), 1)

    def test_evidence_picker_focuses_search_when_opened(self):
        picker = EvidenceContextPicker(
            (
                {
                    "claim_id": "eligible",
                    "text": "Ship the verified action",
                    "review_status": "confirmed",
                    "support_status": "supported",
                    "eligible": True,
                },
            )
        )
        picker.show()
        self.app.processEvents()
        self.app.processEvents()

        self.assertIs(picker.focusWidget(), picker.search)
        picker.close()


if __name__ == "__main__":
    unittest.main()
