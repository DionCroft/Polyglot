"""Native UI checks for onboarding, contact details and bundled offline help."""
import json, os, time
from pathlib import Path
root = Path(__file__).resolve().parents[1]
os.environ["LECTURELIVE_DATA"] = str(root / "tests/polish-data")
from app.system.offline import enforce_offline
enforce_offline()
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QUrl
from app.ui.main_window import MainWindow
from app.ui.help import GuideDialog
from app.author import NAME, EMAIL, COURSES, QUALIFICATIONS
app = QApplication([])
w = MainWindow()
w.show()
def pump_until(condition, seconds=40):
    deadline = time.monotonic() + seconds
    while not condition() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert condition(), "UI did not become ready"
try:
    pump_until(lambda: not w.checker.is_alive())
    app.processEvents()
    assert "Ready" in w.status.text()
    assert not w.windowIcon().isNull()
    w.resize(1060,860)
    app.processEvents()
    w.grab().save(str(root / "docs/evidence/control-panel-0.3.png"))
    w.resize(860,640)
    app.processEvents()
    for control in [w.start_button, w.pause_button, w.compact_button]:
        point = control.mapTo(w, control.rect().bottomRight())
        assert point.y() < w.height() and point.x() < w.width()
    w.grab().save(str(root / "docs/evidence/compact-layout-0.3.png"))
    w.resize(1060,860)
    w.tabs.setCurrentIndex(3)
    app.processEvents()
    text = "\n".join(label.text() for label in w.tabs.currentWidget().findChildren(QLabel))
    assert all(value in text for value in [NAME, EMAIL, QUALIFICATIONS, *COURSES])
    w.grab().save(str(root / "docs/evidence/about-0.3.png"))
    w.show_guide()
    app.processEvents()
    guide = w.guide_dialog
    assert "Your first lecture" in guide.browser.toPlainText()
    guide.grab().save(str(root / "docs/evidence/quick-start-0.3.png"))
    guide.open_link(QUrl("USER_GUIDE.md"))
    assert "Teaching with LectureLive" in guide.browser.toPlainText()
    guide.pages.setCurrentIndex(2)
    app.processEvents()
    assert "double-click setup" in guide.browser.toPlainText()
    guide.close()
    missing = GuideDialog(root / "tests/artifacts/missing-help", w)
    assert "guide is missing" in missing.browser.toPlainText()
    missing.close()
    result = {"version":"0.3.0", "native_ready":True, "contact_details_present":True, "minimum_window_controls_visible":True, "offline_quick_start":True, "relative_help_navigation":True, "installation_help":True, "missing_help_message":True, "custom_icon":True}
    (root / "docs/evidence/polish-0.3.json").write_text(json.dumps(result, indent=2),encoding="utf-8")
    print(json.dumps(result))
finally:
    w.close()
    app.processEvents()
