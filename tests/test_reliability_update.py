"""Functional regressions for the pre-rolling 0.7 audit; inference is stubbed."""

from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from app.audio.vad import Segmenter
from app.captions.state import Caption
from app.config.settings import Settings
from app.export.transcript import Transcript, recover_journal
from app.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = (
    "English Transcript.txt",
    "Chinese Transcript.txt",
    "Bilingual Transcript.txt",
    "English.srt",
    "Chinese.srt",
    "Bilingual.vtt",
)


class Voice:
    def reset(self):
        pass

    def probability(self, frame):
        return 1.0


def segmented(tmp_path, indices, final_end=None):
    submitted = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda *args: None)
    p.segmenter = Segmenter(Voice())
    p._submit_phrase = lambda phrase, epoch: submitted.append(phrase)
    for index in indices:
        p._frame(np.ones(512, np.float32) * 0.1, index * 0.032)
    if final_end is not None:
        p.last_audio_end = final_end
    p.input_closed.set()
    p._segment()
    return submitted


def test_timing_gap_finishes_captured_speech_before_reset(tmp_path):
    submitted = segmented(tmp_path, [*range(1, 31), *range(32, 61)])
    finals = [p for p in submitted if p.final and hasattr(p, "audio")]
    assert len(finals) == 2
    assert (finals[0].start, finals[0].end) == pytest.approx((0, 0.960))
    assert (finals[1].start, finals[1].end) == pytest.approx((0.992, 1.920))
    assert [len(p.audio) for p in finals] == [30 * 512, 29 * 512]


def test_audio_queue_overflow_warns_without_callback_io(tmp_path):
    events = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda *args: events.append(args))
    for i in range(180):
        p._frame(np.ones(512, np.float32), (i + 1) * 0.032)
    assert p.audio.qsize() == p.audio.maxsize == 128
    assert p.metrics["dropped_audio_chunks"] == 52
    assert not events
    p.diagnostics()
    warnings = [v for k, v in events if k == "warning"]
    assert len(warnings) == 1 and "audio" in warnings[0].lower()
    p.diagnostics()
    assert len([v for k, v in events if k == "warning"]) == 1


@pytest.mark.parametrize("first_language", ["en", "zh"])
def test_delayed_alternating_exports_are_ordered(tmp_path, first_language):
    t = Transcript(tmp_path, "Alternating speakers")
    captions = []
    for i in range(1, 4):
        language = (
            first_language if i % 2 else ("zh" if first_language == "en" else "en")
        )
        c = Caption(
            i,
            i * 2,
            i * 2 + 1,
            f"English {i}" if language == "en" else "",
            f"Chinese {i}" if language == "zh" else "",
            True,
            source_language=language,
        )
        t.english(c)
        captions.append(c)
    for c in reversed(captions):
        t.pair(
            replace(
                c,
                english=f"English {c.identifier}",
                chinese=f"Chinese {c.identifier}",
                translation_status="complete",
            )
        )
    t.close()
    recovered, skipped = recover_journal(
        t.folder / "events.jsonl", tmp_path / "recover"
    )
    assert not skipped
    for name in EXPORTS:
        text = (t.folder / name).read_text(encoding="utf-8")
        needle = "Chinese" if name.startswith("Chinese") else "English"
        positions = [text.index(f"{needle} {i}") for i in range(1, 4)]
        assert positions == sorted(positions), name
        assert (t.folder / name).read_bytes() == (recovered / name).read_bytes(), name


def test_stop_records_a_trailing_audio_gap(tmp_path):
    submitted = segmented(tmp_path, range(1, 31), final_end=1.280)
    gaps = [p for p in submitted if not hasattr(p, "audio")]
    assert len(gaps) == 1
    assert (gaps[0].start, gaps[0].end) == pytest.approx((0.960, 1.280))


def assert_recovered(folder, destination):
    recovered, skipped = recover_journal(folder / "events.jsonl", destination)
    assert not skipped
    for name in EXPORTS:
        assert (folder / name).read_bytes() == (recovered / name).read_bytes(), name


@pytest.mark.parametrize("automatic", [False, True])
def test_real_workers_preserve_gap_and_both_sides_in_all_exports(tmp_path, automatic):
    import json
    from test_auto_language import start_auto
    from test_conversations import running_pipeline

    p, events, _ = start_auto(tmp_path) if automatic else running_pipeline(tmp_path)
    folder = p.export.folder
    try:
        for index in [*range(1, 31), *range(32, 61)]:
            p._frame(np.ones(512, np.float32) * 0.2, index * 0.032)
    finally:
        p.close()
    records = [
        json.loads(s)
        for s in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    sources = [c for c in records if c["type"] == "english"]
    gaps = [c for c in records if c["type"] == "audio_gap"]
    assert len(sources) == 2 and len(gaps) == 1
    assert sources[0]["end"] == pytest.approx(0.960)
    assert sources[1]["start"] == pytest.approx(0.992)
    assert (gaps[0]["start"], gaps[0]["end"]) == pytest.approx((0.960, 0.992))
    assert sources[0]["identifier"] < gaps[0]["identifier"] < sources[1]["identifier"]
    for name in EXPORTS:
        assert "[Audio lost]" in (folder / name).read_text(encoding="utf-8"), name
    assert len([v for k, v in events if k == "warning" and "Audio was lost" in v]) == 1
    assert_recovered(folder, tmp_path / "recover")


def test_switch_boundary_records_trailing_gap_once(tmp_path):
    from app.pipeline import TurnBoundary

    submitted = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda *args: None)
    p.segmenter = Segmenter(Voice())
    p._submit_phrase = lambda phrase, epoch: submitted.append(phrase)
    for i in range(30):
        p._frame(np.ones(512, np.float32), (i + 1) * 0.032)
    p.last_audio_end = 1.280
    boundary = TurnBoundary()
    p.audio.put((boundary, 1.280, p.epoch))
    p.input_closed.set()
    p._segment()
    assert len([x for x in submitted if x.final and hasattr(x, "audio")]) == 1
    assert (
        len([x for x in submitted if not hasattr(x, "audio") and x is not boundary])
        == 1
    )
    assert submitted[-1] is boundary


def test_intentional_pause_is_not_an_audio_gap(tmp_path):
    from test_conversations import running_pipeline, speak
    from test_auto_language import wait

    p, events, _ = running_pipeline(tmp_path)
    folder = p.export.folder
    try:
        speak(p)
        wait(lambda: len(p.segmenter.frames) >= 12)
        p.pause()
        p._frame(np.ones(512, np.float32), 5)
        p.pause()
        speak(p, 10)
    finally:
        p.close()
    assert not p.metrics["audio_gaps"] and not p.metrics["dropped_audio_chunks"]
    assert not any(k == "warning" and "Audio was lost" in v for k, v in events)
    assert "audio_gap" not in (folder / "events.jsonl").read_text(encoding="utf-8")
    assert_recovered(folder, tmp_path / "recover")


def test_actual_overflow_at_shutdown_keeps_last_captured_phrase(tmp_path):
    import threading, time, json
    from app.captions.stabiliser import CaptionStabiliser
    from test_conversations import Speech, Translation

    p = Pipeline(ROOT, tmp_path, Settings(), lambda *args: None)
    p.started = True
    p.origin = time.monotonic()
    p.segmenter = Segmenter(Voice())
    p.stabiliser = CaptionStabiliser()
    p.asr = Speech()
    p.mt = Translation("en")
    p.translators = {"en": p.mt}
    p.export = Transcript(tmp_path, "Overflow")
    folder = p.export.folder
    for i in range(180):
        p._frame(np.ones(512, np.float32) * 0.2, (i + 1) * 0.032)
    assert p.metrics["dropped_audio_chunks"] == 52
    for fn in (p._segment, p._recognize, p._translate):
        worker = threading.Thread(target=fn)
        p.threads.append(worker)
        worker.start()
    p.close()
    records = [
        json.loads(s)
        for s in (folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    source = next(c for c in records if c["type"] == "english")
    gap = next(c for c in records if c["type"] == "audio_gap")
    assert source["start"] == 0 and source["end"] == pytest.approx(4.096)
    assert (gap["start"], gap["end"]) == pytest.approx((4.096, 5.760))
    assert all(not w.is_alive() for w in p.threads)
    assert_recovered(folder, tmp_path / "recover")


def test_slow_auto_pipeline_exports_all_languages_in_order(tmp_path):
    import threading
    from test_auto_language import start_auto, phrase, wait

    p, events, translators = start_auto(tmp_path)
    folder = p.export.folder
    entered, release = threading.Event(), threading.Event()
    original = translators["zh"].translate

    def slow(text):
        entered.set()
        assert release.wait(5)
        return original(text)

    translators["zh"].translate = slow
    try:
        phrase(p, 1, -0.2)
        assert entered.wait(3)
        phrase(p, 2, 0.2)
        wait(lambda: len(p.asr.seen) == 2)
        wait(
            lambda: any(
                k == "caption" and v.final and v.identifier == 2 for k, v in events
            )
        )
        assert not (folder / "English Transcript.txt").read_text(encoding="utf-8")
        assert '"identifier": 2' in (folder / "events.jsonl").read_text(
            encoding="utf-8"
        )
    finally:
        release.set()
        p.close()
    text = (folder / "English Transcript.txt").read_text(encoding="utf-8")
    assert text.index("Please explain again.") < text.index("The critical path.")
    assert_recovered(folder, tmp_path / "recover")


def test_uncertain_and_failed_turns_do_not_block_export_order(tmp_path):
    from app.asr.language_detection import UncertainTurn
    from app.captions.state import AudioGap

    t = Transcript(tmp_path, "Mixed outcomes")
    a = Caption(1, 0, 1, "", "Question", True, source_language="zh")
    b = Caption(4, 4, 5, "Reply", final=True)
    t.english(a)
    t.uncertain(UncertainTurn(2, 1, 2))
    t.gap(AudioGap(3, 2, 3))
    t.english(b)
    t.pair(replace(b, chinese="Answer", translation_status="complete"))
    t.pair(replace(a, translation_status="unavailable"))
    t.close()
    for name in EXPORTS:
        text = (t.folder / name).read_text(encoding="utf-8")
        assert text.index("[Not transcribed]") < text.index("[Audio lost]")
    assert_recovered(t.folder, tmp_path / "recover")


def test_export_backlog_is_bounded_while_translation_is_stalled(tmp_path):
    import threading
    from test_auto_language import start_auto, phrase, wait

    p, events, translators = start_auto(tmp_path)
    p.export.capacity = 4
    folder = p.export.folder
    entered, release = threading.Event(), threading.Event()
    original = translators["en"].translate

    def slow(text):
        entered.set()
        assert release.wait(5)
        return original(text)

    translators["en"].translate = slow
    try:
        phrase(p, 1, 0.2)
        assert entered.wait(3)
        for i in range(2, 5):
            phrase(p, i, 0.2 if i % 2 else -0.2)
            wait(lambda: len(p.asr.seen) == i)
        wait(lambda: p.export.full)
        phrase(p, 5, 0.2)
        phrase(p, 6, -0.2)
        assert len(p.export.pending) == 4 and len(p.phrases) <= p.phrases.capacity
    finally:
        release.set()
        p.close()
    assert len(p.asr.seen) == 6
    assert_recovered(folder, tmp_path / "recover")


def test_stop_during_callback_does_not_create_false_audio_gap(tmp_path):
    from unittest.mock import patch

    submitted = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda *args: None)
    p.segmenter = Segmenter(Voice())
    p._submit_phrase = lambda phrase, epoch: submitted.append(phrase)
    for i in range(6):
        p._frame(np.ones(512, np.float32), (i + 1) * 0.032)

    def stop_during_meter(data):
        p.request_stop()
        return 0.0

    with patch("app.pipeline.np.mean", side_effect=stop_during_meter):
        p._frame(np.ones(512, np.float32), 0.224)
    p.input_closed.set()
    p._segment()
    assert p.last_audio_end == pytest.approx(0.192)
    assert not p.metrics["audio_gaps"]
    assert len([x for x in submitted if x.final]) == 1
