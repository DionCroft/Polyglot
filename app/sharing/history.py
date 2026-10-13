"""Disk-backed caption history. No model, Qt or network dependencies."""

import json
import queue
import sqlite3
import threading
import time
from pathlib import Path

MAX_TEXT = 128 * 1024
MAX_PAGE = 120


class Database:
    def __init__(self, path, *, write=False):
        self.path = Path(path)
        if write:
            self.conn = sqlite3.connect(self.path, timeout=2)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA cache_size=-2048")
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS entries(
                    identifier INTEGER PRIMARY KEY, payload TEXT NOT NULL,
                    english TEXT NOT NULL, chinese TEXT NOT NULL,
                    rank INTEGER NOT NULL, revision INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            """)
            for key, value in {
                "revision": "0",
                "count": "0",
                "state": "Waiting for lecture",
                "coverage": "From the start of sharing",
            }.items():
                self.conn.execute(
                    "INSERT OR IGNORE INTO meta VALUES (?,?)", (key, value)
                )
            self.conn.commit()
        else:
            self.conn = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=2
            )
            self.conn.execute("PRAGMA query_only=ON")
            self.conn.execute("PRAGMA cache_size=-1024")
        self.conn.row_factory = sqlite3.Row
        self.conn.set_progress_handler(
            lambda: int(time.monotonic() > self.deadline), 1000
        )
        self.deadline = float("inf")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        try:
            self.conn.rollback() if exc_type else self.conn.commit()
        finally:
            self.conn.close()

    def meta(self):
        data = dict(self.conn.execute("SELECT key,value FROM meta").fetchall())
        data["revision"] = int(data["revision"])
        data["count"] = int(data["count"])
        return data

    def set_meta(self, key, value):
        if key not in {"state", "coverage"}:
            raise ValueError("Unknown metadata")
        self.conn.execute("UPDATE meta SET value=? WHERE key=?", (str(value), key))
        self.conn.execute(
            "UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'"
        )

    def put(self, kind, caption):
        if kind not in {"english", "source", "pair", "gap", "audio_gap", "uncertain"}:
            return
        c = dict(caption if isinstance(caption, dict) else caption.__dict__)
        if kind not in {"gap", "audio_gap", "uncertain"} and not c.get("final"):
            return
        if any(
            len(str(c.get(k, ""))) > MAX_TEXT for k in ("english", "chinese", "reason")
        ):
            raise ValueError(
                "Phone sharing stopped: a caption exceeded the safe text limit; no text was truncated."
            )
        kind = "gap" if kind == "audio_gap" else kind
        c["kind"] = (
            "gap"
            if kind == "gap"
            else "uncertain"
            if kind == "uncertain"
            else "caption"
        )
        c.setdefault("english", "")
        c.setdefault("chinese", "")
        c.setdefault("source_language", "en")
        c.setdefault("translation_status", "pending")
        rank = (
            3
            if c["kind"] != "caption" or c["translation_status"] == "complete"
            else 2
            if c["translation_status"] == "unavailable"
            else 1
        )
        payload = json.dumps(c, ensure_ascii=False, separators=(",", ":"))
        old = self.conn.execute(
            "SELECT rank,payload FROM entries WHERE identifier=?", (c["identifier"],)
        ).fetchone()
        if old and (old["rank"] > rank or old["payload"] == payload):
            return
        self.conn.execute(
            "UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'"
        )
        revision = int(
            self.conn.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[
                0
            ]
        )
        if not old:
            self.conn.execute(
                "UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='count'"
            )
        self.conn.execute(
            "INSERT OR REPLACE INTO entries VALUES (?,?,?,?,?,?)",
            (c["identifier"], payload, c["english"], c["chinese"], rank, revision),
        )

    def page(
        self, *, before=None, after=None, start=None, limit=40, query="", version=None
    ):
        limit = max(1, min(MAX_PAGE, int(limit)))
        query = query[:120]
        self.deadline = time.monotonic() + 1
        self.conn.execute("BEGIN") if not self.conn.in_transaction else None
        try:
            result = self.meta()
            if version is not None and result["revision"] == version:
                return dict(result, unchanged=True)
            clauses = []
            args = []
            if query:
                clauses.append(
                    "(instr(lower(english),lower(?)) OR instr(lower(chinese),lower(?)))"
                )
                args += [query, query]
            base = " AND ".join(clauses) or "1"
            if before is not None:
                clauses.append("identifier<?")
                args.append(int(before))
            elif after is not None:
                clauses.append("identifier>?")
                args.append(int(after))
            elif start is not None:
                clauses.append("identifier>=?")
                args.append(int(start))
            order = (
                "ASC"
                if after is not None or start is not None or (query and before is None)
                else "DESC"
            )
            rows = self.conn.execute(
                "SELECT identifier,payload FROM entries WHERE "
                + (" AND ".join(clauses) or "1")
                + " ORDER BY identifier "
                + order
                + " LIMIT ?",
                (*args, limit),
            ).fetchall()
            if order == "DESC":
                rows = list(reversed(rows))
            entries = [json.loads(row["payload"]) for row in rows]
            search_args = [query, query] if query else []
            lo = entries[0]["identifier"] if entries else 0
            hi = entries[-1]["identifier"] if entries else 0
            more_before = bool(
                entries
                and self.conn.execute(
                    "SELECT 1 FROM entries WHERE " + base + " AND identifier<? LIMIT 1",
                    (*search_args, lo),
                ).fetchone()
            )
            more_after = bool(
                entries
                and self.conn.execute(
                    "SELECT 1 FROM entries WHERE " + base + " AND identifier>? LIMIT 1",
                    (*search_args, hi),
                ).fetchone()
            )
            return dict(
                result, entries=entries, more_before=more_before, more_after=more_after
            )
        finally:
            self.conn.commit()
            self.deadline = float("inf")

    def text_lines(self, view="both"):
        if view not in {"en", "zh", "both"}:
            raise ValueError("Unknown language view")
        yield "LectureLive — shared caption transcript\n\n"
        for row in self.conn.execute("SELECT payload FROM entries ORDER BY identifier"):
            c = json.loads(row[0])
            seconds = max(0, int(c["start"]))
            yield f"[{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}]\n"
            if c["kind"] != "caption":
                yield (
                    ("[Audio lost] " if c["kind"] == "gap" else "[Not transcribed] ")
                    + c["reason"]
                    + "\n\n"
                )
                continue
            source = c["source_language"]
            if view == source and c["translation_status"] != "complete":
                yield (
                    "[Translation unavailable]"
                    if c["translation_status"] == "unavailable"
                    else "[Translation pending]"
                ) + "\n"
            for lang, label in [("en", "English"), ("zh", "简体中文")]:
                if view != "both" and view != lang:
                    continue
                text = c["english" if lang == "en" else "chinese"]
                if not text and source != lang:
                    text = (
                        "[Translation unavailable]"
                        if c["translation_status"] == "unavailable"
                        else "[Translation pending]"
                    )
                yield (
                    label
                    + (" · spoken: " if source == lang else " · translation: ")
                    + text
                    + "\n"
                )
            yield "\n"


class HistoryWriter:
    """Non-blocking bounded fan-out; disk work never runs in the audio callback."""

    max_bytes = 4 * 1024 * 1024
    max_disk = 512 * 1024 * 1024

    def __init__(self, path, *, journal=None, capacity=256):
        self.path = Path(path)
        self.journal = journal
        self.queue = queue.Queue(maxsize=capacity)
        self.lock = threading.Lock()
        self.queued_bytes = 0
        self.error = ""
        self.ready = threading.Event()
        self.ending = threading.Event()
        self.thread = threading.Thread(
            target=self._run, name="Phone caption history", daemon=True
        )

    def start(self):
        self.thread.start()

    def submit(self, kind, caption):
        if self.error or self.ending.is_set():
            return False
        if kind == "meta":
            size = 256
        else:
            size = (
                sum(
                    len(str(getattr(caption, k, ""))) * 4
                    for k in ("english", "chinese", "reason")
                )
                + 1024
            )
        with self.lock:
            if self.error:
                return False
            if self.queued_bytes + size > self.max_bytes or self.queue.full():
                self.error = "Phone sharing stopped: its history writer could not keep up. Local captions and normal transcript saving continue."
                return False
            self.queued_bytes += size
            self.queue.put_nowait((kind, caption, size))
        return True

    def _run(self):
        try:
            with Database(self.path, write=True) as db:
                if self.journal:
                    path, length = self.journal
                    imported = 0
                    with Path(path).open("rb") as source:
                        while source.tell() < length:
                            if self.ending.is_set():
                                return
                            line = source.readline(MAX_TEXT * 8)
                            if not line or source.tell() > length:
                                break
                            record = json.loads(line.decode("utf-8"))
                            kind = record.pop("type")
                            db.put(kind, record)
                            imported += 1
                            if imported % 128 == 0:
                                db.conn.commit()
                                self.check_disk()
                    db.set_meta(
                        "coverage", "Includes earlier saved captions from this lecture"
                    )
                    db.conn.commit()
                self.ready.set()
                while not self.ending.is_set() or not self.queue.empty():
                    try:
                        item = self.queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    kind, caption, size = item
                    try:
                        if kind == "meta":
                            db.set_meta(*caption)
                        else:
                            db.put(kind, caption)
                        db.conn.commit()
                        self.check_disk()
                    except Exception as exc:
                        self.error = (
                            "Phone sharing stopped: "
                            + str(exc)
                            + ". Local captions and normal transcript saving continue."
                        )
                        raise
                    finally:
                        with self.lock:
                            self.queued_bytes -= size
                        self.queue.task_done()
        except Exception as exc:
            self.error = (
                "Phone sharing stopped: "
                + str(exc)
                + ". Local captions and normal transcript saving continue."
            )
        finally:
            self.ready.set()

    def check_disk(self):
        if (
            sum(
                p.stat().st_size
                for p in (self.path, Path(str(self.path) + "-wal"))
                if p.exists()
            )
            > self.max_disk
        ):
            raise OSError("Phone history disk limit reached")

    def flush(self, timeout=5):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if self.error:
                return False
            if self.ready.is_set() and not self.queue.unfinished_tasks:
                return True
            time.sleep(0.01)
        return False

    def close(self):
        self.ending.set()
        if self.thread.is_alive():
            self.thread.join(5)
