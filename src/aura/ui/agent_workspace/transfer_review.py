from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from aura.agent.policy import TransferPreview


_CLASSIFICATION_LABELS = {
    "public": "公開資料",
    "internal": "內部資料",
    "internal_source": "內部工作內容",
    "confidential": "機密資料",
    "personal_data": "可能含個人資料",
    "customer_confidential": "客戶機密資料",
    "credential": "登入資訊或憑證",
    "raw_audio": "原始錄音",
    "local_audit": "本機稽核紀錄",
    "restricted": "限制傳送",
    "unknown": "尚未分類",
}

_DETECTION_LABELS = {
    "credential": "疑似密碼或金鑰",
    "email": "電子郵件",
    "taiwan_phone": "電話號碼",
    "taiwan_national_id": "身分證字號",
}

_INLINE_EXACT_TEXT_LIMIT = 2_000


@dataclass(frozen=True)
class TechnicalDetailView:
    label: str
    value: str


@dataclass(frozen=True)
class TransferItemView:
    label: str
    detail: str | None = None


@dataclass(frozen=True)
class SensitiveFindingView:
    label: str
    count: int
    blocked: bool = False


@dataclass(frozen=True)
class TransferReviewInput:
    preview: TransferPreview
    task_character_count: int
    evidence_scope: str | None
    evidence_segment_count: int
    evidence_character_count: int
    attached_reference_kinds: tuple[str, ...]
    provider_id: str
    model_label: str
    purpose: str
    is_local_demo: bool


@dataclass(frozen=True)
class TransferReviewViewModel:
    title: str
    description: str
    sending_heading: str
    protection_heading: str
    local_only_heading: str
    exact_content_heading: str
    technical_details_label: str
    cancel_label: str
    confirm_label: str
    is_local_demo: bool
    local_demo_notice: str | None
    sending_items: tuple[TransferItemView, ...]
    protection_summary: str
    findings: tuple[SensitiveFindingView, ...]
    local_only_items: tuple[str, ...]
    exact_text: str
    exact_text_is_long: bool
    can_confirm: bool
    can_confirm_after_full_document_confirmation: bool
    blocked_heading: str | None
    blocked_message: str | None
    requires_full_document_confirmation: bool
    full_document_confirmation_text: str
    technical_details: tuple[TechnicalDetailView, ...]
    default_visible_text: str


def build_transfer_review_view_model(
    context: TransferReviewInput,
) -> TransferReviewViewModel:
    classification = _CLASSIFICATION_LABELS.get(
        context.preview.classification,
        "尚未分類",
    )
    counts = Counter(context.preview.detections)
    findings = tuple(
        SensitiveFindingView(
            label=_DETECTION_LABELS.get(value, "其他受保護資訊"),
            count=count,
            blocked=value in context.preview.blocked_categories,
        )
        for value, count in counts.items()
    )
    blocked = bool(context.preview.blocked_categories) or (
        not context.preview.allowed_to_transfer
        and not context.preview.whole_document_confirmation_required
    )
    blocked_heading = "這些內容目前無法傳送" if blocked else None
    blocked_message = (
        "偵測到疑似密碼、金鑰、原始錄音，或其他不允許傳送的內容。\n"
        "請返回移除後再試一次。"
        if blocked
        else None
    )
    if blocked:
        protection_summary = blocked_message
    elif findings:
        finding_lines = "\n".join(
            f"• {finding.label} {finding.count} 處"
            for finding in findings
        )
        protection_summary = (
            f"已自動隱藏 {context.preview.redaction_count} 處敏感資訊：\n"
            f"{finding_lines}\n\n"
            "請確認下方內容仍然足以完成這次工作。"
        )
    else:
        protection_summary = (
            "未發現系統目前能辨識的敏感資訊。\n"
            "仍請快速查看下方內容。"
        )
    sending_items: list[TransferItemView] = []
    if context.task_character_count:
        sending_items.append(
            TransferItemView(
                f"你的任務說明（{context.task_character_count} 字）"
            )
        )
    if context.evidence_scope == "full_transcript":
        sending_items.append(
            TransferItemView(
                f"完整逐字稿（{context.evidence_character_count} 字）"
            )
        )
    elif context.evidence_scope:
        sending_items.append(
            TransferItemView(
                f"已選取的會議內容（{context.evidence_segment_count} 段）"
            )
        )
    reference_counts = Counter(context.attached_reference_kinds)
    if reference_counts["repository"]:
        sending_items.append(
            TransferItemView(
                "附加的 Repository 參照"
                f"（{reference_counts['repository']} 個）"
            )
        )
    if reference_counts["artifact"]:
        sending_items.append(
            TransferItemView(
                f"附加的既有成果（{reference_counts['artifact']} 個）"
            )
        )
    visible_items = "\n".join(item.label for item in sending_items)
    provider_label = (
        "本機 Demo"
        if context.is_local_demo or context.provider_id == "demo"
        else "Codex"
    )
    requires_full_document_confirmation = (
        context.evidence_scope == "full_transcript"
    )
    technical_details = [
        TechnicalDetailView("AI 服務", provider_label),
        TechnicalDetailView("資料類型", classification),
    ]
    if context.preview.classification not in _CLASSIFICATION_LABELS:
        technical_details.append(
            TechnicalDetailView(
                "內部代碼",
                context.preview.classification,
            )
        )
    unknown_detection_codes = tuple(
        dict.fromkeys(
            value
            for value in context.preview.detections
            if value not in _DETECTION_LABELS
        )
    )
    if unknown_detection_codes:
        technical_details.append(
            TechnicalDetailView(
                "其他內部代碼",
                ", ".join(unknown_detection_codes),
            )
        )
    technical_details.extend(
        (
            TechnicalDetailView("來源識別碼", context.preview.source_id),
            TechnicalDetailView(
                "文字長度",
                f"{context.preview.transmitted_length} 字",
            ),
            TechnicalDetailView(
                "傳送大小",
                f"{context.preview.estimated_utf8_bytes} bytes",
            ),
            TechnicalDetailView("使用模型", context.model_label),
            TechnicalDetailView(
                "已隱藏內容",
                f"{context.preview.redaction_count} 處",
            ),
            TechnicalDetailView("用途", context.purpose),
        )
    )
    return TransferReviewViewModel(
        title=(
            "查看模擬內容"
            if context.is_local_demo
            else "確認要傳給 AI 的內容"
        ),
        description=(
            "你可以查看本機模擬會使用的任務內容。"
            "這次執行不會傳送到外部 AI。"
            if context.is_local_demo
            else (
                "請快速確認這次會交給 AI 的文字與附件。"
                "未列出的會議、錄音和 AURA 原始紀錄不會一起送出。"
            )
        ),
        sending_heading=(
            "這次模擬會使用"
            if context.is_local_demo
            else "這次會傳送"
        ),
        protection_heading="敏感資訊檢查",
        local_only_heading="不會一起傳送",
        exact_content_heading=(
            "本機模擬會使用的內容"
            if context.is_local_demo
            else "AI 會看到的內容"
        ),
        technical_details_label="技術詳細資料",
        cancel_label="返回修改",
        confirm_label="確認並繼續",
        is_local_demo=context.is_local_demo,
        local_demo_notice=(
            "Demo 模式：內容只在本機模擬，不會傳到外部 AI。"
            if context.is_local_demo
            else None
        ),
        sending_items=tuple(sending_items),
        protection_summary=protection_summary,
        findings=findings,
        local_only_items=(
            "原始錄音",
            "未選取的會議內容",
            "AURA 原始紀錄",
        ),
        exact_text=context.preview.transmitted_text,
        exact_text_is_long=(
            len(context.preview.transmitted_text) > _INLINE_EXACT_TEXT_LIMIT
        ),
        can_confirm=(
            context.preview.allowed_to_transfer
            and not context.is_local_demo
            and not requires_full_document_confirmation
        ),
        can_confirm_after_full_document_confirmation=(
            not context.is_local_demo
            and requires_full_document_confirmation
            and context.preview.whole_document_confirmation_required
            and not blocked
        ),
        blocked_heading=blocked_heading,
        blocked_message=blocked_message,
        requires_full_document_confirmation=(
            requires_full_document_confirmation
        ),
        full_document_confirmation_text=(
            "我已查看完整逐字稿，確認要把整份內容交給 AI 處理。"
        ),
        technical_details=tuple(technical_details),
        default_visible_text=(
            f"{'查看模擬內容' if context.is_local_demo else '確認要傳給 AI 的內容'}\n"
            f"{'Demo 模式：內容只在本機模擬，不會傳到外部 AI。' if context.is_local_demo else ''}\n"
            f"{visible_items}\n"
            f"{blocked_heading or ''}\n"
            f"{protection_summary}\n"
            f"{context.preview.transmitted_text}"
        ),
    )


class TransferReviewDialog(QDialog):
    """Structured native review of one immutable transfer presentation."""

    def __init__(
        self,
        model: TransferReviewViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.model = model
        self.setObjectName("transferReviewDialog")
        self.setProperty("agentWorkspaceDialog", True)
        self.setAccessibleName(model.title)
        self.setWindowTitle(model.title)
        self.setModal(not model.is_local_demo)
        self.resize(760, 700)
        self.setMinimumSize(640, 560)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        heading = QLabel(self.model.title)
        heading.setObjectName("transferReviewTitle")
        heading.setAccessibleName(self.model.title)
        root.addWidget(heading)

        description = QLabel(self.model.description)
        description.setObjectName("transferReviewDescription")
        description.setWordWrap(True)
        root.addWidget(description)

        if self.model.local_demo_notice:
            notice = QLabel(self.model.local_demo_notice)
            notice.setObjectName("transferReviewDemoNotice")
            notice.setAccessibleName(self.model.local_demo_notice)
            notice.setWordWrap(True)
            root.addWidget(notice)

        scroll = QScrollArea()
        scroll.setObjectName("transferReviewScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 8, 0)
        body_layout.setSpacing(12)

        sending = self._section(
            self.model.sending_heading,
            tuple(f"✓ {item.label}" for item in self.model.sending_items),
        )
        body_layout.addWidget(sending)

        protection_lines = tuple(
            value
            for value in (
                self.model.blocked_heading,
                self.model.protection_summary,
            )
            if value
        )
        protection = self._section(
            self.model.protection_heading,
            protection_lines,
        )
        protection.setProperty(
            "blocked",
            bool(self.model.blocked_message),
        )
        body_layout.addWidget(protection)

        local_only = self._section(
            self.model.local_only_heading,
            tuple(f"• {item}" for item in self.model.local_only_items),
        )
        body_layout.addWidget(local_only)

        exact_section = QFrame()
        exact_section.setObjectName("transferReviewSection")
        exact_layout = QVBoxLayout(exact_section)
        exact_layout.setContentsMargins(0, 0, 0, 0)
        exact_layout.setSpacing(6)
        exact_heading = self._section_heading(
            self.model.exact_content_heading
        )
        exact_layout.addWidget(exact_heading)
        initial_exact_text = (
            self.model.exact_text[:_INLINE_EXACT_TEXT_LIMIT]
            + "\n\n…完整內容可展開查看"
            if self.model.exact_text_is_long
            else self.model.exact_text
        )
        self.exact_text_view = QPlainTextEdit(initial_exact_text)
        self.exact_text_view.setObjectName("transferReviewExactText")
        self.exact_text_view.setAccessibleName(
            "本機模擬會使用的完整內容"
            if self.model.is_local_demo
            else "AI 會看到的完整內容"
        )
        self.exact_text_view.setReadOnly(True)
        self.exact_text_view.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth
        )
        self.exact_text_view.setMinimumHeight(130)
        exact_layout.addWidget(self.exact_text_view)
        self.content_button = QToolButton()
        self.content_button.setObjectName("transferReviewContentDisclosure")
        self.content_button.setText("查看完整內容")
        self.content_button.setAccessibleName("查看完整內容")
        self.content_button.setCheckable(True)
        self.content_button.setVisible(self.model.exact_text_is_long)
        self.content_button.toggled.connect(
            self._set_complete_content_visible
        )
        exact_layout.addWidget(
            self.content_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        body_layout.addWidget(exact_section)

        self.technical_button = QToolButton()
        self.technical_button.setObjectName("transferReviewDisclosure")
        self.technical_button.setText(self.model.technical_details_label)
        self.technical_button.setAccessibleName(
            self.model.technical_details_label
        )
        self.technical_button.setCheckable(True)
        self.technical_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.technical_button.setArrowType(Qt.ArrowType.RightArrow)
        body_layout.addWidget(
            self.technical_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        self.technical_panel = QFrame()
        self.technical_panel.setObjectName("transferReviewTechnicalPanel")
        technical_layout = QVBoxLayout(self.technical_panel)
        technical_layout.setContentsMargins(12, 4, 0, 4)
        technical_layout.setSpacing(4)
        for detail in self.model.technical_details:
            value = QLabel(f"{detail.label}：{detail.value}")
            value.setWordWrap(True)
            technical_layout.addWidget(value)
        self.technical_panel.hide()
        body_layout.addWidget(self.technical_panel)
        self.technical_button.toggled.connect(
            self._set_technical_details_visible
        )

        self.full_document_checkbox = QCheckBox(
            self.model.full_document_confirmation_text
        )
        self.full_document_checkbox.setAccessibleName(
            "確認傳送完整逐字稿"
        )
        self.full_document_checkbox.setVisible(
            self.model.requires_full_document_confirmation
        )
        body_layout.addWidget(self.full_document_checkbox)
        body_layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        buttons = QDialogButtonBox()
        self.confirm_button = buttons.addButton(
            self.model.confirm_label,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self.confirm_button.setAccessibleName(self.model.confirm_label)
        self.confirm_button.setObjectName("transferReviewConfirm")
        self.cancel_button = buttons.addButton(
            "關閉" if self.model.is_local_demo else self.model.cancel_label,
            QDialogButtonBox.ButtonRole.RejectRole,
        )
        self.cancel_button.setAccessibleName(
            "關閉" if self.model.is_local_demo else self.model.cancel_label
        )
        self.cancel_button.setObjectName("transferReviewCancel")
        self.cancel_button.setDefault(True)
        self.cancel_button.setAutoDefault(True)
        self.confirm_button.setEnabled(self.model.can_confirm)
        if self.model.requires_full_document_confirmation:
            self.full_document_checkbox.toggled.connect(
                lambda checked: self.confirm_button.setEnabled(
                    checked
                    and self.model.can_confirm_after_full_document_confirmation
                )
            )
        if self.model.blocked_message:
            self.confirm_button.hide()
        if self.model.is_local_demo:
            self.confirm_button.hide()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        if self.model.exact_text_is_long:
            QWidget.setTabOrder(
                self.exact_text_view,
                self.content_button,
            )
            QWidget.setTabOrder(
                self.content_button,
                self.technical_button,
            )
        else:
            QWidget.setTabOrder(
                self.exact_text_view,
                self.technical_button,
            )
        if self.model.requires_full_document_confirmation:
            QWidget.setTabOrder(
                self.technical_button,
                self.full_document_checkbox,
            )
            QWidget.setTabOrder(
                self.full_document_checkbox,
                self.cancel_button,
            )
        else:
            QWidget.setTabOrder(
                self.technical_button,
                self.cancel_button,
            )
        QWidget.setTabOrder(self.cancel_button, self.confirm_button)
        self.cancel_button.setFocus()

    @staticmethod
    def _section_heading(text: str) -> QLabel:
        heading = QLabel(text)
        heading.setObjectName("transferReviewSectionHeading")
        heading.setAccessibleName(text)
        return heading

    def _section(
        self,
        heading_text: str,
        lines: tuple[str, ...],
    ) -> QFrame:
        section = QFrame()
        section.setObjectName("transferReviewSection")
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._section_heading(heading_text))
        for line in lines:
            label = QLabel(line)
            label.setWordWrap(True)
            layout.addWidget(label)
        return section

    def _set_technical_details_visible(self, visible: bool) -> None:
        self.technical_panel.setVisible(visible)
        self.technical_button.setArrowType(
            Qt.ArrowType.DownArrow
            if visible
            else Qt.ArrowType.RightArrow
        )

    def _set_complete_content_visible(self, visible: bool) -> None:
        self.exact_text_view.setPlainText(
            self.model.exact_text
            if visible
            else (
                self.model.exact_text[:_INLINE_EXACT_TEXT_LIMIT]
                + "\n\n…完整內容可展開查看"
            )
        )
        self.content_button.setText(
            "收合完整內容" if visible else "查看完整內容"
        )
        self.content_button.setAccessibleName(
            "收合完整內容" if visible else "查看完整內容"
        )
