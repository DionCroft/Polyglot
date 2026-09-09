"""Opt-in integration test using public/synthetic WAVs, never a microphone."""

import argparse
import json
import time
import wave
from pathlib import Path
import numpy as np
from app.system.offline import enforce_offline
from app.config.settings import ROOT
from app.system.models import ModelStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wav", type=Path, default=ROOT / "tests/fixtures/jfk.wav")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "tests/artifacts/beta-backends.json"
    )
    parser.add_argument(
        "--backends", nargs="+", default=["cpu", "gpu", "intel_npu", "amd_npu"]
    )
    args = parser.parse_args()
    enforce_offline()
    with wave.open(str(args.wav)) as f:
        assert (f.getnchannels(), f.getframerate(), f.getsampwidth()) == (1, 16000, 2)
        audio = (
            np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32)
            / 32768
        )
    store = ModelStore(ROOT)
    results = []
    try:
        for backend in args.backends:
            start = time.perf_counter()
            bundle = store.load("fast", accelerator=backend)
            setup = time.perf_counter() - start
            start = time.perf_counter()
            text = bundle.asr.transcribe(audio)
            results.append(
                dict(
                    requested=backend,
                    actual=bundle.asr.name,
                    accelerated=bundle.accelerated,
                    npu=bundle.npu,
                    text=text,
                    setup_seconds=setup,
                    inference_seconds=time.perf_counter() - start,
                    messages=bundle.messages,
                )
            )
            assert text
            store.close()
    finally:
        store.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
