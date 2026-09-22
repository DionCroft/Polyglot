"""Real-time alternating public speech replay; not a physical classroom test."""

import argparse
import json
import time
import wave
from pathlib import Path

import numpy as np
import psutil
from app.system.offline import enforce_offline
from app.system.auto_self_test import conversation_wav
from app.export.transcript import recover_journal
from app.config.settings import Settings
from app.pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--profile", default="balanced")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--noise-snr", type=float, default=20)
    parser.add_argument("--normalise-speakers", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    assert args.seconds > 0
    enforce_offline()
    root = Path(__file__).resolve().parents[1]
    report = Path(args.output)
    report.parent.mkdir(parents=True, exist_ok=True)
    seed = report.with_suffix(".seed.wav")
    conversation_wav(root / "tests/fixtures", seed, normalise=args.normalise_speakers)
    with wave.open(str(seed)) as stream:
        source = np.frombuffer(stream.readframes(stream.getnframes()), "<i2")
    audio = np.resize(source, args.seconds * 16000).astype(np.float32) / 32768
    rng = np.random.default_rng(7000)
    noise = float(np.sqrt(np.mean(audio * audio))) / (10 ** (args.noise_snr / 20))
    audio = np.clip(audio + rng.normal(0, noise, len(audio)), -1, 0.9999)
    target = report.with_suffix(".wav")
    with wave.open(str(target), "wb") as stream:
        stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        stream.writeframes((audio * 32768).astype("<i2").tobytes())
    del audio, source
    samples, warnings = [], []
    pipeline = Pipeline(
        root,
        report.parent / (report.stem + "-data"),
        Settings(profile=args.profile, speaking_language="auto"),
        lambda kind, value: warnings.append(str(value)) if kind == "warning" else None,
        wav=target,
        force_cpu=args.cpu,
    )
    process = psutil.Process()
    result = {
        "passed": False,
        "physical_classroom_tested": False,
        "noise_snr_db": args.noise_snr,
        "audio_seconds": args.seconds,
        "normalised_recording_levels": args.normalise_speakers,
    }
    start = time.monotonic()
    try:
        pipeline.start()
        assert pipeline.started and pipeline.source
        folder = pipeline.export.folder
        while pipeline.source.thread.is_alive():
            samples.append(
                {
                    "elapsed": time.monotonic() - start,
                    "rss_mib": process.memory_info().rss / 1048576,
                    "threads": process.num_threads(),
                    **pipeline.diagnostics(),
                }
            )
            pipeline.source.thread.join(10)
            assert not pipeline.failure_reported
        pipeline.close()
        events = [
            json.loads(line)
            for line in (folder / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        pairs = [e for e in events if e["type"] == "pair"]
        ids = [e["identifier"] for e in pairs]
        assert ids == sorted(set(ids))
        assert all(e["english"] and e["chinese"] for e in pairs)
        switches = sum(
            a["source_language"] != b["source_language"]
            for a, b in zip(pairs, pairs[1:])
        )
        result.update(pairs=len(pairs), switches=switches, backend=pipeline.asr.name)
        assert switches >= max(2, args.seconds // 35)
        recovered, skipped = recover_journal(
            folder / "events.jsonl", folder.parent / "recovered"
        )
        assert not skipped
        for name in (
            "English.srt",
            "Chinese.srt",
            "Bilingual.vtt",
            "Bilingual Transcript.txt",
        ):
            assert (folder / name).read_bytes() == (recovered / name).read_bytes()
        assert not any(t.is_alive() for t in pipeline.threads)
        assert all(
            pipeline.metrics[k] == 0
            for k in ("dropped_audio_chunks", "dropped_phrases", "translation_skips")
        )
        result.update(
            passed=True,
            backend=pipeline.asr.name,
            pairs=len(pairs),
            switches=switches,
            journal_recovery=True,
        )
    finally:
        pipeline.close()
        result.update(
            duration_seconds=time.monotonic() - start,
            samples=samples,
            final_metrics=pipeline.diagnostics(),
            warnings=warnings,
        )
        report.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))


if __name__ == "__main__":
    main()
