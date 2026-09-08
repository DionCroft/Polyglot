import json, time, wave
from pathlib import Path
import numpy as np
from app.asr.qnn_whisper import QnnWhisper
from app.asr.cpu_whisper import CpuWhisper
from app.translation.opus_mt import OpusMT
from app.system.readiness import check


def run(root, wav_path, report_path):
    from app import __version__
    result = {"version": __version__, "startup": check(root, "balanced"), "speech": []}
    with wave.open(str(wav_path)) as f:
        if f.getframerate() != 16000 or f.getsampwidth() != 2 or f.getnchannels() != 1:
            raise ValueError("Self-test requires mono 16 kHz 16-bit PCM WAV")
        audio = (
            np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32)
            / 32768
        )
    for profile, cls in [
        ("fast", QnnWhisper),
        ("balanced", QnnWhisper),
        ("cpu", CpuWhisper),
    ]:
        model = cls(root / "models/whisper" / ("fast" if profile == "cpu" else profile))
        t = time.perf_counter()
        text = model.transcribe(audio)
        elapsed = time.perf_counter() - t
        result["speech"].append(
            {"profile": profile, "english": text, "seconds": elapsed}
        )
        if not text:
            raise RuntimeError("No speech output")
        del model
    translator = OpusMT(root / "models/translation/opus")
    t = time.perf_counter()
    text = translator.translate(
        "The interrupt service routine should execute as quickly as possible."
    )
    result["translation"] = {"chinese": text, "seconds": time.perf_counter() - t}
    result["passed"] = all(
        result["startup"][k] for k in ["speech", "translation", "vad", "npu"]
    ) and bool(text)
    Path(report_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0 if result["passed"] else 1
