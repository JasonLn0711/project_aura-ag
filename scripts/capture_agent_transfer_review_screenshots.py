#!/usr/bin/env python3
"""Capture the native plain-language AI transfer review states."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QScrollArea, QWidget

from aura.agent.policy import DataClass, DataTransferGuard, build_transfer_preview
from aura.ui.agent_workspace.transfer_review import (
    TransferReviewDialog,
    TransferReviewInput,
    build_transfer_review_view_model,
)


@dataclass(frozen=True)
class CaptureState:
    state_id: str
    name: str
    input: TransferReviewInput
    full_document_checked: bool = False
    technical_details_expanded: bool = False
    canvas_size: tuple[int, int] | None = None


def _payload(task: str, evidence: str | None = None) -> str:
    sections = [
        "Provider: Codex",
        "Model: gpt-5.6-sol / high",
        "Workflow: Review Repository",
        f"Task:\n{task}",
    ]
    if evidence:
        sections.append(f"Selected confirmed action:\n{evidence}")
    return "\n\n".join(sections)


def _input(
    text: str,
    *,
    classification: str = "internal_source",
    evidence_scope: str | None = None,
    evidence_segments: int = 0,
    evidence_characters: int = 0,
    references: tuple[str, ...] = (),
    local_demo: bool = False,
    full_transcript: bool = False,
) -> TransferReviewInput:
    preview = (
        DataTransferGuard().preview_text(
            text,
            source_id="meeting-review:__full_transcript__",
            classification=DataClass.PERSONAL_DATA,
            content_kind="full_transcript",
            whole_document_confirmed=False,
        )
        if full_transcript
        else build_transfer_preview(
            text,
            source_id=(
                "meeting-review:action-3"
                if evidence_scope
                else "user-task"
            ),
            classification=classification,
        )
    )
    return TransferReviewInput(
        preview=preview,
        task_character_count=28,
        evidence_scope=evidence_scope,
        evidence_segment_count=evidence_segments,
        evidence_character_count=evidence_characters,
        attached_reference_kinds=references,
        provider_id="demo" if local_demo else "codex",
        model_label="本機固定情境" if local_demo else "gpt-5.6-sol / high",
        purpose="覆核 Repository",
        is_local_demo=local_demo,
    )


def _states() -> tuple[CaptureState, ...]:
    clean = _payload("請覆核目前 release 的操作文件。")
    evidence = "會議已確認：先補齊操作指南，再執行回歸測試。"
    redacted = _payload(
        "請整理聯絡資訊：reviewer@example.invalid，電話 0912-345-678。"
    )
    blocked = _payload(
        "請使用 sk-abcdefghijklmnopqrstuv 執行測試。"
    )
    transcript = _payload(
        "請整理完整逐字稿。",
        "這是完整逐字稿的合成測試內容。" * 260,
    )
    return (
        CaptureState(
            "01",
            "live-task-only",
            _input(clean),
        ),
        CaptureState(
            "02",
            "live-evidence-backed",
            _input(
                _payload("依據會議行動覆核操作文件。", evidence),
                classification="personal_data",
                evidence_scope="selected_segments",
                evidence_segments=3,
                evidence_characters=len(evidence),
                references=("repository",),
            ),
        ),
        CaptureState(
            "03",
            "live-email-phone-redacted",
            _input(redacted, classification="personal_data"),
        ),
        CaptureState(
            "04",
            "credential-blocked",
            _input(blocked),
        ),
        CaptureState(
            "05",
            "full-transcript-unchecked",
            _input(
                transcript,
                evidence_scope="full_transcript",
                evidence_segments=18,
                evidence_characters=len(transcript),
                full_transcript=True,
            ),
        ),
        CaptureState(
            "06",
            "full-transcript-checked",
            _input(
                transcript,
                evidence_scope="full_transcript",
                evidence_segments=18,
                evidence_characters=len(transcript),
                full_transcript=True,
            ),
            full_document_checked=True,
        ),
        CaptureState(
            "07",
            "technical-details-expanded",
            _input(redacted, classification="personal_data"),
            technical_details_expanded=True,
        ),
        CaptureState(
            "08",
            "demo-local-only",
            _input(
                "Local Demo\n\nTask:\n重播固定的本機示範情境。",
                local_demo=True,
            ),
        ),
        CaptureState(
            "09",
            "viewport-1024x768",
            _input(clean),
            canvas_size=(1024, 768),
        ),
        CaptureState(
            "10",
            "viewport-1440x900",
            _input(redacted, classification="personal_data"),
            canvas_size=(1440, 900),
        ),
    )


def _capture(
    state: CaptureState,
    *,
    output_dir: Path,
    stylesheet: str,
    app: QApplication,
) -> dict[str, object]:
    style_parent = QWidget()
    style_parent.setStyleSheet(stylesheet)
    model = build_transfer_review_view_model(state.input)
    dialog = TransferReviewDialog(model, style_parent)
    dialog.show()
    app.processEvents()
    if state.full_document_checked:
        dialog.full_document_checkbox.setChecked(True)
    if model.requires_full_document_confirmation:
        app.processEvents()
        scroll = dialog.findChild(QScrollArea, "transferReviewScroll")
        scroll.ensureWidgetVisible(dialog.full_document_checkbox)
        app.processEvents()
    if state.technical_details_expanded:
        dialog.technical_button.setChecked(True)
        app.processEvents()
        scroll = dialog.findChild(QScrollArea, "transferReviewScroll")
        scroll.verticalScrollBar().setValue(
            scroll.verticalScrollBar().maximum()
        )
    app.processEvents()

    dialog_pixmap = dialog.grab()
    capture_kind = "dialog"
    if state.canvas_size:
        width, height = state.canvas_size
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#171b20"))
        painter = QPainter(pixmap)
        painter.drawPixmap(
            max(0, (width - dialog_pixmap.width()) // 2),
            max(0, (height - dialog_pixmap.height()) // 2),
            dialog_pixmap,
        )
        painter.end()
        capture_kind = "centered_dialog_canvas"
    else:
        pixmap = dialog_pixmap

    filename = f"{state.state_id}-{state.name}.png"
    path = output_dir / filename
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"Qt could not save screenshot: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "state_id": state.state_id,
        "state": state.name,
        "source": "synthetic-invalid-test-data",
        "capture_kind": capture_kind,
        "png": filename,
        "sha256": digest,
        "image_size": {
            "width": pixmap.width(),
            "height": pixmap.height(),
        },
        "dialog_size": {
            "width": dialog.width(),
            "height": dialog.height(),
        },
        "local_demo": model.is_local_demo,
        "blocked": bool(model.blocked_message),
        "full_document_confirmation_required": (
            model.requires_full_document_confirmation
        ),
        "full_document_checked": state.full_document_checked,
        "technical_details_expanded": state.technical_details_expanded,
        "confirmation_enabled": dialog.confirm_button.isEnabled(),
        "confirmation_visible": not dialog.confirm_button.isHidden(),
    }
    manifest_path = path.with_suffix(".json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    dialog.close()
    style_parent.close()
    app.processEvents()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stylesheet = (
        Path(__file__).resolve().parents[1]
        / "src/aura/ui/agent_workspace/resources/agent_workspace.qss"
    ).read_text(encoding="utf-8")
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    manifests = [
        _capture(
            state,
            output_dir=output_dir,
            stylesheet=stylesheet,
            app=app,
        )
        for state in _states()
    ]
    checksum_lines = [
        f"{manifest['sha256']}  {manifest['png']}"
        for manifest in manifests
    ]
    (output_dir / "checksums.sha256").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
