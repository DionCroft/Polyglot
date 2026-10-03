from dataclasses import replace
import pytest
from app.captions.state import Caption
from app.audio.speech_output import PlaybackController
from app.config.settings import Settings


class Backend:
    def __init__(self):
        self.calls = []
        self.callbacks = []
        self.stops = 0
        self.missing = False

    def prepare(self, language, voice, rate, volume):
        if self.missing:
            raise RuntimeError("Install an offline Mandarin voice")
        self.language = language

    def play(self, text, done, error):
        self.calls.append((text, self.language))
        self.callbacks.append((done, error))

    def stop(self):
        self.stops += 1


def caption(i=1, language="en", **kwargs):
    return Caption(
        i,
        i,
        i + 1,
        "Good morning",
        "早上好",
        final=True,
        translation_status="complete",
        source_language=language,
        **kwargs,
    )


@pytest.fixture
def playback():
    backend, notices, now = Backend(), [], [0.0]
    player = PlaybackController(backend, notices.append, clock=lambda: now[0])
    return player, backend, notices, now


def test_off_by_default_and_only_completed_translation_is_spoken(playback):
    p, b, _, _ = playback
    p.accept(caption())
    p.tick()
    assert not b.calls
    p.mode = "auto"
    p.accept(replace(caption(2), final=False))
    p.accept(replace(caption(3), translation_status="pending"))
    p.accept(replace(caption(4), translation_status="unavailable"))
    p.tick()
    assert not b.calls
    p.accept(caption(5))
    p.tick()
    assert b.calls == [("早上好", "zh")]


def test_both_directions_are_ordered_without_duplicate_or_late_playback(playback):
    p, b, _, _ = playback
    p.mode = "auto"
    p.accept(caption(1))
    p.tick()
    p.accept(caption(2, "zh"))
    p.accept(caption(2, "zh"))
    b.callbacks[0][0]()
    p.tick()
    assert b.calls == [("早上好", "zh"), ("Good morning", "en")]
    p.accept(caption(1))
    b.callbacks[1][0]()
    p.tick()
    assert len(b.calls) == 2


def test_playback_backlog_is_bounded_and_obsolete_audio_is_reported(playback):
    p, b, notices, now = playback
    p.mode = "auto"
    for i in range(10):
        p.accept(caption(i))
    assert len(p.pending) == 2
    assert any("skipped" in n for n in notices)
    now[0] = 21
    p.tick()
    assert not b.calls and not p.pending


def test_cancelled_callbacks_cannot_finish_new_playback(playback):
    p, b, _, _ = playback
    p.mode = "auto"
    p.accept(caption())
    p.tick()
    old_done, old_error = b.callbacks[0]
    p.reset()
    p.mode = "auto"
    p.accept(caption())
    p.tick()
    old_done()
    old_error("late error")
    assert p.current is not None
    b.callbacks[1][0]()
    assert p.current is None


def test_manual_playback_prepares_voice_before_pausing_and_can_repeat(playback):
    p, b, notices, _ = playback
    p.mode = "manual"
    p.accept(caption())
    paused = []
    b.missing = True
    assert not p.speak_latest(lambda: paused.append(True))
    assert not paused and "Mandarin" in notices[-1]
    b.missing = False
    assert p.speak_latest(lambda: paused.append(True))
    assert paused == [True]
    b.callbacks[0][0]()
    assert p.speak_latest(lambda: paused.append(True))
    assert len(b.calls) == 2


def test_failed_or_uncertain_turn_cannot_replay_previous_translation(playback):
    p, _, _, _ = playback
    p.mode = "manual"
    p.accept(caption())
    p.accept(replace(caption(2), translation_status="unavailable", chinese=""))
    assert not p.speak_latest(lambda: None)
    p.accept(caption(3))
    p.forget_latest()
    assert p.latest is None


def test_output_error_and_timeout_suspend_automatic_audio_only(playback):
    p, b, notices, now = playback
    p.mode = "auto"
    p.accept(caption())
    p.tick()
    b.callbacks[0][1]("Device unavailable")
    assert p.mode == "manual" and not p.pending
    p.mode = "auto"
    p.accept(caption(2))
    p.tick()
    now[0] = 121
    p.tick()
    assert p.mode == "manual" and p.current is None
    assert any("timed out" in n for n in notices)


def test_off_or_reset_drops_pending_and_latest_from_previous_session(playback):
    p, b, _, _ = playback
    p.mode = "auto"
    p.accept(caption())
    p.tick()
    p.accept(caption(2))
    p.reset()
    assert p.latest is None and not p.pending and p.current is None
    p.tick()
    assert len(b.calls) == 1
    p.mode = "off"
    p.accept(caption(3))
    assert not p.speak_latest(lambda: None)


def test_long_translations_are_not_truncated_into_misleading_speech(playback):
    p, b, notices, _ = playback
    p.mode = "auto"
    p.accept(replace(caption(), chinese="字" * 801))
    p.tick()
    assert not b.calls and any("too long" in n for n in notices)


def test_speech_preferences_are_validated_and_old_settings_remain_off():
    assert Settings.from_dict({}).speech_mode == "off"
    cfg = Settings.from_dict(
        {"speech_mode": "bad", "speech_rate": 900, "speech_volume": -20}
    )
    assert cfg.speech_mode == "off" and cfg.speech_rate == 50 and cfg.speech_volume == 0


def test_voice_selection_never_uses_cantonese_or_wrong_language():
    from app.audio.system_speech import SystemSpeech, voice_language
    from unittest.mock import Mock

    assert voice_language("zh_CN") == "zh"
    assert voice_language("zh_TW") == "zh"
    assert voice_language("zh_HK") is None
    assert voice_language("yue_HK") is None
    assert voice_language("en_IN") == "en"
    backend = SystemSpeech()
    backend.engine = Mock()
    backend._voices = [
        {"id": "en_GB|Test", "language": "en", "locale": "en_GB", "voice": Mock()}
    ]
    with pytest.raises(RuntimeError, match="Mandarin"):
        backend.prepare("zh", "", 0, 80)
    with pytest.raises(RuntimeError, match="no longer installed"):
        backend.prepare("en", "removed", 0, 80)
    backend.engine.say.assert_not_called()
    backend.engine.setVoice.assert_not_called()


def test_pending_audio_does_not_restart_after_user_stops(playback):
    p, b, _, _ = playback
    p.mode = "auto"
    p.accept(caption())
    p.tick()
    p.accept(caption(2))
    old_done = b.callbacks[0][0]
    p.stop()
    p.mode = "manual"
    old_done()
    p.tick()
    assert len(b.calls) == 1 and not p.pending


def test_audio_off_never_initializes_or_downloads_voices(playback):
    p, b, _, _ = playback
    b.missing = True
    for i in range(1000):
        p.accept(caption(i))
        p.tick()
    assert not b.calls and not p.pending and p.latest.identifier == 999
