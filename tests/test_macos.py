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


def test_permission_denied_never_starts_capture_and_pending_request_is_not_duplicated():
    from types import SimpleNamespace
    from PySide6.QtCore import Qt
    from app.system.permissions import microphone_permission

    window = SimpleNamespace(warn=Mock(), closing=False)
    resume = Mock()
    with (
        patch("app.system.permissions.is_macos", return_value=True),
        patch("PySide6.QtWidgets.QApplication.instance") as instance,
    ):
        app = instance.return_value
        app.checkPermission.return_value = Qt.PermissionStatus.Denied
        assert not microphone_permission(window, resume)
        app.requestPermission.assert_not_called()
        resume.assert_not_called()
        assert "Microphone" in window.warn.call_args.args[0]
        app.checkPermission.return_value = Qt.PermissionStatus.Undetermined
        assert not microphone_permission(window, resume)
        assert not microphone_permission(window, resume)
        app.requestPermission.assert_called_once()
        callback = app.requestPermission.call_args.args[2]
        denied = Mock()
        denied.status.return_value = Qt.PermissionStatus.Denied
        callback(denied)
        assert not window.microphone_permission_pending
        resume.assert_not_called()


def test_permission_grant_resumes_once_and_late_grant_cannot_reopen_closed_window():
    from types import SimpleNamespace
    from PySide6.QtCore import Qt
    from app.system.permissions import microphone_permission

    window = SimpleNamespace(warn=Mock(), closing=False)
    resume = Mock()
    with (
        patch("app.system.permissions.is_macos", return_value=True),
        patch("PySide6.QtWidgets.QApplication.instance") as instance,
        patch(
            "PySide6.QtCore.QTimer.singleShot",
            side_effect=lambda delay, action: action(),
        ),
    ):
        app = instance.return_value
        app.checkPermission.return_value = Qt.PermissionStatus.Undetermined
        assert not microphone_permission(window, resume)
        callback = app.requestPermission.call_args.args[2]
        granted = Mock()
        granted.status.return_value = Qt.PermissionStatus.Granted
        callback(granted)
        resume.assert_called_once()
        resume.reset_mock()
        window.closing = True
        callback(granted)
        resume.assert_not_called()


def test_mac_runtime_fallback_keeps_small_careful_and_vocabulary(tmp_path):
    import numpy as np
    from app.pipeline import Pipeline
    from app.config.settings import ROOT, Settings

    settings = Settings(
        profile="balanced",
        recognition_mode="careful",
        vocabulary_guidance=True,
        vocabulary="NPV\nTCPI",
        glossary="project_management",
    )
    pipeline = Pipeline(
        ROOT, tmp_path, settings, lambda *event: None, vocabulary=settings.vocabulary
    )
    pipeline.accelerated = True
    pipeline.asr = Mock()
    pipeline.asr.transcribe.side_effect = TimeoutError("Core ML stalled")
    audio = np.zeros(16000, np.float32)
    with (
        patch("app.system.architecture.is_macos", return_value=True),
        patch("app.asr.cpu_whisper.CpuWhisper") as cpu,
    ):
        cpu.return_value.transcribe.return_value = "NPV and TCPI"
        assert pipeline._transcribe(audio, final=False) == "NPV and TCPI"
        cpu.assert_called_once_with(ROOT / "models/whisper/balanced")
        mode, vocabulary = cpu.return_value.configure_recognition.call_args.args
        assert mode == "careful" and "NPV" in vocabulary
        assert cpu.return_value.final_pass is False
        assert cpu.return_value.transcribe.call_args.args[0] is audio
