"""Exercise beta controls with synthetic audio and isolated preferences."""

import os
import time
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.environ["LECTURELIVE_DATA"] = str(root / "tests/beta-ui-data")
from app.system.offline import enforce_offline

enforce_offline()
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

app = QApplication([])
w = MainWindow()
w.show()


def wait(condition, seconds=60):
    deadline = time.monotonic() + seconds
    while not condition() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert condition(), "Beta UI timed out"


try:
    wait(lambda: w.checker is not None and not w.checker.is_alive())
    app.processEvents()
    assert "Beta" in w.windowTitle()
    assert w.profile.count() == 1 and w.profile.currentData() == "fast"
    assert w.accelerator.count() == 5
    assert w.model_store.bundle.accelerated, "Expected real DirectML on this test PC"
    warmed = w.model_store.bundle
    w.apply_shortcuts()
    assert w.model_store.bundle is warmed, "Shortcut updates must preserve the warmed speech worker"
    w.grab().save(str(root / "tests/artifacts/beta-ui.png"))
    w.accelerator.setCurrentIndex(w.accelerator.findData("gpu"))
    w.save.setChecked(False)
    w.wav = str(root / "tests/fixtures/technical-0.wav")
    w.start_stop()
    wait(lambda: w.pipeline is not None and w.pipeline.started)
    assert not w.accelerator.isEnabled()
    wait(lambda: w.last_caption is not None, 90)
    caption = w.last_caption.english
    w.stop()
    wait(lambda: w.pipeline is None, 90)
    assert w.accelerator.isEnabled()
    report = {
        "beta_title": w.windowTitle(),
        "profiles": w.profile.count(),
        "hardware_choices": w.accelerator.count(),
        "synthetic_caption": caption,
        "passed": True,
    }
    (root / "tests/artifacts/beta-ui.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report))
finally:
    w.close()
    wait(lambda: not w.isVisible(), 90)
