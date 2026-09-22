"""Offline native speech/translation smoke checks; results are not human acceptance."""

import gc
import hashlib
import json
import platform
import re
import time
import wave
from pathlib import Path

import numpy as np
import psutil


def read_audio(path):
    with wave.open(str(path)) as stream:
        assert (
            stream.getframerate(),
            stream.getnchannels(),
            stream.getsampwidth(),
        ) == (16000, 1, 2)
        return (
            np.frombuffer(stream.readframes(stream.getnframes()), "<i2").astype(
                np.float32
            )
            / 32768
        )


def character_errors(reference, text):
    # Keep letters and numbers; punctuation/space differences are excluded.
    normalize = lambda s: [c for c in s.lower() if c.isalnum()]
    a, b = normalize(reference), normalize(text)
    previous = list(range(len(b) + 1))
    for i, left in enumerate(a, 1):
        current = [i]
        for j, right in enumerate(b, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right))
            )
        previous = current
    return previous[-1], len(a)


def run(root, fixtures, report_path):
    from app import __version__
    from app.system.architecture import is_macos, is_x64
    from app.system.models import ModelStore
    from opencc import OpenCC

    fixtures = Path(fixtures)
    manifest = json.loads(
        (fixtures / "mandarin-cases.json").read_text(encoding="utf-8")
    )
    english = read_audio(fixtures / "jfk.wav")
    simplify = OpenCC("t2s")
    selections = [("fast", "cpu"), ("fast", "auto")]
    if not is_x64():
        selections.append(("balanced", "auto"))
    result = dict(
        version=__version__,
        platform=platform.platform(),
        speech=[],
        translation=[],
        physical_microphone_tested=False,
        native_speaker_review=False,
        passed=False,
    )
    try:
        for profile, acceleration in selections:
            store = ModelStore(root)
            try:
                bundle = store.load(
                    profile, force_cpu=acceleration == "cpu", accelerator=acceleration
                )
                before = bundle.asr.transcribe(english)
                assert "country" in before.lower(), before
                bundle.asr.configure_recognition("standard", "", language="zh")
                for case in manifest["cases"]:
                    path = fixtures / Path(case["path"]).name
                    assert (
                        hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"]
                    )
                    audio = read_audio(path)
                    started = time.perf_counter()
                    text = simplify.convert(bundle.asr.transcribe(audio))
                    elapsed = time.perf_counter() - started
                    assert len(re.findall(r"[\u4e00-\u9fff]", text)) >= 3, text
                    errors, count = character_errors(case["reference"], text)
                    result["speech"].append(
                        dict(
                            profile=profile,
                            requested=acceleration,
                            backend=bundle.asr.name,
                            accelerated=bundle.accelerated,
                            case=case["id"],
                            reference=case["reference"],
                            text=text,
                            seconds=elapsed,
                            audio_seconds=len(audio) / 16000,
                            character_errors=errors,
                            reference_characters=count,
                        )
                    )
                bundle.asr.configure_recognition("careful", "", language="zh")
                assert not bundle.asr.transcribe(np.zeros(16000, np.float32))
                careful = simplify.convert(
                    bundle.asr.transcribe(read_audio(fixtures / "mandarin-1.wav"))
                )
                assert len(re.findall(r"[\u4e00-\u9fff]", careful)) >= 3
                bundle.asr.configure_recognition()
                assert bundle.asr.transcribe(english) == before, (
                    "English changed after language round trip"
                )
                result["speech"][-1]["careful_first_sample"] = careful
                if profile == "fast" and acceleration == "cpu":
                    rss_before = psutil.Process().memory_info().rss
                    start = time.perf_counter()
                    reverse = store.translation_for("zh")
                    result["reverse_model"] = dict(
                        load_and_warmup_seconds=time.perf_counter() - start,
                        rss_before_bytes=rss_before,
                        rss_after_bytes=psutil.Process().memory_info().rss,
                    )
                    questions = [
                        "请再解释一次。",
                        "我们应该如何管理项目风险？",
                        "这个项目的关键路径是什么？",
                        "机器人为什么停止了？",
                        "我们不应该忽略安全问题。",
                        "截止日期是星期五。",
                        "这个电路的电压是五伏。",
                        "请问这个公式是什么意思？",
                    ]
                    for question in questions:
                        start = time.perf_counter()
                        translated = reverse.translate(question)
                        assert re.search(r"[A-Za-z]", translated), translated
                        result["translation"].append(
                            dict(
                                chinese=question,
                                english=translated,
                                seconds=time.perf_counter() - start,
                                human_review="pending",
                            )
                        )
                    assert any(
                        "\u4e00" <= c <= "\u9fff"
                        for c in bundle.mt.translate("Welcome to the lecture.")
                    )
                    assert store.translation_for("zh") is reverse
                print(
                    "Verified conversation backend",
                    profile,
                    acceleration,
                    bundle.asr.name,
                    flush=True,
                )
            finally:
                store.close()
                del store, bundle
                gc.collect()
        result["passed"] = True
        return 0
    finally:
        Path(report_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
