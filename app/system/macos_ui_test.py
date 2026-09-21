"""Native Cocoa GUI smoke test. No physical microphone permission is requested."""

import json
import os
from pathlib import Path
import time
from unittest.mock import patch


def run(report_path):
    from PySide6.QtCore import QMicrophonePermission
    from PySide6.QtWidgets import QApplication
    from app.config.settings import Settings

    cfg = Settings()
    cfg.accelerator = "cpu"
    cfg.save_transcripts = False
    cfg.save()
    app = QApplication([])
    app.setApplicationName("LectureLive")
    from app.ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    def wait(condition, seconds=180):
        deadline = time.monotonic() + seconds
        while not condition() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert condition(), "Native macOS UI timed out"

    result = {"passed": False, "physical_microphone_tested": False}
    try:
        wait(lambda: not window.checker.is_alive())
        app.processEvents()
        assert window.accelerator.findData("coreml") >= 0
        assert window.accelerator.findData("gpu") == -1
        window.course_vocabulary.setCurrentIndex(10)
        window.use_course_vocabulary.click()
        assert "Gantt chart" in window.vocabulary.toPlainText()
        assert window.glossary.currentData() == "project_management"
        window.recognition_mode.setCurrentIndex(
            window.recognition_mode.findData("careful")
        )
        window.vocabulary_guidance.setChecked(True)
        with patch(
            "app.ui.main_window.QInputDialog.getText", return_value=("Mac test", True)
        ):
            window.save_preset()
        window.recognition_mode.setCurrentIndex(0)
        window.load_preset()
        assert (
            window.cfg.recognition_mode == "careful"
            and window.vocabulary_guidance.isChecked()
        )
        window.overlay.show()
        app.processEvents()
        import objc
        import ctypes

        view = objc.objc_object(c_void_p=ctypes.c_void_p(int(window.overlay.winId())))
        native = view.window()
        window.overlay.lock(True)
        assert native.ignoresMouseEvents()
        window.overlay.lock(False)
        assert not native.ignoresMouseEvents()
        result["overlay_native_flags"] = int(native.collectionBehavior())
        result["shortcuts_registered"] = len(window.hotkeys.registered)
        result["shortcut_conflicts"] = window.hotkeys.errors
        assert len(window.hotkeys.registered) == 2, window.hotkeys.errors
        result["microphone_permission_status"] = str(
            app.checkPermission(QMicrophonePermission())
        )
        window.vocabulary_guidance.setChecked(False)
        window.wav = os.environ["LECTURELIVE_TEST_WAV"]
        window.start_stop()
        wait(lambda: window.last_caption is not None)
        result["wav_caption"] = window.last_caption.english
        window.stop()
        wait(lambda: window.pipeline is None)
        window.resize(860, 640)
        app.processEvents()
        for control in (
            window.start_button,
            window.pause_button,
            window.compact_button,
        ):
            assert (
                control.mapTo(window, control.rect().bottomRight()).y()
                < window.height()
            )
        window.resize(1060, 860)
        app.processEvents()
        window.grab().save(str(Path(report_path).with_suffix(".png")))
        result.update(
            passed=True,
            presets=True,
            co7000=True,
            overlay_lock=True,
            minimum_controls_visible=True,
        )
        return 0
    finally:
        window.close()
        wait(lambda: not window.isVisible())
        Path(report_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
