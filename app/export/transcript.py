import json, re, threading
from collections import OrderedDict
from datetime import datetime
from pathlib import Path


def timestamp(seconds, vtt=False):
    ms = max(0, round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{'.' if vtt else ','}{ms:03}"


class Transcript:
    """Append and flush every event; bounded memory and recoverable JSONL journal."""

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
            language = "English" if c.source_language == "en" else "Chinese"
            self._write(
                language + " Transcript.txt",
                f"[{timestamp(c.start)}] {c.source_text}\n",
            )
            self._write(
                language + ".srt",
                f"{c.identifier}\n{timestamp(c.start)} --> {timestamp(c.end)}\n{c.source_text}\n\n",
            )

    def pair(self, c):
        with self.lock:
            if self.closed:
                return
            self._write(
                "events.jsonl",
                json.dumps({"type": "pair", **c.__dict__}, ensure_ascii=False) + "\n",
            )
            self.ready[c.identifier] = c
            self._flush_pairs()

    def _flush_pairs(self):
        while self.pending:
            identifier = next(iter(self.pending))
            if identifier not in self.ready:
                break
            c = self.ready.pop(identifier)
            self.pending.pop(identifier)
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
            if c.translated_text:
                language = "Chinese" if c.source_language == "en" else "English"
                self._write(
                    language + " Transcript.txt",
                    f"[{timestamp(c.start)}] {c.translated_text}\n",
                )
                self._write(
                    language + ".srt",
                    f"{c.identifier}\n{timestamp(c.start)} --> {timestamp(c.end)}\n{c.translated_text}\n\n",
                )

    def close(self):
        with self.lock:
            if self.closed:
                return
            error = None
            try:
                for identifier, caption in self.pending.items():
                    self.ready.setdefault(identifier, caption)
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
            recovered.english(caption)
            recovered.pair(pairs.get(identifier, caption))
    finally:
        recovered.close()
    return recovered.folder, skipped
