"""Replay public accent clips at microphone cadence through the real offline pipeline.

This is a diagnostic subset, not independent accuracy validation or a microphone test.
"""

import argparse
import hashlib
import json
import wave
from pathlib import Path

import numpy as np
from app.config.settings import Settings
from app.export.transcript import recover_journal
from app.pipeline import Pipeline
from app.system.conversation_self_test import read_audio
from app.system.offline import enforce_offline
from scripts.evaluate_speech import errors

DIAGNOSTIC_IDS = [
    "vctk-p248-018",
    "vctk-p251-005",
    "vctk-p251-015",
    "vctk-p251-018",
    "vctk-p251-019",
    "vctk-p251-023",
    "vctk-p225-018",
    "vctk-p226-018",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["standard", "careful"], default="standard")
    parser.add_argument("--vocabulary", default="")
    parser.add_argument("--profile", choices=["fast", "balanced"], default="balanced")
    parser.add_argument("--accelerator", choices=["auto", "cpu"], default="auto")
    args = parser.parse_args()
    enforce_offline()
    root = Path(__file__).resolve().parents[1]
    cases = json.loads(
        (root / "tests/fixtures/vctk-accent-cases.json").read_text(encoding="utf-8")
    )["cases"]
    selected = [{c["id"]: c for c in cases}[key] for key in DIAGNOSTIC_IDS]
    parts = []
    for case in selected:
        path = root / case["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"]
        parts.extend([read_audio(path), np.zeros(16000, np.float32)])
    audio = np.concatenate(parts)
    duration = len(audio) / 16000
    args.output.parent.mkdir(parents=True, exist_ok=True)
    wav = args.output.with_suffix(".wav")
    with wave.open(str(wav), "wb") as writer:
        writer.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        writer.writeframes(np.rint(audio * 32768).astype("<i2").tobytes())
    events = []
    vocabulary = args.vocabulary.replace("|", "\n")
    data = args.output.parent / (args.output.stem + "-data")
    pipeline = Pipeline(
        root,
        data,
        Settings(
            speaking_language="en",
            profile=args.profile,
            accelerator=args.accelerator,
            recognition_mode=args.mode,
            vocabulary_guidance=bool(vocabulary),
            glossary="general",
        ),
        lambda kind, value: events.append((kind, value)),
        vocabulary=vocabulary,
        title="Public accent replay",
        wav=str(wav),
        force_cpu=args.accelerator == "cpu",
    )
    result = dict(
        functional_pass=False,
        classroom_validated=False,
        physical_microphone_tested=False,
        diagnostic_ids=DIAGNOSTIC_IDS,
        mode=args.mode,
        vocabulary=vocabulary,
        profile=args.profile,
        audio_seconds=duration,
        translation_review="pending",
    )
    try:
        pipeline.start()
        assert pipeline.started and pipeline.source is not None
        folder = pipeline.export.folder
        pipeline.source.thread.join(duration + 60)
        assert not pipeline.source.thread.is_alive(), "Replay did not complete"
        pipeline.close()
        journal = [
            json.loads(line)
            for line in (folder / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        captions = [row for row in journal if row["type"] == "english"]
        pairs = [row for row in journal if row["type"] == "pair"]
        assert captions and [c["identifier"] for c in captions] == [
            c["identifier"] for c in pairs
        ]
        assert all(c["english"] and c["chinese"] for c in pairs)
        recovered, skipped = recover_journal(
            folder / "events.jsonl", data / "recovered"
        )
        assert not skipped
        for name in (
            "English Transcript.txt",
            "Chinese Transcript.txt",
            "Bilingual Transcript.txt",
            "English.srt",
            "Chinese.srt",
            "Bilingual.vtt",
        ):
            assert (folder / name).read_bytes() == (recovered / name).read_bytes(), name
        reference = " ".join(c["reference"] for c in selected)
        text = " ".join(c["english"] for c in captions)
        count, total = errors(reference, text)
        result.update(
            reference=reference,
            text=text,
            errors=count,
            words=total,
            wer=count / total,
            completed_pairs=len(pairs),
            captions=pairs,
            journal_recovery=True,
        )
        assert not pipeline.failure_reported
        assert all(
            pipeline.metrics[key] == 0
            for key in ("dropped_audio_chunks", "dropped_phrases", "translation_skips")
        )
        result["functional_pass"] = (
            True  # Functional/export gate; WER is a measurement, not a pass.
        )
    finally:
        pipeline.close()
        result.update(
            backend=getattr(getattr(pipeline, "asr", None), "name", None),
            metrics=pipeline.diagnostics(),
            warnings=[str(value) for kind, value in events if kind == "warning"],
        )
        args.output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in {"captions", "reference", "text", "metrics"}
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
