"""Isolated live-pipeline/voice experiment; no physical microphone or audible output."""

import json
import os
import time
import wave
from pathlib import Path

import numpy as np
from PySide6.QtWidgets import QApplication

if not os.environ.get("LECTURELIVE_DATA"):
    raise SystemExit(
        "Set LECTURELIVE_DATA to an isolated test folder before this replay; it saves test preferences."
    )
from app import __version__
from app.config.settings import Settings
from app.export.transcript import recover_journal
from app.system.conversation_self_test import read_audio
from app.system.offline import enforce_offline
from app.ui.main_window import MainWindow

enforce_offline()
art = Path("tests/artifacts")
art.mkdir(parents=True, exist_ok=True)
audio = read_audio(Path("tests/fixtures/mandarin-1.wav"))
stream = np.concatenate(
    [part for _ in range(3) for part in (audio, np.zeros(16000, np.float32))]
)
wav = art / "spoken-072-live-mandarin.wav"
with wave.open(str(wav), "wb") as writer:
    writer.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
    writer.writeframes(
        np.rint(stream * 32768).clip(-32768, 32767).astype("<i2").tobytes()
    )
app = QApplication([])
Settings(speaking_language="zh", profile="fast", speech_volume=0).save()
window = MainWindow()
window.show()
max_queue = 0


def pump():
    global max_queue
    app.processEvents()
    max_queue = max(max_queue, len(window.spoken.player.pending))
    assert len(window.spoken.player.pending) <= 2
    time.sleep(0.01)


def wait(condition, timeout=180):
    end = time.monotonic() + timeout
    while not condition() and time.monotonic() < end:
        pump()
    assert condition(), "Replay timed out"


result = {
    "passed": False,
    "version": __version__,
    "physical_microphone_tested": False,
    "sound_heard_by_human": False,
    "runs": [],
}
try:
    wait(lambda: not window.checker.is_alive())
    for rate in (0, -50):
        max_queue = 0
        panel = window.spoken
        panel.mode.setCurrentIndex(2)
        panel.volume.setValue(0)
        panel.rate.setValue(rate)
        window.wav = str(wav)
        window.start_stop()
        panel.headphones.setChecked(True)
        started, completed, notices = [], [], []
        backend = panel.player.backend
        play = backend.play
        notify = panel.player.notify

        def observe_play(
            text,
            done,
            error,
            *,
            panel=panel,
            started=started,
            completed=completed,
            play=play,
        ):
            identifier = panel.player.current[0].identifier
            started.append(identifier)

            def finished():
                completed.append(identifier)
                done()

            play(text, finished, error)

        def observe_notice(message, *, notices=notices, notify=notify):
            notices.append(message)
            notify(message)

        backend.play = observe_play
        panel.player.notify = observe_notice
        try:
            wait(
                lambda: (
                    window.pipeline.source is not None
                    and not window.pipeline.source.thread.is_alive()
                )
            )
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                pump()
            wait(
                lambda panel=panel: (
                    panel.player.current is None and not panel.player.pending
                )
            )
            assert panel.player.mode == "auto", notices
            metrics = window.pipeline.diagnostics()
            assert (
                metrics["dropped_audio_chunks"]
                == metrics["dropped_phrases"]
                == metrics["translation_skips"]
                == 0
            ), metrics
            folder = window.pipeline.export.folder
            window.stop()
            wait(lambda: window.pipeline is None)
            recovered, skipped = recover_journal(
                folder / "events.jsonl", folder.parent / "verified-recovery"
            )
            assert skipped == 0
            for name in (
                "English Transcript.txt",
                "Chinese Transcript.txt",
                "Bilingual Transcript.txt",
                "English.srt",
                "Chinese.srt",
                "Bilingual.vtt",
            ):
                assert (folder / name).read_bytes() == (
                    recovered / name
                ).read_bytes(), name
            assert started and started == sorted(set(started)) and completed == started
            events = [
                json.loads(line)
                for line in (folder / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            result["runs"].append(
                {
                    "rate": rate,
                    "audio_seconds": len(stream) / 16000,
                    "speech_started": started,
                    "speech_completed": completed,
                    "maximum_waiting_audio": max_queue,
                    "notices": notices,
                    "metrics": metrics,
                    "completed_caption_pairs": sum(e["type"] == "pair" for e in events),
                    "six_exports_recovered": True,
                }
            )
            print(
                "Rate",
                rate,
                "passed:",
                len(started),
                "spoken translations; max queue",
                max_queue,
                flush=True,
            )
        finally:
            backend.play = play
            panel.player.notify = notify
    result["passed"] = True
finally:
    window.close()
    wait(lambda: not window.isVisible())
    (art / "spoken-072-live-auto.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
