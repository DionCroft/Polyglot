"""Phone history consumes final records, independent of the projector and audio queues."""

from dataclasses import replace
import json
from pathlib import Path
import threading

from app.captions.display import CaptionDisplay
from app.captions.state import Caption, AudioGap
from app.asr.language_detection import UncertainTurn
from app.export.transcript import Transcript
from app.sharing.history import Database, HistoryWriter


def caption(i, language="en", complete=False):
    return Caption(
        i,
        i * 2,
        i * 2 + 1,
        f"English {i}" if complete or language == "en" else "",
        f"中文 {i}" if complete or language == "zh" else "",
        True,
        epoch=i // 4,
        source_language=language,
        translation_status="complete" if complete else "pending",
    )


def test_investigation_overlay_replaces_text_while_exports_retain_it(tmp_path):
    display = CaptionDisplay()
    writer = Transcript(tmp_path, "Long explanation")
    paragraphs = []
    for i in range(1, 9):
        c = replace(
            caption(i, complete=True),
            english=(f"paragraph-{i} " * 600),
            chinese=(f"段落{i}。" * 600),
        )
        display.accept(c)
        writer.english(replace(c, chinese="", translation_status="pending"))
        writer.pair(c)
        paragraphs.append(c)
    writer.close()
    assert display.contents()[:2] == (paragraphs[-1].english, paragraphs[-1].chinese)
    saved = (writer.folder / "Bilingual Transcript.txt").read_text(encoding="utf-8")
    assert all(c.english in saved and c.chinese in saved for c in paragraphs)
    assert "paragraph-1" not in display.contents()[0]


def test_delayed_pairs_update_original_entries_without_duplicates(tmp_path):
    with Database(tmp_path / "history.sqlite", write=True) as db:
        for i in range(1, 7):
            db.put("english", caption(i, "en" if i % 2 else "zh"))
        for i in (6, 4, 2, 5, 3, 1):
            db.put("pair", caption(i, "en" if i % 2 else "zh", True))
        db.put("english", caption(1))  # late bootstrap must not erase a translation
        db.put("pair", caption(2, "zh", True))
        rows = db.page(limit=120)["entries"]
        assert [r["identifier"] for r in rows] == list(range(1, 7))
        assert all(
            r["english"] and r["chinese"] and r["translation_status"] == "complete"
            for r in rows
        )
        assert db.meta()["count"] == 6


def test_full_paragraphs_not_truncated_and_search_reaches_old_history(tmp_path):
    text = "A technical paragraph with risk probability and impact. " * 300
    with Database(tmp_path / "h.sqlite", write=True) as db:
        for i in range(1, 2001):
            c = caption(i, complete=True)
            if i == 1:
                c = replace(
                    c, english=text + "needle-first", chinese="完整中文。" * 300
                )
            db.put("pair", c)
        assert len(db.page(limit=120)["entries"]) == 120
        assert (
            db.page(query="needle-first")["entries"][0]["english"]
            == text + "needle-first"
        )
        assert "English 2000" in "".join(db.text_lines("en"))
        assert text in "".join(db.text_lines("both"))
        ids = []
        after = 0
        while True:
            page = db.page(after=after, limit=120)["entries"]
            if not page:
                break
            ids.extend(r["identifier"] for r in page)
            after = ids[-1]
        assert ids == list(range(1, 2001))


def test_notices_failures_and_pending_are_honest_in_every_download(tmp_path):
    with Database(tmp_path / "h.sqlite", write=True) as db:
        db.put("english", caption(1))
        db.put("pair", replace(caption(2), translation_status="unavailable"))
        db.put("gap", AudioGap(3, 6, 7))
        db.put("uncertain", UncertainTurn(4, 8, 9))
        for view in ["en", "zh", "both"]:
            text = "".join(db.text_lines(view))
            assert "[Audio lost]" in text and "[Not transcribed]" in text
            assert "Translation unavailable" in text and "Translation pending" in text
        assert db.page(query="complete")["entries"] == []


def test_partial_hypotheses_are_not_persisted(tmp_path):
    with Database(tmp_path / "h.sqlite", write=True) as db:
        db.put("english", replace(caption(1), final=False))
        assert db.meta()["count"] == 0


def test_writer_replays_journal_and_accepts_live_updates(tmp_path):
    original = Transcript(tmp_path, "Earlier lecture")
    original.english(caption(1))
    original.pair(caption(1, complete=True))
    original.close()
    journal = original.folder / "events.jsonl"
    writer = HistoryWriter(
        tmp_path / "h.sqlite", journal=(journal, journal.stat().st_size)
    )
    writer.submit("english", caption(2, "zh"))
    writer.submit("pair", caption(2, "zh", True))
    writer.start()
    assert writer.flush(5)
    with Database(writer.path) as db:
        assert db.meta()["count"] == 2
        assert all(r["translation_status"] == "complete" for r in db.page()["entries"])
    writer.close()
    assert not writer.error


def test_bounded_writer_reports_overload_instead_of_blocking(tmp_path):
    writer = HistoryWriter(tmp_path / "h.sqlite", capacity=2)
    assert writer.submit("english", caption(1))
    assert writer.submit("pair", caption(1, complete=True))
    assert not writer.submit("english", caption(2))
    assert writer.error and "stopped" in writer.error.lower()
    assert writer.queue.qsize() == 2


def test_pipeline_sink_runs_when_text_saving_is_off_and_cannot_break_exports(tmp_path):
    from app.pipeline import Pipeline
    from app.config.settings import Settings

    seen = []
    p = Pipeline(
        Path(__file__).resolve().parents[1],
        tmp_path,
        Settings(save_transcripts=False),
        lambda *a: None,
        caption_sink=lambda kind, c: seen.append((kind, c)),
    )
    p._save("pair", caption(1, complete=True))
    assert len(seen) == 1 and p.export is None
    p.export = Transcript(tmp_path, "Independent export")
    p.caption_sink = lambda *a: (_ for _ in ()).throw(OSError("phone disk failed"))
    p._save("english", caption(2))
    p._save("pair", caption(2, complete=True))
    p.export.close()
    assert "English 2" in (p.export.folder / "Bilingual Transcript.txt").read_text(
        encoding="utf-8"
    )
    assert p.caption_sink is None


def test_old_epoch_translation_is_shared_while_projector_stays_paused(tmp_path):
    from test_conversations import running_pipeline
    from test_auto_language import phrase, wait

    p, events, translator = running_pipeline(tmp_path)
    writer = HistoryWriter(tmp_path / "phone.sqlite")
    writer.start()
    p.caption_sink = writer.submit
    entered, release = threading.Event(), threading.Event()
    original = p.mt.translate

    def delayed(text):
        entered.set()
        assert release.wait(5)
        return original(text)

    p.mt.translate = delayed
    try:
        phrase(p, 1, 0.2)
        assert entered.wait(5)
        p.pause()
        assert p.paused.is_set()
        release.set()
        wait(lambda: any(c[0] == "caption" for c in events))
    finally:
        release.set()
        p.close()
    assert writer.flush()
    with Database(writer.path) as db:
        rows = db.page()["entries"]
        assert rows and all(r["translation_status"] == "complete" for r in rows)
        assert all(r["english"] and r["chinese"] for r in rows)
    writer.close()


def test_byte_budget_and_disk_failure_are_visible(tmp_path):
    writer = HistoryWriter(tmp_path / "h.sqlite")
    writer.max_bytes = 2000
    assert not writer.submit(
        "pair", replace(caption(1, complete=True), english="x" * 1000)
    )
    assert writer.error and writer.queue.empty()
    writer = HistoryWriter(tmp_path / "disk.sqlite")
    writer.max_disk = 1
    writer.start()
    writer.submit("pair", caption(1, complete=True))
    assert not writer.flush()
    assert "disk limit" in writer.error
    writer.close()


def test_service_stop_deletes_history_and_revokes_link(tmp_path):
    import time
    from app.sharing.service import SharingSession

    session = SharingSession(tmp_path, "127.0.0.1")
    session.start()
    try:
        end = time.monotonic() + 15
        while not session.url and not session.problem() and time.monotonic() < end:
            time.sleep(0.02)
        assert session.url and not session.problem()
        assert session.capture("pair", caption(1, complete=True))
        assert session.history.flush()
    finally:
        session.close()
    assert session.process.poll() is not None
    assert not session.folder.exists()
