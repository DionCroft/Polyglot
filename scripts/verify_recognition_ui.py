"""Qt checks using synthetic audio and isolated preferences; never a live microphone."""

import json, os, time
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
from app.system.architecture import is_x64

os.environ["LECTURELIVE_DATA"] = str(
    root
    / (
        "tests/recognition-ui-x64-data"
        if is_x64()
        else "tests/recognition-ui-arm64-data"
    )
)
from app.system.offline import enforce_offline

enforce_offline()
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.system.architecture import is_x64

app = QApplication([])
window = MainWindow()
window.show()


def wait(condition, seconds=90):
    deadline = time.monotonic() + seconds
    while not condition() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert condition(), "Recognition UI timed out"


try:
    wait(lambda: not window.checker.is_alive())
    app.processEvents()
    window.recognition_mode.setCurrentIndex(0)
    window.vocabulary_guidance.setChecked(False)
    window.course_vocabulary.setCurrentIndex(10)
    window.use_course_vocabulary.click()
    assert window.glossary.currentData() == "project_management"
    assert "Gantt chart" in window.vocabulary.toPlainText()
    assert window.recognition_mode.currentData() == "standard"
    assert not window.vocabulary_guidance.isChecked()
    window.glossary.setCurrentIndex(window.glossary.findData("embedded_systems"))
    window.recognition_mode.setCurrentIndex(window.recognition_mode.findData("careful"))
    window.vocabulary.setPlainText("ESP32\nI2C\nFreeRTOS")
    window.vocabulary_guidance.setChecked(True)
    window.accelerator.setCurrentIndex(window.accelerator.findData("auto"))
    with patch(
        "app.ui.main_window.QInputDialog.getText",
        return_value=("Recognition test", True),
    ):
        window.save_preset()
    window.recognition_mode.setCurrentIndex(0)
    window.vocabulary_guidance.setChecked(False)
    window.accelerator.setCurrentIndex(window.accelerator.findData("cpu"))
    window.load_preset()
    assert (
        window.cfg.recognition_mode == "careful"
        and window.vocabulary_guidance.isChecked()
    )
    assert window.accelerator.currentData() == "auto"
    window.save.setChecked(False)
    window.wav = str(root / "tests/fixtures/technical-0.wav")
    window.start_stop()
    wait(lambda: window.pipeline is not None and window.pipeline.started)
    assert (
        not window.recognition_mode.isEnabled()
        and not window.vocabulary_guidance.isEnabled()
    )
    assert not window.course_vocabulary.isEnabled()
    assert not window.use_course_vocabulary.isEnabled()
    wait(lambda: window.last_caption is not None)
    text = window.last_caption.english
    window.stop()
    wait(lambda: window.pipeline is None)
    assert (
        window.recognition_mode.isEnabled() and window.vocabulary_guidance.isEnabled()
    )
    window.resize(860, 640)
    app.processEvents()
    for control in (window.start_button, window.pause_button, window.compact_button):
        assert control.mapTo(window, control.rect().bottomRight()).y() < window.height()
    window.course_vocabulary.setCurrentIndex(10)
    window.use_course_vocabulary.click()
    window.resize(1060, 860)
    app.processEvents()
    tag = "x64" if is_x64() else "arm64"
    window.grab().save(str(root / f"tests/artifacts/recognition-ui-{tag}.png"))
    from PySide6.QtWidgets import QScrollArea

    for scroll in window.findChildren(QScrollArea):
        if scroll.isAncestorOf(window.vocabulary):
            scroll.ensureWidgetVisible(window.vocabulary_guidance)
            app.processEvents()
    window.grab().save(str(root / f"tests/artifacts/course-ui-{tag}.png"))
    result = dict(
        passed=True,
        architecture=tag,
        preset_roundtrip=True,
        course_list_apply=True,
        synthetic_lecture=text,
        minimum_controls_visible=True,
    )
    (root / f"tests/artifacts/recognition-ui-{tag}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result))
finally:
    window.close()
    wait(lambda: not window.isVisible())
