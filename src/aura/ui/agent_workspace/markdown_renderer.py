from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from dataclasses import dataclass
from urllib.parse import urlsplit

from PyQt6.QtCore import QByteArray, QSizeF
from PyQt6.QtGui import (
    QFont,
    QFontMetricsF,
    QPalette,
    QTextCursor,
    QTextDocument,
)

from .view_state import TimelineContentFormat


_INLINE_IMAGE = re.compile(r"!\[([^\]\n]{0,512})\]\([^)\n]*\)")
_REFERENCE_IMAGE = re.compile(r"!\[([^\]\n]{0,512})\]\[[^\]\n]*\]")
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


class DenyResourceTextDocument(QTextDocument):
    """A rich-text document that cannot resolve external or local resources."""

    def __init__(self) -> None:
        super().__init__()
        self.blocked_resources: list[str] = []

    def loadResource(self, resource_type: int, name) -> QByteArray:  # noqa: N802
        self.blocked_resources.append(str(name.toString()))
        return QByteArray()


@dataclass(frozen=True)
class MarkdownRenderKey:
    stable_id: str
    body_revision: str
    content_format: TimelineContentFormat
    width_px: int
    font_key: str
    palette_key: str
    expanded: bool
    max_collapsed_lines: int | None
    device_pixel_ratio: float


@dataclass(frozen=True)
class MarkdownLayoutResult:
    document: QTextDocument
    raw_source: str
    plain_text: str
    links: tuple[str, ...]
    full_size: QSizeF
    visible_height: float
    collapsed: bool
    render_failed: bool = False

    @property
    def full_height(self) -> float:
        return float(self.full_size.height())


class MarkdownLinkPolicy:
    """Pure policy for untrusted Markdown destinations."""

    @staticmethod
    def allowed_https(destination: str) -> str | None:
        if (
            not destination
            or destination != destination.strip()
            or _CONTROL_CHARACTERS.search(destination)
        ):
            return None
        parsed = urlsplit(destination)
        if (
            parsed.scheme.casefold() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            return None
        return destination

    @classmethod
    def describe(cls, destination: str) -> str | None:
        allowed = cls.allowed_https(destination)
        if allowed is None:
            return None
        return f"{urlsplit(allowed).hostname} — {allowed}"


class MarkdownRenderer:
    SAFE_FEATURES = (
        QTextDocument.MarkdownFeature.MarkdownDialectGitHub
        | QTextDocument.MarkdownFeature.MarkdownNoHTML
    )

    def __init__(self, *, max_cache_entries: int = 256) -> None:
        if max_cache_entries < 1:
            raise ValueError("Markdown cache must retain at least one entry.")
        self.max_cache_entries = max_cache_entries
        self._cache: OrderedDict[MarkdownRenderKey, MarkdownLayoutResult] = (
            OrderedDict()
        )
        self.cache_hits = 0
        self.cache_misses = 0

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        self._cache.clear()

    def invalidate(self, stable_id: str) -> None:
        for key in tuple(self._cache):
            if key.stable_id == stable_id:
                del self._cache[key]

    def render(
        self,
        *,
        stable_id: str,
        source: str,
        content_format: TimelineContentFormat,
        width_px: int,
        font: QFont,
        palette: QPalette,
        expanded: bool = False,
        max_collapsed_lines: int | None = None,
        device_pixel_ratio: float = 1.0,
    ) -> MarkdownLayoutResult:
        width_px = max(40, int(width_px))
        key = MarkdownRenderKey(
            stable_id=stable_id,
            body_revision=hashlib.sha256(source.encode("utf-8")).hexdigest(),
            content_format=content_format,
            width_px=width_px,
            font_key=font.toString(),
            palette_key=":".join(
                (
                    palette.text().color().name(),
                    palette.base().color().name(),
                    palette.highlight().color().name(),
                )
            ),
            expanded=expanded,
            max_collapsed_lines=max_collapsed_lines,
            device_pixel_ratio=round(float(device_pixel_ratio), 2),
        )
        cached = self._cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            self._cache.move_to_end(key)
            return cached

        self.cache_misses += 1
        result = self._layout(
            source=source,
            content_format=content_format,
            width_px=width_px,
            font=font,
            palette=palette,
            expanded=expanded,
            max_collapsed_lines=max_collapsed_lines,
        )
        self._cache[key] = result
        self._cache.move_to_end(key)
        while len(self._cache) > self.max_cache_entries:
            self._cache.popitem(last=False)
        return result

    def _layout(
        self,
        *,
        source: str,
        content_format: TimelineContentFormat,
        width_px: int,
        font: QFont,
        palette: QPalette,
        expanded: bool,
        max_collapsed_lines: int | None,
    ) -> MarkdownLayoutResult:
        document = DenyResourceTextDocument()
        document.setDocumentMargin(0)
        document.setDefaultFont(font)
        document.setDefaultStyleSheet(self._style_sheet(font, palette))
        render_failed = self._set_source(
            document,
            source,
            content_format,
        )
        document.setTextWidth(width_px)
        size = document.documentLayout().documentSize()
        full_height = max(float(size.height()), float(font.pointSizeF() * 1.5))
        collapsed_height = (
            max_collapsed_lines * max(1.0, QFontMetricsF(font).lineSpacing())
            if max_collapsed_lines
            else full_height
        )
        collapsed_height = self._avoid_partial_frames(
            document,
            collapsed_height,
        )
        collapsed = not expanded and full_height > collapsed_height + 1
        return MarkdownLayoutResult(
            document=document,
            raw_source=source,
            plain_text=document.toPlainText(),
            links=self._links(document),
            full_size=QSizeF(float(size.width()), full_height),
            visible_height=collapsed_height if collapsed else full_height,
            collapsed=collapsed,
            render_failed=render_failed,
        )

    @staticmethod
    def _avoid_partial_frames(
        document: QTextDocument,
        proposed_height: float,
    ) -> float:
        root = document.rootFrame()
        iterator = root.begin()
        while not iterator.atEnd():
            frame = iterator.currentFrame()
            if frame is not None:
                rect = document.documentLayout().frameBoundingRect(frame)
                if rect.top() < proposed_height < rect.bottom():
                    return max(1.0, float(rect.top()) - 8.0)
            iterator += 1
        return proposed_height

    @classmethod
    def plain_text(
        cls,
        source: str,
        content_format: TimelineContentFormat,
    ) -> str:
        document = DenyResourceTextDocument()
        cls._set_source(document, source, content_format)
        return document.toPlainText()

    @classmethod
    def _set_source(
        cls,
        document: QTextDocument,
        source: str,
        content_format: TimelineContentFormat,
    ) -> bool:
        try:
            if content_format is TimelineContentFormat.MARKDOWN:
                document.setMarkdown(
                    cls._replace_images(source),
                    cls.SAFE_FEATURES,
                )
                cls._allow_wrapped_code_blocks(document)
            else:
                document.setPlainText(source)
            return False
        except (RuntimeError, TypeError, ValueError):
            document.setPlainText(source)
            return True

    @staticmethod
    def _allow_wrapped_code_blocks(document: QTextDocument) -> None:
        positions: list[int] = []
        block = document.begin()
        while block.isValid():
            if block.blockFormat().nonBreakableLines():
                positions.append(block.position())
            block = block.next()
        cursor = QTextCursor(document)
        for position in positions:
            cursor.setPosition(position)
            block_format = cursor.blockFormat()
            block_format.setNonBreakableLines(False)
            cursor.setBlockFormat(block_format)

    @staticmethod
    def _replace_images(source: str) -> str:
        def placeholder(match: re.Match[str]) -> str:
            alt = _CONTROL_CHARACTERS.sub("", match.group(1))
            alt = re.sub(r"[\[\]()*_`<>#]", "", alt).strip()[:160]
            return f"[圖片：{alt or '未命名'}]"

        return _REFERENCE_IMAGE.sub(
            placeholder,
            _INLINE_IMAGE.sub(placeholder, source),
        )

    @staticmethod
    def _links(document: QTextDocument) -> tuple[str, ...]:
        links: list[str] = []
        block = document.begin()
        while block.isValid():
            fragment_iterator = block.begin()
            while not fragment_iterator.atEnd():
                fragment = fragment_iterator.fragment()
                if fragment.isValid():
                    char_format = fragment.charFormat()
                    if char_format.isAnchor():
                        destination = char_format.anchorHref()
                        if destination and destination not in links:
                            links.append(destination)
                fragment_iterator += 1
            block = block.next()
        return tuple(links)

    @staticmethod
    def _style_sheet(font: QFont, palette: QPalette) -> str:
        body_size = max(9.0, font.pointSizeF())
        text = palette.text().color().name()
        muted = "#aebbc6"
        code_background = "#202830"
        return f"""
            body {{ color: {text}; }}
            p {{ margin-top: 3px; margin-bottom: 7px; }}
            h1 {{ font-size: {body_size * 1.30:.1f}pt; margin: 4px 0 7px 0; }}
            h2 {{ font-size: {body_size * 1.18:.1f}pt; margin: 4px 0 6px 0; }}
            h3 {{ font-size: {body_size * 1.08:.1f}pt; margin: 3px 0 5px 0; }}
            blockquote {{ color: {muted}; margin-left: 10px; }}
            code, pre {{
                font-family: monospace;
                background-color: {code_background};
                white-space: pre-wrap;
            }}
            a {{ color: #78bce8; text-decoration: underline; }}
            table {{ border-collapse: collapse; }}
            th, td {{ padding: 2px 5px; }}
        """
