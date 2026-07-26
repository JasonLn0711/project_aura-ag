#!/usr/bin/env python3
"""Measure the bounded native timeline presentation paths."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import subprocess
import time
import tracemalloc
from pathlib import Path
from typing import Callable, TypeVar

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QRect
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QStyleOptionViewItem

from aura.agent.contracts import AgentUiEvent
from aura.ui.agent_workspace.coalescer import TimelineCoalescer
from aura.ui.agent_workspace.markdown_renderer import MarkdownRenderer
from aura.ui.agent_workspace.timeline import TimelineModel
from aura.ui.agent_workspace.timeline_view import ThreadTimelineView
from aura.ui.agent_workspace.view_state import (
    TimelineContentFormat,
    TimelineItemViewState,
)


T = TypeVar("T")
THRESHOLDS = {
    "model_10000_ms": 1000.0,
    "markdown_1000_ms": 5000.0,
    "streaming_1000_ms": 1000.0,
    "lifecycle_500_ms": 1000.0,
    "resize_max_ms": 250.0,
    "long_50kb_ms": 1500.0,
    "max_gui_stall_ms": 250.0,
    "rss_growth_mib": 512.0,
    "cache_entries": 256,
}


def measure(action: Callable[[], T]) -> tuple[T, float]:
    started = time.perf_counter()
    result = action()
    return result, (time.perf_counter() - started) * 1000


def rss_kib() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except (OSError, ValueError):
        return None
    return None


def event(
    sequence: int,
    event_type: str,
    payload: dict[str, object],
) -> AgentUiEvent:
    return AgentUiEvent.create(
        run_id="benchmark-run",
        event_type=event_type,
        sequence=sequence,
        source="benchmark",
        severity="info",
        payload=payload,
        created_at="2026-07-26T18:00:00+08:00",
        event_id=f"benchmark-{sequence}",
    )


def option(
    app: QApplication,
    *,
    width: int,
    font: QFont | None = None,
) -> QStyleOptionViewItem:
    value = QStyleOptionViewItem()
    value.font = QFont(font or app.font())
    value.palette = app.palette()
    value.rect = QRect(0, 0, width, 100_000)
    return value


def benchmark() -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    rss_before = rss_kib()
    tracemalloc.start()
    stalls: list[float] = []

    short_items = tuple(
        TimelineItemViewState(
            stable_id=f"short-{index}",
            kind="assistant",
            title="Aura",
            body=f"Result {index}",
            created_at="2026-07-26T18:00:00+08:00",
            content_format=TimelineContentFormat.MARKDOWN,
        )
        for index in range(10_000)
    )
    model = TimelineModel()
    _, model_ms = measure(lambda: model.replace_items(short_items))
    view = ThreadTimelineView()
    view.timeline_model.replace_items(short_items)
    permanent_index_widgets = sum(
        view.indexWidget(view.timeline_model.index(row, 0)) is not None
        for row in (0, 1, 9_999)
    )

    renderer = MarkdownRenderer(max_cache_entries=256)
    markdown_sources = tuple(
        (
            f"## Result {index}\n\n"
            "這是一段自然換行的繁體中文內容，包含 **重點**、"
            "`inline code` 與清單。\n\n"
            "1. 先確認資料。\n2. 再執行驗證。"
        )
        for index in range(1_000)
    )

    def render_markdown_rows() -> None:
        for index, source in enumerate(markdown_sources):
            _, elapsed = measure(
                lambda index=index, source=source: renderer.render(
                    stable_id=f"markdown-{index}",
                    source=source,
                    content_format=TimelineContentFormat.MARKDOWN,
                    width_px=720,
                    font=app.font(),
                    palette=app.palette(),
                )
            )
            stalls.append(elapsed)

    _, markdown_ms = measure(render_markdown_rows)
    renderer.render(
        stable_id="markdown-999",
        source=markdown_sources[-1],
        content_format=TimelineContentFormat.MARKDOWN,
        width_px=720,
        font=app.font(),
        palette=app.palette(),
    )

    streaming = TimelineCoalescer()

    def project_streaming() -> None:
        for sequence in range(1, 1_001):
            _, elapsed = measure(
                lambda sequence=sequence: streaming.consume(
                    event(
                        sequence,
                        "message.assistant.delta",
                        {"item_id": "stream", "text": "字"},
                    )
                )
            )
            stalls.append(elapsed)

    _, streaming_ms = measure(project_streaming)

    lifecycle = TimelineCoalescer()

    def project_lifecycle() -> None:
        for command_index in range(250):
            started_sequence = command_index * 2 + 1
            command_id = f"command-{command_index}"
            lifecycle.consume(
                event(
                    started_sequence,
                    "command.started",
                    {
                        "command_id": command_id,
                        "command": "git status --short",
                        "cwd": "/benchmark/repository",
                    },
                )
            )
            lifecycle.consume(
                event(
                    started_sequence + 1,
                    "command.completed",
                    {
                        "command_id": command_id,
                        "command": "git status --short",
                        "cwd": "/benchmark/repository",
                        "exit_code": 0,
                        "duration_ms": 12,
                        "output": "clean",
                    },
                )
            )

    _, lifecycle_ms = measure(project_lifecycle)

    representative = TimelineItemViewState(
        stable_id="resize",
        kind="assistant",
        title="Aura",
        body=(
            "## 檢查結果\n\n"
            + "這是一段會依 viewport 寬度重新排版的內容。" * 30
        ),
        created_at="2026-07-26T18:00:00+08:00",
        content_format=TimelineContentFormat.MARKDOWN,
    )
    resize_view = ThreadTimelineView()
    resize_view.timeline_model.replace_items((representative,))
    resize_index = resize_view.timeline_model.index(0, 0)
    resize_measurements: list[dict[str, object]] = []
    for width in (1_400, 984, 1_400):
        hint, elapsed = measure(
            lambda width=width: resize_view.itemDelegate().sizeHint(
                option(app, width=width),
                resize_index,
            )
        )
        stalls.append(elapsed)
        resize_measurements.append(
            {
                "width_px": width,
                "height_px": hint.height(),
                "elapsed_ms": round(elapsed, 3),
            }
        )

    scaled_font = QFont(app.font())
    scaled_font.setPointSizeF(app.font().pointSizeF() * 1.5)
    scaled_hint, scaled_ms = measure(
        lambda: resize_view.itemDelegate().sizeHint(
            option(app, width=984, font=scaled_font),
            resize_index,
        )
    )
    stalls.append(scaled_ms)

    long_source = (
        "## Long reply\n\n"
        + ("- **驗證項目**：保留段落、換行與 evidence。\n" * 2_000)
    ).encode("utf-8")[: 50 * 1024].decode("utf-8", errors="ignore")
    long_result, long_ms = measure(
        lambda: renderer.render(
            stable_id="long-50kb",
            source=long_source,
            content_format=TimelineContentFormat.MARKDOWN,
            width_px=984,
            font=app.font(),
            palette=app.palette(),
        )
    )
    stalls.append(long_ms)

    heavy_source = (
        "## Heavy\n\n"
        "1. Parent\n   - Nested\n     - Deep\n\n"
        "| Column | Value |\n| --- | --- |\n"
        f"| table | {'寬' * 300} |\n\n"
        f"```\n{'x' * 1_000}\n```"
    )
    heavy_result, heavy_ms = measure(
        lambda: renderer.render(
            stable_id="heavy",
            source=heavy_source,
            content_format=TimelineContentFormat.MARKDOWN,
            width_px=984,
            font=app.font(),
            palette=app.palette(),
        )
    )
    stalls.append(heavy_ms)

    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_after = rss_kib()
    rss_growth_mib = (
        max(0, rss_after - rss_before) / 1024
        if rss_before is not None and rss_after is not None
        else None
    )
    cache_requests = renderer.cache_hits + renderer.cache_misses
    metrics = {
        "model_10000": {
            "rows": model.rowCount(),
            "elapsed_ms": round(model_ms, 3),
            "permanent_index_widgets_sampled": permanent_index_widgets,
        },
        "markdown_1000": {
            "rows": len(markdown_sources),
            "elapsed_ms": round(markdown_ms, 3),
        },
        "streaming_1000": {
            "events": 1_000,
            "elapsed_ms": round(streaming_ms, 3),
            "projected_rows": len(streaming.items),
            "body_characters": len(streaming.items[0].body),
            "ui_throttle_interval_ms": 50,
        },
        "activity_lifecycle_500": {
            "events": 500,
            "elapsed_ms": round(lifecycle_ms, 3),
            "projected_rows": len(lifecycle.items),
            "detail_count": lifecycle.items[0].detail_count,
        },
        "viewport_resize": resize_measurements,
        "font_scale_150_percent": {
            "height_px": scaled_hint.height(),
            "elapsed_ms": round(scaled_ms, 3),
        },
        "long_markdown_50kb": {
            "source_bytes": len(long_source.encode("utf-8")),
            "elapsed_ms": round(long_ms, 3),
            "height_px": round(long_result.full_height, 3),
            "document_width_px": round(long_result.full_size.width(), 3),
        },
        "nested_table_code": {
            "elapsed_ms": round(heavy_ms, 3),
            "height_px": round(heavy_result.full_height, 3),
            "document_width_px": round(heavy_result.full_size.width(), 3),
        },
        "memory": {
            "python_current_mib": round(current_bytes / 1024 / 1024, 3),
            "python_peak_mib": round(peak_bytes / 1024 / 1024, 3),
            "rss_before_kib": rss_before,
            "rss_after_kib": rss_after,
            "rss_growth_mib": (
                round(rss_growth_mib, 3)
                if rss_growth_mib is not None
                else None
            ),
        },
        "cache": {
            "entries": renderer.cache_size,
            "maximum_entries": renderer.max_cache_entries,
            "hits": renderer.cache_hits,
            "misses": renderer.cache_misses,
            "hit_rate": round(
                renderer.cache_hits / cache_requests,
                6,
            ),
        },
        "maximum_gui_thread_stall_ms": round(max(stalls), 3),
    }
    checks = {
        "model_10000": (
            model.rowCount() == 10_000
            and model_ms <= THRESHOLDS["model_10000_ms"]
            and permanent_index_widgets == 0
        ),
        "markdown_1000": markdown_ms <= THRESHOLDS["markdown_1000_ms"],
        "streaming_1000": (
            streaming_ms <= THRESHOLDS["streaming_1000_ms"]
            and len(streaming.items) == 1
        ),
        "lifecycle_500": (
            lifecycle_ms <= THRESHOLDS["lifecycle_500_ms"]
            and len(lifecycle.items) == 1
            and lifecycle.items[0].detail_count == 250
        ),
        "resize": max(
            row["elapsed_ms"] for row in resize_measurements
        )
        <= THRESHOLDS["resize_max_ms"],
        "width_bounded": (
            long_result.full_size.width() <= 985
            and heavy_result.full_size.width() <= 985
        ),
        "long_50kb": long_ms <= THRESHOLDS["long_50kb_ms"],
        "maximum_gui_stall": (
            max(stalls) <= THRESHOLDS["max_gui_stall_ms"]
        ),
        "memory": (
            rss_growth_mib is None
            or rss_growth_mib <= THRESHOLDS["rss_growth_mib"]
        ),
        "cache_bounded": (
            renderer.cache_size <= THRESHOLDS["cache_entries"]
        ),
    }
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "schema_version": 1,
        "captured_at": dt.datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "source_commit": source_commit,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pyqt": PYQT_VERSION_STR,
            "qt": QT_VERSION_STR,
            "qpa": os.environ["QT_QPA_PLATFORM"],
        },
        "thresholds": THRESHOLDS,
        "metrics": metrics,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def report_markdown(result: dict[str, object]) -> str:
    metrics = result["metrics"]
    checks = result["checks"]
    lines = [
        "# Agent Timeline Markdown Performance Evidence",
        "",
        f"- Status: `{result['status']}`",
        f"- Source commit: `{result['source_commit']}`",
        f"- Captured at: `{result['captured_at']}`",
        "",
        "## Measurements",
        "",
        "| Path | Measurement |",
        "| --- | --- |",
        f"| 10,000-row model | `{metrics['model_10000']}` |",
        f"| 1,000 Markdown rows | `{metrics['markdown_1000']}` |",
        f"| 1,000 streaming deltas | `{metrics['streaming_1000']}` |",
        f"| 500 lifecycle events | `{metrics['activity_lifecycle_500']}` |",
        f"| Viewport resize | `{metrics['viewport_resize']}` |",
        f"| 150% font | `{metrics['font_scale_150_percent']}` |",
        f"| 50 KiB reply | `{metrics['long_markdown_50kb']}` |",
        f"| Nested list/table/code | `{metrics['nested_table_code']}` |",
        f"| Memory | `{metrics['memory']}` |",
        f"| Cache | `{metrics['cache']}` |",
        f"| Maximum measured GUI-thread stall | `{metrics['maximum_gui_thread_stall_ms']} ms` |",
        "",
        "## Threshold checks",
        "",
    ]
    lines.extend(
        f"- [{'x' if passed else ' '}] `{name}`"
        for name, passed in checks.items()
    )
    lines.extend(
        (
            "",
            "The benchmark exercises native Qt model/view and QTextDocument "
            "paths offscreen. Target-host compositor and assistive-technology "
            "field performance remain separate validation layers.",
            "",
        )
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    result = benchmark()
    (output_dir / "performance-benchmark.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "performance-benchmark.md").write_text(
        report_markdown(result),
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "output": str(output_dir)}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
