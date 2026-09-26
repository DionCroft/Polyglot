"""Native reader/projector checks with deterministic text, never microphone audio."""

import json
import os
import time
from dataclasses import replace
from pathlib import Path


def run(report_path):
    if not os.environ.get("LECTURELIVE_DATA"):
        raise RuntimeError("Set LECTURELIVE_DATA to an isolated test folder first")
    from PySide6.QtWidgets import QApplication
    from app.captions.state import Caption
    from app.asr.language_detection import UncertainTurn
    from app.config.settings import Settings, ROOT
    from app.ui.main_window import MainWindow
    from app.ui.help import GuideDialog
    from app.system.architecture import is_macos

    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    Settings(save_transcripts=False, width=1100, projector_height=420).save()
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    result = {
        "passed": False,
        "physical_microphone_tested": False,
        "speech_accuracy_tested": False,
    }

    def pump():
        app.processEvents()

    try:
        deadline = time.monotonic() + 60
        while window.checker.is_alive() and time.monotonic() < deadline:
            pump()
            time.sleep(0.02)
        assert not window.checker.is_alive()
        view = window.transcript_view
        # Populate while the tab is hidden, as it is at the start of a lecture.
        for i in range(30):
            window.on_event(
                "transcript-entry",
                Caption(
                    i,
                    i * 5,
                    i * 5 + 4,
                    f"Passage {i}: The critical path determines the project duration.",
                    "关键路径决定项目工期。",
                    True,
                ),
            )
        window.tabs.setCurrentWidget(view)
        pump()
        pump()
        bar = view.reader.verticalScrollBar()
        assert bar.value() == bar.maximum()
        bar.setSliderDown(True)
        bar.setSliderPosition(bar.maximum() // 2)
        bar.setSliderDown(False)
        position = bar.value()
        source = Caption(
            30,
            150,
            154,
            "A risk register records risks, their owners and planned responses.",
            final=True,
        )
        window.on_event("transcript-entry", source)
        pump()
        assert bar.value() == position and view.unseen == 1
        window.on_event(
            "transcript-entry",
            replace(
                source,
                chinese="风险登记册记录风险、负责人和计划的应对措施。",
                translation_status="complete",
            ),
        )
        window.on_event(
            "transcript-entry",
            Caption(
                31,
                156,
                160,
                "Please explain the critical path again.",
                "请再解释一下关键路径。",
                True,
                1,
                "complete",
                "zh",
            ),
        )
        view.search.setText("critical path")
        view.find_next()
        assert "critical path" == view.reader.textCursor().selectedText().lower()
        view.reader.copy()
        assert "critical path" == QApplication.clipboard().text().lower()
        # Synthetic uncertain turn is visible, without invented words or language.
        window.on_event("transcript-entry", UncertainTurn(32, 160, 162, 1))
        view.copy_transcript()
        assert "Speech not transcribed" in QApplication.clipboard().text()
        assert "请再解释一下关键路径" in QApplication.clipboard().text()
        view.back_to_live()
        window.grab().save(str(report.with_suffix(".reader.png")))
        window.overlay.preview = False
        window.overlay.show()
        window.overlay.lock(True)
        pump()
        if not is_macos():
            from app.system.windows import user32

            style = user32.GetWindowLongPtrW(int(window.overlay.winId()), -20)
            assert style & 0x20 and style & 0x08000000
        window.overlay.grab().save(str(report.with_suffix(".projector.png")))
        assert (
            window.overlay.projector.columns["en"].document.defaultFont().pointSize()
            == window.cfg.font_size
        )
        window.resize(860, 640)
        pump()
        pump()
        assert view.following and bar.value() == bar.maximum()
        for control in [
            view.live,
            view.copy_all,
            window.start_button,
            window.pause_button,
        ]:
            position = control.mapTo(window, control.rect().bottomRight())
            assert position.y() < window.height() and position.x() < window.width()
        window.grab().save(str(report.with_suffix(".minimum.png")))
        guide = GuideDialog(ROOT / "docs", window)
        index = guide.pages.findData("TRANSCRIPT.md")
        assert index >= 0
        guide.pages.setCurrentIndex(index)
        assert "Back to live" in guide.browser.toPlainText()
        guide.close()
        from types import SimpleNamespace
        from threading import Event

        # A previous translation must not erase newer provisional speech, and
        # an uncertain Auto final must retract provisional text in BOTH views.
        window.pipeline = SimpleNamespace(epoch=1, paused=Event())
        try:
            window.cfg.speaking_language = "auto"
            window.on_event(
                "caption", Caption(33, 162, 164, "Unfinished next question", epoch=1)
            )
            window.on_event(
                "caption",
                Caption(31, 156, 160, "Previous answer", "先前的回答", True, 1),
            )
            assert "Unfinished next question" in view.provisional.text()
            window.on_event(
                "language-detection",
                {"epoch": 1, "identifier": 33, "language": None, "final": True},
            )
            assert "Unfinished next question" not in view.provisional.text()
            assert "not transcribed" in view.provisional.text()
        finally:
            window.pipeline = None
            window.cfg.speaking_language = "en"
        # New sessions clear temporary history; changing languages does not.
        window.select_language()
        assert len(window.history.entries) == 33
        view.clear(False)
        assert not window.history.entries and not view.reader.toPlainText()
        result.update(
            passed=True,
            native_qt_platform=app.platformName(),
            scroll_anchor=True,
            search_copy=True,
            late_translation=True,
            bilingual_rows=True,
            explicit_gap=True,
            minimum_window=True,
            offline_help=True,
            temporary_history_reset=True,
            fixed_projector_font=True,
            uncertain_partial_retracted=True,
            provisional_survives_older_translation=True,
        )
        return 0
    finally:
        window.close()
        pump()
        report.write_text(json.dumps(result, indent=2), encoding="utf-8")
