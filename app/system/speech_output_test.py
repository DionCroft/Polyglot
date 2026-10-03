"""Exercise speech UI without capture, plus muted real system-voice playback."""

import json
import threading
import time
from pathlib import Path
from unittest.mock import patch


def run(report_path):
    from PySide6.QtWidgets import QApplication
    from app.captions.state import Caption
    from app.config.settings import Settings
    from app.ui.main_window import MainWindow
    from app.ui.teaching import TeachingControls
    from app.audio.system_speech import SystemSpeech
    from app import __version__

    app = QApplication.instance() or QApplication([])
    Settings(speech_mode="auto").save()
    result = {
        "passed": False,
        "version": __version__,
        "physical_microphone_tested": False,
        "sound_heard_by_human": False,
        "voice_quality_validated": False,
    }

    def wait(condition, seconds=20):
        deadline = time.monotonic() + seconds
        while not condition() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert condition(), "Spoken audio check timed out"

    class FakeSpeech:
        def __init__(self):
            self.calls = []
            self.done = None

        def voices(self, refresh=False):
            return [
                {"id": code, "name": "Test fixture", "locale": code, "language": lang}
                for code, lang in (("en_GB", "en"), ("zh_CN", "zh"))
            ]

        def prepare(self, language, voice, rate, volume):
            self.language = language

        def play(self, text, done, error):
            self.calls.append((text, self.language))
            self.done = done

        def stop(self):
            pass

    class Session:
        def __init__(self, window):
            self.window = window
            self.loading = False
            self.started = True
            self.paused, self.switching, self.stop_event = (
                threading.Event() for _ in range(3)
            )
            self.epoch = 0
            self.level = 0

        def pause(self):
            self.epoch += 1
            self.paused.clear() if self.paused.is_set() else self.paused.set()
            self.window.on_event(
                "state", "Paused" if self.paused.is_set() else "Listening"
            )

        def request_stop(self):
            self.stop_event.set()

        def close(self):
            self.started = False

        def diagnostics(self):
            return {"test_fixture": True}

    with patch.object(MainWindow, "check_local_models", lambda self: None):
        window = MainWindow()
    window.show()
    window.tabs.setCurrentWidget(window.spoken)
    wait(lambda: not window.checker.is_alive())
    native = SystemSpeech(window)
    try:
        voices = native.voices()
        result["native_engine"] = native.engine_name
        result["installed_voices"] = [
            {k: v for k, v in item.items() if k != "voice"} for item in voices
        ]
        result["native_muted_playback"] = []
        result["missing_voice_languages"] = []
        for language, text in (
            ("en", "Welcome to the lecture."),
            ("zh", "欢迎参加今天的讲座。"),
        ):
            if not any(v["language"] == language for v in voices):
                result["missing_voice_languages"].append(language)
                continue
            native.prepare(language, "", 0, 0)
            finished, errors = [], []
            native.play(text, lambda: finished.append(True), errors.append)
            wait(lambda: finished or errors)
            assert not errors, errors
            result["native_muted_playback"].append(language)
        # Exercise native cancellation and immediate reuse, not only a mock.
        if result["native_muted_playback"]:
            language = result["native_muted_playback"][0]
            native.prepare(language, "", 0, 0)
            cancelled, errors = [], []
            native.play(
                ("Hello. " if language == "en" else "你好。") * 40,
                lambda: cancelled.append(True),
                errors.append,
            )
            wait(lambda: native._began or errors)
            assert not errors
            native.stop()
            finished = []
            native.play(
                "Ready." if language == "en" else "准备好了。",
                lambda: finished.append(True),
                errors.append,
            )
            wait(lambda: finished or errors)
            assert not errors and not cancelled
            result["native_stop_and_reuse"] = True
        native.stop()
        panel, fake = window.spoken, FakeSpeech()
        panel.player.backend = fake
        session = window.pipeline = Session(window)
        window.teaching = TeachingControls(window)
        assert panel.player.mode == "off"
        panel.mode.setCurrentIndex(1)

        def emit(i, source="en", final=True, status="complete"):
            value = Caption(
                i,
                i,
                i + 1,
                "Please explain the project risks.",
                "请解释项目风险。",
                final,
                session.epoch,
                status,
                source,
            )
            window.on_event("caption", value)
            return value

        emit(1)
        window.speech_hotkey()
        assert session.paused.is_set() and fake.calls[-1][1] == "zh"
        assert "Resume" in panel.status.text()
        fake.done()
        window.pause()
        assert not session.paused.is_set() and panel.player.latest is None
        emit(2, "zh")
        window.speak_translation()
        assert fake.calls[-1][1] == "en" and session.paused.is_set()
        window.pause()
        panel.mode.setCurrentIndex(2)
        emit(3)
        panel.tick()
        assert len(fake.calls) == 2, "Auto must wait for headphone confirmation"
        panel.headphones.setChecked(True)
        emit(4, final=False)
        panel.tick()
        emit(4, status="pending")
        panel.tick()
        assert len(fake.calls) == 2
        emit(4)
        panel.tick()
        assert len(fake.calls) == 3
        emit(4)
        panel.tick()
        assert not panel.player.pending
        old_done = fake.done
        window.on_event("language", "zh")
        assert panel.player.current is None and panel.player.latest is None
        old_done()
        emit(5, "zh")
        panel.tick()
        assert len(fake.calls) == 4
        window.pause()
        assert panel.player.current is None and not panel.player.pending
        window.pause()
        emit(6)
        panel.tick()
        window.speech_hotkey()
        assert panel.mode.currentData() == "manual" and panel.player.current is None
        panel.mode.setCurrentIndex(2)
        emit(7)
        panel.tick()
        window.stop()
        emit(8)
        assert panel.player.current is None and not panel.player.pending
        wait(lambda: window.pipeline is None)
        panel.new_session()
        assert not panel.headphones.isChecked()
        panel.mode.setCurrentIndex(1)
        panel.player.backend = native
        panel.refresh_voices()
        window.resize(1060, 860)
        app.processEvents()
        window.grab().save(str(Path(report_path).with_suffix(".png")))
        window.teaching.show()
        panel.sync()
        app.processEvents()
        window.teaching.grab().save(str(Path(report_path).with_suffix(".teaching.png")))
        window.resize(860, 640)
        app.processEvents()
        assert (
            window.start_button.mapTo(
                window, window.start_button.rect().bottomRight()
            ).y()
            < window.height()
        )
        panel.show_help()
        assert window.guide_dialog.pages.currentData() == "SPOKEN_AUDIO.md"
        window.guide_dialog.close()
        result.update(
            passed=True,
            mock_ui_lifecycle=True,
            manual_pauses_listening=True,
            automatic_requires_headphones=True,
            both_directions=True,
            final_only=True,
            duplicate_suppression=True,
            pause_resume=True,
            language_switch_cancels=True,
            stop_cancels=True,
            late_events_ignored=True,
            speak_stop_shortcut=True,
            minimum_controls_visible=True,
            in_app_guide=True,
        )
        return 0
    finally:
        native.stop()
        window.close()
        wait(lambda: not window.isVisible())
        Path(report_path).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
