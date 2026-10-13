"""Native/frozen sharing controls, observer, QR and helper lifecycle smoke test.

Uses explicit text fixtures, never a microphone or changed user settings.
"""

import json
import time
from pathlib import Path
from types import SimpleNamespace


def run(report_path):
    from PySide6.QtWidgets import QApplication
    from app.config.settings import DATA, ROOT, Settings
    from app.pipeline import Pipeline
    from app.captions.state import Caption
    from app.export.transcript import Transcript
    from app.sharing.history import Database
    from app.ui.phone_sharing import PhoneSharing

    app = QApplication.instance() or QApplication([])
    warnings = []
    owner = SimpleNamespace(pipeline=None, warn=warnings.append)
    panel = PhoneSharing(owner)
    panel.resize(800, 820)
    panel.show()
    result = {"passed": False, "physical_phones_tested": False}

    def wait(condition, timeout=20):
        end = time.monotonic() + timeout
        while not condition() and time.monotonic() < end:
            app.processEvents()
            panel.tick()
            time.sleep(0.02)
        assert condition(), "Phone controls timed out: " + panel.status.text()

    try:
        assert panel.session is None and not panel.link.text()
        p = Pipeline(
            ROOT, DATA, Settings(), lambda *a: None, caption_sink=panel.capture
        )
        p.export = Transcript(DATA, "Phone smoke fixture")
        owner.pipeline = p
        first = Caption(
            1, 0, 3, "Before sharing", "完整译文", True, translation_status="complete"
        )
        p._save("pair", first)
        panel.start_sharing("127.0.0.1")
        wait(lambda: bool(panel.link.text()))
        session = panel.session
        old_url = panel.link.text()
        assert not panel.qr.pixmap().isNull()
        panel.qr.pixmap().save(str(Path(report_path).with_suffix(".qr.png")))
        pending = Caption(2, 3, 6, "A long explanation. " * 150, "", True)
        p._save("english", pending)
        p.paused.set()
        p.epoch += 1
        from dataclasses import replace

        complete = replace(
            pending, chinese="长段落译文。" * 150, translation_status="complete"
        )
        p._save("pair", complete)
        p._save(
            "pair",
            Caption(
                3,
                7,
                9,
                "A Mandarin question",
                "请再解释一次。",
                True,
                source_language="zh",
                translation_status="complete",
            ),
        )
        panel.state("Paused")
        assert session.history.flush()
        with Database(session.history.path) as db:
            rows = db.page()["entries"]
            assert [r["identifier"] for r in rows] == [1, 2, 3]
            assert rows[1]["chinese"] == complete.chinese
            assert "earlier saved" in db.meta()["coverage"]
        panel.grab().save(str(Path(report_path).with_suffix(".png")))
        p.export.close()
        owner.pipeline = None
        panel.state("Lecture ended")
        assert session.history.flush()
        panel.begin_lecture()
        assert panel.session is None  # New lecture explicitly revokes old sharing.
        wait(lambda: panel.cleaner is None)
        assert session.process.poll() is not None and not session.folder.exists()
        panel.start_sharing("127.0.0.1")
        wait(lambda: bool(panel.link.text()))
        assert panel.link.text() != old_url
        with Database(panel.session.history.path) as db:
            assert db.meta()["count"] == 0
        assert not warnings, warnings
        result.update(
            passed=True,
            default_off=True,
            journal_bootstrap=True,
            late_pair_during_pause=True,
            bilingual_long_text=True,
            qr_generated=True,
            new_lecture_revokes_link=True,
            history_removed=True,
            new_link_empty_history=True,
            helper_process_started=True,
        )
        return 0
    finally:
        panel.stop_sharing()
        wait(lambda: panel.cleaner is None)
        panel.close()
        Path(report_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
