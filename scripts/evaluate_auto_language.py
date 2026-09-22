"""Offline development evaluation: coverage and wrong accepted choices are separate."""

import argparse
import gc
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from app.asr.language_detection import choose_language
from app.audio.vad import SileroVAD
from app.system.conversation_self_test import read_audio
from app.system.models import ModelStore
from app.system.offline import enforce_offline


def speech_audio(audio, vad):
    vad.reset()
    first = None
    voiced = []
    for offset in range(0, len(audio) - 511, 512):
        is_voice = vad.probability(audio[offset : offset + 512]) >= 0.5
        voiced.append(is_voice)
        if is_voice and first is None:
            first = max(0, offset - 8 * 512)
    if first is None:
        return np.empty(0, np.float32), []
    return audio[first:], voiced[first // 512 :]


def run(root, output, accelerator="cpu", profile="fast", limit=None):
    enforce_offline()
    root = Path(root)
    cases = json.loads(
        (root / "tests/fixtures/auto-language-cases.json").read_text(encoding="utf-8")
    )["cases"]
    if limit:
        # Preserve both supported languages and the negative examples in small CI runs.
        cases = [
            c
            for language in ("zh", "en", "fr", "es")
            for c in [x for x in cases if x["language"] == language][:limit]
        ]
    else:
        cases += [
            {**c, "language": "en"}
            for c in json.loads(
                (root / "tests/fixtures/accent-cases.json").read_text(encoding="utf-8")
            )["cases"]
        ]
    store = ModelStore(root)
    result = {
        "passed": False,
        "classroom_validated": False,
        "profile": profile,
        "requested": accelerator,
        "cases": [],
    }
    try:
        bundle = store.load(
            profile, force_cpu=accelerator == "cpu", accelerator=accelerator
        )
        result["backend"] = bundle.asr.name
        vad = SileroVAD(root / "models/vad/silero_vad.onnx")
        rng = np.random.default_rng(7000)
        for n, c in enumerate(cases):
            path = root / c["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == c["sha256"]
            original = read_audio(path)
            for variant in (
                "clean",
                "short-1s",
                "short-2s",
                "noise-20dB",
                "noise-10dB",
            ):
                audio = original.copy()
                if variant.startswith("noise"):
                    snr = 20 if variant == "noise-20dB" else 10
                    scale = float(np.sqrt(np.mean(audio * audio))) / (10 ** (snr / 20))
                    audio = np.clip(
                        audio + rng.normal(0, scale, len(audio)).astype(np.float32),
                        -1,
                        1,
                    )
                audio, voiced = speech_audio(audio, vad)
                if variant.startswith("short"):
                    seconds = 1 if variant == "short-1s" else 2
                    audio = audio[: seconds * 16000]
                    voiced = voiced[: len(audio) // 512]
                start = time.perf_counter()
                scores = bundle.asr.detect_language(audio) if len(audio) else {}
                elapsed = time.perf_counter() - start
                selected = choose_language(scores, sum(voiced) * 0.032, final=True)
                top = sorted(scores.items(), key=lambda item: -item[1])[:3]
                result["cases"].append(
                    dict(
                        id=c["id"],
                        expected=c["language"],
                        variant=variant,
                        selected=selected,
                        top=top,
                        voiced_seconds=sum(voiced) * 0.032,
                        seconds=elapsed,
                    )
                )
            if (n + 1) % 10 == 0:
                print("Evaluated", n + 1, "recordings", flush=True)
        result["summary"] = {}
        for variant in ("clean", "short-1s", "short-2s", "noise-20dB", "noise-10dB"):
            group = [c for c in result["cases"] if c["variant"] == variant]
            accepted = [c for c in group if c["selected"] is not None]
            result["summary"][variant] = {
                "total": len(group),
                "accepted": len(accepted),
                "wrong_accepted": sum(c["selected"] != c["expected"] for c in accepted),
                "supported_total": sum(c["expected"] in {"en", "zh"} for c in group),
                "correct_supported": sum(c["selected"] == c["expected"] for c in group),
                "unsupported_accepted": sum(
                    c["expected"] not in {"en", "zh"} for c in accepted
                ),
            }
        # A completed evaluation is not a release accuracy gate; preserve failures as evidence.
        result["passed"] = True
        return result
    finally:
        store.close()
        gc.collect()
        Path(output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accelerator", default="cpu")
    parser.add_argument("--profile", default="fast")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(
        Path(__file__).resolve().parents[1],
        args.output,
        args.accelerator,
        args.profile,
        args.limit,
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
