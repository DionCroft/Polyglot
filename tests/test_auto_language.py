"""Safety of automatic directions, concurrent translation, abstention and recovery."""

import json
import threading
import time
from dataclasses import replace
from unittest.mock import Mock, patch
import numpy as np
import pytest
from app.asr.language_detection import (
    PhraseLanguage,
    UncertainTurn,
    choose_language,
    language_scores,
)
from app.audio.vad import AudioPhrase
from app.captions.display import CaptionDisplay
from app.captions.state import Caption
from app.config.settings import Settings
from app.config.presets import Presets
from app.export.transcript import Transcript, recover_journal
from app.system.readiness import check
from test_conversations import running_pipeline, Speech


def certain(language):
    return {language: 0.999, "en" if language != "en" else "zh": 0.001}


def wait(condition):
    end = time.monotonic() + 5
    while not condition() and time.monotonic() < end:
        time.sleep(0.01)
    assert condition()


class AutomaticSpeech(Speech):
    def __init__(self):
        self.seen = []

    def detect_language(self, audio):
        return (
            certain("en" if audio[0] > 0 else "zh")
            if abs(audio[0]) > 0.1
            else {"fr": 0.98, "en": 0.01, "zh": 0.01}
        )

    def transcribe(self, audio):
        self.seen.append((self.language, self.vocabulary))
        return super().transcribe(audio)


def start_auto(tmp_path):
    p, events, translators = running_pipeline(tmp_path)
    p.asr = AutomaticSpeech()
    p.switch_language("auto")
    return p, events, translators


def phrase(p, identifier, value, final=True):
    audio = np.full(32000, value, np.float32)
    item = AudioPhrase(
        identifier, identifier * 3, identifier * 3 + 2, audio, final, 1.5
    )
    p.phrases.put((item, p.epoch))


def test_language_probabilities_include_unsupported_languages():
    scores = language_scores(
        np.array([1, 2, 10]), {"<|en|>": 0, "<|zh|>": 1, "<|fr|>": 2}
    )
    assert sum(scores.values()) == pytest.approx(1)
    assert choose_language(scores, 3, True) is None
    with pytest.raises(RuntimeError):
        language_scores([float("nan")], {"<|en|>": 0})


def test_short_speech_requires_stronger_evidence_and_silence_cannot_select():
    ambiguous = {"en": 0.91, "zh": 0.02, "ko": 0.07}
    assert choose_language(ambiguous, 0.67, True) is None
    assert choose_language(certain("zh"), 0.1, True) is None
    assert choose_language(certain("zh"), 0.7, True) == "zh"
    assert choose_language({"en": 0.8, "zh": 0.19, "fr": 0.01}, 3, True) is None


def test_partial_decisions_need_two_growing_hypotheses_and_final_agreement():
    policy = PhraseLanguage()
    assert policy.decide((0, 1), certain("zh"), 1.5, 24000, False) is None
    assert policy.decide((0, 1), certain("zh"), 1.5, 24000, False) is None
    assert policy.decide((0, 1), certain("zh"), 2, 32000, False) == "zh"
    assert policy.decide((0, 1), certain("en"), 3, 48000, True) is None
    assert policy.decide((0, 2), certain("en"), 2, 32000, False) is None
    assert policy.decide((1, 2), certain("en"), 2, 32000, False) is None


def test_auto_preset_and_legacy_default(tmp_path):
    p = Presets(tmp_path / "presets.json")
    cfg = Settings(speaking_language="auto", vocabulary="PRINCE2")
    p.save("Conversation", cfg)
    assert p.load("Conversation") == cfg
    assert Settings.from_dict({}).speaking_language == "en"


def test_alternating_turns_keep_direction_when_translation_is_slow(tmp_path):
    p, events, translators = start_auto(tmp_path)
    folder = p.export.folder
    entered, release = threading.Event(), threading.Event()
    original = translators["en"].translate

    def slow(text):
        entered.set()
        assert release.wait(5)
        return original(text)

    translators["en"].translate = slow
    epoch = p.epoch
    try:
        phrase(p, 1, 0.2)
        assert entered.wait(3)
        phrase(p, 2, -0.2)
        phrase(p, 3, 0.2)
        wait(lambda: len(p.asr.seen) == 3)
        assert not p.switching.is_set() and p.epoch == epoch
        release.set()
    finally:
        release.set()
        p.close()
    assert p.asr.seen == [
        ("en", "CO7000\nPRINCE2"),
        ("zh", ""),
        ("en", "CO7000\nPRINCE2"),
    ]
    pairs = [
        json.loads(s)
        for s in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if json.loads(s)["type"] == "pair"
    ]
    assert [c["source_language"] for c in pairs] == ["en", "zh", "en"]
    assert len(translators["en"].seen) == 2 and translators["zh"].seen == [
        "请再解释一次。"
    ]
    assert all(c["epoch"] == epoch for c in pairs)


def test_uncertain_turn_never_transcribes_or_translates(tmp_path):
    p, events, translators = start_auto(tmp_path)
    folder = p.export.folder
    try:
        phrase(p, 1, 0.01)
        wait(lambda: p.metrics["uncertain_language_phrases"] == 1)
    finally:
        p.close()
    assert not p.asr.seen and not any(t.seen for t in translators.values())
    assert any(
        k == "language-detection" and v["language"] is None and v["final"]
        for k, v in events
    )
    assert "[Not transcribed]" in (folder / "Bilingual Transcript.txt").read_text(
        encoding="utf-8"
    )


def test_uncertain_export_preserves_order_and_roundtrips_recovery(tmp_path):
    writer = Transcript(tmp_path, "Auto conversation")
    a = Caption(1, 0, 1, "Hello", final=True)
    c = Caption(3, 4, 5, "Again", final=True)
    writer.english(a)
    writer.uncertain(UncertainTurn(2, 2, 3))
    writer.english(c)
    writer.pair(replace(c, chinese="再次", translation_status="complete"))
    writer.pair(replace(a, chinese="你好", translation_status="complete"))
    writer.close()
    text = (writer.folder / "Bilingual Transcript.txt").read_text(encoding="utf-8")
    assert text.index("Hello") < text.index("[Not transcribed]") < text.index("Again")
    recovered, skipped = recover_journal(
        writer.folder / "events.jsonl", tmp_path / "recover"
    )
    assert not skipped
    for name in [
        "English.srt",
        "Chinese.srt",
        "Bilingual.vtt",
        "Bilingual Transcript.txt",
    ]:
        assert (writer.folder / name).read_bytes() == (recovered / name).read_bytes()


def test_auto_detection_accelerator_failure_retries_on_cpu(tmp_path):
    p, _, _ = start_auto(tmp_path)
    p.accelerated = True
    p.asr.detect_language = Mock(side_effect=RuntimeError("device lost"))
    with patch("app.asr.cpu_whisper.CpuWhisper") as cpu:
        cpu.return_value.detect_language.return_value = certain("zh")
        assert p._detect_language(np.ones(32000)) == certain("zh")
        assert not p.accelerated
        p._configure_speech("zh")
        cpu.return_value.configure_recognition.assert_called_with(
            "standard", "", language="zh"
        )
    p.close()


def test_pause_discards_inflight_detection(tmp_path):
    p, events, _ = start_auto(tmp_path)
    entered, release = threading.Event(), threading.Event()

    def detect(audio):
        entered.set()
        assert release.wait(5)
        return certain("zh")

    p.asr.detect_language = detect
    try:
        phrase(p, 1, -0.2)
        assert entered.wait(3)
        p.pause()
        release.set()
        wait(lambda: not len(p.phrases))
    finally:
        release.set()
        p.close()
    assert not any(k == "caption" for k, v in events)
    assert not p.asr.seen


def test_manual_override_drains_auto_without_losing_transcript(tmp_path):
    p, _, _ = start_auto(tmp_path)
    folder = p.export.folder
    try:
        phrase(p, 1, 0.2)
        p.switch_language("zh")
        assert p.export.folder == folder
        p.asr.detect_language = Mock(
            side_effect=AssertionError("manual mode must not detect")
        )
        phrase(p, 2, 0.2)
    finally:
        p.close()
    assert p.settings.speaking_language == "zh"
    assert p.asr.seen == [("en", "CO7000\nPRINCE2"), ("zh", "")]


def test_auto_needs_both_models_and_keeps_previous_mode_if_missing(tmp_path):
    p, _, _ = running_pipeline(tmp_path)
    p._store.translation_for.side_effect = FileNotFoundError("missing reverse model")
    try:
        with pytest.raises(FileNotFoundError):
            p.switch_language("auto")
        assert p.settings.speaking_language == "en"
    finally:
        p.close()


def test_visible_caption_language_is_independent_of_current_detector():
    display = CaptionDisplay()
    en = Caption(1, 0, 1, "Hello", "你好", True, translation_status="complete")
    zh = Caption(2, 2, 3, "", "请解释", False, source_language="zh")
    display.accept(en)
    display.accept(zh)
    assert display.primary().source_language == "en"
    assert display.contents()[2] == "请解释"


def test_uncertain_final_retracts_provisional_text_but_retains_previous_pair():
    display = CaptionDisplay()
    pair = Caption(1, 0, 1, "Hello", "你好", True, translation_status="complete")
    partial = Caption(2, 2, 3, "Possibly wrong", final=False)
    display.accept(pair)
    display.accept(partial)
    display.reject_partial(2, 0)
    assert display.contents() == ("Hello", "你好", "")
    assert not display.accept(partial)
    assert display.accept(replace(partial, identifier=3))
    display.reject_partial(3, -1)
    assert display.partial.identifier == 3
    assert display.accept(replace(partial, identifier=2, epoch=1))


def test_auto_readiness_checks_concrete_translation_languages(tmp_path):
    store = Mock()
    store.load.return_value = Mock(
        mt=object(), npu=False, accelerated=False, messages=[]
    )
    result = check(tmp_path, "fast", store, language="auto")
    assert result["speech"] and result["translation"]
    assert [x.args[0] for x in store.translation_for.call_args_list] == ["en", "zh"]
