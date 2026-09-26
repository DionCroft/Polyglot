"""Reading history must survive boundaries without altering saved transcripts."""

from dataclasses import replace

from app.asr.language_detection import UncertainTurn
from app.captions.history import TranscriptHistory, passage_text
from app.captions.state import Caption
from app.config.settings import Settings
from app.export.transcript import recover_journal, Transcript
from app.pipeline import Pipeline


def test_partial_duplicate_and_late_translation_do_not_duplicate_or_reorder():
    history = TranscriptHistory()
    first = Caption(1, 0, 4, "Critical path", final=True)
    assert history.accept(replace(first, final=False)) is None
    assert history.accept(first).added
    assert history.accept(first) is None
    second = Caption(2, 4, 8, "", "请再解释一次", True, source_language="zh")
    history.accept(second)
    pair = replace(first, chinese="关键路径", translation_status="complete")
    assert not history.accept(pair).added
    assert history.accept(first) is None
    assert list(history.entries.values()) == [pair, second]
    assert history.text().count("Critical path") == 1
    assert "简体中文 · spoken: 请再解释一次" in history.text()


def test_completed_history_survives_pause_language_epochs_and_late_work():
    history = TranscriptHistory()
    old = Caption(1, 0, 3, "Risk register", final=True)
    history.accept(old)
    history.accept(Caption(2, 4, 7, "", "风险登记册", True, 2, source_language="zh"))
    history.accept(replace(old, chinese="风险登记册", translation_status="complete"))
    assert len(history.entries) == 2
    assert history.entries[(0, 1)].chinese == "风险登记册"
    assert "Translating…" in history.text()


def test_missing_translation_and_uncertain_language_are_explicit():
    history = TranscriptHistory()
    source = Caption(1, 0, 1, "Hello", final=True)
    history.accept(source)
    history.accept(replace(source, translation_status="unavailable"))
    history.accept(UncertainTurn(2, 1, 2))
    assert "Translation unavailable" in history.text()
    assert "Speech not transcribed" in history.text()
    assert history.accept(Caption(2, 1, 2, "Invented", final=True)) is None


def test_retention_bounds_memory_and_cannot_resurrect_evicted_passages():
    history = TranscriptHistory(limit=20)
    for i in range(1500):
        history.accept(Caption(i, i * 5, i * 5 + 4, f"Passage {i}", "翻译", True))
    assert len(history.entries) == 20 and history.trimmed == 1480
    assert history.accept(Caption(1, 0, 1, "Very late", "迟到", True)) is None
    assert len(history.recent()) == 4
    assert history.recent()[-1].identifier == 1499
    history.clear()
    assert not history.entries and history.trimmed == 0
    assert history.accept(Caption(1, 0, 1, "New session", final=True)).added


def test_saving_off_still_delivers_committed_history_without_writing(tmp_path):
    events = []
    pipeline = Pipeline(
        tmp_path,
        tmp_path,
        Settings(save_transcripts=False),
        lambda *event: events.append(event),
    )
    caption = Caption(1, 0, 2, "CO7000", final=True)
    pipeline._save("english", caption)
    pipeline.paused.set()
    pipeline.epoch += 1
    pipeline._save(
        "pair", replace(caption, chinese="项目管理", translation_status="complete")
    )
    assert [event[0] for event in events] == ["transcript-entry", "transcript-entry"]
    history = TranscriptHistory()
    for _, entry in events:
        history.accept(entry)
    assert len(history.entries) == 1 and "项目管理" in history.text()
    assert list(tmp_path.iterdir()) == []


def test_journal_exports_are_unchanged_by_reading_history(tmp_path):
    events = []
    pipeline = Pipeline(
        tmp_path, tmp_path, Settings(), lambda *event: events.append(event)
    )
    pipeline.export = Transcript(tmp_path, "Bilingual class")
    for i, lang in enumerate(["en", "zh", "en"], 1):
        source = Caption(
            i,
            i * 4,
            i * 4 + 3,
            "Critical path" if lang == "en" else "",
            "关键路径" if lang == "zh" else "",
            True,
            i,
            source_language=lang,
        )
        pipeline._save("english", source)
        pipeline._save(
            "pair",
            replace(
                source,
                english="Critical path",
                chinese="关键路径",
                translation_status="complete",
            ),
        )
    pipeline.export.close()
    folder = pipeline.export.folder
    recovered, skipped = recover_journal(
        folder / "events.jsonl", tmp_path / "recovered"
    )
    assert skipped == 0
    for path in folder.iterdir():
        if path.name != "events.jsonl":
            assert path.read_bytes() == (recovered / path.name).read_bytes()
    history = TranscriptHistory()
    for _, entry in events:
        history.accept(entry)
    assert len(history.entries) == 3


def test_projector_settings_validate_and_keep_compact_available():
    assert Settings.from_dict({}).overlay_layout == "rolling"
    cfg = Settings.from_dict({"overlay_layout": "compact", "projector_height": 9000})
    assert cfg.overlay_layout == "compact" and cfg.projector_height == 1200
    assert Settings.from_dict({"overlay_layout": "invalid"}).overlay_layout == "rolling"
    assert passage_text(Caption(1, 3661, 3665, "Hello", final=True)).startswith(
        "[01:01:01]"
    )
