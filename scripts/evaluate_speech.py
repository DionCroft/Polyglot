"""Offline paired ASR evaluation; never records audio or uploads recordings."""

import argparse, json, re, time, wave, hashlib
from pathlib import Path
import numpy as np
from app.system.offline import enforce_offline
from app.asr.qnn_whisper import QnnWhisper
from app.asr.cpu_whisper import CpuWhisper


def audio_variant(audio, identifier, variant):
    """Repeatable per clip, independent of manifest order and decoder settings."""
    if variant == "clean":
        return audio.copy()
    if variant == "quiet-12dB":
        return audio * np.float32(10 ** (-12 / 20))
    snr = {"noise-20dB": 20, "noise-10dB": 10}[variant]
    seed = int.from_bytes(
        hashlib.sha256(identifier.encode("utf-8")).digest()[:8], "big"
    )
    rng = np.random.default_rng(seed)
    scale = float(np.sqrt(np.mean(audio * audio))) / (10 ** (snr / 20))
    return np.clip(audio + rng.normal(0, scale, len(audio)).astype(np.float32), -1, 1)


def words(text):
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.casefold())


def errors(reference, actual):
    reference, actual = words(reference), words(actual)
    previous = list(range(len(actual) + 1))
    for i, word in enumerate(reference, 1):
        current = [i]
        for j, token in enumerate(actual, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (word != token))
            )
        previous = current
    return previous[-1], len(reference)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=Path, default=Path("tests/fixtures/accent-cases.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--backend", choices=["cpu", "fast", "balanced"], default="balanced"
    )
    parser.add_argument("--mode", choices=["standard", "careful"], default="standard")
    parser.add_argument(
        "--variant",
        choices=["clean", "noise-20dB", "noise-10dB", "quiet-12dB"],
        default="clean",
    )
    parser.add_argument(
        "--language-check",
        action="store_true",
        help="Also measure Auto final-language acceptance after VAD; WER remains manual English",
    )
    hints = parser.add_mutually_exclusive_group()
    hints.add_argument("--vocabulary", default="")
    hints.add_argument(
        "--case-vocabulary",
        action="store_true",
        help="Use each case's explicit short vocabulary list",
    )
    args = parser.parse_args()
    enforce_offline()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    identifiers = [case["id"] for case in manifest["cases"]]
    if not identifiers or len(set(identifiers)) != len(identifiers):
        raise ValueError("Use a nonempty manifest with unique case IDs")
    if any(not words(case["reference"]) for case in manifest["cases"]):
        raise ValueError("Every case needs a nonempty English reference transcript")
    if any(case.get("language", "en") != "en" for case in manifest["cases"]):
        raise ValueError("This WER evaluator is for English speech")
    model = (
        CpuWhisper(root / "models/whisper/fast")
        if args.backend == "cpu"
        else QnnWhisper(root / "models/whisper" / args.backend)
    )
    if hasattr(model, "configure_recognition"):
        model.configure_recognition(args.mode, args.vocabulary.replace("|", "\n"))
    elif args.mode != "standard" or args.vocabulary:
        raise RuntimeError(
            "Requested recognition settings are not supported in this version"
        )
    rows = []
    if args.language_check:
        from app.asr.language_detection import choose_language
        from app.audio.vad import SileroVAD
        from scripts.evaluate_auto_language import speech_audio

        vad = SileroVAD(root / "models/vad/silero_vad.onnx")
    try:
        for case in manifest["cases"]:
            if args.case_vocabulary:
                model.configure_recognition(args.mode, case.get("vocabulary", ""))
            path = root / case["path"]
            if (
                case.get("sha256")
                and hashlib.sha256(path.read_bytes()).hexdigest() != case["sha256"]
            ):
                raise ValueError("Fixture changed: " + case["id"])
            with wave.open(str(path)) as f:
                if (f.getnchannels(), f.getframerate(), f.getsampwidth()) != (
                    1,
                    16000,
                    2,
                ):
                    raise ValueError("Use mono 16 kHz, 16-bit PCM WAV fixtures")
                audio = (
                    np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(
                        np.float32
                    )
                    / 32768
                )
            if not audio.size:
                raise ValueError("Empty audio fixture: " + case["id"])
            if audio.size > 30 * 16000:
                raise ValueError(
                    "Split recordings into clips of at most 30 seconds: " + case["id"]
                )
            audio = audio_variant(audio, case["id"], args.variant)
            start = time.perf_counter()
            text = model.transcribe(audio)
            elapsed = time.perf_counter() - start
            count, total = errors(case["reference"], text)
            rows.append(
                dict(
                    id=case["id"],
                    speaker=case["speaker"],
                    accent=case.get("accent", "unspecified"),
                    reference=case["reference"],
                    text=text,
                    errors=count,
                    words=total,
                    seconds=elapsed,
                    audio_seconds=len(audio) / 16000,
                )
            )
            if args.language_check:
                voiced_audio, voiced = speech_audio(audio, vad)
                detection_start = time.perf_counter()
                scores = (
                    model.detect_language(voiced_audio) if len(voiced_audio) else {}
                )
                selected = choose_language(scores, sum(voiced) * 0.032, final=True)
                rows[-1]["auto"] = dict(
                    selected=selected,
                    voiced_seconds=sum(voiced) * 0.032,
                    top=sorted(scores.items(), key=lambda item: -item[1])[:3],
                    seconds=time.perf_counter() - detection_start,
                )
            print(case["id"], count, "/", total, round(elapsed, 3), flush=True)
    finally:
        close = getattr(model, "close", None)
        if close:
            close()
    summary = {}
    for speaker in dict.fromkeys(x["speaker"] for x in rows):
        subset = [x for x in rows if x["speaker"] == speaker]
        total = sum(x["words"] for x in subset)
        count = sum(x["errors"] for x in subset)
        summary[speaker] = dict(
            clips=len(subset),
            errors=count,
            words=total,
            wer=count / max(1, total),
            rtf=sum(x["seconds"] for x in subset)
            / sum(x["audio_seconds"] for x in subset),
        )
        if args.language_check:
            summary[speaker]["auto"] = dict(
                correct=sum(x["auto"]["selected"] == "en" for x in subset),
                withheld=sum(x["auto"]["selected"] is None for x in subset),
                wrong=sum(x["auto"]["selected"] not in {None, "en"} for x in subset),
            )
    report = dict(
        manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        variant=args.variant,
        language_check=args.language_check,
        scope="Full-clip manual English ASR; optional Auto final decisions. Not a live microphone or classroom test.",
        backend=args.backend,
        mode=args.mode,
        vocabulary=args.vocabulary,
        case_vocabulary=args.case_vocabulary,
        summary=summary,
        rows=rows,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
