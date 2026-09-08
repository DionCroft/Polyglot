import json, threading, queue
from dataclasses import replace
from pathlib import Path
import numpy as np
from app.audio.vad import AudioPhrase, Segmenter
from app.captions.stabiliser import CaptionStabiliser
from app.captions.glossary import Glossary
from app.captions.state import Caption
from app.export.transcript import Transcript, timestamp
from app.pipeline import PhraseQueue, Pipeline
from app.config.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def phrase(identifier=1, final=False):
    return AudioPhrase(identifier, 0, 1, np.zeros(512, np.float32), final)


def test_only_final_commits_and_stale_partial_rejected():
    s = CaptionStabiliser()
    assert not s.accept(phrase(), "hello").final
    assert s.accept(phrase(final=True), "hello world").final
    assert s.accept(phrase(), "old partial") is None
    assert s.accept(phrase(final=True), "duplicate") is None
    assert s.accept(phrase(2, True), "next").english == "next"


def test_blank_hypothesis_not_committed():
    assert CaptionStabiliser().accept(phrase(final=True), "  ") is None


def test_queue_final_replaces_partial():
    q = PhraseQueue(2)
    q.put((phrase(), 0))
    q.put((phrase(final=True), 0))
    assert len(q) == 1
    assert q.get()[0].final


def test_queue_bounded_prefers_final():
    q = PhraseQueue(2)
    q.put((phrase(1, True), 0))
    q.put((phrase(2, True), 0))
    assert q.put((phrase(3), 0))[0].identifier == 3
    assert len(q) == 2
    assert q.put((phrase(3, True), 0))[0].identifier == 1


def test_glossary_requires_source_context():
    g = Glossary(ROOT / "glossaries/embedded_systems.json")
    assert (
        g.chinese(
            "The interrupt service routine should execute quickly.",
            "中断服务常规应尽快执行。",
        )
        == "中断服务程序应尽快执行。"
    )
    assert g.chinese("other text", "中断服务常规") == "中断服务常规"
    assert g.chinese("microcontroller", "bad") == "微控制器"


def test_vocabulary_only_exact_bounded_matches():
    g = Glossary(vocabulary="ESP32\nAI")
    assert g.english("esp32 and paid AI") == "ESP32 and paid AI"


class FakeVad:
    def __init__(self, prob):
        self.prob = prob

    def reset(self):
        pass

    def probability(self, frame):
        return self.prob


def test_vad_silence_not_submitted_and_audio_bounded():
    vad = FakeVad(0)
    seg = Segmenter(vad)
    for n in range(2000):
        assert seg.push(np.zeros(512, np.float32), n * 0.032) is None
    assert len(seg.pre) <= 8 and len(seg.frames) == 0
    vad.prob = 1
    final = []
    for n in range(1000):
        result = seg.push(np.zeros(512, np.float32), 64 + n * 0.032)
        assert len(seg.frames) <= 300
        if result and result.final:
            final.append(result)
    assert len(final) >= 3


def test_vad_pause_boundary():
    vad = FakeVad(1)
    seg = Segmenter(vad)
    for n in range(20):
        seg.push(np.zeros(512, np.float32), (n + 1) * 0.032)
    vad.prob = 0
    result = None
    for n in range(18):
        result = seg.push(np.zeros(512, np.float32), (n + 21) * 0.032)
    assert result.final and result.identifier == 1


def test_utf8_exports_are_incremental(tmp_path):
    t = Transcript(tmp_path, "Lecture: one")
    c = Caption(1, 1.25, 3.5, "Hello", final=True)
    t.english(c)
    assert "Hello" in (t.folder / "English Transcript.txt").read_text(encoding="utf-8")
    t.pair(replace(c, chinese="你好"))
    t.close()
    assert "你好" in (t.folder / "Chinese.srt").read_text(encoding="utf-8")
    assert "00:00:01.250 --> 00:00:03.500" in (t.folder / "Bilingual.vtt").read_text(
        encoding="utf-8"
    )
    assert (
        len((t.folder / "events.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    )


def test_timestamp_rounding_carries():
    assert timestamp(59.9996) == "00:01:00,000"


def test_pause_discards_buffer_and_invalidates_pending(tmp_path):
    events = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda k, v: events.append((k, v)))
    p._frame(np.zeros(512, np.float32), 0.032)
    assert p.audio.qsize() == 1
    p.pause()
    assert p.audio.qsize() == 0 and p.paused.is_set() and p.epoch == 1
    p._frame(np.zeros(512, np.float32), 0.064)
    assert p.audio.empty()
    p.pause()
    assert not p.paused.is_set() and p.epoch == 2


def test_translation_failure_preserves_english(tmp_path):
    events = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda k, v: events.append((k, v)))

    class Broken:
        def translate(self, text):
            raise RuntimeError("local model failure")

    p.mt = Broken()
    p.origin = 0
    p.export = Transcript(tmp_path, "Failure")
    c = Caption(1, 0, 1, "English survives", final=True)
    p._save("english", c)
    p.translation.put(c)
    p.stop_event.set()
    p._translate()
    p.export.close()
    assert (
        "English survives" in (p.export.folder / "English Transcript.txt").read_text()
    )
    assert any(k == "warning" for k, v in events)


def test_offline_guard_blocks_python_network_in_subprocess():
    import subprocess, sys

    code = "from app.system.offline import enforce_offline;enforce_offline();import socket;socket.create_connection(('example.com',443))"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode != 0 and "runtime networking is disabled" in result.stderr


def test_out_of_order_translation_preserves_subtitle_timeline(tmp_path):
    t = Transcript(tmp_path, "Ordering")
    a = Caption(1, 0, 1, "First", final=True)
    b = Caption(2, 2, 3, "Second", final=True)
    t.english(a)
    t.english(b)
    t.pair(b)
    assert "Second" not in (t.folder / "Bilingual.vtt").read_text(encoding="utf-8")
    t.pair(replace(a, chinese="第一"))
    t.close()
    vtt = (t.folder / "Bilingual.vtt").read_text(encoding="utf-8")
    assert vtt.index("First") < vtt.index("Second")


def test_close_preserves_untranslated_english(tmp_path):
    t = Transcript(tmp_path, "Interrupted")
    t.english(Caption(1, 0, 1, "Still saved", final=True))
    t.close()
    assert "Still saved" in (t.folder / "Bilingual.vtt").read_text(encoding="utf-8")


def test_explicit_asr_alias_preserves_freertos_without_correcting_free():
    glossary = Glossary(ROOT / "glossaries/embedded_systems.json")
    assert (
        glossary.english("The free RTOS scheduler runs.")
        == "The FreeRTOS scheduler runs."
    )
    assert glossary.english("Free software is useful.") == "Free software is useful."
