import json
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
import pytest
from app.asr.decoding import RecognitionOptions, WhisperTokenizer, search
from app.asr.qnn_whisper import QnnWhisper
from app.asr.cpu_whisper import CpuWhisper
from app.config.settings import ROOT, Settings


@pytest.fixture
def options(tmp_path):
    (tmp_path / "generation_config.json").write_text(
        json.dumps({"begin_suppress_tokens": [220, 50257], "suppress_tokens": [1]})
    )
    return RecognitionOptions(tmp_path)


def test_filters_suppress_control_tokens_without_altering_input(options):
    original = np.zeros(51865)
    original[50364] = 100
    result = options.filtered(original, True)
    assert original[50364] == 100
    assert not np.isfinite(result[50364]) and not np.isfinite(result[50259])
    assert not np.isfinite(result[50257]) and not np.isfinite(result[1])
    assert np.isfinite(options.filtered(original, False)[50257])
    with pytest.raises(RuntimeError):
        options.filtered(np.full(51865, np.nan), True)


def test_prompt_is_prefilled_and_never_returned_as_caption(options):
    options.prompt = [123, 456]
    called = []

    def step(token, position, cache):
        called.append((token, position))
        scores = np.full(51865, -1000.0)
        scores[42 if token == 50363 else 50257] = 0
        return scores, tuple((cache or ())) + (token,)

    assert search(step, options, 50, 1) == [42]
    assert [x[0] for x in called[: len(options.prefix)]] == [
        50361,
        123,
        456,
        50258,
        50259,
        50359,
        50363,
    ]
    assert [x[1] for x in called] == list(range(len(called)))


def test_beam_can_recover_sequence_missed_by_greedy(options):
    def step(token, position, cache):
        history = tuple(cache or ()) + (token,)
        assert len(history) == position + 1  # sibling caches must stay separate
        scores = np.full(51865, -1000.0)
        if token == 50363:
            scores[42] = np.log(0.6)
            scores[43] = np.log(0.4)
        elif token == 42:
            scores[44] = np.log(0.11)
            scores[45:54] = np.log(0.89 / 9)
        else:
            scores[50257] = 0
        return scores, history

    assert search(step, options, 25, 1) == [42, 44]
    assert search(step, options, 25, 3) == [43]


def test_decoder_position_budget_is_bounded(options):
    positions = []

    def step(token, position, cache):
        positions.append(position)
        scores = np.full(51865, -1000.0)
        scores[42] = 0
        return scores, None

    result = search(step, options, 12, 1)
    assert len(result) <= 8 and max(positions) < 12


def test_standard_path_is_explicitly_unchanged(options):
    model = QnnWhisper.__new__(QnnWhisper)
    model.recognition = options
    model._transcribe_standard = Mock(return_value="existing transcript")
    model._transcribe_guided = Mock(
        side_effect=AssertionError("advanced path not requested")
    )
    assert model.transcribe(np.ones(20)) == "existing transcript"


@pytest.mark.parametrize("cls", [QnnWhisper, CpuWhisper])
def test_guided_silence_cannot_repeat_vocabulary(cls, options):
    options.mode = "careful"
    options.prompt = [123, 456]
    model = cls.__new__(cls)
    model.recognition = options
    assert model.transcribe(np.zeros(16000, np.float32)) == ""


def test_tokenizer_matches_reference_and_bounds_context():
    folder = ROOT / "models/whisper/fast"
    if not (folder / "tokenizer.json").is_file():
        pytest.skip("requires installed model assets")
    tokenizer = WhisperTokenizer(folder / "tokenizer.json")
    vectors = json.loads(
        (ROOT / "tests/fixtures/tokenizer-vectors.json").read_text(encoding="utf-8")
    )
    for case in vectors:
        assert tokenizer.encode(case["text"]) == case["tokens"]
    assert all(x < 50257 for x in tokenizer.encode(" <|startoftranscript|>"))
    assert (
        len(tokenizer.vocabulary_tokens("\n".join("term" + str(i) for i in range(100))))
        <= 32
    )
    assert tokenizer.vocabulary_tokens("MOSFET\nmosfet") == tokenizer.vocabulary_tokens(
        "MOSFET"
    )
    settings = RecognitionOptions(folder)
    settings.configure("careful", "MOSFET")
    assert settings.prompt
    settings.configure("standard", "")
    assert not settings.enabled and settings.prefix == [50258, 50259, 50359, 50363]


def test_cpu_recovery_preserves_mode_vocabulary_and_final_flag(tmp_path):
    from app.pipeline import Pipeline

    cfg = Settings(recognition_mode="careful", vocabulary_guidance=True)
    p = Pipeline(ROOT, tmp_path, cfg, lambda *args: None, vocabulary="ESP32\nFreeRTOS")
    p.asr = Mock()
    p.asr.transcribe.side_effect = RuntimeError("accelerator failed")
    p.accelerated = True
    with patch("app.asr.cpu_whisper.CpuWhisper") as cpu:
        cpu.return_value.transcribe.return_value = "recovered"
        assert p._transcribe(np.ones(512), final=False) == "recovered"
        cpu.return_value.configure_recognition.assert_called_once_with(
            "careful", "ESP32\nFreeRTOS"
        )
        assert cpu.return_value.final_pass is False


def test_settings_preserve_standard_defaults_and_new_preset_fields():
    cfg = Settings.from_dict({})
    assert cfg.recognition_mode == "standard" and not cfg.vocabulary_guidance
    assert (
        Settings.from_dict({"recognition_mode": "unknown"}).recognition_mode
        == "standard"
    )
    with pytest.raises(ValueError):
        Settings.from_dict({"vocabulary_guidance": "yes"})
