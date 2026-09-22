"""Real-time WAV conversations through the production pipeline; no microphone use."""

import json
import time
import wave
from pathlib import Path
import numpy as np
from app.system.conversation_self_test import read_audio


def conversation_wav(fixtures, destination):
    parts = []
    for name in ("jfk.wav", "mandarin-1.wav", "jfk.wav"):
        parts.extend([read_audio(Path(fixtures) / name), np.zeros(16000, np.float32)])
    audio = np.concatenate(parts)
    with wave.open(str(destination), "wb") as writer:
        writer.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        writer.writeframes(
            np.rint(np.clip(audio * 32768, -32768, 32767)).astype("<i2").tobytes()
        )
    return len(audio) / 16000


def verify_exports(folder):
    from app.export.transcript import recover_journal

    events = [
        json.loads(line)
        for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    pairs = [c for c in events if c["type"] == "pair"]
    directions = []
    for caption in pairs:
        if not directions or directions[-1] != caption["source_language"]:
            directions.append(caption["source_language"])
        assert caption["english"] and caption["chinese"], caption
    assert directions == ["en", "zh", "en"], directions
    ids = [c["identifier"] for c in pairs]
    assert ids == sorted(set(ids))
    recovered, skipped = recover_journal(
        folder / "events.jsonl", folder.parent / "recovered"
    )
    assert not skipped
    for name in (
        "English.srt",
        "Chinese.srt",
        "Bilingual.vtt",
        "Bilingual Transcript.txt",
    ):
        assert (folder / name).read_bytes() == (recovered / name).read_bytes()
    return {
        "directions": directions,
        "completed_pairs": len(pairs),
        "uncertain_phrases": sum(c["type"] == "uncertain" for c in events),
        "journal_recovery": True,
    }


def run(root, fixtures, report_path):
    from app.config.settings import Settings, DATA
    from app.pipeline import Pipeline
    from app import __version__

    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    wav = report.with_suffix(".wav")
    duration = conversation_wav(fixtures, wav)
    result = {
        "passed": False,
        "version": __version__,
        "physical_microphone_tested": False,
        "classroom_validated": False,
        "audio_seconds": duration,
    }
    events = []
    pipeline = Pipeline(
        root,
        DATA,
        Settings(speaking_language="auto", profile="fast", accelerator="cpu"),
        lambda k, v: events.append((k, v)),
        wav=str(wav),
        force_cpu=True,
    )
    try:
        pipeline.start()
        assert pipeline.started and pipeline.source is not None
        folder = pipeline.export.folder
        pipeline.source.thread.join(duration + 60)
        assert not pipeline.source.thread.is_alive()
        pipeline.close()
        result.update(verify_exports(folder))
        assert not pipeline.failure_reported
        assert (
            pipeline.metrics["dropped_audio_chunks"]
            == pipeline.metrics["dropped_phrases"]
            == pipeline.metrics["translation_skips"]
            == 0
        ), pipeline.metrics
        result.update(passed=True, backend=pipeline.asr.name, metrics=pipeline.metrics)
        return 0
    finally:
        pipeline.close()
        report.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def run_ui(fixtures, report_path):
    from unittest.mock import patch
    from PySide6.QtWidgets import QApplication
    from app.config.settings import Settings
    from app.ui.main_window import MainWindow
    from app.ui.teaching import TeachingControls

    Settings(speaking_language="auto", profile="fast", accelerator="cpu").save()
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    result = {"passed": False, "physical_microphone_tested": False}

    def wait(condition, seconds=180):
        end = time.monotonic() + seconds
        while not condition() and time.monotonic() < end:
            app.processEvents()
            time.sleep(0.01)
        assert condition(), "Auto UI timed out"

    try:
        wait(lambda: not window.checker.is_alive())
        assert window.speaking_language.currentData() == "auto"
        assert window.language_status.isVisible()
        with patch(
            "app.ui.main_window.QInputDialog.getText",
            return_value=("Auto classroom", True),
        ):
            window.save_preset()
        window.speaking_language.setCurrentIndex(0)
        window.load_preset()
        assert window.cfg.speaking_language == "auto"
        wav = report.with_suffix(".wav")
        conversation_wav(fixtures, wav)
        window.wav = str(wav)
        window.start_stop()
        wait(lambda: window.pipeline and window.pipeline.source)
        engine = window.pipeline
        folder = engine.export.folder
        window.teaching = TeachingControls(window)
        window.teaching.show()
        wait(
            lambda: (
                window.last_caption is not None
                and window.last_caption.source_language == "zh"
                and bool(window.last_caption.english)
            )
        )
        assert "translation" in window.preview_en_label.text()
        assert "spoken" in window.preview_zh_label.text()
        assert window.teaching.language.currentData() == "auto"
        document = window.overlay._caption_document(26).toPlainText()
        assert "English · translation" in document and "简体中文 · spoken" in document
        window.mode.setCurrentText("English")
        document = window.overlay._caption_document(26).toPlainText()
        assert (
            "English · translation" in document and "简体中文 · spoken" not in document
        )
        window.mode.setCurrentText("Chinese")
        document = window.overlay._caption_document(26).toPlainText()
        assert (
            "简体中文 · spoken" in document and "English · translation" not in document
        )
        window.mode.setCurrentText("Bilingual")
        window.resize(1060, 860)
        app.processEvents()
        window.grab().save(str(report.with_suffix(".png")))
        window.overlay.grab().save(str(report.with_suffix(".overlay.png")))
        wait(lambda: not engine.source.thread.is_alive())
        # Manual override drains the last captured phrase while preserving the same session.
        window.teaching.language.setCurrentIndex(
            window.teaching.language.findData("en")
        )
        wait(
            lambda: (
                window.cfg.speaking_language == "en" and not engine.switching.is_set()
            )
        )
        assert engine.export.folder == folder
        window.pause()
        window.speaking_language.setCurrentIndex(
            window.speaking_language.findData("auto")
        )
        wait(
            lambda: (
                window.cfg.speaking_language == "auto" and not engine.switching.is_set()
            )
        )
        assert engine.paused.is_set()
        assert window.teaching.language_status.isVisible()
        window.stop()
        wait(lambda: window.pipeline is None)
        result.update(verify_exports(folder))
        window.resize(860, 640)
        app.processEvents()
        assert (
            window.start_button.mapTo(
                window, window.start_button.rect().bottomRight()
            ).y()
            < window.height()
        )
        result.update(
            passed=True,
            auto_preset=True,
            compact_selector=True,
            detected_labels=True,
            single_language_modes=True,
            manual_override=True,
            paused_auto=True,
            minimum_controls_visible=True,
        )
        return 0
    finally:
        window.close()
        wait(lambda: not window.isVisible())
        report.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
