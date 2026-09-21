import json
from unittest.mock import Mock, patch
import pytest
from app.system.architecture import data_directory, is_x64
from app.system.macos import parse_shortcut
from app.audio.capture import microphones


def test_apple_silicon_is_not_windows_beta(monkeypatch, tmp_path):
    monkeypatch.setattr("app.system.architecture.sys.platform", "darwin")
    monkeypatch.setattr("app.system.architecture.platform.machine", lambda: "arm64")
    monkeypatch.delenv("LECTURELIVE_DATA", raising=False)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    assert not is_x64()
    assert data_directory() == tmp_path / "Library/Application Support/LectureLive"
    monkeypatch.setenv("LECTURELIVE_DATA", str(tmp_path / "test"))
    assert data_directory() == tmp_path / "test"


def test_mac_shortcuts_are_native_and_modifier_aliases_agree():
    assert (
        parse_shortcut("Cmd+Option+C") == parse_shortcut("Alt+Command+c") == (2304, 8)
    )
    assert parse_shortcut("Ctrl+Alt+Space") == (6144, 49)
    assert parse_shortcut("Cmd+Shift+F12") == (768, 111)
    assert parse_shortcut("Cmd+7")[1] == 26
    assert parse_shortcut("Cmd+8")[1] == 28
    for text in ("A", "Shift+A", "Ctrl+Control+A", "Win+A", "Cmd+F13"):
        with pytest.raises(ValueError):
            parse_shortcut(text)


def test_mac_microphone_discovery_uses_core_audio():
    with (
        patch("app.audio.capture.is_macos", return_value=True),
        patch(
            "app.audio.capture.sd.query_hostapis",
            return_value=[{"name": "Core Audio"}, {"name": "MME"}],
        ),
        patch(
            "app.audio.capture.sd.query_devices",
            return_value=[
                {
                    "name": "MacBook Air Microphone",
                    "hostapi": 0,
                    "max_input_channels": 1,
                },
                {"name": "Legacy", "hostapi": 1, "max_input_channels": 1},
                {"name": "Speakers", "hostapi": 0, "max_input_channels": 0},
            ],
        ),
    ):
        assert microphones() == [(0, "MacBook Air Microphone", "Core Audio")]


def test_mac_cpu_fallback_uses_selected_small_profile(tmp_path):
    from app.system.models import ModelStore

    with (
        patch("app.system.models.is_macos", return_value=True),
        patch("app.system.models.is_x64", return_value=False),
        patch("app.system.models.cpu_profile", return_value="balanced"),
        patch("app.asr.cpu_whisper.CpuWhisper") as cpu,
        patch("app.asr.qnn_whisper.QnnWhisper") as qnn,
        patch("app.translation.opus_mt.OpusMT"),
        patch("app.audio.vad.SileroVAD"),
    ):
        bundle = ModelStore(tmp_path).load("balanced", force_cpu=True)
        cpu.assert_called_once_with(tmp_path / "models/whisper/balanced")
        qnn.assert_not_called()
        assert not bundle.npu
