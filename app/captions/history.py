"""Session reading history, independent of live-caption epochs and disk saving."""

from collections import OrderedDict
from dataclasses import dataclass

from app.captions.state import Caption
from app.languages import caption_labels


@dataclass(frozen=True)
class HistoryChange:
    key: tuple
    added: bool
    removed: tuple | None = None


def passage_text(entry):
    minutes, seconds = divmod(max(0, int(entry.start)), 60)
    stamp = f"[{minutes // 60:02}:{minutes % 60:02}:{seconds:02}]"
    if not isinstance(entry, Caption):
        return f"{stamp} Speech not transcribed\n{entry.reason}"
    en_label, zh_label = caption_labels(entry.source_language)
    missing = (
        "Translation unavailable"
        if entry.translation_status == "unavailable"
        else "Translating…"
    )
    lines = [(en_label, entry.english), (zh_label, entry.chinese)]
    if entry.source_language == "zh":
        lines.reverse()
    return (
        stamp + "\n" + "\n".join(f"{label}: {text or missing}" for label, text in lines)
    )


class TranscriptHistory:
    # About fourteen hours even at one completed passage every five seconds.
    # The export journal remains complete; no disk writes are needed for this view.
    def __init__(self, limit=10000):
        if limit < 1:
            raise ValueError("History limit must be positive")
        self.limit = limit
        self.entries = OrderedDict()
        self.newest = (-1, -1)
        self.trimmed = 0

    def accept(self, entry):
        if isinstance(entry, Caption) and (not entry.final or not entry.source_text):
            return None
        key = (entry.epoch, entry.identifier)
        old = self.entries.get(key)
        if old is not None:
            # A late source event must never erase a translation or an explicit gap.
            if not isinstance(old, Caption) or old == entry:
                return None
            if isinstance(entry, Caption) and (
                old.translated_text or old.translation_status == "unavailable"
            ):
                return None
            self.entries[key] = entry
            return HistoryChange(key, False)
        if key <= self.newest:
            return None  # An evicted passage cannot be resurrected by late work.
        self.newest = key
        self.entries[key] = entry
        removed = None
        if len(self.entries) > self.limit:
            removed, _ = self.entries.popitem(last=False)
            self.trimmed += 1
        return HistoryChange(key, True, removed)

    def recent(self, count=4):
        keys = []
        for key in reversed(self.entries):
            keys.append(key)
            if len(keys) >= count:
                break
        return [self.entries[key] for key in reversed(keys)]

    def text(self):
        return "\n\n".join(passage_text(entry) for entry in self.entries.values())

    def clear(self):
        self.entries.clear()
        self.newest = (-1, -1)
        self.trimmed = 0
