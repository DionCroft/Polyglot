"""Exercise native controls, safe switching and exports using local WAVs only."""

import json
import time
from pathlib import Path
from unittest.mock import patch


def run(fixtures, report_path):
    from PySide6.QtWidgets import QApplication
    from app.config.settings import Settings
    from app.ui.main_window import MainWindow
    from app.ui.teaching import TeachingControls
    from app.captions.state import Caption

    cfg = Settings(accelerator="cpu", profile="fast")
    cfg.save()
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()

    def wait(condition, seconds=120):
        deadline = time.monotonic() + seconds
        while not condition() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert condition(), "Conversation UI timed out"

    result = {"passed": False, "physical_microphone_tested": False}
    try:
        wait(lambda: not window.checker.is_alive())
        app.processEvents()
        window.speaking_language.setCurrentIndex(1)
        with patch(
            "app.ui.main_window.QInputDialog.getText",
            return_value=("Mandarin questions", True),
        ):
            window.save_preset()
        window.speaking_language.setCurrentIndex(0)
        window.load_preset()
        assert window.cfg.speaking_language == "zh"
        assert "spoken" in window.preview_zh_label.text()
        window.speaking_language.setCurrentIndex(0)
        window.wav = str(Path(fixtures) / "jfk.wav")
        window.start_stop()
        wait(
            lambda: (
                window.pipeline
                and window.pipeline.source
                and not window.pipeline.source.thread.is_alive()
            )
        )
        wait(lambda: window.last_caption is not None)
        window.teaching = TeachingControls(window)
        window.teaching.show()
        window.teaching.language.setCurrentIndex(1)
        wait(
            lambda: (
                window.cfg.speaking_language == "zh"
                and not window.pipeline.switching.is_set()
            )
        )
        assert window.speaking_language.currentData() == "zh"
        assert window.pipeline.export is not None
        folder = window.pipeline.export.folder
        caption = Caption(
            100,
            20,
            21,
            "Please explain again.",
            "请再解释一次。",
            True,
            window.pipeline.epoch,
            "complete",
            "zh",
        )
        window.on_event("caption", caption)
        text = window.overlay._caption_document(26).toPlainText()
        assert "English · translation" in text and "简体中文 · spoken" in text
        assert caption.english in text and caption.chinese in text
        window.overlay.grab().save(str(Path(report_path).with_suffix(".overlay.png")))
        window.teaching.grab().save(str(Path(report_path).with_suffix(".teaching.png")))
        window.pause()
        window.speaking_language.setCurrentIndex(0)
        wait(
            lambda: (
                window.cfg.speaking_language == "en"
                and not window.pipeline.switching.is_set()
            )
        )
        assert window.pipeline.paused.is_set()
        assert window.pipeline.export.folder == folder
        window.stop()
        wait(lambda: window.pipeline is None)
        assert window.speaking_language.isEnabled()
        assert (folder / "English.srt").stat().st_size > 0
        window.speaking_language.setCurrentIndex(1)
        window.wav = str(Path(fixtures) / "mandarin-1.wav")
        window.start_stop()
        wait(
            lambda: (
                window.pipeline
                and window.pipeline.source
                and not window.pipeline.source.thread.is_alive()
            )
        )
        wait(
            lambda: (
                window.last_caption is not None and bool(window.last_caption.english)
            )
        )
        result["mandarin_wav_caption"] = window.last_caption.__dict__
        mandarin_folder = window.pipeline.export.folder
        window.stop()
        wait(lambda: window.pipeline is None)
        assert "English · translation" in (
            mandarin_folder / "Bilingual Transcript.txt"
        ).read_text(encoding="utf-8")
        window.resize(860, 640)
        app.processEvents()
        for control in [
            window.start_button,
            window.pause_button,
            window.compact_button,
        ]:
            assert (
                control.mapTo(window, control.rect().bottomRight()).y()
                < window.height()
            )
        window.resize(1060, 860)
        app.processEvents()
        window.grab().save(str(Path(report_path).with_suffix(".png")))
        result.update(
            passed=True,
            language_preset=True,
            compact_selector=True,
            live_switch=True,
            paused_switch=True,
            one_transcript_folder=True,
            labels_verified=True,
            minimum_controls_visible=True,
            mandarin_audio_pipeline=True,
            overlay_text_test="explicit UI fixture; speech accuracy evaluated separately",
        )
        return 0
    finally:
        window.close()
        wait(lambda: not window.isVisible())
        Path(report_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
