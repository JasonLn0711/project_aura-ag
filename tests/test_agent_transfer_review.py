import os
import unittest
from dataclasses import replace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (
    QApplication,
    QAbstractButton,
    QDialog,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QToolButton,
)

from aura.agent.policy import (
    DataClass,
    DataTransferGuard,
    build_transfer_preview,
)
from aura.ui.agent_workspace.transfer_review import (
    TransferReviewInput,
    TransferReviewDialog,
    build_transfer_review_view_model,
)


class TransferReviewViewModelTests(unittest.TestCase):
    def make_input(self, preview, **changes):
        values = {
            "preview": preview,
            "task_character_count": 19,
            "evidence_scope": None,
            "evidence_segment_count": 0,
            "evidence_character_count": 0,
            "attached_reference_kinds": (),
            "provider_id": "codex",
            "model_label": "gpt-5.6-sol / high",
            "purpose": "覆核 Repository",
            "is_local_demo": False,
        }
        values.update(changes)
        return TransferReviewInput(**values)

    def test_internal_classification_is_presented_in_taiwan_zh_tw(self):
        preview = build_transfer_preview(
            "Review the release.",
            source_id="user-task",
            classification="internal_source",
        )

        model = build_transfer_review_view_model(
            self.make_input(preview)
        )

        details = {item.label: item.value for item in model.technical_details}
        self.assertEqual(details["資料類型"], "內部工作內容")
        self.assertNotIn("internal_source", model.default_visible_text)

    def test_no_finding_copy_states_rule_limit_without_safety_overclaim(self):
        preview = build_transfer_preview(
            "Review the release.",
            source_id="user-task",
            classification="internal_source",
        )

        model = build_transfer_review_view_model(self.make_input(preview))

        self.assertEqual(
            model.protection_summary,
            "未發現系統目前能辨識的敏感資訊。\n仍請快速查看下方內容。",
        )
        self.assertNotIn("安全", model.protection_summary)
        self.assertNotIn("沒有敏感資訊", model.protection_summary)

    def test_repeated_detections_are_aggregated_with_plain_language_labels(self):
        preview = build_transfer_preview(
            "Email a@example.invalid or b@example.invalid; call 0912-345-678.",
            source_id="user-task",
            classification="personal_data",
        )

        model = build_transfer_review_view_model(self.make_input(preview))

        self.assertEqual(
            [(finding.label, finding.count) for finding in model.findings],
            [("電子郵件", 2), ("電話號碼", 1)],
        )
        self.assertEqual(
            model.protection_summary,
            "已自動隱藏 3 處敏感資訊：\n"
            "• 電子郵件 2 處\n"
            "• 電話號碼 1 處\n\n"
            "請確認下方內容仍然足以完成這次工作。",
        )

    def test_sending_items_describe_task_evidence_and_reference_counts(self):
        preview = build_transfer_preview(
            "Review the selected context.",
            source_id="meeting-1:action-1",
            classification="personal_data",
        )
        model = build_transfer_review_view_model(
            self.make_input(
                preview,
                task_character_count=19,
                evidence_scope="selected_segments",
                evidence_segment_count=3,
                evidence_character_count=48,
                attached_reference_kinds=(
                    "repository",
                    "repository",
                    "artifact",
                ),
            )
        )

        self.assertEqual(
            [item.label for item in model.sending_items],
            [
                "你的任務說明（19 字）",
                "已選取的會議內容（3 段）",
                "附加的 Repository 參照（2 個）",
                "附加的既有成果（1 個）",
            ],
        )

    def test_task_only_and_full_transcript_sending_items_use_plain_counts(self):
        preview = build_transfer_preview(
            "Review the release.",
            source_id="user-task",
            classification="internal_source",
        )
        task_only = build_transfer_review_view_model(
            self.make_input(preview)
        )
        full_transcript = build_transfer_review_view_model(
            self.make_input(
                preview,
                evidence_scope="full_transcript",
                evidence_segment_count=8,
                evidence_character_count=4321,
            )
        )

        self.assertEqual(
            [item.label for item in task_only.sending_items],
            ["你的任務說明（19 字）"],
        )
        self.assertEqual(
            [item.label for item in full_transcript.sending_items],
            [
                "你的任務說明（19 字）",
                "完整逐字稿（4321 字）",
            ],
        )

    def test_blocked_credential_has_plain_next_step_and_cannot_confirm(self):
        preview = build_transfer_preview(
            "Use sk-abcdefghijklmnopqrstuv for the request.",
            source_id="user-task",
            classification="internal_source",
        )

        model = build_transfer_review_view_model(self.make_input(preview))

        self.assertEqual(model.blocked_heading, "這些內容目前無法傳送")
        self.assertEqual(
            model.blocked_message,
            "偵測到疑似密碼、金鑰、原始錄音，或其他不允許傳送的內容。\n"
            "請返回移除後再試一次。",
        )
        self.assertFalse(model.can_confirm)
        self.assertNotIn("sk-abcdefghijklmnopqrstuv", model.exact_text)
        self.assertIn("[REDACTED_CREDENTIAL]", model.exact_text)

    def test_technical_details_and_local_items_keep_metadata_out_of_default_copy(self):
        preview = build_transfer_preview(
            "Contact a@example.invalid.",
            source_id="meeting-1:action-3",
            classification="personal_data",
        )

        model = build_transfer_review_view_model(self.make_input(preview))
        details = {item.label: item.value for item in model.technical_details}

        self.assertEqual(
            model.local_only_items,
            ("原始錄音", "未選取的會議內容", "AURA 原始紀錄"),
        )
        self.assertEqual(details["AI 服務"], "Codex")
        self.assertEqual(details["來源識別碼"], "meeting-1:action-3")
        self.assertEqual(details["資料類型"], "可能含個人資料")
        self.assertEqual(details["使用模型"], "gpt-5.6-sol / high")
        self.assertEqual(details["用途"], "覆核 Repository")
        self.assertEqual(details["已隱藏內容"], "1 處")
        for hidden_term in (
            "meeting-1:action-3",
            "gpt-5.6-sol",
            "bytes",
            "personal_data",
        ):
            self.assertNotIn(hidden_term, model.default_visible_text)

    def test_unknown_classification_uses_fallback_and_keeps_raw_code_advanced(self):
        preview = replace(
            build_transfer_preview(
                "Review the release.",
                source_id="user-task",
                classification="unknown",
            ),
            classification="new_enum_value",
        )

        model = build_transfer_review_view_model(self.make_input(preview))
        details = {item.label: item.value for item in model.technical_details}

        self.assertEqual(details["資料類型"], "尚未分類")
        self.assertEqual(details["內部代碼"], "new_enum_value")
        self.assertNotIn("new_enum_value", model.default_visible_text)

    def test_long_full_transcript_remains_exact_and_requires_extra_confirmation(self):
        transcript = "完整逐字稿內容。" * 400
        preview = DataTransferGuard().preview_text(
            transcript,
            source_id="meeting-1:__full_transcript__",
            classification=DataClass.PERSONAL_DATA,
            content_kind="full_transcript",
            whole_document_confirmed=False,
        )

        model = build_transfer_review_view_model(
            self.make_input(
                preview,
                evidence_scope="full_transcript",
                evidence_segment_count=20,
                evidence_character_count=len(transcript),
            )
        )

        self.assertEqual(model.exact_text, transcript)
        self.assertTrue(model.exact_text_is_long)
        self.assertTrue(model.requires_full_document_confirmation)
        self.assertTrue(
            model.can_confirm_after_full_document_confirmation
        )
        self.assertEqual(
            model.full_document_confirmation_text,
            "我已查看完整逐字稿，確認要把整份內容交給 AI 處理。",
        )
        self.assertFalse(model.can_confirm)

    def test_demo_view_model_is_explicitly_local_only_without_external_approval(self):
        preview = build_transfer_preview(
            "Replay the deterministic demo.",
            source_id="user-task",
            classification="internal_source",
        )

        model = build_transfer_review_view_model(
            self.make_input(
                preview,
                provider_id="demo",
                model_label="本機固定情境",
                is_local_demo=True,
            )
        )
        details = {item.label: item.value for item in model.technical_details}

        self.assertTrue(model.is_local_demo)
        self.assertEqual(model.title, "查看模擬內容")
        self.assertEqual(
            model.local_demo_notice,
            "Demo 模式：內容只在本機模擬，不會傳到外部 AI。",
        )
        self.assertEqual(details["AI 服務"], "本機 Demo")
        self.assertFalse(model.can_confirm)


class TransferReviewDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_model(self):
        preview = build_transfer_preview(
            "Review the release.",
            source_id="user-task",
            classification="internal_source",
        )
        return build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=19,
                evidence_scope=None,
                evidence_segment_count=0,
                evidence_character_count=0,
                attached_reference_kinds=(),
                provider_id="codex",
                model_label="gpt-5.6-sol / high",
                purpose="覆核 Repository",
                is_local_demo=False,
            )
        )

    def test_dialog_exposes_four_decision_sections_and_collapsed_details(self):
        dialog = TransferReviewDialog(self.make_model())

        self.assertEqual(dialog.windowTitle(), "確認要傳給 AI 的內容")
        labels = {label.text() for label in dialog.findChildren(QLabel)}
        self.assertTrue(
            {
                "這次會傳送",
                "敏感資訊檢查",
                "不會一起傳送",
                "AI 會看到的內容",
            }.issubset(labels)
        )
        button_text = {
            button.text() for button in dialog.findChildren(QAbstractButton)
        }
        self.assertIn("返回修改", button_text)
        self.assertIn("確認並繼續", button_text)
        technical = next(
            button
            for button in dialog.findChildren(QToolButton)
            if button.text() == "技術詳細資料"
        )
        self.assertFalse(technical.isChecked())
        self.assertTrue(dialog.technical_panel.isHidden())
        dialog.close()

    def test_default_visible_layer_omits_engineering_and_repository_permission_copy(self):
        dialog = TransferReviewDialog(self.make_model())
        dialog.show()
        self.app.processEvents()
        visible_text = "\n".join(
            (
                *(
                    label.text()
                    for label in dialog.findChildren(QLabel)
                    if label.isVisibleTo(dialog)
                ),
                *(
                    view.toPlainText()
                    for view in dialog.findChildren(QPlainTextEdit)
                    if view.isVisibleTo(dialog)
                ),
            )
        )

        for forbidden in (
            "資料邊界",
            "canonical artifacts",
            "fixture",
            "internal_source",
            "PII",
            "UTF-8 位元組",
            "確定性規則",
            "Sandbox",
            "worktree",
            "commit",
            "push",
            "PR",
        ):
            self.assertNotIn(forbidden, visible_text)
        dialog.close()

    def test_full_transcript_checkbox_is_accessible_and_controls_confirmation(self):
        transcript = "完整逐字稿內容。" * 30
        preview = DataTransferGuard().preview_text(
            transcript,
            source_id="meeting-1:__full_transcript__",
            classification=DataClass.PERSONAL_DATA,
            content_kind="full_transcript",
        )
        model = build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=12,
                evidence_scope="full_transcript",
                evidence_segment_count=3,
                evidence_character_count=len(transcript),
                attached_reference_kinds=(),
                provider_id="codex",
                model_label="gpt-5.6-sol / high",
                purpose="整理完整逐字稿",
                is_local_demo=False,
            )
        )
        dialog = TransferReviewDialog(model)

        self.assertEqual(
            dialog.full_document_checkbox.accessibleName(),
            "確認傳送完整逐字稿",
        )
        self.assertFalse(dialog.confirm_button.isEnabled())
        dialog.full_document_checkbox.setChecked(True)
        self.assertTrue(dialog.confirm_button.isEnabled())
        dialog.full_document_checkbox.setChecked(False)
        self.assertFalse(dialog.confirm_button.isEnabled())
        dialog.close()

    def test_blocked_dialog_has_no_confirm_path(self):
        preview = build_transfer_preview(
            "Use sk-abcdefghijklmnopqrstuv for the request.",
            source_id="user-task",
            classification="internal_source",
        )
        model = build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=44,
                evidence_scope=None,
                evidence_segment_count=0,
                evidence_character_count=0,
                attached_reference_kinds=(),
                provider_id="codex",
                model_label="gpt-5.6-sol / high",
                purpose="覆核 Repository",
                is_local_demo=False,
            )
        )
        dialog = TransferReviewDialog(model)

        self.assertTrue(dialog.confirm_button.isHidden())
        self.assertFalse(dialog.confirm_button.isEnabled())
        self.assertTrue(
            any(
                "請返回移除後再試一次。" in label.text()
                for label in dialog.findChildren(QLabel)
            )
        )
        dialog.close()

    def test_cancel_is_default_focus_and_escape_rejects(self):
        dialog = TransferReviewDialog(self.make_model())
        dialog.show()
        self.app.processEvents()

        self.assertTrue(dialog.cancel_button.isDefault())
        self.assertIs(dialog.focusWidget(), dialog.cancel_button)
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        self.app.processEvents()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)

    def test_long_exact_content_expands_to_the_same_complete_redacted_text(self):
        original = ("Contact a@example.invalid about the release. " * 100).strip()
        preview = build_transfer_preview(
            original,
            source_id="meeting-1:action-3",
            classification="personal_data",
        )
        model = build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=34,
                evidence_scope="selected_segments",
                evidence_segment_count=1,
                evidence_character_count=len(original),
                attached_reference_kinds=(),
                provider_id="codex",
                model_label="gpt-5.6-sol / high",
                purpose="覆核 Repository",
                is_local_demo=False,
            )
        )
        dialog = TransferReviewDialog(model)

        self.assertTrue(model.exact_text_is_long)
        self.assertNotEqual(
            dialog.exact_text_view.toPlainText(),
            model.exact_text,
        )
        self.assertEqual(
            dialog.content_button.accessibleName(),
            "查看完整內容",
        )
        dialog.content_button.click()
        self.assertEqual(
            dialog.exact_text_view.toPlainText(),
            model.exact_text,
        )
        self.assertNotIn("a@example.invalid", model.exact_text)
        dialog.close()

    def test_demo_inspection_has_close_only_and_no_external_confirm_action(self):
        preview = build_transfer_preview(
            "Replay the deterministic demo.",
            source_id="user-task",
            classification="internal_source",
        )
        model = build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=30,
                evidence_scope=None,
                evidence_segment_count=0,
                evidence_character_count=0,
                attached_reference_kinds=(),
                provider_id="demo",
                model_label="本機固定情境",
                purpose="本機示範",
                is_local_demo=True,
            )
        )
        dialog = TransferReviewDialog(model)
        button_text = {
            button.text()
            for button in dialog.findChildren(QAbstractButton)
            if not button.isHidden()
        }

        self.assertIn("關閉", button_text)
        self.assertNotIn("確認並繼續", button_text)
        self.assertFalse(dialog.isModal())
        dialog.close()

    def test_full_transcript_controls_remain_reachable_at_1024_by_768(self):
        transcript = "完整逐字稿內容。" * 500
        preview = DataTransferGuard().preview_text(
            transcript,
            source_id="meeting-1:__full_transcript__",
            classification=DataClass.PERSONAL_DATA,
            content_kind="full_transcript",
        )
        model = build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=18,
                evidence_scope="full_transcript",
                evidence_segment_count=12,
                evidence_character_count=len(transcript),
                attached_reference_kinds=(),
                provider_id="codex",
                model_label="gpt-5.6-sol / high",
                purpose="整理完整逐字稿",
                is_local_demo=False,
            )
        )
        dialog = TransferReviewDialog(model)
        dialog.resize(760, 700)
        dialog.show()
        self.app.processEvents()

        self.assertLessEqual(dialog.width(), 1024)
        self.assertLessEqual(dialog.height(), 768)
        self.assertTrue(dialog.cancel_button.isVisibleTo(dialog))
        self.assertTrue(dialog.confirm_button.isVisibleTo(dialog))
        scroll = dialog.findChild(QScrollArea, "transferReviewScroll")
        self.assertIsNotNone(scroll)
        scroll.ensureWidgetVisible(dialog.full_document_checkbox)
        self.app.processEvents()
        self.assertTrue(
            dialog.full_document_checkbox.isVisibleTo(scroll.viewport())
        )
        dialog.close()

    def test_full_transcript_tab_order_uses_real_keyboard_events(self):
        transcript = "完整逐字稿內容。" * 500
        preview = DataTransferGuard().preview_text(
            transcript,
            source_id="meeting-1:__full_transcript__",
            classification=DataClass.PERSONAL_DATA,
            content_kind="full_transcript",
        )
        model = build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=18,
                evidence_scope="full_transcript",
                evidence_segment_count=12,
                evidence_character_count=len(transcript),
                attached_reference_kinds=(),
                provider_id="codex",
                model_label="gpt-5.6-sol / high",
                purpose="整理完整逐字稿",
                is_local_demo=False,
            )
        )
        dialog = TransferReviewDialog(model)
        dialog.show()
        self.app.processEvents()

        expected_chain = (
            dialog.exact_text_view,
            dialog.content_button,
            dialog.technical_button,
            dialog.full_document_checkbox,
            dialog.cancel_button,
        )
        expected_chain[0].setFocus()
        for expected in expected_chain[1:]:
            QTest.keyClick(dialog.focusWidget(), Qt.Key.Key_Tab)
            self.app.processEvents()
            self.assertIs(dialog.focusWidget(), expected)

        dialog.full_document_checkbox.setChecked(True)
        dialog.cancel_button.setFocus()
        QTest.keyClick(dialog.cancel_button, Qt.Key.Key_Tab)
        self.app.processEvents()
        self.assertIs(dialog.focusWidget(), dialog.confirm_button)
        dialog.close()

    def test_all_interactive_review_controls_have_accessible_names(self):
        dialog = TransferReviewDialog(self.make_model())

        controls = (
            dialog.exact_text_view,
            dialog.technical_button,
            dialog.cancel_button,
            dialog.confirm_button,
        )
        for control in controls:
            self.assertTrue(control.accessibleName(), control.objectName())
        dialog.close()


if __name__ == "__main__":
    unittest.main()
