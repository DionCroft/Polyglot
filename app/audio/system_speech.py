"""Use installed Windows/macOS voices through Qt; never fetch voice models."""

import sys
from PySide6.QtTextToSpeech import QTextToSpeech


def voice_language(locale_name):
    if locale_name.startswith("en_"):
        return "en"
    # Hong Kong voices may be Cantonese, so do not offer them for Mandarin.
    if locale_name in {"zh_CN", "zh_TW", "zh_SG"}:
        return "zh"
    return None


class SystemSpeech:
    def __init__(self, parent=None):
        self.parent = parent
        self.engine = None
        self.engine_name = None
        self._voices = None
        self._active = None
        self._began = False

    def _ensure(self):
        if self.engine is not None:
            return
        available = QTextToSpeech.availableEngines()
        candidates = (
            ("darwin", "macos") if sys.platform == "darwin" else ("winrt", "sapi")
        )
        for name in candidates:
            if name not in available:
                continue
            engine = QTextToSpeech(name, self.parent)
            if (
                engine.state() == QTextToSpeech.State.Error
                or not engine.availableLocales()
            ):
                engine.deleteLater()
                continue
            self.engine, self.engine_name = engine, name
            engine.stateChanged.connect(self._state)
            engine.errorOccurred.connect(self._error)
            return
        raise RuntimeError(
            "No installed system speech engine is available. Repair the app or install a system voice"
        )

    def voices(self, refresh=False):
        self._ensure()
        if self._voices is not None and not refresh:
            return self._voices
        result = []
        for locale in self.engine.availableLocales():
            language = voice_language(locale.name())
            if language is None:
                continue
            self.engine.setLocale(locale)
            for voice in self.engine.availableVoices():
                # Avoid third-party SAPI providers that may use online synthesis.
                if sys.platform == "win32" and not voice.name().startswith(
                    "Microsoft "
                ):
                    continue
                result.append(
                    {
                        "id": locale.name() + "|" + voice.name(),
                        "name": voice.name(),
                        "locale": locale.name(),
                        "language": language,
                        "voice": voice,
                    }
                )
        self._voices = result
        return result

    def prepare(self, language, preferred, rate, volume):
        voices = [v for v in self.voices() if v["language"] == language]
        if not voices:
            raise RuntimeError(
                "Install an offline "
                + ("Mandarin Chinese" if language == "zh" else "English")
                + " voice in system settings, then Refresh voices. See Help → Spoken translations"
            )
        selected = next((v for v in voices if v["id"] == preferred), None)
        if preferred and selected is None:
            raise RuntimeError(
                "The selected voice is no longer installed. Choose an available voice in Spoken audio"
            )
        selected = selected or next(
            (
                v
                for v in voices
                if v["locale"] == ("zh_CN" if language == "zh" else "en_GB")
            ),
            voices[0],
        )
        self.engine.setLocale(selected["voice"].locale())
        self.engine.setVoice(selected["voice"])
        self.engine.setRate(rate / 100.0)
        self.engine.setVolume(volume / 100.0)

    def play(self, text, done, error):
        self._active = (done, error)
        self._began = False
        self.engine.say(text)

    def _state(self, state):
        if self._active is None:
            return
        if state == QTextToSpeech.State.Speaking:
            self._began = True
        elif (
            state == QTextToSpeech.State.Ready
            and self._began
            and self.engine.state() == QTextToSpeech.State.Ready
        ):
            done, _ = self._active
            self._active = None
            done()
        elif state == QTextToSpeech.State.Error:
            self._error(None, self.engine.errorString())

    def _error(self, reason, message):
        if self._active:
            _, error = self._active
            self._active = None
            error(message or "System voice failed")

    def stop(self):
        self._active = None
        if self.engine is not None:
            self.engine.stop(QTextToSpeech.BoundaryHint.Immediate)
