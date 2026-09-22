import io
import json
import wave
from pathlib import Path

import numpy as np
import pytest

from scripts.evaluate_speech import audio_variant, errors
from scripts.prepare_vctk_fixtures import downsample


def test_word_error_metric_counts_substitutions_insertions_and_deletions():
    assert errors("We plan the project", "we planned a project today") == (3, 4)
    assert errors("We plan the project", "project") == (3, 4)
    assert errors("Don't stop, please!", "don't STOP please") == (0, 3)


def test_noise_is_paired_across_modes_and_preserves_requested_snr():
    audio = np.full(16000, 0.05, np.float32)
    noisy = audio_variant(audio, "speaker-001", "noise-20dB")
    assert np.array_equal(noisy, audio_variant(audio, "speaker-001", "noise-20dB"))
    assert not np.array_equal(noisy, audio_variant(audio, "speaker-002", "noise-20dB"))
    snr = 10 * np.log10(np.mean(audio**2) / np.mean((noisy - audio) ** 2))
    assert 19.8 < snr < 20.2
    assert np.all(audio == np.float32(0.05))
    assert (
        np.max(np.abs(audio_variant(np.ones(16000, np.float32), "x", "noise-10dB")))
        <= 1
    )
    assert np.allclose(
        audio_variant(audio, "x", "quiet-12dB"), audio * 10 ** (-12 / 20)
    )


def pcm(audio, rate=48000):
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        writer.writeframes(np.rint(audio * 10000).astype("<i2").tobytes())
    return output.getvalue()


def test_resampling_preserves_duration_and_rejects_aliasing():
    time = np.arange(48000) / 48000
    rms = []
    for frequency in (1000, 12000):
        data = downsample(pcm(np.sin(2 * np.pi * frequency * time)))
        with wave.open(io.BytesIO(data)) as reader:
            assert (
                reader.getframerate(),
                reader.getnframes(),
                reader.getnchannels(),
            ) == (16000, 16000, 1)
            samples = np.frombuffer(
                reader.readframes(reader.getnframes()), "<i2"
            ).astype(float)
        rms.append(np.sqrt(np.mean(samples[50:-50] ** 2)))
    assert 6900 < rms[0] < 7200
    assert rms[1] < rms[0] / 100
    with pytest.raises(ValueError, match="48 kHz"):
        downsample(pcm(np.zeros(16000), 16000))


def test_new_corpus_contains_four_separate_speakers_with_no_duplicate_mics():
    root = Path(__file__).resolve().parents[1]
    cases = json.loads(
        (root / "tests/fixtures/vctk-accent-cases.json").read_text(encoding="utf-8")
    )["cases"]
    assert len(cases) == len({x["id"] for x in cases}) == 120
    for speaker, accent in (
        ("p248", "Indian"),
        ("p251", "Indian"),
        ("p225", "English"),
        ("p226", "English"),
    ):
        subset = [x for x in cases if x["speaker"] == speaker]
        assert len(subset) == 30
        assert all(
            x["accent"] == accent and x["source"]["file"].endswith("_mic1.flac")
            for x in subset
        )
        assert len({x["source"]["file"] for x in subset}) == 30
        assert all(len(x["sha256"]) == len(x["source"]["sha256"]) == 64 for x in subset)
