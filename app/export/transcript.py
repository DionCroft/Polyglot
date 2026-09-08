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
                json.dumps({"type": "english", **c.__dict__}, ensure_ascii=False)
                + "\n",
            )
            self._write(
                "English Transcript.txt", f"[{timestamp(c.start)}] {c.english}\n"
            )
            self._write(
                "English.srt",
                f"{c.identifier}\n{timestamp(c.start)} --> {timestamp(c.end)}\n{c.english}\n\n",
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
            self._write(
                "Bilingual Transcript.txt",
                f"[{timestamp(c.start)}] {c.english}\n{c.chinese}\n\n",
            )
            self._write(
                "Bilingual.vtt",
                f"{c.identifier}\n{timestamp(c.start, True)} --> {timestamp(c.end, True)}\n{c.english}\n{c.chinese}\n\n",
            )
            if c.chinese:
                self._write(
                    "Chinese Transcript.txt", f"[{timestamp(c.start)}] {c.chinese}\n"
                )
                self._write(
                    "Chinese.srt",
                    f"{c.identifier}\n{timestamp(c.start)} --> {timestamp(c.end)}\n{c.chinese}\n\n",
                )

    def close(self):
        with self.lock:
            if self.closed:
                return
            for identifier, caption in self.pending.items():
                self.ready.setdefault(identifier, caption)
            self._flush_pairs()
            for f in self.files.values():
                f.close()
            self.closed = True
