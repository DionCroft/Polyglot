"""Optional translation playback. No imports of microphone or inference code."""

from collections import deque
import time


class PlaybackController:
    """Called on the UI thread; at most one active and two waiting utterances."""

    capacity = 2
    max_age = 20.0
    max_characters = 800
    timeout = 120.0

    def __init__(self, backend, notify, clock=time.monotonic):
        self.backend = backend
        self.notify = notify
        self.clock = clock
        self.mode = "off"
        self.voices = {"en": "", "zh": ""}
        self.rate = 0
        self.volume = 80
        self.pending = deque()
        self.latest = None
        self.current = None
        self.highest = -1
        self.generation = 0
        self.status = "Spoken translations off"

    def accept(self, caption):
        if not caption.final or caption.identifier <= self.highest:
            return
        if caption.translation_status == "unavailable":
            self.highest = caption.identifier
            self.forget_latest()
            return
        if (
            caption.translation_status != "complete"
            or not caption.translated_text.strip()
            or caption.source_language not in {"en", "zh"}
        ):
            return
        self.highest = caption.identifier
        self.latest = caption
        if self.mode == "auto":
            if len(self.pending) >= self.capacity:
                self.pending.popleft()
                self.notify(
                    "Speech fell behind; older queued audio was skipped. Captions and transcripts are unchanged."
                )
            self.pending.append((caption, self.clock()))

    def forget_latest(self):
        self.latest = None

    def stop(self, clear_latest=False):
        self.generation += 1
        self.pending.clear()
        self.current = None
        try:
            self.backend.stop()
        except Exception:
            # A broken output device must never prevent stopping a lecture.
            self.notify(
                "Speech output could not stop normally. Turn down the system volume if needed."
            )
        if clear_latest:
            self.latest = None
        self.status = "Audio stopped"

    def reset(self):
        self.stop(clear_latest=True)
        self.highest = -1

    def speak_latest(self, before_start=lambda: None):
        if self.mode == "off" or self.latest is None:
            return False
        caption = self.latest
        self.stop()
        return self._start(caption, before_start)

    def tick(self):
        if self.current is not None:
            if self.clock() - self.current[1] > self.timeout:
                self._fail("Speech playback timed out")
            return
        if self.mode != "auto":
            return
        while self.pending:
            caption, queued = self.pending.popleft()
            if self.clock() - queued > self.max_age:
                self.notify(
                    "Speech fell behind; expired audio was skipped. Captions and transcripts are unchanged."
                )
                continue
            self._start(caption)
            break

    def _start(self, caption, before_start=lambda: None):
        text = caption.translated_text.strip()
        if len(text) > self.max_characters:
            self.notify(
                "This translation is too long to read live. Read the captions or saved transcript; no shortened audio was generated."
            )
            return False
        language = "zh" if caption.source_language == "en" else "en"
        try:
            self.backend.prepare(
                language, self.voices[language], self.rate, self.volume
            )
            before_start()
            token = self.generation = self.generation + 1
            self.current = (caption, self.clock())
            self.status = "Speaking " + ("Mandarin" if language == "zh" else "English")
            self.backend.play(
                text,
                lambda: self._done(token),
                lambda error: self._failed(token, error),
            )
            return True
        except Exception as exc:
            self._fail(str(exc))
            return False

    def _done(self, token):
        if token != self.generation:
            return
        self.current = None
        self.status = "Audio finished"

    def _failed(self, token, message):
        if token == self.generation:
            self._fail(message)

    def _fail(self, message):
        self.stop()
        self.mode = "manual"
        self.status = "Audio unavailable · captions continue"
        self.notify(
            "Speech output unavailable: "
            + message
            + ". Captions continue. Automatic playback is off."
        )
