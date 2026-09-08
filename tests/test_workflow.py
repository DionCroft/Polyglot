from unittest.mock import patch
import pytest
from app.config.settings import Settings
from app.config.presets import Presets
from app.system.shortcuts import parse_shortcut
from app.system.models import ModelStore
from app.captions.display import CaptionDisplay
from app.captions.state import Caption


def test_preset_roundtrip_preserves_teaching_configuration(tmp_path):
    store = Presets(tmp_path / "presets.json")
    settings = Settings(
        lecture_title="Robotics",
        vocabulary="ESP32\n位置",
        microphone="External microphone",
        monitor="PROJECTOR",
        profile="fast",
        glossary="robotics",
    )
    store.save("Morning class", settings)
    assert store.load("Morning class") == settings
    with pytest.raises(ValueError):
        store.save("", settings)


def test_invalid_preset_is_not_silently_overwritten(tmp_path):
    path = tmp_path / "presets.json"
    path.write_text("broken")
    with pytest.raises(ValueError):
        Presets(path).save("class", Settings())
    assert path.read_text() == "broken"


@pytest.mark.parametrize(
    "text", ["A", "Shift+A", "Ctrl+Ctrl+A", "Win+A", "Alt+F13", "Ctrl+Alt+"]
)
def test_unsafe_or_invalid_shortcut_rejected(text):
    with pytest.raises(ValueError):
        parse_shortcut(text)


def test_equivalent_shortcuts_have_same_native_binding():
    assert parse_shortcut("Ctrl+Alt+C") == parse_shortcut("Alt+Ctrl+c")
    assert parse_shortcut("Ctrl+Alt+Shift+F12")[1] == 0x7B


def test_model_store_reuses_verified_bundle_and_reloads_profile(tmp_path):
    with (
        patch("app.asr.qnn_whisper.QnnWhisper") as speech,
        patch("app.translation.opus_mt.OpusMT") as mt,
        patch("app.audio.vad.SileroVAD"),
    ):
        speech.return_value.transcribe.return_value = "test"
        mt.return_value.translate.return_value = "测试"
        store = ModelStore(tmp_path)
        first = store.load("fast")
        second = store.load("fast")
        assert first is second and speech.call_count == 1
        store.load("balanced")
        assert speech.call_count == 2 and store.loads == 2


def test_failed_translation_replaces_stale_chinese_with_current_english():
    display = CaptionDisplay()
    display.accept(Caption(1, 0, 1, "first", "第一", True))
    display.accept(Caption(2, 1, 2, "second", final=True))
    assert display.contents()[1] == "第一"
    display.accept(
        Caption(2, 1, 2, "second", final=True, translation_status="unavailable")
    )
    assert display.contents() == ("second", "", "")
