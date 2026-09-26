"""Real Qt widgets: streaming updates, scrolling, selection and projector layout."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dataclasses import replace
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextCursor

from app.captions.history import TranscriptHistory
from app.captions.state import Caption
from app.config.settings import Settings
from app.ui.transcript import TranscriptView
from app.ui.overlay import Overlay


@pytest.fixture(scope="module")
def qt():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def view(qt):
    widget = TranscriptView(TranscriptHistory())
    widget.resize(940, 650)
    widget.show()
    qt.processEvents()
    yield widget
    widget.close()


def populate(view, qt, count=40):
    for i in range(count):
        view.accept(
            Caption(
                i,
                i * 5,
                i * 5 + 4,
                f"Passage {i}: critical path and risk register.",
                "关键路径和风险登记册。",
                True,
            )
        )
    qt.processEvents()


def test_scroll_back_new_count_back_to_live_and_copy(view, qt):
    populate(view, qt)
    bar = view.reader.verticalScrollBar()
    assert bar.value() == bar.maximum() and view.following
    bar.setSliderDown(True)
    bar.setSliderPosition(bar.maximum() // 3)
    bar.setSliderDown(False)
    assert not view.following
    position = bar.value()
    view.accept(Caption(100, 210, 214, "New material", "新内容", True))
    qt.processEvents()
    assert bar.value() == position and view.unseen == 1
    assert "1 new" in view.live.text()
    view.back_to_live()
    assert bar.value() == bar.maximum() and view.unseen == 0
    view.copy_transcript()
    assert QApplication.clipboard().text() == view.history.text()
    assert "New material" in QApplication.clipboard().text()


def test_late_translation_does_not_jump_reader_or_duplicate(view, qt):
    first = Caption(0, 0, 4, "First source", final=True)
    view.accept(first)
    for i in range(1, 35):
        view.accept(Caption(i, i * 5, i * 5 + 4, f"Passage {i}", "翻译", True))
    qt.processEvents()
    bar = view.reader.verticalScrollBar()
    bar.setSliderDown(True)
    bar.setSliderPosition(bar.maximum() // 2)
    bar.setSliderDown(False)
    anchor = view.reader.cursorForPosition(view.reader.viewport().rect().topLeft())
    top = view.reader.cursorRect(anchor).top()
    view.accept(
        replace(first, chinese="很长的翻译。" * 100, translation_status="complete")
    )
    qt.processEvents()
    assert abs(view.reader.cursorRect(anchor).top() - top) <= 2
    assert view.reader.toPlainText().count("First source") == 1
    assert view.reader.document().blockCount() == 35


def test_search_wraps_both_languages_and_selection_survives_new_passages(view, qt):
    populate(view, qt)
    view.search.setText("关键路径")
    view.find_next()
    assert view.reader.textCursor().selectedText() == "关键路径"
    assert not view.following
    selected = view.reader.textCursor().selectedText()
    position = view.reader.verticalScrollBar().value()
    view.accept(Caption(100, 210, 214, "More speech", "更多内容", True))
    assert view.reader.textCursor().selectedText() == selected
    assert view.reader.verticalScrollBar().value() == position
    view.reader.copy()
    assert QApplication.clipboard().text() == selected
    view.find_next(backwards=True)
    assert view.reader.textCursor().selectedText() == "关键路径"
    view.search.setText("CRITICAL PATH")
    view.find_next()
    assert view.reader.textCursor().selectedText() == "critical path"
    view.search.setText("not present")
    view.find_next()
    assert "No match" in view.search_status.text()


def test_two_hour_history_uses_one_block_per_passage_and_clears_without_disk(
    view, qt, tmp_path
):
    view.set_saving(False)
    for i in range(1440):
        source = Caption(
            i, i * 5, i * 5 + 4, f"CO7000 passage {i}", final=True, epoch=i // 100
        )
        view.accept(source)
        view.accept(
            replace(source, chinese="项目管理。", translation_status="complete")
        )
    qt.processEvents()
    assert len(view.blocks) == view.reader.document().blockCount() == 1440
    assert view.reader.toPlainText().count("CO7000 passage") == 1440
    assert "saving is off" in view.note.text()
    view.clear(False)
    assert not view.history.entries and not view.reader.toPlainText()
    assert view.following and not list(tmp_path.iterdir())


def test_retention_evicts_whole_pairs_and_block_index(qt):
    view = TranscriptView(TranscriptHistory(limit=5))
    try:
        populate(view, qt, 30)
        assert len(view.blocks) == view.reader.document().blockCount() == 5
        assert "Passage 24:" not in view.reader.toPlainText()
        assert "Passage 25:" in view.reader.toPlainText()
        assert "latest 5 passages" in view.note.text()
        source = Caption(
            29,
            145,
            149,
            "Passage 29: critical path and risk register.",
            "关键路径和风险登记册。",
            True,
        )
        assert not view.accept(source)
    finally:
        view.close()


def test_copying_source_survives_its_translation_including_utf16(view, qt):
    source = Caption(1, 0, 4, "Robot 🤖 uses ESP32", final=True)
    view.accept(source)
    view.search.setText("ESP32")
    view.find_next()
    view.accept(
        replace(source, chinese="机器人使用 ESP32。", translation_status="complete")
    )
    qt.processEvents()
    assert view.reader.textCursor().selectedText() == "ESP32"
    assert "Robot 🤖 uses ESP32" in view.reader.toPlainText()
    assert "机器人使用 ESP32。" in view.reader.toPlainText()


def test_resize_while_following_and_hidden_tab_arrival(view, qt):
    populate(view, qt)
    view.hide()
    view.accept(Caption(100, 210, 214, "Latest while hidden", "最新内容", True))
    view.resize(800, 450)
    view.show()
    qt.processEvents()
    qt.processEvents()
    bar = view.reader.verticalScrollBar()
    assert view.following and bar.value() == bar.maximum()
    bar.setSliderDown(True)
    bar.setSliderPosition(bar.maximum() // 2)
    bar.setSliderDown(False)
    view.resize(940, 650)
    qt.processEvents()
    assert not view.following and bar.value() < bar.maximum()


def test_projector_uses_fixed_font_geometry_labels_and_compact_option(qt, monkeypatch):
    # Offscreen Qt has no native HWND/NSWindow. Native overlay flags are checked
    # by the separate packaged UI smoke test.
    monkeypatch.setattr("app.ui.overlay.overlay_input", lambda *_: None)
    history = TranscriptHistory()
    history.accept(Caption(1, 0, 4, "Critical path " * 100, "关键路径。" * 100, True))
    cfg = Settings(font_size=32, projector_height=400)
    overlay = Overlay(cfg, history)
    try:
        overlay.preview = False
        overlay.show()
        qt.processEvents()
        doc = overlay.projector.columns["en"].document
        assert doc.defaultFont().pointSize() == 32
        assert "Critical path" in doc.toPlainText()
        assert "关键路径" in overlay.projector.columns["zh"].document.toPlainText()
        height = overlay.height()
        qt.processEvents()
        assert overlay.height() == height
        cfg.mode = "English"
        overlay.repaint()
        assert list(overlay.projector.columns) == ["en"]
        cfg.overlay_layout = "compact"
        overlay.set_caption(Caption(2, 5, 8, "Hello", "你好", True))
        assert "Hello" in overlay._caption_document(30).toPlainText()
    finally:
        overlay.close()
