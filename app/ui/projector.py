"""Ordered projector playback, with independent wrapped-line positions per language."""

from collections import OrderedDict
from dataclasses import dataclass

from PySide6.QtGui import (
    QColor,
    QFont,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextOption,
)

from app.captions.state import Caption
from app.system.architecture import is_macos


@dataclass(frozen=True)
class ReadingLine:
    start: int
    end: int
    top: float
    bottom: float


class ReadingColumn:
    """Advance whole lines only; preserve a UTF-16 text anchor when rewrapping."""

    def __init__(self):
        self.document = QTextDocument()
        self.document.setDocumentMargin(0)
        self.signature = None
        self.lines = []
        self.index = 0
        self.elapsed = 0.0
        self.done = False
        self.height = 1
        self.hold_lines = 1

    def configure(self, text, width, height, settings, colour):
        signature = (text, width, height, settings.font_size, settings.spacing, colour)
        if signature == self.signature:
            return
        same_text = self.signature is not None and text == self.signature[0]
        anchor = self.lines[self.index].start if same_text and self.lines else 0
        self.signature = signature
        self.height = height
        doc = self.document
        doc.setDefaultFont(
            QFont(
                "PingFang SC" if is_macos() else "Microsoft YaHei UI",
                settings.font_size,
            )
        )
        option = doc.defaultTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        doc.setDefaultTextOption(option)
        doc.setPlainText(text)
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.Document)
        block_format = QTextBlockFormat()
        block_format.setLineHeight(
            settings.spacing, QTextBlockFormat.ProportionalHeight.value
        )
        cursor.mergeBlockFormat(block_format)
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(colour))
        cursor.mergeCharFormat(char_format)
        doc.setTextWidth(width)
        doc.size()  # Force wrapping before reading QTextLine geometry.
        self.lines = []
        block = doc.begin()
        while block.isValid():
            top = doc.documentLayout().blockBoundingRect(block).top()
            layout = block.layout()
            for i in range(layout.lineCount()):
                line = layout.lineAt(i)
                start = block.position() + line.textStart()
                end = start + line.textLength()
                if i == layout.lineCount() - 1 and block.next().isValid():
                    end += 1  # Include the paragraph break in the text coverage.
                self.lines.append(
                    ReadingLine(
                        start, end, top + line.y(), top + line.y() + line.height()
                    )
                )
            block = block.next()
        self.index = max(
            (i for i, line in enumerate(self.lines) if line.start <= anchor), default=0
        )
        self.elapsed = 0.0
        self.done = False
        self.hold_lines = max(1, len(self.visible_lines()))

    def visible_lines(self):
        if not self.lines:
            return []
        top = self.lines[self.index].top
        visible = []
        for index in range(self.index, len(self.lines)):
            line = self.lines[index]
            if line.bottom > top + self.height + 0.01:
                break
            visible.append(line)
        return visible

    @property
    def offset(self):
        return self.lines[self.index].top if self.lines else 0

    def advance(self, seconds, seconds_per_line):
        visible = self.visible_lines()
        if self.done or not visible:
            return
        self.elapsed += seconds
        if self.elapsed < self.hold_lines * seconds_per_line:
            return
        self.elapsed = 0.0
        if visible[-1] == self.lines[-1]:
            self.done = True
        else:
            previous_end = visible[-1].end
            self.index += 1
            self.hold_lines = max(
                1, sum(line.end > previous_end for line in self.visible_lines())
            )


class RollingProjector:
    """Pending passages cannot overtake each other or replace unread text.

    Only the current passage owns Qt documents. Queued passages retain text, not
    laid-out documents. Completed passages are discarded when the next starts.
    """

    def __init__(self):
        self.entries = OrderedDict()
        self.newest = (-1, -1)
        self.columns = {}
        self.labels = {}
        self.waiting = set()
        self.key = None
        self.drawn = False

    def accept(self, entry):
        if isinstance(entry, Caption) and (
            not entry.final or not entry.source_text.strip()
        ):
            return
        key = (entry.epoch, entry.identifier)
        if key in self.entries:
            old = self.entries[key]
            if (
                old == entry
                or not isinstance(old, Caption)
                or old.translated_text
                or old.translation_status == "unavailable"
            ):
                return
        elif key <= self.newest:
            return
        else:
            self.newest = key
        self.entries[key] = entry

    @property
    def current(self):
        return next(iter(self.entries.values()), None)

    @property
    def backlog(self):
        return max(0, len(self.entries) - 1)

    def prepare(self, width, height, settings):
        entry = self.current
        if entry is None:
            return
        key = (entry.epoch, entry.identifier)
        if key != self.key:
            self.key = key
            self.columns = {}
            self.drawn = False
        languages = (
            (
                ["en", "zh"]
                if settings.mode == "Bilingual"
                else ["en" if settings.mode == "English" else "zh"]
            )
            if isinstance(entry, Caption)
            else ["notice"]
        )
        self.columns = {
            lang: self.columns[lang] if lang in self.columns else ReadingColumn()
            for lang in languages
        }
        self.labels = {}
        self.waiting = set()
        column_width = (width - 24 * (len(languages) - 1)) / len(languages)
        for lang in languages:
            if lang == "notice":
                text = "Speech not transcribed · " + entry.reason
                label, colour = "Speech not transcribed", "#ffd59b"
            else:
                label = ("English" if lang == "en" else "简体中文") + (
                    " · Spoken" if entry.source_language == lang else " · Translation"
                )
                colour = (
                    settings.english_color if lang == "en" else settings.chinese_color
                )
                text = entry.english if lang == "en" else entry.chinese
                if not text:
                    if entry.translation_status == "unavailable":
                        text = (
                            "Translation unavailable"
                            if lang == "en"
                            else "翻译暂不可用"
                        )
                    else:
                        text = "Translating…" if lang == "en" else "正在翻译…"
                        self.waiting.add(lang)
            column = self.columns[lang]
            before = column.signature
            column.configure(text, column_width, height, settings, colour)
            if before != column.signature:
                self.drawn = False
            self.labels[lang] = label

    def advance(self, seconds, seconds_per_line):
        # Time may only count towards text which has actually been painted.
        if not self.drawn or not self.columns:
            return
        for lang, column in self.columns.items():
            if lang not in self.waiting:
                column.advance(seconds, seconds_per_line)
        if (
            not self.waiting
            and all(column.done for column in self.columns.values())
            and self.backlog
        ):
            self.entries.popitem(last=False)
            self.key = None
            self.columns = {}
        self.drawn = False
