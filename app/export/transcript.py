import json, re, threading
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from app.asr.language_detection import UncertainTurn
from app.captions.state import AudioGap


def timestamp(seconds, vtt=False):
    ms = max(0, round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{'.' if vtt else ','}{ms:03}"


class Transcript:
    """Append and flush every event; bounded memory and recoverable JSONL journal."""

    capacity = 32

    def __init__(self, root, title):
        clean = (
            re.sub(r"[^\w .-]", "_", title, flags=re.UNICODE).strip(" .")[:70]
            or "Lecture"
        )
        self.folder = Path(root) / (
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f") + "_" + clean
        )
        self.folder.mkdir(parents=True)
        self.lock = threading.RLock()
        self.pending = OrderedDict()
        self.ready = {}
        self.written = {"en": set(), "zh": set()}
        self.closed = False
        names = [
            "English Transcript.txt",
            "Chinese Transcript.txt",
            "Bilingual Transcript.txt",
            "English.srt",
            "Chinese.srt",
            "Bilingual.vtt",
            "events.jsonl",
        ]
        self.files = {
            n: (self.folder / n).open("w", encoding="utf-8", newline="\n")
            for n in names
        }
        self.files["Bilingual.vtt"].write("WEBVTT\n\n")

    def _write(self, name, text):
        self.files[name].write(text)
        self.files[name].flush()

    def english(self, c):
        with self.lock:
            if self.closed:
                return
            self.pending[c.identifier] = c
            self._write(
                "events.jsonl",
                json.dumps(
                    {
                        "type": "english" if c.source_language == "en" else "source",
                        **c.__dict__,
                    },
                    ensure_ascii=False,
                )
                + "\n",
            )
            self._flush_languages()

    @property
    def full(self):
        with self.lock:
            return len(self.pending) >= self.capacity

    def pair(self, c):
        with self.lock:
            if self.closed:
                return
            self._write(
                "events.jsonl",
                json.dumps({"type": "pair", **c.__dict__}, ensure_ascii=False) + "\n",
            )
            self.ready[c.identifier] = c
            self._flush_languages()
            self._flush_pairs()

    def uncertain(self, turn):
        self._notice("uncertain", turn)

    def gap(self, turn):
        self._notice("audio_gap", turn)

    def _notice(self, kind, turn):
        with self.lock:
            if self.closed:
                return
            self._write(
                "events.jsonl",
                json.dumps({"type": kind, **turn.__dict__}, ensure_ascii=False) + "\n",
            )
            self.pending[turn.identifier] = turn
            self.ready[turn.identifier] = turn
            self._flush_languages()
            self._flush_pairs()

    @staticmethod
    def _notice_text(turn):
        prefix = "[Audio lost] " if isinstance(turn, AudioGap) else "[Not transcribed] "
        return prefix + turn.reason

    def _flush_languages(self):
        # Each language has its own ordered cursor: source text can be saved
        # immediately unless an earlier translation into that language is pending.
        for code, language in (("en", "English"), ("zh", "Chinese")):
            for identifier, source in self.pending.items():
                if identifier in self.written[code]:
                    continue
                if isinstance(source, (AudioGap, UncertainTurn)):
                    text = self._notice_text(source)
                elif source.source_language == code:
                    text = source.source_text
                elif identifier in self.ready:
                    text = self.ready[identifier].translated_text
                else:
                    break
                if not text:
                    self.written[code].add(identifier)
                    continue
                self._write(
                    language + " Transcript.txt",
                    f"[{timestamp(source.start)}] {text}\n",
                )
                self._write(
                    language + ".srt",
                    f"{identifier}\n{timestamp(source.start)} --> {timestamp(source.end)}\n{text}\n\n",
                )
                self.written[code].add(identifier)

    def _flush_pairs(self):
        while self.pending:
            identifier = next(iter(self.pending))
            if identifier not in self.ready:
                break
            c = self.ready.pop(identifier)
            self.pending.pop(identifier)
            for written in self.written.values():
                written.discard(identifier)
            if isinstance(c, (AudioGap, UncertainTurn)):
                message = self._notice_text(c)
                self._write(
                    "Bilingual Transcript.txt", f"[{timestamp(c.start)}] {message}\n\n"
                )
                self._write(
                    "Bilingual.vtt",
                    f"{c.identifier}\n{timestamp(c.start, True)} --> {timestamp(c.end, True)}\n{message}\n\n",
                )
                continue
            from app.languages import caption_labels

            en_label, zh_label = caption_labels(c.source_language)
            labelled = f"{en_label}: {c.english}\n{zh_label}: {c.chinese}"
            self._write(
                "Bilingual Transcript.txt",
                f"[{timestamp(c.start)}] {labelled}\n\n",
            )
            self._write(
                "Bilingual.vtt",
                f"{c.identifier}\n{timestamp(c.start, True)} --> {timestamp(c.end, True)}\n{c.english}\n{c.chinese}\n\n",
            )

    def close(self):
        with self.lock:
            if self.closed:
                return
            error = None
            try:
                for identifier, caption in self.pending.items():
                    self.ready.setdefault(identifier, caption)
                self._flush_languages()
                self._flush_pairs()
            except OSError as exc:
                error = exc
            finally:
                self.closed = True
                for handle in self.files.values():
                    try:
                        handle.close()
                    except OSError as exc:
                        error = error or exc
            if error:
                raise error


def recover_journal(journal, destination):
    """Rebuild new exports from complete journal records; never overwrite originals."""
    from app.captions.state import Caption

    english, pairs = {}, {}
    skipped = 0
    with Path(journal).open("rb") as source:
        for line in source:
            try:
                event = json.loads(line.decode("utf-8"))
                if not isinstance(event, dict):
                    raise ValueError("Invalid journal record")
                kind = event.pop("type")
                if kind in {"uncertain", "audio_gap"}:
                    turn = (AudioGap if kind == "audio_gap" else UncertainTurn)(**event)
                    english[turn.identifier] = turn
                    continue
                caption = Caption(**event)
                if kind in {"english", "source"}:
                    english[caption.identifier] = caption
                elif kind == "pair":
                    pairs[caption.identifier] = caption
                else:
                    skipped += 1
            except (ValueError, TypeError, KeyError):
                skipped += 1
    recovered = Transcript(destination, "Recovered lecture")
    try:
        for identifier in sorted(english):
            caption = english[identifier]
            if isinstance(caption, (AudioGap, UncertainTurn)):
                if isinstance(caption, AudioGap):
                    recovered.gap(caption)
                else:
                    recovered.uncertain(caption)
                continue
            recovered.english(caption)
            recovered.pair(pairs.get(identifier, caption))
    finally:
        recovered.close()
    return recovered.folder, skipped
