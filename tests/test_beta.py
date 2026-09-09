import json
from unittest.mock import patch, Mock
import numpy as np
import pytest
from app.system.accelerators import verify_trace, candidates, read_registry
from app.system.models import ModelStore
from app.config.settings import Settings


def test_acceleration_requires_executed_provider_without_cpu_work():
    def event(provider):
        return {"cat": "Node", "args": {"provider": provider}}

    verify_trace([event("DmlExecutionProvider")], "DmlExecutionProvider")
    for trace in (
        [],
        [event("CPUExecutionProvider")],
        [event("DmlExecutionProvider"), event("CPUExecutionProvider")],
    ):
        with pytest.raises(RuntimeError):
            verify_trace(trace, "DmlExecutionProvider")


def test_auto_only_tries_prepared_npus_and_gpu(tmp_path):
    path = tmp_path / "acceleration.json"
    with patch("app.system.accelerators.registry_path", return_value=path):
        assert candidates("auto") == ["gpu"]
        path.write_text(json.dumps({"version": 1, "providers": {"intel_npu": {}}}))
        assert candidates("auto") == ["intel_npu", "gpu"]
        assert candidates("cpu") == []
        path.write_text("broken")
        assert read_registry() == {}


def test_npu_failure_is_cpu_not_false_npu_success(tmp_path):
    with (
        patch("app.system.models.is_x64", return_value=True),
        patch(
            "app.asr.encoder_worker.EncoderWorker",
            side_effect=RuntimeError("driver missing"),
        ),
        patch("app.asr.cpu_whisper.CpuWhisper") as cpu,
        patch("app.translation.opus_mt.OpusMT"),
        patch("app.audio.vad.SileroVAD"),
    ):
        store = ModelStore(tmp_path)
        bundle = store.load("fast", accelerator="intel_npu")
        assert bundle.asr is cpu.return_value
        assert not bundle.npu and not bundle.accelerated
        assert any("driver missing" in message for message in bundle.messages)
        store.close()
        cpu.return_value.close.assert_called_once()


def test_beta_gpu_cache_is_reused_and_closed_on_selection_change(tmp_path):
    with (
        patch("app.system.models.is_x64", return_value=True),
        patch("app.asr.encoder_worker.EncoderWorker") as worker,
        patch("app.asr.cpu_whisper.CpuWhisper") as cpu,
        patch("app.translation.opus_mt.OpusMT"),
        patch("app.audio.vad.SileroVAD"),
    ):
        store = ModelStore(tmp_path)
        bundle = store.load("fast", accelerator="gpu")
        assert bundle.accelerated and not bundle.npu
        assert store.load("fast", accelerator="gpu") is bundle
        assert worker.call_count == 1
        store.load("fast", accelerator="cpu")
        cpu.return_value.close.assert_called_once()
        store.close()


def test_gpu_runtime_failure_retries_same_phrase_on_cpu(tmp_path):
    from app.pipeline import Pipeline
    from app.config.settings import ROOT

    events = []
    pipeline = Pipeline(
        ROOT, tmp_path, Settings(profile="fast"), lambda *event: events.append(event)
    )
    failed = Mock()
    failed.transcribe.side_effect = TimeoutError("GPU timeout")
    pipeline.asr = failed
    pipeline.accelerated = True
    samples = np.zeros(16000, np.float32)
    with patch("app.asr.cpu_whisper.CpuWhisper") as cpu:
        cpu.return_value.transcribe.return_value = "Retried phrase"
        assert pipeline._transcribe(samples) == "Retried phrase"
        assert cpu.return_value.transcribe.call_args.args[0] is samples
    assert not pipeline.accelerated and not pipeline.using_npu
    failed.close.assert_called_once()
    assert any(kind == "warning" for kind, value in events)


def test_beta_settings_normalize_profile_and_accelerator():
    with patch("app.config.settings.is_x64", return_value=True):
        cfg = Settings.from_dict({"profile": "balanced", "accelerator": "invalid"})
        assert cfg.profile == "fast" and cfg.accelerator == "auto"
