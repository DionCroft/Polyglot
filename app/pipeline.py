"""Bounded, cancellable offline pipeline. No Qt or network dependencies."""

import logging, queue, threading, time
from dataclasses import replace
from collections import deque
import numpy as np
from app.audio.capture import Microphone, WavSource
from app.audio.vad import Segmenter
from app.captions.stabiliser import CaptionStabiliser
from app.captions.glossary import Glossary
from app.export.transcript import Transcript

log = logging.getLogger(__name__)


class PhraseQueue:
    """Final boundaries replace queued partials; capacity is always bounded."""

    def __init__(self, capacity=4):
        self.items = deque()
        self.capacity = capacity
        self.condition = threading.Condition()

    def put(self, item):
        phrase, epoch = item
        with self.condition:
            self.items = deque(
                x
                for x in self.items
                if not (x[0].identifier == phrase.identifier and x[1] == epoch)
            )
            dropped = None
            if len(self.items) >= self.capacity:
                partial = next((x for x in self.items if not x[0].final), None)
                if partial is not None:
                    self.items.remove(partial)
                elif not phrase.final:
                    return item
                else:
                    dropped = self.items.popleft()
            self.items.append(item)
            self.condition.notify()
            return dropped

    def get(self, timeout=0.1):
        with self.condition:
            if not self.items:
                self.condition.wait(timeout)
            return self.items.popleft() if self.items else None

    def clear(self):
        with self.condition:
            self.items.clear()

    def __len__(self):
        with self.condition:
            return len(self.items)


class Pipeline:
    def __init__(
        self,
        root,
        data,
        settings,
        emit,
        vocabulary="",
        title="Lecture",
        wav=None,
        force_cpu=False,
        model_store=None,
    ):
        self.root = root
        self.data = data
        self.settings = settings
        self.emit = emit
        self.title = title
        self.wav = wav
        self.using_npu = False
        self.force_cpu = force_cpu
        self.model_store = model_store
        self.glossary = Glossary(
            root / "glossaries" / f"{settings.glossary}.json", vocabulary
        )
        self.stop_event = threading.Event()
        self.input_closed = threading.Event()
        self.segment_done = threading.Event()
        self.asr_done = threading.Event()
        self.export_lock = threading.RLock()
        self.latencies = {key: deque(maxlen=2048) for key in ("english", "bilingual")}
        self.last_audio_end = 0.0
        self.paused = threading.Event()
        self.epoch = 0
        self.audio = queue.Queue(maxsize=128)
        self.phrases = PhraseQueue(4)
        self.translation = queue.Queue(maxsize=4)
        self.threads = []
        self.source = None
        self.export = None
        self.started = False
        self.loading = False
        self.level = 0
        self.metrics = {
            "dropped_audio_chunks": 0,
            "dropped_phrases": 0,
            "translation_skips": 0,
            "asr_seconds": 0,
            "translation_seconds": 0,
            "rtf": 0,
            "english_latency": 0,
            "bilingual_latency": 0,
        }
        self.failure_reported = False
        self.last_meter = 0
        self.last_warning = 0

    def _notify(self, kind, value):
        self.emit(kind, value)

    def start(self):
        self.loading = True
        try:
            self._notify("state", "Loading local models…")
            from app.system.models import ModelStore

            bundle = (self.model_store or ModelStore(self.root)).load(
                self.settings.profile, self.force_cpu
            )
            self.asr, self.mt = bundle.asr, bundle.mt
            self.using_npu = bundle.npu
            for message in bundle.messages:
                self._notify("warning", message)
            self.segmenter = Segmenter(bundle.vad)
            self.segmenter.reset()
            self.stabiliser = CaptionStabiliser()
            if self.stop_event.is_set():
                return
            if self.settings.save_transcripts:
                try:
                    self.export = Transcript(self.data / "transcripts", self.title)
                    self._notify("transcript", str(self.export.folder))
                except OSError:
                    log.exception("Transcript directory unavailable")
                    self._notify(
                        "warning",
                        "Transcript saving unavailable. Check free space and folder permissions.",
                    )
            self.origin = time.monotonic()
            self.started = True
            for name, fn in [
                ("VAD", self._segment),
                ("ASR", self._recognize),
                ("Translation", self._translate),
            ]:
                thread = threading.Thread(
                    target=fn, name=f"LectureLive {name}", daemon=False
                )
                self.threads.append(thread)
                thread.start()
            if self.wav:
                self.source = WavSource(
                    self.wav,
                    self._frame,
                    self._error,
                    lambda: self._notify(
                        "warning",
                        "WAV replay finished. Captions remain visible; stop to finish the session.",
                    ),
                )
            else:
                self.source = Microphone(
                    self.settings.microphone
                    if self.settings.microphone != ""
                    else None,
                    self._frame,
                    self._error,
                )
            self.source.start()
            log.info(
                "Started backend=%s translation=%s", self.asr.name, self.mt is not None
            )
            self._notify("backend", self.asr.name)
            self._notify("state", "Paused" if self.paused.is_set() else "Listening")
        except Exception as e:
            log.exception("Cannot start lecture")
            self._error(str(e), True)
        finally:
            self.loading = False

    def _frame(self, frame, end):
        epoch = self.epoch
        if self.stop_event.is_set() or self.paused.is_set():
            return
        self.last_audio_end = end
        self.level = min(100, int(float(np.sqrt(np.mean(frame * frame))) * 450))
        try:
            if epoch != self.epoch or self.paused.is_set() or self.stop_event.is_set():
                return
            self.audio.put_nowait((frame, end, epoch))
        except queue.Full:
            self.metrics["dropped_audio_chunks"] += 1

    def _error(self, message, fatal=False):
        if not fatal:
            if time.monotonic() - self.last_warning < 5:
                return
            self.last_warning = time.monotonic()
        if fatal:
            self.paused.set()
            self.epoch += 1
            self.failure_reported = True
            self._notify("state", "Input unavailable — stop and retry")
        self._notify("warning", message)

    def pause(self):
        if self.stop_event.is_set():
            return
        if self.paused.is_set():
            if self.failure_reported:
                return
            self.epoch += 1
            self.paused.clear()
            self._notify("state", "Listening")
        else:
            self.paused.set()
            self.epoch += 1
            self.level = 0
            self.phrases.clear()
            self._notify("state", "Paused")
        while True:
            try:
                self.audio.get_nowait()
            except queue.Empty:
                break

    def _submit_phrase(self, phrase, epoch):
        # Once capture stops, preserve accepted final phrases instead of dropping
        # them to maintain live latency. The downstream worker still drains.
        while self.stop_event.is_set() and len(self.phrases) >= self.phrases.capacity:
            if self.asr_done.wait(0.02):
                return
        dropped = self.phrases.put((phrase, epoch))
        if dropped and dropped[0].final:
            self.metrics["dropped_phrases"] += 1
            self._notify(
                "warning",
                "Recognition is behind live speech. A phrase was skipped; try Fast mode.",
            )

    def _segment(self):
        epoch = -1
        last_end = None
        try:
            while not self.input_closed.is_set() or not self.audio.empty():
                try:
                    frame, end, current = self.audio.get(timeout=0.1)
                except queue.Empty:
                    continue
                if current != self.epoch or self.paused.is_set():
                    continue
                if current != epoch or (last_end is not None and end - last_end > 0.05):
                    self.segmenter.reset()
                    epoch = current
                last_end = end
                phrase = self.segmenter.push(frame, end)
                if phrase:
                    self._submit_phrase(phrase, current)
            if (
                last_end is not None
                and epoch == self.epoch
                and not self.paused.is_set()
            ):
                phrase = self.segmenter.finish(last_end)
                if phrase:
                    self._submit_phrase(phrase, epoch)
        except Exception:
            log.exception("VAD failed")
            self._error("Voice detection failed. Stop and restart the session.", True)
        finally:
            self.segment_done.set()

    def _save(self, method, caption):
        # ASR and translation both write exports. Detach a failed writer before
        # cleanup so another worker cannot reuse it or emit repeated errors.
        with self.export_lock:
            writer = self.export
            if writer is None:
                return
            try:
                getattr(writer, method)(caption)
            except OSError:
                self.export = None
                log.exception("Transcript write failed")
                try:
                    writer.close()
                except Exception:
                    log.exception("Failed transcript cleanup")
                self._notify(
                    "warning",
                    "Transcript saving stopped: check disk space or folder access. Live captions continue; earlier journal entries can be recovered.",
                )

    def _transcribe(self, audio):
        try:
            return self.asr.transcribe(audio)
        except Exception:
            if not self.using_npu:
                raise
            log.exception("NPU failed during lecture; retrying this phrase on CPU")
            from app.asr.cpu_whisper import CpuWhisper

            self.asr = CpuWhisper(self.root / "models/whisper/fast")
            self.using_npu = False
            text = self.asr.transcribe(audio)
            if self.model_store:
                self.model_store.invalidate()
            self._notify("backend", self.asr.name)
            self._notify(
                "warning",
                "NPU processing failed. This phrase was retried on local CPU; captions continue.",
            )
            return text

    def _recognize(self):
        try:
            self._recognize_loop()
        finally:
            self.asr_done.set()

    def _recognize_loop(self):
        while not self.segment_done.is_set() or len(self.phrases):
            item = self.phrases.get()
            if not item:
                continue
            phrase, epoch = item
            if epoch != self.epoch or self.paused.is_set():
                continue
            try:
                start = time.monotonic()
                text = self._transcribe(phrase.audio)
                elapsed = time.monotonic() - start
                self.metrics.update(
                    asr_seconds=elapsed,
                    rtf=elapsed / max(0.032, len(phrase.audio) / 16000),
                )
                if epoch != self.epoch or self.paused.is_set():
                    continue
                if text.rstrip().endswith((".", "?", "!")):
                    self.segmenter.sentence_complete(phrase.identifier)
                caption = self.stabiliser.accept(
                    phrase, self.glossary.english(text), epoch
                )
                if not caption:
                    continue
                self.metrics["english_latency"] = max(
                    0, time.monotonic() - self.origin - phrase.end
                )
                self.latencies["english"].append(self.metrics["english_latency"])
                self._notify("caption", caption)
                if caption.final:
                    self._save("english", caption)
                    try:
                        if self.stop_event.is_set():
                            self.translation.put(caption)
                        else:
                            self.translation.put_nowait(caption)
                    except queue.Full:
                        self.metrics["translation_skips"] += 1
                        caption = replace(caption, translation_status="unavailable")
                        self._save("pair", caption)
                        self._notify("caption", caption)
                        self._notify(
                            "warning",
                            "Chinese translation is behind. English captions continue; a translation was skipped.",
                        )
                log.info(
                    "ASR %.3fs rtf %.3f final=%s",
                    elapsed,
                    self.metrics["rtf"],
                    caption.final,
                )
            except Exception:
                log.exception("Speech inference failed")
                self._error(
                    "Speech recognition failed locally. Stop and restart; try Fast mode.",
                    True,
                )

    def _translate(self):
        while (
            not (
                self.asr_done.is_set()
                or (not self.started and self.stop_event.is_set())
            )
            or not self.translation.empty()
        ):
            try:
                caption = self.translation.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                start = time.monotonic()
                text = (
                    self.glossary.chinese(
                        caption.english, self.mt.translate(caption.english)
                    )
                    if self.mt
                    else ""
                )
                self.metrics["translation_seconds"] = time.monotonic() - start
                caption = replace(
                    caption,
                    chinese=text,
                    translation_status="complete" if text else "unavailable",
                )
                self.metrics["bilingual_latency"] = max(
                    0, time.monotonic() - self.origin - caption.end
                )
                self.latencies["bilingual"].append(self.metrics["bilingual_latency"])
                if caption.epoch == self.epoch and not self.paused.is_set():
                    self._notify("caption", caption)
            except Exception:
                caption = replace(caption, translation_status="unavailable")
                if caption.epoch == self.epoch and not self.paused.is_set():
                    self._notify("caption", caption)
                log.exception("Translation failed")
                self._notify(
                    "warning",
                    "Chinese translation failed locally. English captions continue.",
                )
            finally:
                self._save("pair", caption)

    def diagnostics(self):
        if (
            isinstance(self.source, Microphone)
            and self.source.stream is not None
            and not self.stop_event.is_set()
            and not self.failure_reported
        ):
            if (
                not self.source.stream.active
                or time.monotonic() - self.source.last_callback > 3
            ):
                self._error(
                    "Microphone disconnected. Stop, refresh microphones, and start again.",
                    True,
                )
        return {
            **self.metrics,
            **{
                f"{key}_p95_seconds": round(float(np.percentile(values, 95)), 3)
                if values
                else 0
                for key, values in self.latencies.items()
            },
            "audio_queue": self.audio.qsize(),
            "asr_queue": len(self.phrases),
            "translation_queue": self.translation.qsize(),
        }

    def request_stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.level = 0
            self._notify("state", "Finishing captions…")

    def close(self):
        self.request_stop()
        try:
            if self.source:
                self.source.close()
        except Exception:
            log.exception("Audio source cleanup failed")
            self._notify(
                "warning", "Audio cleanup reported an error; finishing captured speech."
            )
        finally:
            self.input_closed.set()
        for thread in self.threads:
            # Keep the UI informed if a slow backend delays shutdown.
            while thread.is_alive():
                thread.join(timeout=5)
                if thread.is_alive():
                    self._notify(
                        "state", "Finishing captions… waiting for local processing"
                    )
        with self.export_lock:
            writer, self.export = self.export, None
            if writer:
                try:
                    writer.close()
                except OSError:
                    log.exception("Final transcript flush failed")
                    self._notify(
                        "warning",
                        "Final transcript save failed. Earlier journal entries remain available for recovery.",
                    )
        self.started = False
        log.info("Session stopped; all pipeline workers joined")
