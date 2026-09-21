"""Real native inference checks; records fallback separately from acceleration."""

import gc
import json
import platform
import time
import wave
from pathlib import Path
import numpy as np
from app.system.models import ModelStore


def run(root, wav_path, report_path):
    from app import __version__
    from app.captions.glossary import Glossary

    course = json.loads((root / "assets/co7000-vocabulary.json").read_text())
    glossary = Glossary(root / "glossaries/project_management.json")
    assert len(course["lists"]) == 12
    assert glossary.english("N P V and T C P I") == "NPV and TCPI"
    with wave.open(str(wav_path)) as wav:
        assert (wav.getnchannels(), wav.getframerate(), wav.getsampwidth()) == (
            1,
            16000,
            2,
        )
        audio = (
            np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(
                np.float32
            )
            / 32768
        )
    result = {
        "version": __version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "course_vocabulary": {"weeks": 12, "terms": len(glossary.entries)},
        "speech": [],
        "physical_microphone_tested": False,
        "m2_tested": False,
        "passed": False,
    }
    try:
        for profile in ("fast", "balanced"):
            for selection in ("cpu", "coreml"):
                store = ModelStore(root)
                try:
                    started = time.perf_counter()
                    bundle = store.load(profile, accelerator=selection)
                    warmup = time.perf_counter() - started
                    started = time.perf_counter()
                    text = bundle.asr.transcribe(audio)
                    elapsed = time.perf_counter() - started
                    assert "country" in text.lower(), text
                    bundle.asr.configure_recognition("careful", "country\nAmericans")
                    started = time.perf_counter()
                    guided = bundle.asr.transcribe(audio)
                    careful_seconds = time.perf_counter() - started
                    assert "country" in guided.lower(), guided
                    assert not bundle.asr.transcribe(np.zeros(16000, np.float32))
                    assert bundle.mt is not None
                    translated = bundle.mt.translate("Welcome to the lecture.")
                    assert any("\u4e00" <= c <= "\u9fff" for c in translated)
                    bundle.vad.probability(np.zeros(512, np.float32))
                    entry = {
                        "profile": profile,
                        "requested": selection,
                        "backend": bundle.asr.name,
                        "accelerated": bundle.accelerated,
                        "messages": bundle.messages,
                        "warmup_seconds": warmup,
                        "standard_seconds": elapsed,
                        "careful_seconds": careful_seconds,
                        "english": text,
                        "guided": guided,
                        "chinese": translated,
                    }
                    if bundle.accelerated:
                        entry["coreml"] = bundle.asr.encoder.details
                    result["speech"].append(entry)
                    print(json.dumps(entry, ensure_ascii=False), flush=True)
                finally:
                    store.close()
                    del store
                    gc.collect()
        result["passed"] = True
        return 0
    finally:
        import resource

        result["parent_peak_rss_bytes"] = resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
        result["child_peak_rss_bytes"] = resource.getrusage(
            resource.RUSAGE_CHILDREN
        ).ru_maxrss
        Path(report_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
