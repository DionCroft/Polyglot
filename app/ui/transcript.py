"""Incremental, selectable session transcript. Scrolling never controls capture."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QTextCursor, QTextBlockFormat, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextBrowser,
    QApplication,
)

from app.captions.history import passage_text


class TranscriptReader(QTextBrowser):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def resizeEvent(self, event):
        updating = self.owner.updating
        self.owner.updating = True
        try:
            super().resizeEvent(event)
        finally:
            self.owner.updating = updating
        QTimer.singleShot(0, self.owner.follow_if_live)

    def wheelEvent(self, event):
        self.owner.hold_position()
        super().wheelEvent(event)
        self.owner._scrolled(self.verticalScrollBar().value())

    def keyPressEvent(self, event):
        if event.key() in {
            Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_PageUp,
            Qt.Key_PageDown,
            Qt.Key_Home,
            Qt.Key_End,
            Qt.Key_Space,
        }:
            self.owner.hold_position()
        super().keyPressEvent(event)
        self.owner._scrolled(self.verticalScrollBar().value())


class TranscriptView(QWidget):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self.blocks = {}
        self.following = True
        self.unseen = 0
        self.updating = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find English or Chinese text…")
        self.search.setAccessibleName("Search transcript")
        self.search.returnPressed.connect(self.find_next)
        self.search.textChanged.connect(lambda: self.search_status.setText(""))
        controls.addWidget(self.search, 1)
        self.previous = QPushButton("Previous")
        self.previous.clicked.connect(lambda: self.find_next(backwards=True))
        controls.addWidget(self.previous)
        self.next = QPushButton("Next")
        self.next.clicked.connect(self.find_next)
        controls.addWidget(self.next)
        layout.addLayout(controls)
        actions = QHBoxLayout()
        self.live = QPushButton("Following live")
        self.live.clicked.connect(self.back_to_live)
        actions.addWidget(self.live)
        self.copy_selection = QPushButton("Copy selection")
        self.copy_selection.setEnabled(False)
        actions.addWidget(self.copy_selection)
        self.copy_all = QPushButton("Copy transcript")
        self.copy_all.clicked.connect(self.copy_transcript)
        actions.addWidget(self.copy_all)
        actions.addStretch()
        layout.addLayout(actions)
        self.search_status = QLabel("")
        self.search_status.setWordWrap(True)
        layout.addWidget(self.search_status)
        self.reader = TranscriptReader(self)
        self.reader.setAccessibleName("Rolling bilingual transcript")
        self.reader.setPlaceholderText(
            "Start a lecture. Completed passages will stay here as you speak."
        )
        self.reader.setOpenLinks(False)
        self.reader.setUndoRedoEnabled(False)
        self.reader.document().setMaximumBlockCount(history.limit)
        self.reader.setStyleSheet("QTextBrowser { font-size:20px; }")
        self.reader.copyAvailable.connect(self.copy_selection.setEnabled)
        self.reader.selectionChanged.connect(self._selection_changed)
        self.copy_selection.clicked.connect(self.reader.copy)
        self.reader.verticalScrollBar().valueChanged.connect(self._scrolled)
        self.reader.verticalScrollBar().sliderPressed.connect(self.hold_position)
        self.reader.verticalScrollBar().actionTriggered.connect(self.hold_position)
        self.reader.verticalScrollBar().rangeChanged.connect(self.follow_if_live)
        layout.addWidget(self.reader, 1)
        self.provisional = QLabel(
            "Listening text will appear here while a phrase is unfinished."
        )
        self.provisional.setWordWrap(True)
        self.provisional.setMaximumHeight(76)
        self.provisional.setObjectName("muted")
        layout.addWidget(self.provisional)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setObjectName("muted")
        layout.addWidget(self.note)
        self.set_saving(True)
        self.find_shortcut = QShortcut(QKeySequence.Find, self)
        self.find_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.find_shortcut.activated.connect(self.search.setFocus)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.follow_if_live)

    def follow_if_live(self, *_):
        if self.following and not self.updating:
            self.back_to_live()

    def hold_position(self, *_):
        self.following = False
        self._live_label()

    def set_saving(self, saving):
        self.saving = saving
        self._note()

    def _note(self):
        text = (
            "Transcript saving is on. Scroll back to read; listening continues."
            if self.saving
            else "Temporary history only — saving is off. Copy anything you need before starting another lecture or closing the app."
        )
        if self.history.trimmed:
            text += f" Showing the latest {self.history.limit:,} passages; older passages have left this view."
        self.note.setText(text)

    def _scrolled(self, value):
        if self.updating or self.following:
            return
        bar = self.reader.verticalScrollBar()
        self.following = (
            value >= bar.maximum() - 2 and not self.reader.textCursor().hasSelection()
        )
        if self.following:
            self.unseen = 0
        self._live_label()

    def _selection_changed(self):
        if not self.updating and self.reader.textCursor().hasSelection():
            self.following = False
            self._live_label()

    def _live_label(self):
        self.live.setText(
            "Following live"
            if self.following
            else "Back to live" + (f" · {self.unseen} new" if self.unseen else "")
        )

    def back_to_live(self):
        self.updating = True
        cursor = self.reader.textCursor()
        cursor.clearSelection()
        self.reader.setTextCursor(cursor)
        self.following = True
        self.unseen = 0
        self.reader.verticalScrollBar().setValue(
            self.reader.verticalScrollBar().maximum()
        )
        self.updating = False
        self._live_label()

    def accept(self, entry):
        change = self.history.accept(entry)
        if change is None:
            return False
        bar = self.reader.verticalScrollBar()
        # Anchor the first visible block: a late translation above it may add lines.
        anchor = self.reader.cursorForPosition(self.reader.viewport().rect().topLeft())
        before = self.reader.cursorRect(anchor).top()
        self.updating = True
        try:
            doc = self.reader.document()
            if change.added:
                cursor = QTextCursor(doc)
                cursor.movePosition(QTextCursor.End)
                if self.blocks:
                    cursor.insertBlock()
            else:
                block = self.blocks[change.key]
                old = block.text()
                new = passage_text(entry).replace("\n", "\u2028")
                # Replace only the changed suffix/prefix, so selecting recognised
                # words survives the arrival of their translation. Qt uses UTF-16
                # positions (including two units for emoji/non-BMP characters).
                prefix = 0
                while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
                    prefix += 1
                suffix = 0
                while (
                    suffix < min(len(old), len(new)) - prefix
                    and old[-suffix - 1] == new[-suffix - 1]
                ):
                    suffix += 1
                cursor = QTextCursor(block)
                cursor.setPosition(
                    block.position() + len(old[:prefix].encode("utf-16-le")) // 2
                )
                end = len(old) - suffix
                cursor.setPosition(
                    block.position() + len(old[:end].encode("utf-16-le")) // 2,
                    QTextCursor.KeepAnchor,
                )
            # Each passage is ONE document block; line separators preserve formatting
            # and let Qt evict complete passages instead of half a bilingual pair.
            cursor.insertText(
                passage_text(entry).replace("\n", "\u2028")
                if change.added
                else new[prefix : len(new) - suffix if suffix else len(new)]
            )
            fmt = QTextBlockFormat()
            fmt.setBottomMargin(20)
            fmt.setLineHeight(125, QTextBlockFormat.ProportionalHeight.value)
            cursor.setBlockFormat(fmt)
            self.blocks[change.key] = cursor.block()
            if change.removed is not None:
                self.blocks.pop(change.removed, None)
            if self.following:
                bar.setValue(bar.maximum())
            else:
                bar.setValue(
                    bar.value() + self.reader.cursorRect(anchor).top() - before
                )
                self.unseen += int(change.added)
        finally:
            self.updating = False
        self._live_label()
        self._note()
        return True

    def find_next(self, _checked=False, backwards=False):
        query = self.search.text().strip()
        if not query:
            self.search_status.setText("Enter a word or phrase to find.")
            return
        self.following = False
        self.updating = True
        try:
            from PySide6.QtGui import QTextDocument

            flags = (
                QTextDocument.FindBackward if backwards else QTextDocument.FindFlags()
            )
            found = self.reader.find(query, flags)
            if not found:
                cursor = self.reader.textCursor()
                cursor.movePosition(QTextCursor.End if backwards else QTextCursor.Start)
                self.reader.setTextCursor(cursor)
                found = self.reader.find(query, flags)
            self.search_status.setText(
                "Match selected. Use Next or Previous to continue."
                if found
                else "No match in the current transcript."
            )
        finally:
            self.updating = False
        self._live_label()

    def copy_transcript(self):
        QApplication.clipboard().setText(self.history.text())
        self.search_status.setText("Transcript copied. Unfinished speech is excluded.")

    def clear(self, saving=True):
        self.updating = True
        self.history.clear()
        self.blocks.clear()
        self.reader.clear()
        self.search_status.clear()
        self.provisional.setText(
            "Listening text will appear here while a phrase is unfinished."
        )
        self.updating = False
        self.set_saving(saving)
        self.back_to_live()
