"""Local microphone and noisy-speech checks; no captured audio is written to disk."""

import json, time, wave, re
from pathlib import Path
import numpy as np
from app.system.offline import enforce_offline
from app.audio.capture import microphones
from app.audio.check import check_microphone
from app.asr.qnn_whisper import QnnWhisper
from app.audio.vad import Segmenter, SileroVAD


def words(text):
    return re.findall(r"[a-z0-9]+", text.casefold())


def wer(reference, actual):
    a = words(reference)
    b = words(actual)
    row = list(range(len(b) + 1))
    for i, word in enumerate(a, 1):
        current = [i]
        for j, other in enumerate(b, 1):
            current.append(
                min(current[-1] + 1, row[j] + 1, row[j - 1] + (word != other))
            )
        row = current
    return row[-1] / max(1, len(a))


def main():
    enforce_offline()
    root = Path(__file__).resolve().parents[1]
    result = {
        "microphone_assumption": "User will have a microphone",
        "physical_room_rehearsal": "pending",
    }
    devices = microphones()
    if devices:
        result["microphone"] = check_microphone(devices[0][0], lambda *args: None)
    else:
        result["microphone"] = {
            "available_now": False,
            "note": "Connect the intended lecture microphone before rehearsal",
        }
    source = json.loads(
        (root / "docs/evidence/technical-benchmark.json").read_text(encoding="utf-8")
    )["results"]
    model = QnnWhisper(root / "models/whisper/balanced")
    rng = np.random.default_rng(20260909)
    rows = []
    for index, case in enumerate(source):
        with wave.open(str(root / f"tests/fixtures/technical-{index}.wav")) as stream:
            audio = (
                np.frombuffer(
                    stream.readframes(stream.getnframes()), dtype="<i2"
                ).astype(np.float32)
                / 32768
            )
        for label, snr in [("clean", None), ("noise_20db", 20), ("noise_10db", 10)]:
            sample = audio.copy()
            if snr is not None:
                sample += (
                    rng.standard_normal(sample.size).astype(np.float32)
                    * float(np.sqrt(np.mean(sample * sample)))
                    / (10 ** (snr / 20))
                )
            sample = np.clip(sample, -1, 1)
            start = time.perf_counter()
            text = model.transcribe(sample)
            elapsed = time.perf_counter() - start
            rows.append(
                {
                    "case": index,
                    "condition": label,
                    "english": text,
                    "raw_wer": wer(case["reference_english"], text),
                    "asr_seconds": elapsed,
                }
            )
    segmenter = Segmenter(SileroVAD(root / "models/vad/silero_vad.onnx"))
    silence_phrases = 0
    for n in range(600):
        phrase = segmenter.push(np.zeros(512, np.float32), (n + 1) * 0.032)
        silence_phrases += int(phrase is not None)
    assert silence_phrases == 0
    result.update(
        noise_results=rows,
        silence_phrases=silence_phrases,
        source="Locally synthesized technical fixtures with deterministic additive noise; not real classroom audio",
    )
    (root / "docs/evidence/classroom-audio-check.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "microphone": result["microphone"],
                "noise_cases": len(rows),
                "silence_phrases": silence_phrases,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
