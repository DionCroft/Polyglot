from unittest.mock import patch
import pytest
from app.asr.macos_encoder import verify_trace, PROVIDER
from app.system.models import ModelStore


def test_coreml_proof_requires_executed_nodes_not_just_registration():
    with pytest.raises(RuntimeError):
        verify_trace([{"cat": "Node", "args": {"provider": "CPUExecutionProvider"}}])
    assert verify_trace([{"cat": "Node", "args": {"provider": PROVIDER}}]) == [PROVIDER]
    with pytest.raises(RuntimeError):
        verify_trace([{"cat": "Session", "args": {"provider": PROVIDER}}])


@pytest.mark.parametrize("selection", ["cpu", "auto", "coreml"])
def test_mac_unavailable_accelerator_preserves_profile_and_cpu_choice(
    tmp_path, selection
):
    with (
        patch("app.system.models.is_macos", return_value=True),
        patch("app.system.models.is_x64", return_value=False),
        patch("app.system.models.cpu_profile", return_value="balanced"),
        patch(
            "app.asr.macos_encoder.MacEncoder", side_effect=TimeoutError("timeout")
        ) as worker,
        patch("app.asr.cpu_whisper.CpuWhisper") as cpu,
        patch("app.translation.opus_mt.OpusMT"),
        patch("app.audio.vad.SileroVAD"),
    ):
        bundle = ModelStore(tmp_path).load("balanced", accelerator=selection)
        cpu.assert_called_once_with(tmp_path / "models/whisper/balanced")
        assert not bundle.accelerated and not bundle.npu
        assert worker.call_count == (selection == "coreml")


def test_coreml_does_not_claim_verified_ane_execution(tmp_path):
    with (
        patch("app.system.models.is_macos", return_value=True),
        patch("app.system.models.is_x64", return_value=False),
        patch("app.asr.macos_encoder.MacEncoder"),
        patch("app.asr.cpu_whisper.CpuWhisper"),
        patch("app.translation.opus_mt.OpusMT"),
        patch("app.audio.vad.SileroVAD"),
    ):
        bundle = ModelStore(tmp_path).load("fast")
        assert bundle.accelerated and not bundle.npu


@pytest.mark.skipif(__import__("os").name != "posix", reason="POSIX inherited pipes")
def test_stalled_worker_has_bounded_write_and_closed_worker_fails_fast():
    import os
    import time
    from app.asr.macos_encoder import send, receive

    incoming, outgoing = os.pipe()
    os.set_blocking(outgoing, False)
    try:
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            send(outgoing, b"x" * 2_000_000, started + 0.15)
        assert time.monotonic() - started < 2
    finally:
        os.close(incoming)
        os.close(outgoing)
    incoming, outgoing = os.pipe()
    os.close(outgoing)
    try:
        with pytest.raises(EOFError):
            receive(incoming, time.monotonic() + 0.15)
    finally:
        os.close(incoming)


@pytest.mark.skipif(__import__("os").name != "posix", reason="POSIX inherited pipes")
def test_worker_rejects_oversized_response_without_waiting_for_payload():
    import os
    import struct
    import time
    from app.asr.macos_encoder import receive

    incoming, outgoing = os.pipe()
    try:
        os.write(outgoing, struct.pack("!I", 0xFFFFFFFF))
        with pytest.raises(ValueError, match="Oversized"):
            receive(incoming, time.monotonic() + 0.15)
    finally:
        os.close(incoming)
        os.close(outgoing)
