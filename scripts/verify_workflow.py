"""Exercise the new native workflow without recording audio or changing user preferences."""

import os, time, json
from pathlib import Path
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
os.environ["LECTURELIVE_DATA"] = str(root / "tests/workflow-data")
from app.system.offline import enforce_offline

enforce_offline()
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

app = QApplication([])
w = MainWindow()
w.show()


def pump_until(condition, seconds=30):
    deadline = time.monotonic() + seconds
    while not condition() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert condition(), "Timed out waiting for native workflow"


try:
    pump_until(lambda: w.start_button.isEnabled())
    loads = w.model_store.loads
    assert loads == 1
    w.title.setText("Saved robotics lecture")
    w.vocabulary.setPlainText("ESP32\nFreeRTOS")
    with patch(
        "app.ui.main_window.QInputDialog.getText", return_value=("Workflow test", True)
    ):
        w.save_preset()
    w.title.setText("changed")
    w.vocabulary.clear()
    w.load_preset()
    assert (
        w.title.text() == "Saved robotics lecture"
        and "ESP32" in w.vocabulary.toPlainText()
    )
    w.projector_preview()
    app.processEvents()
    assert w.overlay.isVisible()
    # A long caption expands as needed, then the next short pair restores height.
    from app.captions.state import Caption

    base_height = w.cfg.height
    w.overlay.set_caption(
        Caption(2, 0, 1, "Detailed explanation. " * 35, "技术说明。" * 35, True)
    )
    pump_until(lambda: w.overlay.height() > base_height)
    w.overlay.set_caption(Caption(3, 0, 1, "Short sentence.", "短句。", True))
    pump_until(lambda: w.overlay.height() == base_height)
    w.overlay.hide()
    w.lock_shortcut_edit.setText("Ctrl+Alt+Shift+F11")
    w.pause_shortcut_edit.setText("Ctrl+Alt+Shift+F12")
    w.apply_shortcuts()
    assert not w.hotkeys.errors and w.cfg.pause_shortcut == "Ctrl+Alt+Shift+F12"
    if w.microphone.count():
        w.test_microphone()
        pump_until(lambda: w.mic_test_button.isEnabled(), 10)
        assert "failed" not in w.mic_test_result.text().lower()
        microphone_result = w.mic_test_result.text()
    else:
        microphone_result = "No connected input available during workflow test"
    w.wav = str(root / "tests/fixtures/technical.wav")
    w.start_stop()
    pump_until(
        lambda: w.pipeline and w.pipeline.source is not None and w.pipeline.started
    )
    w.show_teaching()
    app.processEvents()
    assert w.teaching.isVisible() and not w.isVisible()
    pump_until(lambda: w.last_caption and bool(w.last_caption.chinese))
    w.teaching.grab().save(str(root / "docs/evidence/teaching-controls.png"))
    w.teaching.close()
    app.processEvents()
    assert w.isVisible()
    previous = w.pipeline
    w.pipeline._error("Simulated disconnected microphone", True)
    app.processEvents()
    assert w.retry_button.isVisible()
    w.reconnect()
    pump_until(
        lambda: (
            w.pipeline is not None
            and w.pipeline is not previous
            and w.pipeline.source is not None
        )
    )
    assert not w.pipeline.failure_reported
    w.stop()
    pump_until(lambda: w.pipeline is None)
    assert w.model_store.loads == loads, "Readiness models should be reused"
    w.grab().save(str(root / "docs/evidence/control-panel.png"))
    report = {
        "presets_roundtrip": True,
        "projector_preview": True,
        "configurable_hotkeys": True,
        "microphone_check": microphone_result,
        "compact_controls": True,
        "model_bundle_loads": w.model_store.loads,
        "graceful_stop": True,
        "simulated_disconnect_retry": True,
        "physical_projector_test": "pending",
        "long_caption_layout_and_shrink": True,
    }
    (root / "docs/evidence/workflow-verification.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report), flush=True)
finally:
    if w.pipeline:
        w.stop()
        pump_until(lambda: w.pipeline is None)
    w.close()
    app.processEvents()
