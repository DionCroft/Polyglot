"""Actual wrapped-line coverage, queue ordering and readable playback timing."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dataclasses import replace
import pytest
from PySide6.QtWidgets import QApplication

from app.captions.state import Caption
from app.asr.language_detection import UncertainTurn
from app.config.settings import Settings
from app.ui.overlay import Overlay
from app.system.long_paragraph_test import ENGLISH, CHINESE, exercise, scenarios


@pytest.fixture
def display(monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr("app.ui.overlay.overlay_input", lambda *_: None)
    overlay = Overlay(Settings(width=1000, projector_height=360, locked=True))
    yield overlay, app
    overlay.close()


@pytest.mark.parametrize("name,entries", scenarios().items())
def test_every_character_reaches_fully_visible_lines(display, name, entries):
    overlay, app = display
    exercise(overlay, app, entries)


@pytest.mark.parametrize("mode", ["Bilingual", "English", "Chinese"])
def test_small_panel_large_font_and_display_modes(display, mode):
    overlay, app = display
    overlay.settings.mode = mode
    overlay.settings.width = 400
    overlay.settings.projector_height = 200
    overlay.settings.font_size = 64
    overlay.settings.spacing = 180
    exercise(overlay, app, [Caption(1, 0, 4, ENGLISH, CHINESE, True)])
    assert all(
        c.document.defaultFont().pointSize() == 64
        for c in overlay.projector.columns.values()
    )


def paint(overlay, app):
    overlay.show()
    overlay.roll_timer.stop()
    app.processEvents()
    overlay.repaint()


def test_late_translation_keeps_source_position_and_waits(display):
    overlay, app = display
    source = Caption(1, 0, 4, ENGLISH * 3, final=True)
    overlay.enqueue(source)
    overlay.enqueue(Caption(2, 5, 9, "Next", "下一段", True))
    paint(overlay, app)
    player = overlay.projector
    for _ in range(500):
        player.advance(10, 0.5)
        overlay.repaint()
    assert player.current == source and player.waiting == {"zh"}
    source_column = player.columns["en"]
    position = source_column.index
    translated = replace(source, chinese=CHINESE * 5, translation_status="complete")
    overlay.enqueue(translated)
    overlay.repaint()
    assert source_column.index == position and source_column.done
    assert player.columns["zh"].index == 0 and not player.waiting
    assert not player.columns["zh"].done
    # A stale source cannot erase a finished translation.
    overlay.enqueue(source)
    assert player.current == translated
    for _ in range(500):
        player.advance(10, 0.5)
        overlay.repaint()
    assert player.current.identifier == 2
    overlay.enqueue(translated)
    assert len(player.entries) == 1


def test_resize_keeps_text_anchor_and_new_session_is_only_reset(display):
    overlay, app = display
    overlay.enqueue(Caption(1, 0, 4, "🤖 " + ENGLISH * 10, CHINESE * 10, True))
    paint(overlay, app)
    player = overlay.projector
    for _ in range(10):
        player.advance(10, 0.5)
        overlay.repaint()
    anchors = {lang: c.lines[c.index].start for lang, c in player.columns.items()}
    overlay.settings.width = 420
    overlay.settings.font_size = 40
    overlay.place()
    paint(overlay, app)
    for lang, column in player.columns.items():
        assert column.lines[column.index].start <= anchors[lang]
        assert column.lines[column.index].end > anchors[lang]
    overlay.reset()  # Language switch preserves unread passages.
    assert overlay.projector is player and player.current
    overlay.reset(new_session=True)
    assert overlay.projector.current is None


def test_time_holds_hidden_stall_and_paint_required(display, monkeypatch):
    overlay, app = display
    overlay.enqueue(Caption(1, 0, 4, ENGLISH * 2, CHINESE * 2, True))
    paint(overlay, app)
    player = overlay.projector
    column = player.columns["en"]
    hold = len(column.visible_lines()) * 1.4
    player.advance(hold - 0.01, 1.4)
    assert column.index == 0
    player.advance(1000, 1.4)  # No intervening paint: no progress.
    assert column.index == 0
    overlay.repaint()
    player.advance(0.02, 1.4)
    assert column.index == 1
    overlay.repaint()
    overlay.hide()
    assert not overlay.roll_timer.isActive()
    before = column.elapsed
    overlay._roll_tick()
    assert column.elapsed == before
    paint(overlay, app)
    overlay.last_tick -= 3600  # Event loop was blocked: never jump past text.
    overlay._roll_tick()
    assert column.elapsed <= before + 0.1001
    assert column.index == 1


def test_missing_translation_and_uncertain_turn_do_not_block_queue(display):
    overlay, app = display
    overlay.enqueue(
        Caption(1, 0, 4, "Source", final=True, translation_status="unavailable")
    )
    overlay.enqueue(UncertainTurn(2, 5, 9))
    overlay.enqueue(Caption(3, 10, 14, "Last", "最后", True))
    paint(overlay, app)
    seen = set()
    for _ in range(100):
        seen.add(overlay.projector.current.identifier)
        overlay.projector.advance(10, 0.5)
        overlay.repaint()
    assert seen == {1, 2, 3}


def test_speed_validation():
    assert Settings.from_dict({"projector_line_ms": 1}).projector_line_ms == 500
    assert Settings.from_dict({"projector_line_ms": 99999}).projector_line_ms == 5000


def test_real_timer_rolls_and_pauses_when_hidden(display):
    from PySide6.QtTest import QTest

    overlay, app = display
    overlay.settings.projector_height = 200
    overlay.settings.font_size = 48
    overlay.settings.projector_line_ms = 500
    overlay.enqueue(Caption(1, 0, 4, ENGLISH * 2, CHINESE * 2, True))
    overlay.show()
    app.processEvents()
    app.processEvents()
    column = overlay.projector.columns["en"]
    assert column.index == 0
    hold_ms = len(column.visible_lines()) * 500
    QTest.qWait(hold_ms + 400)
    assert column.index > 0
    overlay.hide()
    index = column.index
    QTest.qWait(700)
    assert column.index == index and not overlay.roll_timer.isActive()
