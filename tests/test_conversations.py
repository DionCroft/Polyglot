"""Conversation boundaries, direction routing, legacy exports and CPU recovery."""

import json
import threading
import time
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from app.asr.decoding import RecognitionOptions
from app.audio.vad import AudioPhrase, Segmenter
from app.captions.display import CaptionDisplay
from app.captions.stabiliser import CaptionStabiliser
from app.captions.state import Caption
from app.config.presets import Presets
from app.config.settings import Settings
from app.export.transcript import Transcript, recover_journal
from app.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]


class Voice:
    def reset(self):
        pass

    def probability(self, frame):
        return 1.0


class Speech:
    language = "en"

    def configure_recognition(self, mode, vocabulary, language="en"):
        self.language = language
        self.vocabulary = vocabulary

    def transcribe(self, audio):
        return "The critical path." if self.language == "en" else "請再解釋一次。"


class Translation:
    def __init__(self, language):
        self.language = language
        self.seen = []

    def translate(self, text):
        self.seen.append(text)
        return "关键路径。" if self.language == "en" else "Please explain again."


def running_pipeline(tmp_path, language="en"):
    events = []
    cfg = Settings(speaking_language=language, vocabulary_guidance=True)
    p = Pipeline(
        ROOT,
        tmp_path,
        cfg,
        lambda *args: events.append(args),
        vocabulary="CO7000\nPRINCE2",
    )
    p.started = True
    p.origin = time.monotonic()
    p.segmenter = Segmenter(Voice())
    p.stabiliser = CaptionStabiliser()
    p.asr = Speech()
    p._configure_speech()
    translators = {key: Translation(key) for key in ("en", "zh")}
    p.mt = translators[language]
    p._store = Mock()
    p._store.translation_for.side_effect = translators.__getitem__
    p.export = Transcript(tmp_path, "Conversation")
    for fn in (p._segment, p._recognize, p._translate):
        worker = threading.Thread(target=fn)
        p.threads.append(worker)
        worker.start()
    return p, events, translators


def speak(p, offset=0):
    for i in range(12):
        p._frame(np.ones(512, np.float32) * 0.05, offset + (i + 1) * 0.032)


def test_switch_drains_old_turn_and_preserves_one_conversation(tmp_path):
    p, events, translators = running_pipeline(tmp_path)
    folder = p.export.folder
    try:
        speak(p)
        p.switch_language("zh")
        assert p.settings.speaking_language == "zh"
        assert p.asr.language == "zh" and not p.asr.vocabulary
        speak(p, 1)
        p.switch_language("en")
        assert p.asr.vocabulary == "CO7000\nPRINCE2"
        speak(p, 2)
    finally:
        p.close()
    assert len(translators["en"].seen) == 2
    assert translators["zh"].seen == ["请再解释一次。"]
    journal = [
        json.loads(line)
        for line in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    pairs = [x for x in journal if x["type"] == "pair"]
    assert [x["source_language"] for x in pairs] == ["en", "zh", "en"]
    assert [x["identifier"] for x in pairs] == [1, 2, 3]
    assert [x["epoch"] for x in pairs] == [0, 1, 2]
    assert len(list(tmp_path.iterdir())) == 1
    for language, expected in [
        ("English", "Please explain again."),
        ("Chinese", "请再解释一次。"),
    ]:
        txt = (folder / (language + " Transcript.txt")).read_text(encoding="utf-8")
        srt = (folder / (language + ".srt")).read_text(encoding="utf-8")
        assert expected in txt and expected in srt
        assert (
            "关键路径" not in srt
            if language == "English"
            else "Please explain" not in srt
        )
        assert "\n1\n" not in srt  # IDs must not restart after switching.
    recovered, skipped = recover_journal(folder / "events.jsonl", tmp_path / "recover")
    assert skipped == 0
    for filename in [
        "English.srt",
        "Chinese.srt",
        "Bilingual.vtt",
        "Bilingual Transcript.txt",
    ]:
        assert (recovered / filename).read_bytes() == (folder / filename).read_bytes()


def test_switch_waits_for_pending_translation_and_drops_only_transition_audio(tmp_path):
    p, _, translators = running_pipeline(tmp_path)
    entered, release = threading.Event(), threading.Event()
    original = translators["en"].translate

    def slow(text):
        entered.set()
        assert release.wait(5)
        return original(text)

    translators["en"].translate = slow
    speak(p)
    errors = []

    def switch():
        try:
            p.switch_language("zh")
        except Exception as exc:
            errors.append(exc)

    worker = threading.Thread(target=switch)
    worker.start()
    try:
        assert entered.wait(3)
        assert p.switching.is_set() and p.settings.speaking_language == "en"
        speak(p, 2)
        assert p.audio.empty()
        release.set()
        worker.join(5)
        assert not worker.is_alive() and not errors
        assert p.settings.speaking_language == "zh"
    finally:
        release.set()
        worker.join(5)
        p.close()


def test_missing_reverse_model_keeps_previous_language_and_saved_turn(tmp_path):
    p, _, _ = running_pipeline(tmp_path)
    folder = p.export.folder
    p._store.translation_for.side_effect = FileNotFoundError("opus-zh-en")
    try:
        speak(p)
        with pytest.raises(FileNotFoundError):
            p.switch_language("zh")
        assert p.settings.speaking_language == p.asr.language == "en"
        assert not p.switching.is_set()
    finally:
        p.close()
    assert "critical path" in (folder / "English Transcript.txt").read_text()


def test_paused_switch_does_not_resume_microphone(tmp_path):
    p, _, _ = running_pipeline(tmp_path)
    try:
        p.pause()
        p.switch_language("zh")
        assert p.paused.is_set() and p.settings.speaking_language == "zh"
        speak(p)
        assert p.audio.empty()
        p.pause()
        assert not p.paused.is_set()
    finally:
        p.close()


def test_mandarin_pending_source_is_not_mistaken_for_completed_translation():
    d = CaptionDisplay()
    c = Caption(1, 0, 1, "", "你好", True, source_language="zh")
    d.accept(c)
    assert d.pending == c and d.pair is None
    assert d.contents() == ("", "你好", "")
    d.accept(replace(c, english="Hello", translation_status="complete"))
    assert d.contents() == ("Hello", "你好", "")
    assert d.contents("English") == ("Hello", "", "")
    assert not d.accept(replace(c, epoch=-1))


def test_mandarin_translation_failure_keeps_source_in_export(tmp_path):
    c = Caption(1, 0, 1, "", "你好", True, source_language="zh")
    writer = Transcript(tmp_path, "Failure")
    writer.english(c)
    writer.pair(replace(c, translation_status="unavailable"))
    writer.close()
    assert "你好" in (writer.folder / "Chinese.srt").read_text(encoding="utf-8")
    assert not (writer.folder / "English.srt").read_text()


def test_chinese_partial_prefix_uses_characters_without_inventing_spaces():
    s = CaptionStabiliser()
    phrase = AudioPhrase(1, 0, 1, np.ones(512), False)
    assert s.accept(phrase, "请解释项目", source_language="zh") is None
    c = s.accept(phrase, "请解释项目管理", source_language="zh")
    assert c.chinese == "请解释项目" and not c.english


def test_language_and_old_defaults_roundtrip_in_presets(tmp_path):
    assert Settings.from_dict({}).speaking_language == "en"
    assert Settings.from_dict({"speaking_language": "unknown"}).speaking_language == "en"
    presets = Presets(tmp_path / "presets.json")
    cfg = Settings(
        speaking_language="zh", vocabulary="PRINCE2", vocabulary_guidance=True
    )
    presets.save("Student questions", cfg)
    assert presets.load("Student questions") == cfg


def test_mandarin_cpu_fallback_retains_language_without_english_vocabulary(tmp_path):
    p = Pipeline(
        ROOT,
        tmp_path,
        Settings(speaking_language="zh", vocabulary_guidance=True),
        lambda *args: None,
        vocabulary="CO7000",
    )
    p.asr = Mock()
    p.asr.transcribe.side_effect = RuntimeError("accelerator failed")
    p.accelerated = True
    with patch("app.asr.cpu_whisper.CpuWhisper") as cpu:
        cpu.return_value.transcribe.return_value = "你好"
        assert p._transcribe(np.ones(512)) == "你好"
        cpu.return_value.configure_recognition.assert_called_once_with(
            "standard", "", language="zh"
        )


def test_decoder_prefix_language_change_preserves_english_path(tmp_path):
    (tmp_path / "generation_config.json").write_text("{}")
    options = RecognitionOptions(tmp_path)
    assert options.prefix == [50258, 50259, 50359, 50363] and not options.enabled
    options.configure("standard", "", "zh")
    assert options.prefix == [50258, 50260, 50359, 50363] and not options.enabled
    with pytest.raises(ValueError):
        options.configure("standard", "", "auto")


def test_all_installers_pin_the_same_reverse_model():
    assets = []
    for filename in [
        "assets.lock.json",
        "assets-x64-beta.lock.json",
        "assets-macos.lock.json",
    ]:
        manifest = json.loads((ROOT / filename).read_text())
        assets.append(
            [
                x
                for x in manifest["assets"]
                if x["path"].startswith("models/translation/opus-zh-en/")
            ]
        )
    assert len(assets[0]) == 8 and assets[0] == assets[1] == assets[2]
    assert sum(x["bytes"] for x in assets[0]) == 172673277
