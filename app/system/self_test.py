import json, time, wave
from pathlib import Path
import numpy as np
from app.asr.qnn_whisper import QnnWhisper
from app.asr.cpu_whisper import CpuWhisper
from app.translation.opus_mt import OpusMT
from app.system.readiness import check
from app.system.architecture import is_x64


def run(root, wav_path, report_path):
    from app.system.architecture import is_macos

    if is_macos():
        from app.system.macos_self_test import run as run_mac

        return run_mac(root, wav_path, report_path)
    from app import __version__

    result = {
        "version": __version__,
        "architecture": "x64" if is_x64() else "ARM64",
        "startup": check(root, "fast" if is_x64() else "balanced"),
        "speech": [],
    }
    from app.captions.glossary import Glossary

    course = json.loads(
        (root / "assets/co7000-vocabulary.json").read_text(encoding="utf-8")
    )
    glossary = Glossary(root / "glossaries/project_management.json")
    if (
        len(course["lists"]) != 12
        or glossary.english("N P V and T C P I") != "NPV and TCPI"
    ):
        raise RuntimeError("Packaged course vocabulary verification failed")
    result["course_vocabulary"] = {
        "weeks": 12,
        "glossary_terms": len(glossary.entries),
        "passed": True,
    }
    with wave.open(str(wav_path)) as f:
        if f.getframerate() != 16000 or f.getsampwidth() != 2 or f.getnchannels() != 1:
            raise ValueError("Self-test requires mono 16 kHz 16-bit PCM WAV")
        audio = (
            np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32)
            / 32768
        )
    profiles = (
        [("cpu", CpuWhisper)]
        if is_x64()
        else [
            ("fast", QnnWhisper),
            ("balanced", QnnWhisper),
            ("cpu", CpuWhisper),
        ]
    )
    for profile, cls in profiles:
        model = cls(root / "models/whisper" / ("fast" if profile == "cpu" else profile))
        t = time.perf_counter()
        text = model.transcribe(audio)
        elapsed = time.perf_counter() - t
        result["speech"].append(
            {"profile": profile, "english": text, "seconds": elapsed}
        )
        if not text:
            raise RuntimeError("No speech output")
        model.configure_recognition("careful", "country\nAmericans")
        guided = model.transcribe(audio)
        if not guided or model.transcribe(np.zeros(16000, np.float32)):
            raise RuntimeError("Guided speech or silence verification failed")
        result["speech"].append({"profile": profile + "-guided", "english": guided})
        del model
    if is_x64() and result["startup"].get("accelerated"):
        from app.system.models import ModelStore

        store = ModelStore(root)
        try:
            bundle = store.load("fast")
            if not bundle.accelerated:
                raise RuntimeError("Previously verified accelerator became unavailable")
            t = time.perf_counter()
            text = bundle.asr.transcribe(audio)
            if not text:
                raise RuntimeError("No accelerated speech output")
            result["speech"].append(
                {
                    "profile": "accelerated",
                    "backend": bundle.asr.name,
                    "english": text,
                    "seconds": time.perf_counter() - t,
                }
            )
            bundle.asr.configure_recognition("careful", "country\nAmericans")
            guided = bundle.asr.transcribe(audio)
            if not guided:
                raise RuntimeError("Guided accelerator verification failed")
            result["speech"].append(
                {"profile": "accelerated-guided", "english": guided}
            )
        finally:
            store.close()
    translator = OpusMT(root / "models/translation/opus")
    t = time.perf_counter()
    text = translator.translate(
        "The interrupt service routine should execute as quickly as possible."
    )
    result["translation"] = {"chinese": text, "seconds": time.perf_counter() - t}
    result["passed"] = all(
        result["startup"][k]
        for k in (
            ["speech", "translation", "vad"]
            if is_x64()
            else ["speech", "translation", "vad", "npu"]
        )
    ) and bool(text)
    Path(report_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0 if result["passed"] else 1
