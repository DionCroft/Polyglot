"""Beginner controls for optional, local spoken translations."""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
    QPushButton,
    QSpinBox,
    QFormLayout,
    QScrollArea,
)
from app.audio.speech_output import PlaybackController


class UnavailableSpeech:
    def __init__(self, error):
        self.error = error

    def voices(self, refresh=False):
        raise RuntimeError(self.error)

    def prepare(self, *args):
        raise RuntimeError(self.error)

    def stop(self):
        pass


class SpokenAudio(QScrollArea):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        try:
            from app.audio.system_speech import SystemSpeech

            backend = SystemSpeech(owner)
        except ImportError:
            backend = UnavailableSpeech(
                "The system speech component is missing. Repair the app"
            )
        self.player = PlaybackController(backend, self.notice)
        self.setWidgetResizable(True)
        body = QWidget()
        self.setWidget(body)
        layout = QVBoxLayout(body)
        title = QLabel("Hear the translation")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        intro = QLabel(
            "Optional English and Mandarin audio using installed system voices. Captions and transcripts continue independently. Output starts off whenever you open the app."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        layout.addLayout(form)
        self.mode = QComboBox()
        for text, value in (
            ("Off", "off"),
            ("On demand · pauses listening", "manual"),
            ("Automatic · headphones only", "auto"),
        ):
            self.mode.addItem(text, value)
        self.mode.setAccessibleName("Spoken translation mode")
        form.addRow("Playback", self.mode)
        self.headphones = QCheckBox(
            "Headphones connected: playback cannot reach the microphone"
        )
        layout.addWidget(self.headphones)
        row = QHBoxLayout()
        self.speak = QPushButton("Speak last translation")
        self.speak.clicked.connect(owner.speak_translation)
        self.stop = QPushButton("Stop audio")
        self.stop.clicked.connect(self.stop_audio)
        row.addWidget(self.speak)
        row.addWidget(self.stop)
        layout.addLayout(row)
        self.status = QLabel("Spoken translations off")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.message = QLabel()
        self.message.setWordWrap(True)
        self.message.setObjectName("warning")
        self.message.hide()
        layout.addWidget(self.message)
        layout.addLayout(voices_form := QFormLayout())
        self.voice_en = QComboBox()
        self.voice_zh = QComboBox()
        for language, combo in (("en", self.voice_en), ("zh", self.voice_zh)):
            combo.addItem("Automatic installed voice", "")
            combo.setAccessibleName(
                "English voice" if language == "en" else "Mandarin voice"
            )
        voices_form.addRow("English voice", self.voice_en)
        voices_form.addRow("Mandarin voice", self.voice_zh)
        self.rate = QSpinBox()
        self.rate.setRange(-50, 50)
        self.rate.setValue(owner.cfg.speech_rate)
        self.rate.setSuffix("  (0 = normal)")
        voices_form.addRow("Speaking speed", self.rate)
        self.volume = QSpinBox()
        self.volume.setRange(0, 100)
        self.volume.setValue(owner.cfg.speech_volume)
        self.volume.setSuffix("%")
        voices_form.addRow("Volume", self.volume)
        refresh = QPushButton("Refresh installed voices")
        refresh.clicked.connect(self.refresh_voices)
        layout.addWidget(refresh)
        self.voice_status = QLabel(
            "Select a playback mode to check voices. Additional voices may need a one-time download in Windows or macOS settings."
        )
        self.voice_status.setWordWrap(True)
        layout.addWidget(self.voice_status)
        self.note = QLabel(
            "For speakers: finish speaking and wait for the translation, then select Speak last translation. Listening pauses and unfinished speech is discarded. Press Resume after playback. Completed captions stay visible during playback. The normal Pause button still hides captions.\n\nAutomatic playback requires headphones and reads only new completed translations. There is no echo cancellation. Use the system sound settings to select your output device before starting."
        )
        self.shortcut_label = QLabel()
        layout.addWidget(self.shortcut_label)
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        help_button = QPushButton("Voice setup and testing guide")
        help_button.clicked.connect(self.show_help)
        layout.addWidget(help_button)
        layout.addStretch()
        self.mode.currentIndexChanged.connect(self.configure)
        self.headphones.toggled.connect(self.configure)
        for control in (self.voice_en, self.voice_zh):
            control.currentIndexChanged.connect(self.configure)
        self.rate.valueChanged.connect(self.configure)
        self.volume.valueChanged.connect(self.configure)
        self.player.voices = {
            "en": owner.cfg.speech_voice_en,
            "zh": owner.cfg.speech_voice_zh,
        }
        self.player.rate, self.player.volume = self.rate.value(), self.volume.value()
        self.sync()

    def show_help(self):
        self.owner.show_guide()
        self.owner.guide_dialog.pages.setCurrentIndex(
            self.owner.guide_dialog.pages.findData("SPOKEN_AUDIO.md")
        )

    def notice(self, message):
        self.message.setText(message)
        self.message.show()
        self.owner.warn(message)

    def refresh_voices(self):
        self.player.stop()
        try:
            voices = self.player.backend.voices(refresh=True)
            missing = []
            for language, combo in (("en", self.voice_en), ("zh", self.voice_zh)):
                selected = getattr(self.owner.cfg, "speech_voice_" + language)
                combo.blockSignals(True)
                combo.clear()
                combo.addItem("Automatic installed voice", "")
                matches = [v for v in voices if v["language"] == language]
                for voice in matches:
                    combo.addItem(voice["name"] + " · " + voice["locale"], voice["id"])
                if selected and combo.findData(selected) < 0:
                    combo.addItem("Unavailable saved voice — choose another", selected)
                combo.setCurrentIndex(max(0, combo.findData(selected)))
                combo.blockSignals(False)
                if not matches:
                    missing.append("Mandarin" if language == "zh" else "English")
            self.voice_status.setText(
                "Missing voice: "
                + ", ".join(missing)
                + ". Install it in system settings, then Refresh. Captions still work."
                if missing
                else "English and Mandarin voices are installed. Try a short phrase at low volume."
            )
            return True
        except Exception as exc:
            self.voice_status.setText(str(exc))
            return False

    def configure(self, *_):
        previous = self.owner.cfg.speech_mode
        requested = self.mode.currentData()
        self.player.stop()
        if requested != "off" and previous == "off":
            self.refresh_voices()
        self.owner.cfg.speech_mode = requested
        self.player.mode = (
            requested
            if requested != "auto" or self.headphones.isChecked()
            else "manual"
        )
        for language, combo in (("en", self.voice_en), ("zh", self.voice_zh)):
            value = combo.currentData() or ""
            setattr(self.owner.cfg, "speech_voice_" + language, value)
            self.player.voices[language] = value
        self.player.rate = self.owner.cfg.speech_rate = self.rate.value()
        self.player.volume = self.owner.cfg.speech_volume = self.volume.value()
        self.message.hide()
        self.player.status = "Ready for spoken translations"
        self.owner.persist()
        self.sync()

    def stop_audio(self):
        self.player.stop()
        if self.mode.currentData() == "auto":
            self.mode.setCurrentIndex(self.mode.findData("manual"))
        self.sync()

    def new_session(self):
        self.player.reset()
        self.headphones.setChecked(False)
        if self.mode.currentData() == "auto":
            self.player.mode = "manual"
        self.sync()

    def sync(self):
        # Output errors suspend Auto until the lecturer explicitly enables it again.
        if (
            self.mode.currentData() == "auto"
            and self.headphones.isChecked()
            and self.player.mode == "manual"
        ):
            self.mode.blockSignals(True)
            self.mode.setCurrentIndex(self.mode.findData("manual"))
            self.mode.blockSignals(False)
            self.owner.cfg.speech_mode = "manual"
        enabled = self.mode.currentData() != "off"
        busy = self.player.current is not None or bool(self.player.pending)
        engine = self.owner.pipeline
        allowed = (
            not self.owner.closing
            and not self.owner.closer
            and not (
                engine
                and (
                    engine.loading
                    or engine.switching.is_set()
                    or engine.stop_event.is_set()
                )
            )
        )
        self.speak.setEnabled(enabled and self.player.latest is not None and allowed)
        self.stop.setEnabled(busy or self.mode.currentData() == "auto")
        text = self.player.status if enabled else "Spoken translations off"
        if self.mode.currentData() == "auto" and not self.headphones.isChecked():
            text = "Automatic audio waiting: confirm headphones above. On-demand playback is available."
        if engine and engine.paused.is_set():
            text += " · Listening paused — press Resume before speaking."
        self.status.setText(text)
        self.headphones.setVisible(self.mode.currentData() == "auto")
        self.shortcut_label.setText(
            "Speak / Stop shortcut: " + self.owner.cfg.speech_shortcut
        )
        if self.owner.teaching:
            self.owner.teaching.speech_status.setText(text)
            self.owner.teaching.speak.setEnabled(self.speak.isEnabled())
            self.owner.teaching.stop_audio.setEnabled(self.stop.isEnabled())

    def tick(self):
        self.player.tick()
        self.sync()
