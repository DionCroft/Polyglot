import json
import threading
from dataclasses import replace
from pathlib import Path
import numpy as np
from app.pipeline import Pipeline
from app.config.settings import Settings
from app.audio.vad import Segmenter, AudioPhrase
from app.captions.stabiliser import CaptionStabiliser
from app.captions.state import Caption
from app.captions.display import CaptionDisplay
from app.export.transcript import Transcript, recover_journal

ROOT = Path(__file__).resolve().parents[1]


class Voice:
    def reset(self):
        pass

    def probability(self, frame):
        return 1.0


class Speech:
    def transcribe(self, audio):
        return "The final sentence."


class Translation:
    def translate(self, text):
        return "最后一句。"


def test_stop_finishes_speech_without_waiting_for_silence(tmp_path):
    events = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda k, v: events.append((k, v)))
    p.started = True
    p.origin = 0
    p.segmenter = Segmenter(Voice())
    p.stabiliser = CaptionStabiliser()
    p.asr = Speech()
    p.mt = Translation()
    writer = Transcript(tmp_path, "Drain")
    p.export = writer
    for fn in (p._segment, p._recognize, p._translate):
        worker = threading.Thread(target=fn)
        p.threads.append(worker)
        worker.start()
    for i in range(12):
        p._frame(np.ones(512, np.float32) * 0.05, (i + 1) * 0.032)
    p.request_stop()
    assert not p.paused.is_set()
    p.close()
    assert all(not t.is_alive() for t in p.threads)
    pairs = [v for k, v in events if k == "caption" and v.chinese]
    assert len(pairs) == 1 and pairs[0].english == "The final sentence."
    assert "最后一句" in (writer.folder / "Bilingual Transcript.txt").read_text(
        encoding="utf-8"
    )


def test_write_and_cleanup_failure_does_not_escape_or_repeat(tmp_path):
    events = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda *a: events.append(a))

    class Broken:
        def english(self, c):
            raise OSError("disk full")

        def close(self):
            raise OSError("flush also failed")

    p.export = Broken()
    p._save("english", Caption(1, 0, 1, "Still captioning", final=True))
    p._save("english", Caption(2, 1, 2, "Next", final=True))
    assert p.export is None and len(events) == 1
    assert not p.failure_reported


def test_journal_recovers_valid_records_after_truncated_tail(tmp_path):
    c = Caption(1, 0, 1, "Hello", "你好", True)
    journal = tmp_path / "events.jsonl"
    journal.write_text(
        json.dumps({"type": "english", **replace(c, chinese="").__dict__})
        + "\n"
        + json.dumps({"type": "pair", **c.__dict__})
        + '\n{"type":',
        encoding="utf-8",
    )
    original = journal.read_bytes()
    folder, skipped = recover_journal(journal, tmp_path / "recovered")
    assert skipped == 1 and "你好" in (folder / "Bilingual.vtt").read_text(
        encoding="utf-8"
    )
    assert journal.read_bytes() == original


def test_pair_remains_visible_until_next_translation_arrives():
    d = CaptionDisplay()
    a = Caption(1, 0, 1, "First", "第一", True)
    b = Caption(2, 1, 2, "Second", final=True)
    d.accept(a)
    d.accept(b)
    assert d.contents() == ("First", "第一", "Second")
    assert d.contents("English")[0] == "Second"
    d.accept(replace(b, chinese="第二"))
    assert d.contents() == ("Second", "第二", "")


def test_delayed_pair_can_arrive_behind_newer_english_without_going_backwards():
    d = CaptionDisplay()
    d.accept(Caption(1, 0, 1, "First", final=True))
    d.accept(Caption(2, 1, 2, "Second", final=True))
    d.accept(Caption(1, 0, 1, "First", "第一", True))
    assert d.contents() == ("First", "第一", "Second")
    d.accept(Caption(2, 1, 2, "Second", "第二", True))
    assert not d.accept(Caption(1, 0, 1, "First", "第一", True))
    d.accept(Caption(1, 0, 1, "New session", "新", True, 1))
    assert not d.accept(Caption(3, 0, 1, "Old epoch", "旧", True, 0))


def test_provisional_prefix_waits_for_agreement_and_final_corrects_it():
    p = AudioPhrase(1, 0, 1, np.zeros(512, np.float32), False)
    s = CaptionStabiliser()
    assert s.accept(p, "The robot moves") is None
    assert s.accept(p, "The robot stops").english == "The robot"
    assert s.accept(p, "A robotic device").english == "The robot"
    assert (
        s.accept(replace(p, final=True), "A robot stops.").english == "A robot stops."
    )


def test_sentence_hint_allows_short_pause_but_never_cuts_ongoing_speech():
    class Vad(Voice):
        speech = True

        def probability(self, frame):
            return float(self.speech)

    v = Vad()
    s = Segmenter(v)
    frame = np.zeros(512, np.float32)
    for i in range(80):
        s.push(frame, (i + 1) * 0.032)
    s.sentence_complete(s.identifier)
    ongoing = s.push(frame, 81 * 0.032)
    assert ongoing is None or not ongoing.final
    v.speech = False
    result = None
    for i in range(10):
        result = s.push(frame, (83 + i) * 0.032)
    assert result and result.final


def test_midlecture_npu_failure_retries_same_audio_on_cpu(tmp_path):
    from unittest.mock import patch, Mock

    events = []
    p = Pipeline(ROOT, tmp_path, Settings(), lambda *a: events.append(a))
    p.asr = Mock()
    p.asr.transcribe.side_effect = RuntimeError("device failed")
    p.using_npu = True
    audio = np.ones(512, np.float32)
    with patch("app.asr.cpu_whisper.CpuWhisper") as cpu:
        cpu.return_value.transcribe.return_value = "Recovered phrase"
        cpu.return_value.name = "Local CPU"
        assert p._transcribe(audio) == "Recovered phrase"
        assert cpu.return_value.transcribe.call_args.args[0] is audio
    assert not p.using_npu and any(k == "warning" for k, v in events)


def test_pause_invalidates_inflight_recognition(tmp_path):
    import time

    events = []
    entered = threading.Event()
    release = threading.Event()
    p = Pipeline(
        ROOT, tmp_path, Settings(save_transcripts=False), lambda *a: events.append(a)
    )

    class SlowSpeech:
        def transcribe(self, audio):
            entered.set()
            assert release.wait(2)
            return "Private paused words"

    p.asr = SlowSpeech()
    p.segmenter = Segmenter(Voice())
    p.stabiliser = CaptionStabiliser()
    p.origin = time.monotonic()
    p.phrases.put((AudioPhrase(1, 0, 1, np.zeros(512, np.float32), True), 0))
    p.segment_done.set()
    worker = threading.Thread(target=p._recognize)
    worker.start()
    assert entered.wait(2)
    p.pause()
    release.set()
    worker.join(2)
    assert not worker.is_alive() and not any(k == "caption" for k, v in events)


def test_transcript_close_attempts_every_handle_even_after_flush_error(tmp_path):
    from unittest.mock import Mock

    t = Transcript(tmp_path, "cleanup")
    for f in t.files.values():
        f.close()
    handles = {str(i): Mock() for i in range(3)}
    handles["0"].close.side_effect = OSError("disk full")
    t.files = handles
    import pytest

    with pytest.raises(OSError):
        t.close()
    assert t.closed and all(h.close.call_count == 1 for h in handles.values())


def test_finish_latency_endpoint_excludes_trailing_silence():
    class Vad(Voice):
        speaking = True

        def probability(self, frame):
            return float(self.speaking)

    v = Vad()
    s = Segmenter(v)
    frame = np.zeros(512, np.float32)
    for i in range(20):
        s.push(frame, (i + 1) * 0.032)
    v.speaking = False
    for i in range(18):
        result = s.push(frame, (21 + i) * 0.032)
    assert result.final and abs(result.end - 0.640) < 1e-9


def test_pause_during_callback_does_not_stamp_old_audio_with_new_epoch(tmp_path):
    from unittest.mock import patch

    p = Pipeline(ROOT, tmp_path, Settings(), lambda *a: None)

    def crossed_boundary(data):
        p.pause()
        p.pause()
        return 0.0

    with patch("app.pipeline.np.mean", side_effect=crossed_boundary):
        p._frame(np.zeros(512, np.float32), 0.032)
    assert p.epoch == 2 and p.audio.empty()


def test_journal_skips_torn_utf8_and_non_object_records(tmp_path):
    c = Caption(1, 0, 1, "Hello", "你好", True)
    complete = "\n".join(
        [
            json.dumps(
                {"type": "english", **replace(c, chinese="").__dict__},
                ensure_ascii=False,
            ),
            json.dumps({"type": "pair", **c.__dict__}, ensure_ascii=False),
        ]
    ).encode("utf-8")
    original = complete + b'\n[]\n{"chinese":"' + "中".encode("utf-8")[:2]
    journal = tmp_path / "events.jsonl"
    journal.write_bytes(original)
    folder, skipped = recover_journal(journal, tmp_path / "recovered")
    assert skipped == 2
    assert "你好" in (folder / "Bilingual.vtt").read_text(encoding="utf-8")
    assert journal.read_bytes() == original
