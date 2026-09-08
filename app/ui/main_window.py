import json, logging, threading
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QLineEdit,
    QPlainTextEdit,
    QTabWidget,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QFileDialog,
    QScrollArea,
    QColorDialog,
)
from app.config.settings import ROOT, DATA, Settings
from app.audio.capture import microphones
from app.pipeline import Pipeline
from app.ui.overlay import Overlay
from app.system.windows import Hotkeys

STYLE = """
QWidget { background:#111a21; color:#e8f0f3; font-family:'Segoe UI'; font-size:14px; }
QMainWindow { background:#111a21; }
QLabel,QCheckBox { background:transparent; }
QLabel#previewEnglish { font-size:26px; font-weight:500; }
QLabel#previewChinese { font-family:'Microsoft YaHei UI'; font-size:24px; color:#8ce2c9; }
QLabel#brand { font-size:30px; font-weight:700; letter-spacing:-1px; }
QLabel#muted { color:#97adb8; }
QLabel#status { color:#8ce2c9; background:#193830; border-radius:12px; padding:7px 15px; font-weight:600; }
QLabel#warning { color:#ffd59b; background:#342a20; padding:12px; border-radius:8px; }
QGroupBox { background:#18242d; border:1px solid #2c3d48; border-radius:12px; margin-top:16px; padding:12px 16px 12px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:16px; padding:0 6px; color:#a5bdc9; }
QComboBox,QLineEdit,QSpinBox,QPlainTextEdit { background:#111d26; border:1px solid #3b505e; border-radius:7px; padding:10px; selection-background-color:#24725e; }
QComboBox { min-height:20px; }
QLineEdit { min-height:20px; }
QComboBox::drop-down { border:0; width:25px; }
QPushButton { background:#283b49; border:1px solid #3b5262; border-radius:8px; padding:12px 18px; font-weight:600; }
QPushButton:hover { background:#344f60; }
QPushButton:disabled { color:#70838d; background:#1d2b34; }
QPushButton#primary { background:#8ce2c9; border:0; color:#0b2b24; font-size:18px; padding:17px; }
QPushButton#primary:hover { background:#b4f4df; }
QCheckBox { spacing:10px; padding:5px; }
QCheckBox::indicator { width:20px; height:20px; }
QProgressBar { background:#101c24; border:0; border-radius:4px; max-height:8px; }
QProgressBar::chunk { background:#8ce2c9; border-radius:4px; }
QTabWidget::pane { border:0; padding-top:12px; }
QTabBar::tab { color:#97adb8; padding:12px 22px; border-bottom:2px solid transparent; }
QTabBar::tab:selected { color:#8ce2c9; border-bottom:2px solid #8ce2c9; }
QScrollArea { border:0; }
"""


class Bridge(QObject):
    event = Signal(str, object)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = Settings.load()
        self.pipeline = None
        self.loader = None
        self.closer = None
        self.closing = False
        self.wav = None
        self.checker = None
        self.bridge = Bridge()
        self.bridge.event.connect(self.on_event)
        self.last_caption = None
        self.transcript_path = DATA / "transcripts"
        self.setWindowTitle("LectureLive")
        self.resize(1060, 920)
        self.setMinimumSize(860, 760)
        self.setStyleSheet(STYLE)
        self.overlay = Overlay(self.cfg)
        self.overlay.moved.connect(self.persist)
        host = QWidget()
        self.setCentralWidget(host)
        layout = QVBoxLayout(host)
        layout.setContentsMargins(28, 22, 28, 20)
        layout.setSpacing(16)
        head = QHBoxLayout()
        brand = QVBoxLayout()
        name = QLabel("LectureLive")
        name.setObjectName("brand")
        brand.addWidget(name)
        tagline = QLabel("Offline bilingual live captions for teaching")
        tagline.setObjectName("muted")
        brand.addWidget(tagline)
        head.addLayout(brand)
        head.addStretch()
        self.status = QLabel("●  Ready")
        self.status.setObjectName("status")
        head.addWidget(self.status, 0, Qt.AlignVCenter)
        layout.addLayout(head)
        self.warning = QLabel()
        self.warning.setObjectName("warning")
        self.warning.setWordWrap(True)
        self.warning.hide()
        layout.addWidget(self.warning)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)
        tabs.addTab(self.lecture_tab(), "Lecture")
        tabs.addTab(self.appearance_tab(), "Overlay")
        tabs.addTab(self.diagnostics_tab(), "Diagnostics")
        tabs.addTab(self.about_tab(), "About")
        footer = QHBoxLayout()
        privacy = QLabel("LOCAL PROCESSING  ·  ENGLISH → 简体中文")
        privacy.setObjectName("muted")
        footer.addWidget(privacy)
        footer.addStretch()
        shortcut = QLabel("Pause  Ctrl+Alt+Space     Lock  Ctrl+Alt+C")
        shortcut.setObjectName("muted")
        footer.addWidget(shortcut)
        layout.addLayout(footer)
        self.hotkeys = Hotkeys(QApplication.instance(), self.toggle_lock, self.pause)
        if self.hotkeys.errors:
            self.warn(
                "Shortcut already in use: "
                + ", ".join(self.hotkeys.errors)
                + ". Use the on-screen controls."
            )
        QApplication.instance().screenAdded.connect(self.refresh_displays)
        QApplication.instance().screenRemoved.connect(self.display_removed)
        self.refresh_displays()
        self.refresh_microphones()
        self.readiness()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(250)
        self.start_button.setEnabled(False)
        self.status.setText("●  Checking local models…")
        self.checker = threading.Thread(
            target=self.check_local_models, name="LectureLive readiness", daemon=False
        )
        self.checker.start()

    def check_local_models(self):
        from app.system.readiness import check

        try:
            result = check(ROOT, self.cfg.profile)
        except Exception:
            logging.exception("Readiness check failed")
            result = {
                "speech": False,
                "vad": False,
                "translation": False,
                "npu": False,
                "messages": ["Readiness check failed. See local logs."],
            }
        self.bridge.event.emit("readiness", result)

    def group(self, title):
        box = QGroupBox(title)
        form = QVBoxLayout(box)
        form.setSpacing(10)
        return box, form

    def lecture_tab(self):
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        controls = QWidget()
        left = QVBoxLayout(controls)
        left.setContentsMargins(0, 0, 0, 0)
        mic, form = self.group("MICROPHONE")
        row = QHBoxLayout()
        self.microphone = QComboBox()
        row.addWidget(self.microphone, 1)
        refresh = QPushButton("↻")
        refresh.setToolTip("Refresh microphones")
        refresh.setMaximumWidth(52)
        refresh.clicked.connect(self.refresh_microphones)
        row.addWidget(refresh)
        form.addLayout(row)
        self.meter = QProgressBar()
        self.meter.setRange(0, 100)
        self.meter.setTextVisible(False)
        form.addWidget(self.meter)
        note = QLabel("Shared audio input · audio recording is off")
        note.setObjectName("muted")
        form.addWidget(note)
        left.addWidget(mic)
        captions, form = self.group("CAPTIONS")
        self.mode = QComboBox()
        self.mode.addItems(["Bilingual", "English", "Chinese"])
        self.mode.setCurrentText(self.cfg.mode)
        self.mode.currentTextChanged.connect(self.set_mode)
        form.addWidget(self.mode)
        self.profile = QComboBox()
        for title, key in [
            ("Fast · Whisper Base", "fast"),
            ("Balanced · Whisper Small", "balanced"),
            ("Accuracy · not installed", "accuracy"),
        ]:
            exists = (ROOT / "models/whisper" / key / "config.json").exists()
            self.profile.addItem(
                title if exists or key == "accuracy" else title + " · not installed",
                key,
            )
            self.profile.model().item(self.profile.count() - 1).setEnabled(exists)
        idx = self.profile.findData(self.cfg.profile)
        self.profile.setCurrentIndex(max(0, idx))
        form.addWidget(self.profile)
        left.addWidget(captions)
        topic, form = self.group("LECTURE")
        self.title = QLineEdit()
        self.title.setPlaceholderText("Lecture title (optional)")
        form.addWidget(self.title)
        self.glossary = QComboBox()
        for path in sorted((ROOT / "glossaries").glob("*.json")):
            self.glossary.addItem(path.stem.replace("_", " ").title(), path.stem)
        self.glossary.setCurrentIndex(max(0, self.glossary.findData(self.cfg.glossary)))
        form.addWidget(self.glossary)
        self.save = QCheckBox("Save text transcripts and subtitles")
        self.save.setChecked(self.cfg.save_transcripts)
        form.addWidget(self.save)
        left.addWidget(topic)
        self.start_button = QPushButton("Start lecture")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.start_stop)
        left.addWidget(self.start_button)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause)
        left.addWidget(self.pause_button)
        left.addStretch()
        right = QVBoxLayout()
        preview, form = self.group("CAPTION PREVIEW")
        self.preview_en = QLabel("Your words. Understood.")
        self.preview_en.setObjectName("previewEnglish")
        self.preview_en.setWordWrap(True)
        self.preview_en.setFont(QFont("Segoe UI", 22))
        form.addWidget(self.preview_en)
        self.preview_zh = QLabel("让每一句话，都被听懂。")
        self.preview_zh.setObjectName("previewChinese")
        self.preview_zh.setWordWrap(True)
        self.preview_zh.setFont(QFont("Microsoft YaHei UI", 20))
        form.addWidget(self.preview_zh)
        self.preview_hint = QLabel("Stable English and Chinese appear together.")
        self.preview_hint.setObjectName("muted")
        self.preview_hint.setWordWrap(True)
        form.addWidget(self.preview_hint)
        row = QHBoxLayout()
        self.show_button = QPushButton("Show overlay")
        self.show_button.clicked.connect(self.toggle_overlay)
        self.lock_button = QPushButton("Lock overlay")
        self.lock_button.clicked.connect(self.toggle_lock)
        row.addWidget(self.show_button)
        row.addWidget(self.lock_button)
        form.addLayout(row)
        right.addWidget(preview)
        terms, form = self.group("TODAY’S VOCABULARY")
        self.vocabulary = QPlainTextEdit()
        self.vocabulary.setPlaceholderText(
            "One term per line, for example:\nESP32\nFreeRTOS\ninterrupt service routine"
        )
        self.vocabulary.setMaximumHeight(140)
        form.addWidget(self.vocabulary)
        label = QLabel(
            "Preserves spelling of exact matches. This backend does not support acoustic vocabulary biasing."
        )
        label.setWordWrap(True)
        label.setObjectName("muted")
        form.addWidget(label)
        right.addWidget(terms)
        self.ready = QLabel()
        self.ready.setWordWrap(True)
        self.ready.setObjectName("muted")
        right.addWidget(self.ready)
        right.addStretch()
        grid.addWidget(controls, 0, 0)
        grid.addLayout(right, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return widget

    def appearance_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        scroll.setWidget(widget)
        form = QFormLayout(widget)
        form.setVerticalSpacing(18)
        self.displays = QComboBox()
        self.displays.currentIndexChanged.connect(self.select_display)
        form.addRow("Caption display", self.displays)
        self.control_displays = QComboBox()
        self.control_displays.currentIndexChanged.connect(self.select_control_display)
        form.addRow("Control panel display", self.control_displays)
        self.placement = QComboBox()
        self.placement.addItems(["Bottom", "Top", "Custom"])
        self.placement.setCurrentText(self.cfg.placement)
        self.placement.currentTextChanged.connect(self.change_placement)
        form.addRow("Placement", self.placement)
        for title, key, minimum, maximum in [
            ("Text size", "font_size", 16, 64),
            ("Backdrop opacity (%)", "opacity", 10, 100),
            ("Overlay width", "width", 400, 4000),
            ("Line spacing (%)", "spacing", 100, 180),
        ]:
            spin = QSpinBox()
            spin.setRange(minimum, maximum)
            spin.setValue(getattr(self.cfg, key))
            spin.valueChanged.connect(lambda value, k=key: self.appearance(k, value))
            form.addRow(title, spin)
        for title, key in [
            ("English colour", "english_color"),
            ("Chinese colour", "chinese_color"),
        ]:
            button = QPushButton("Choose colour")
            button.clicked.connect(lambda _, k=key: self.choose_color(k))
            form.addRow(title, button)
        help = QLabel(
            "Show the overlay, then drag it to position it. Drag its lower-right corner to resize.\nLock it before teaching so clicks pass through to your slides.\nPause immediately hides captions; resume restores them."
        )
        help.setWordWrap(True)
        form.addRow(help)
        return scroll

    def diagnostics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.backend = QLabel("Backend is verified when a lecture starts.")
        layout.addWidget(self.backend)
        self.diagnostics = QPlainTextEdit()
        self.diagnostics.setReadOnly(True)
        layout.addWidget(self.diagnostics)
        row = QHBoxLayout()
        for title, fn in [
            ("Open logs", lambda: self.open_folder(DATA / "logs")),
            ("Open transcripts", lambda: self.open_folder(self.transcript_path)),
            ("Test local WAV", self.choose_wav),
        ]:
            b = QPushButton(title)
            b.clicked.connect(fn)
            row.addWidget(b)
        layout.addLayout(row)
        self.wav_label = QLabel("Live microphone input")
        layout.addWidget(self.wav_label)
        reset = QPushButton("Use microphone again")
        reset.clicked.connect(self.clear_wav)
        layout.addWidget(reset)
        return widget

    def about_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        title = QLabel("Teach freely. Keep your data here.")
        title.setFont(QFont("Segoe UI", 24))
        title.setWordWrap(True)
        layout.addWidget(title)
        text = QLabel(
            "LectureLive runs speech recognition and English-to-Simplified-Chinese translation using model files on this computer. No account or cloud fallback is used.\n\nAudio recording is not implemented; microphone samples are held only briefly for captioning. Optional transcripts stay in your local LectureLive folder. Diagnostic logs omit caption text.\n\nPython networking is blocked in the runtime. Physical Airplane Mode and OS network-trace acceptance tests still need sign-off; see STATUS.md before relying on this development build in a lecture.\n\nWhisper: Qualcomm NPU, with native ARM64 CPU recovery. Translation: local OPUS-MT. Voice detection: local Silero VAD."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()
        b = QPushButton("Open user guide")
        b.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(ROOT / "docs/USER_GUIDE.md"))
            )
        )
        layout.addWidget(b)
        return widget

    def warn(self, message):
        self.warning.setText(message)
        self.warning.show()

    def open_folder(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def refresh_microphones(self):
        if self.pipeline:
            return
        selected = self.cfg.microphone
        self.microphone.clear()
        try:
            for index, name, host in microphones():
                label = (
                    "Surface microphone array"
                    if name.startswith("Microphone Array (Qualcomm")
                    else name[:32]
                )
                self.microphone.addItem(
                    f"{label} · {host.replace('Windows ', '')}", index
                )
                self.microphone.setItemData(
                    self.microphone.count() - 1, name, Qt.ToolTipRole
                )
            # Persist a device label rather than an unstable PortAudio index.
            match = self.microphone.findText(str(selected))
            self.microphone.setCurrentIndex(max(0, match))
            if not self.microphone.count():
                self.warn(
                    "Microphone unavailable. Connect an input device and refresh."
                )
        except Exception:
            self.warn(
                "Could not list microphones. Check Windows microphone permissions."
            )

    def refresh_displays(self, *args):
        self.displays.blockSignals(True)
        self.control_displays.blockSignals(True)
        self.displays.clear()
        self.control_displays.clear()
        for i, screen in enumerate(QApplication.screens()):
            label = f"Display {i + 1} · {screen.name()} · {screen.size().width()} × {screen.size().height()}"
            self.displays.addItem(label, screen.name())
            self.control_displays.addItem(label, screen.name())
        self.displays.setCurrentIndex(max(0, self.displays.findData(self.cfg.monitor)))
        self.displays.blockSignals(False)
        self.control_displays.blockSignals(False)

    def display_removed(self, *args):
        self.refresh_displays()
        self.overlay.place()
        self.warn("A display was disconnected. Captions moved to an available display.")

    def select_display(self, index):
        self.cfg.monitor = self.displays.itemData(index) or ""
        self.overlay.place()
        self.persist()

    def select_control_display(self, index):
        name = self.control_displays.itemData(index)
        screen = next((s for s in QApplication.screens() if s.name() == name), None)
        if screen:
            self.move(
                screen.availableGeometry().topLeft()
                + screen.availableGeometry().center()
                - screen.availableGeometry().topLeft()
                - self.rect().center()
            )

    def set_mode(self, mode):
        self.cfg.mode = mode
        self.preview_en.setVisible(mode != "Chinese")
        self.preview_zh.setVisible(mode != "English")
        self.overlay.update()
        self.persist()

    def change_placement(self, value):
        self.cfg.placement = value
        self.overlay.place()
        self.persist()

    def appearance(self, key, value):
        setattr(self.cfg, key, value)
        if key == "width":
            self.overlay.place()
        self.overlay.update()
        self.persist()

    def choose_color(self, key):
        colour = QColorDialog.getColor(
            QColor(getattr(self.cfg, key)), self, "Caption colour"
        )
        if colour.isValid():
            setattr(self.cfg, key, colour.name())
            self.overlay.update()
            self.persist()

    def persist(self):
        try:
            self.cfg.save()
        except OSError:
            self.warn(
                "Could not save preferences. Check your local application-data folder."
            )

    def readiness(self):
        states = [
            ("Microphone", self.microphone.count() > 0),
            (
                "Speech model",
                (ROOT / "models/whisper" / self.cfg.profile / "config.json").exists(),
            ),
            (
                "Translation model",
                (
                    ROOT / "models/translation/opus/onnx/encoder_model_quantized.onnx"
                ).exists(),
            ),
            ("Voice detection", (ROOT / "models/vad/silero_vad.onnx").exists()),
        ]
        self.ready.setText(
            "LOCAL READINESS\n"
            + "    ".join(("✓ " if ok else "Missing: ") + name for name, ok in states)
        )

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
            self.cfg.visible = False
        else:
            self.overlay.show()
            self.cfg.visible = True
        self.show_button.setText(
            "Hide overlay" if self.overlay.isVisible() else "Show overlay"
        )
        self.persist()

    def toggle_lock(self):
        try:
            self.overlay.lock(not self.cfg.locked)
        except OSError:
            self.warn(
                "Could not change overlay click-through mode. Try showing the overlay again."
            )
        self.lock_button.setText(
            "Unlock overlay" if self.cfg.locked else "Lock overlay"
        )
        self.persist()

    def choose_wav(self):
        if self.pipeline:
            self.warn("Stop the lecture before changing the audio source.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose local test audio",
            str(ROOT / "tests/fixtures"),
            "PCM WAV (*.wav)",
        )
        if path:
            self.wav = path
            self.wav_label.setText("TEST AUDIO · " + Path(path).name)

    def clear_wav(self):
        if self.pipeline:
            self.warn("Stop the lecture before changing the audio source.")
            return
        self.wav = None
        self.wav_label.setText("Live microphone input")

    def start_stop(self):
        if self.pipeline:
            self.stop()
            return
        self.warning.hide()
        self.cfg.microphone = self.microphone.currentText()
        self.cfg.profile = self.profile.currentData()
        self.cfg.glossary = self.glossary.currentData()
        self.cfg.save_transcripts = self.save.isChecked()
        self.persist()
        from dataclasses import replace

        run_cfg = replace(self.cfg, microphone=self.microphone.currentData())
        self.pipeline = Pipeline(
            ROOT,
            DATA,
            run_cfg,
            self.bridge.event.emit,
            self.vocabulary.toPlainText(),
            self.title.text(),
            self.wav,
        )
        self.last_caption = None
        self.overlay.reset()
        self.overlay.lock(True)
        self.cfg.locked = True
        self.lock_button.setText("Unlock overlay")
        self.start_button.setText("Stop lecture")
        self.pause_button.setEnabled(True)
        for w in [
            self.microphone,
            self.profile,
            self.glossary,
            self.save,
            self.vocabulary,
        ]:
            w.setEnabled(False)
        self.loader = threading.Thread(
            target=self.pipeline.start, name="LectureLive startup", daemon=False
        )
        self.loader.start()

    def pause(self):
        if not self.pipeline:
            return
        self.pipeline.pause()
        if self.pipeline.paused.is_set():
            self.overlay.hide()
        elif self.cfg.visible:
            self.overlay.show()

    def stop(self):
        if not self.pipeline or self.closer:
            return
        self.pipeline.request_stop()
        self.overlay.hide()
        self.status.setText("●  Finishing…")
        self.pause_button.setEnabled(False)
        self.start_button.setEnabled(False)
        engine = self.pipeline
        loader = self.loader

        def finish():
            if loader:
                loader.join()
            engine.close()
            self.bridge.event.emit("stopped", None)

        self.closer = threading.Thread(
            target=finish, name="LectureLive shutdown", daemon=False
        )
        self.closer.start()

    def on_event(self, kind, value):
        if kind == "readiness":
            self.start_button.setEnabled(True)
            self.status.setText(
                "●  Ready" if value["speech"] and value["vad"] else "●  Setup needed"
            )
            self.ready.setText(
                "LOCAL INFERENCE CHECK\n"
                + "    ".join(
                    ("✓ " if value[k] else "Unavailable: ") + label
                    for k, label in [
                        ("speech", "Speech"),
                        ("translation", "Chinese"),
                        ("vad", "Voice detection"),
                        ("npu", "NPU"),
                    ]
                )
            )
            self.backend.setText(
                "Startup inference passed on "
                + (
                    "Qualcomm NPU"
                    if value["npu"]
                    else "local CPU"
                    if value["speech"]
                    else "no speech backend"
                )
            )
            if value["messages"]:
                self.warn(" ".join(value["messages"]))
            if self.closing:
                QTimer.singleShot(50, self.close)
        elif kind == "stopped":
            self.pipeline = None
            self.loader = None
            self.closer = None
            self.status.setText("●  Ready")
            self.start_button.setText("Start lecture")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.pause_button.setText("Pause")
            for w in [
                self.microphone,
                self.profile,
                self.glossary,
                self.save,
                self.vocabulary,
            ]:
                w.setEnabled(True)
            if self.closing:
                self.close()
        elif kind == "warning":
            self.warn(str(value))
        elif kind == "backend":
            self.backend.setText(str(value))
        elif kind == "transcript":
            self.transcript_path = Path(value)
        elif kind == "state":
            self.status.setText("●  " + str(value))
            self.pause_button.setText("Resume" if value == "Paused" else "Pause")
            if (
                value == "Listening"
                and self.cfg.visible
                and self.pipeline
                and not self.pipeline.stop_event.is_set()
            ):
                self.overlay.show()
            if value == "Paused" or "unavailable" in str(value):
                self.overlay.hide()
        elif kind == "caption":
            if (
                not self.pipeline
                or self.pipeline.paused.is_set()
                or value.epoch != self.pipeline.epoch
            ):
                return
            if self.last_caption and (value.epoch, value.identifier) < (
                self.last_caption.epoch,
                self.last_caption.identifier,
            ):
                return
            self.overlay.set_caption(value)
            if value.final:
                self.last_caption = value
                self.preview_en.setText(value.english)
                self.preview_zh.setText(value.chinese or "Translation pending…")
                self.preview_hint.setText("Stable phrase")
            else:
                if not self.last_caption:
                    self.preview_en.setText(value.english)
                    self.preview_zh.setText("")
                self.preview_hint.setText("Live English: " + value.english)

    def tick(self):
        if self.pipeline:
            self.meter.setValue(self.pipeline.level)
            self.diagnostics.setPlainText(
                json.dumps(self.pipeline.diagnostics(), indent=2)
            )
        else:
            self.meter.setValue(0)

    def closeEvent(self, event):
        if self.checker and self.checker.is_alive():
            self.closing = True
            event.ignore()
            QTimer.singleShot(100, self.close)
            return
        if self.pipeline:
            self.closing = True
            self.stop()
            event.ignore()
            return
        self.hotkeys.close()
        self.overlay.close()
        self.persist()
        event.accept()
