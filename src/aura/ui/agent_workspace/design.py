from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QWidget


RESOURCE_ROOT = Path(__file__).with_name("resources")


def apply_agent_workspace_style(widget: QWidget) -> None:
    widget.setStyleSheet(
        (RESOURCE_ROOT / "agent_workspace.qss").read_text(encoding="utf-8")
    )
