"""Bounded, cancellable offline pipeline. No Qt or network dependencies."""

import logging, queue, threading, time
from dataclasses import dataclass, field, replace
from collections import deque
import numpy as np
from app.audio.capture import Microphone, WavSource
from app.audio.vad import Segmenter
from app.captions.stabiliser import CaptionStabiliser
from app.captions.glossary import Glossary
from app.export.transcript import Transcript
from app.asr.language_detection import PhraseLanguage, UncertainTurn

log = logging.getLogger(__name__)


@dataclass
class TurnBoundary:
    """A FIFO barrier acknowledged only after captured speech and translation drain."""

    identifier: int = -1
    final: bool = True
    done: threading.Event = field(default_factory=threading.Event)


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
        self.accelerated = False
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
        self.switching = threading.Event()
        self.capture_lock = threading.RLock()
        self.switch_lock = threading.Lock()
        self._store = model_store
        self.active_language = (
            settings.speaking_language if settings.speaking_language != "auto" else "en"
        )
        self.auto_language = PhraseLanguage()
        self.translators = {}
        self.auto_waiting = None
        self.metrics["uncertain_language_phrases"] = 0
        from opencc import OpenCC

        self.simplify = OpenCC("t2s")

    def _notify(self, kind, value):
        self.emit(kind, value)

    def start(self):
        self.loading = True
        try:
            self._notify("state", "Loading local models…")
            from app.system.models import ModelStore

            self._store = self.model_store or ModelStore(self.root)
            bundle = self._store.load(
                self.settings.profile, self.force_cpu, self.settings.accelerator
            )
            self.asr, self.mt = bundle.asr, bundle.mt
            self.translators = {"en": self.mt}
            if self.settings.speaking_language in {"zh", "auto"}:
                self.translators["zh"] = self._store.translation_for("zh")
                if self.settings.speaking_language == "auto":
                    self.translators["en"] = self._store.translation_for("en")
                else:
                    self.mt = self.translators["zh"]
            self._configure_speech()
            self.using_npu = bundle.npu
            self.accelerated = bundle.accelerated
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
        with self.capture_lock:
            self._accept_frame(frame, end)

    def _accept_frame(self, frame, end):
        epoch = self.epoch
        if self.stop_event.is_set() or self.paused.is_set() or self.switching.is_set():
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
        if self.stop_event.is_set() or self.switching.is_set():
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
        while (self.stop_event.is_set() or self.switching.is_set()) and len(
            self.phrases
        ) >= self.phrases.capacity:
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
                if isinstance(frame, TurnBoundary):
                    if epoch == self.epoch and not self.paused.is_set():
                        phrase = self.segmenter.finish(end)
                        if phrase:
                            self._submit_phrase(phrase, current)
                    self._submit_phrase(frame, current)
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
        # Committed history also works with saving off. Unlike the live overlay,
        # it accepts late translations of speech committed before a pause/switch.
        self._notify("transcript-entry", caption)
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
                self._notify("transcript-saving", False)
                log.exception("Transcript write failed")
                try:
                    writer.close()
                except Exception:
                    log.exception("Failed transcript cleanup")
                self._notify(
                    "warning",
                    "Transcript saving stopped: check disk space or folder access. Live captions continue; earlier journal entries can be recovered.",
                )

    def _configure_speech(self, language=None):
        if language is not None:
            self.active_language = language
        elif self.settings.speaking_language != "auto":
            self.active_language = self.settings.speaking_language
        configure = getattr(self.asr, "configure_recognition", None)
        if configure:
            args = (
                self.settings.recognition_mode,
                "\n".join(self.glossary.vocabulary)
                if self.settings.vocabulary_guidance and self.active_language == "en"
                else "",
            )
            if self.active_language == "en":
                configure(*args)
            else:
                configure(*args, language=self.active_language)

    def switch_language(self, language):
        """Run off the GUI thread. Preserve one transcript and the microphone clock."""
        from app.languages import validate_selection

        validate_selection(language)
        with self.switch_lock:
            if not self.started or self.loading or self.stop_event.is_set():
                raise RuntimeError(
                    "Wait until the lecture is listening before switching."
                )
            if self.failure_reported:
                raise RuntimeError(
                    "Reconnect the microphone before switching languages."
                )
            if language == self.settings.speaking_language:
                return
            boundary = TurnBoundary()
            with self.capture_lock:
                self.switching.set()
            self._notify("state", "Switching language… finish speaking and wait")
            try:
                # No new audio can enter behind the marker, even from an active callback.
                self.audio.put((boundary, self.last_audio_end, self.epoch))
                while not boundary.done.wait(0.1):
                    if self.asr_done.is_set() or self.segment_done.is_set():
                        raise RuntimeError(
                            "Speech processing stopped before the language switch."
                        )
                if self.stop_event.is_set():
                    return
                if self.failure_reported:
                    raise RuntimeError(
                        "Speech input failed. Stop and reconnect before switching."
                    )
                if language == "auto":
                    translators = {
                        key: self._store.translation_for(key) for key in ("en", "zh")
                    }
                    translator = translators[self.active_language]
                else:
                    translator = self._store.translation_for(language)
                    translators = {**self.translators, language: translator}
                if self.stop_event.is_set():
                    return
                previous = self.settings
                self.settings = replace(self.settings, speaking_language=language)
                try:
                    self._configure_speech()
                except Exception:
                    self.settings = previous
                    self._configure_speech()
                    raise
                self.mt = translator
                self.translators = translators
                self.auto_language = PhraseLanguage()
                self.auto_waiting = None
                self.segmenter.reset()
                self.stabiliser.reset()
                self.epoch += 1
                self._notify("language", language)
            finally:
                self.switching.clear()
                if not self.stop_event.is_set() and not self.failure_reported:
                    self._notify(
                        "state", "Paused" if self.paused.is_set() else "Listening"
                    )

    def _recover_cpu(self):
        if not (self.using_npu or self.accelerated):
            return False
        from app.asr.cpu_whisper import CpuWhisper
        from app.system.architecture import cpu_profile

        close = getattr(self.asr, "close", None)
        if close:
            close()
        self.asr = CpuWhisper(
            self.root / "models/whisper" / cpu_profile(self.settings.profile)
        )
        self._configure_speech()
        self.using_npu = self.accelerated = False
        if self.model_store:
            self.model_store.invalidate()
        self._notify("backend", self.asr.name)
        self._notify(
            "warning",
            "Accelerator processing failed. This phrase was retried on local CPU; captions continue.",
        )
        return True

    def _transcribe(self, audio, final=True):
        try:
            self.asr.final_pass = final
            return self.asr.transcribe(audio)
        except Exception:
            log.exception("Speech inference failed; checking CPU recovery")
            if not self._recover_cpu():
                raise
            self.asr.final_pass = final
            return self.asr.transcribe(audio)

    def _detect_language(self, audio):
        try:
            return self.asr.detect_language(audio)
        except Exception:
            log.exception("Language detection failed; checking CPU recovery")
            if not self._recover_cpu():
                raise
            return self.asr.detect_language(audio)

    def _automatic_language(self, phrase, epoch):
        key = (epoch, phrase.identifier)
        voiced = (
            phrase.voiced_seconds
            if phrase.voiced_seconds is not None
            else len(phrase.audio) / 16000
        )
        if self.auto_waiting != key:
            self.auto_waiting = key
            self._notify(
                "language-detection", {"epoch": epoch, "language": None, "final": False}
            )
        if (
            not phrase.final
            and self.auto_language.key == key
            and self.auto_language.locked
        ):
            return self.auto_language.locked
        scores = (
            self._detect_language(phrase.audio)
            if voiced >= (0.32 if phrase.final else 1.2)
            else {}
        )
        language = self.auto_language.decide(
            key, scores, voiced, len(phrase.audio), phrase.final
        )
        if epoch != self.epoch or self.paused.is_set():
            return None
        if language:
            self._configure_speech(language)
            self._notify(
                "language-detection",
                {"epoch": epoch, "language": language, "final": phrase.final},
            )
        elif phrase.final:
            self.metrics["uncertain_language_phrases"] += 1
            notice = UncertainTurn(phrase.identifier, phrase.start, phrase.end, epoch)
            self._save("uncertain", notice)
            self._notify(
                "language-detection",
                {
                    "epoch": epoch,
                    "language": None,
                    "final": True,
                    "identifier": phrase.identifier,
                },
            )
        return language

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
            if isinstance(phrase, TurnBoundary):
                self.translation.put(phrase)
                continue
            if epoch != self.epoch or self.paused.is_set():
                continue
            try:
                start = time.monotonic()
                language = self.settings.speaking_language
                if language == "auto":
                    language = self._automatic_language(phrase, epoch)
                    if language is None:
                        continue
                text = self._transcribe(phrase.audio, final=phrase.final)
                elapsed = time.monotonic() - start
                self.metrics.update(
                    asr_seconds=elapsed,
                    rtf=elapsed / max(0.032, len(phrase.audio) / 16000),
                )
                if epoch != self.epoch or self.paused.is_set():
                    continue
                if text.rstrip().endswith((".", "?", "!", "。", "？", "！")):
                    self.segmenter.sentence_complete(phrase.identifier)
                caption = self.stabiliser.accept(
                    phrase,
                    self.glossary.english(text)
                    if language == "en"
                    else self.simplify.convert(text),
                    epoch,
                    language,
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
                        if self.stop_event.is_set() or self.switching.is_set():
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
                            "Translation is behind. Recognised speech continues; a translation was skipped.",
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
            if isinstance(caption, TurnBoundary):
                caption.done.set()
                continue
            if isinstance(caption, UncertainTurn):
                self._save("uncertain", caption)
                continue
            try:
                start = time.monotonic()
                translator = self.translators.get(caption.source_language, self.mt)
                text = (
                    self.glossary.chinese(
                        caption.english, translator.translate(caption.english)
                    )
                    if translator and caption.source_language == "en"
                    else translator.translate(caption.chinese)
                    if translator
                    else ""
                )
                self.metrics["translation_seconds"] = time.monotonic() - start
                caption = replace(
                    caption,
                    **(
                        {"chinese": text}
                        if caption.source_language == "en"
                        else {"english": text}
                    ),
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
                    "Translation failed locally. Recognised speech continues.",
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
            "speaking_language": self.settings.speaking_language,
            "detected_language": self.active_language
            if self.settings.speaking_language == "auto"
            else None,
            "switching_language": self.switching.is_set(),
            "recognition_mode": self.settings.recognition_mode,
            "vocabulary_guidance": self.settings.vocabulary_guidance,
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
        if not self.model_store and self._store:
            self._store.close()
        self.started = False
        log.info("Session stopped; all pipeline workers joined")
