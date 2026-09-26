import json, logging, threading
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QUrl
from PySide6.QtGui import QFont, QDesktopServices, QColor, QIcon
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
    QInputDialog,
)
from app.config.settings import ROOT, DATA, Settings
from app.system.architecture import is_x64, is_macos
from app.audio.capture import microphones
from app.pipeline import Pipeline
from app.ui.overlay import Overlay
from app.captions.history import TranscriptHistory
from app.ui.transcript import TranscriptView
from app.system.desktop import Hotkeys
from app.system.permissions import microphone_permission

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
QPushButton:focus, QComboBox:focus, QLineEdit:focus, QPlainTextEdit:focus { border:2px solid #8ce2c9; }
QLabel#sectionTitle { font-size:22px; font-weight:600; }
QLabel#authorName { font-size:23px; font-weight:600; color:#8ce2c9; }
QTextBrowser { background:#18242d; border:1px solid #2c3d48; border-radius:8px; padding:18px; font-size:16px; }
QScrollBar:vertical { background:#111a21; width:10px; margin:0; }
QScrollBar::handle:vertical { background:#435967; border-radius:5px; min-height:28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }

"""


class Bridge(QObject):
    event = Signal(str, object)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = Settings.load()
        from app.system.models import ModelStore

        self.model_store = ModelStore(ROOT)
        from app.config.presets import Presets

        self.presets = Presets(DATA / "presets.json")
        self.microphone_checker = None
        self.microphone_cancel = threading.Event()
        self.teaching = None
        self.appearance_spins = {}
        self.restart_requested = False
        self.pipeline = None
        self.loader = None
        self.closer = None
        self.language_worker = None
        self.closing = False
        self.wav = None
        self.checker = None
        self.bridge = Bridge()
        self.bridge.event.connect(self.on_event)
        self.last_caption = None
        self.transcript_path = DATA / "transcripts"
        self.setWindowTitle(
            "LectureLive · Apple Silicon Beta"
            if is_macos()
            else "LectureLive · Windows x64 Beta"
            if is_x64()
            else "LectureLive"
        )
        self.resize(1060, 860)
        self.setMinimumSize(860, 640)
        self.setWindowIcon(QIcon(str(ROOT / "assets/lecturelive.png")))
        self.setStyleSheet(
            STYLE.replace("Segoe UI", "Helvetica Neue").replace(
                "Microsoft YaHei UI", "PingFang SC"
            )
            if is_macos()
            else STYLE
        )
        self.history = TranscriptHistory()
        self.transcript_view = TranscriptView(self.history)
        self.transcript_view.set_saving(self.cfg.save_transcripts)
        self.overlay = Overlay(self.cfg, self.history)
        self.overlay.moved.connect(self.persist)
        host = QWidget()
        self.setCentralWidget(host)
        layout = QVBoxLayout(host)
        layout.setContentsMargins(28, 22, 28, 20)
        layout.setSpacing(16)
        head = QHBoxLayout()
        brand = QVBoxLayout()
        name = QLabel("LectureLive · Beta" if is_x64() or is_macos() else "LectureLive")
        name.setObjectName("brand")
        brand.addWidget(name)
        tagline = QLabel("Offline bilingual live captions for teaching")
        tagline.setObjectName("muted")
        brand.addWidget(tagline)
        head.addLayout(brand)
        head.addStretch()
        quick_start = QPushButton("Quick start")
        quick_start.setToolTip("Read the guide inside LectureLive")
        quick_start.clicked.connect(self.show_guide)
        head.addWidget(quick_start, 0, Qt.AlignVCenter)
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
        self.tabs = tabs
        layout.addWidget(tabs, 1)
        tabs.addTab(self.lecture_tab(), "Lecture")
        tabs.addTab(self.transcript_view, "Transcript")
        tabs.addTab(self.appearance_tab(), "Overlay")
        tabs.addTab(self.diagnostics_tab(), "Diagnostics")
        tabs.addTab(self.about_tab(), "About")
        actions = QHBoxLayout()
        actions.addWidget(self.start_button, 2)
        actions.addWidget(self.pause_button, 1)
        actions.addWidget(self.compact_button, 1)
        self.retry_button = QPushButton("Reconnect / retry")
        self.retry_button.clicked.connect(self.reconnect)
        self.retry_button.hide()
        actions.addWidget(self.retry_button)
        layout.addLayout(actions)
        footer = QHBoxLayout()
        from app.languages import DIRECTIONS

        privacy = QLabel(
            "LOCAL PROCESSING  ·  " + DIRECTIONS[self.cfg.speaking_language]
        )
        self.direction_label = privacy
        privacy.setObjectName("muted")
        footer.addWidget(privacy)
        footer.addStretch()
        shortcut = QLabel(
            f"Pause  {self.cfg.pause_shortcut}     Lock  {self.cfg.lock_shortcut}"
        )
        self.shortcut_label = shortcut
        shortcut.setObjectName("muted")
        footer.addWidget(shortcut)
        layout.addLayout(footer)
        try:
            self.hotkeys = Hotkeys(
                QApplication.instance(),
                self.toggle_lock,
                self.pause,
                self.cfg.lock_shortcut,
                self.cfg.pause_shortcut,
            )
        except ValueError:
            self.cfg.lock_shortcut, self.cfg.pause_shortcut = (
                "Ctrl+Alt+C",
                "Ctrl+Alt+Space",
            )
            self.hotkeys = Hotkeys(
                QApplication.instance(), self.toggle_lock, self.pause
            )
            self.warn("Saved shortcuts were invalid; defaults have been restored.")
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
            result = check(
                ROOT,
                self.cfg.profile,
                self.model_store,
                self.cfg.accelerator,
                self.cfg.speaking_language,
            )
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

    def sync_language_controls(self):
        from app.languages import caption_labels, DIRECTIONS

        for widget in [self.speaking_language] + (
            [self.teaching.language] if self.teaching else []
        ):
            widget.blockSignals(True)
            widget.setCurrentIndex(widget.findData(self.cfg.speaking_language))
            widget.blockSignals(False)
        primary = self.overlay.display.primary(self.cfg.mode)
        language = primary.source_language if primary else self.cfg.speaking_language
        en, zh = caption_labels(language)
        automatic = self.cfg.speaking_language == "auto"
        self.language_status.setVisible(automatic)
        self.language_status.setText("Auto · waiting for speech")
        self.language_hint.setText(
            "Auto chooses each phrase. Pause briefly between speakers; use manual selection if unclear."
            if automatic
            else "Switch between speakers. Wait for Listening before speaking again."
        )
        self.overlay.language_notice = ""
        if self.teaching:
            self.teaching.language_status.setVisible(automatic)
            self.teaching.language_status.setText(self.language_status.text())
        self.preview_en_label.setText(en)
        self.preview_zh_label.setText(zh)
        self.direction_label.setText(
            "LOCAL PROCESSING  ·  " + DIRECTIONS[self.cfg.speaking_language]
        )

    def enable_language_controls(self, enabled):
        self.speaking_language.setEnabled(enabled)
        if self.teaching:
            self.teaching.language.setEnabled(enabled)

    def select_language(self, *_):
        language = self.speaking_language.currentData()
        if not self.pipeline:
            self.cfg.speaking_language = language
            self.overlay.reset()
            self.sync_language_controls()
            self.readiness()
            self.persist()
            return
        if (
            self.closer
            or not self.pipeline.started
            or self.pipeline.loading
            or (self.language_worker and self.language_worker.is_alive())
        ):
            self.sync_language_controls()
            return
        self.enable_language_controls(False)
        self.pause_button.setEnabled(False)
        engine = self.pipeline

        def switch():
            try:
                engine.switch_language(language)
            except Exception as exc:
                logging.exception("Language switch failed; previous direction retained")
                self.bridge.event.emit(
                    "warning",
                    "Language was not changed. "
                    + str(exc)
                    + " Repair setup if the Mandarin translation model is missing.",
                )
            finally:
                self.bridge.event.emit("language-finished", None)

        self.language_worker = threading.Thread(
            target=switch, name="LectureLive language switch", daemon=False
        )
        self.language_worker.start()

    def select_accelerator(self):
        self.cfg.accelerator = self.accelerator.currentData()
        self.backend.setText(
            "Hardware selection will be checked when the next lecture starts."
        )
        self.persist()

    def apply_course_vocabulary(self):
        if self.pipeline:
            self.warn("Finish the lecture before changing vocabulary.")
            return
        selected = self.course_vocabulary.currentData()
        if selected is None:
            return
        entry = self.course_lists[selected]
        self.vocabulary.setPlainText("\n".join(entry["terms"]))
        self.glossary.setCurrentIndex(self.glossary.findData(entry["glossary"]))
        self.cfg.glossary = entry["glossary"]
        self.persist()

    def capture_preset_settings(self):
        from dataclasses import replace

        return replace(
            self.cfg,
            lecture_title=self.title.text(),
            vocabulary=self.vocabulary.toPlainText(),
            microphone=self.microphone.currentText(),
            profile=self.profile.currentData(),
            accelerator=self.accelerator.currentData(),
            recognition_mode=self.recognition_mode.currentData(),
            vocabulary_guidance=self.vocabulary_guidance.isChecked(),
            glossary=self.glossary.currentData(),
            save_transcripts=self.save.isChecked(),
            speaking_language=self.speaking_language.currentData(),
        )

    def save_preset(self):
        name, ok = QInputDialog.getText(
            self,
            "Save lecture preset",
            "Preset name:",
            text=self.preset_choice.currentText(),
        )
        if not ok:
            return
        try:
            self.presets.save(name, self.capture_preset_settings())
            self.preset_choice.clear()
            self.preset_choice.addItems(sorted(self.presets.read()))
            self.preset_choice.setCurrentText(name.strip())
        except (OSError, ValueError) as exc:
            self.warn(str(exc))

    def load_preset(self):
        if self.pipeline:
            self.warn("Finish the lecture before loading a different preset.")
            return
        try:
            cfg = self.presets.load(self.preset_choice.currentText())
            # Global shortcuts are app preferences, not changed by a lecture preset.
            cfg.lock_shortcut = self.cfg.lock_shortcut
            cfg.pause_shortcut = self.cfg.pause_shortcut
            self.cfg = cfg
            self.sync_language_controls()
            self.overlay.settings = cfg
            self.title.setText(cfg.lecture_title)
            self.vocabulary.setPlainText(cfg.vocabulary)
            self.profile.setCurrentIndex(max(0, self.profile.findData(cfg.profile)))
            self.accelerator.blockSignals(True)
            try:
                self.accelerator.setCurrentIndex(
                    max(0, self.accelerator.findData(cfg.accelerator))
                )
            finally:
                self.accelerator.blockSignals(False)
            self.glossary.setCurrentIndex(max(0, self.glossary.findData(cfg.glossary)))
            self.recognition_mode.setCurrentIndex(
                max(0, self.recognition_mode.findData(cfg.recognition_mode))
            )
            self.vocabulary_guidance.setChecked(cfg.vocabulary_guidance)
            self.save.setChecked(cfg.save_transcripts)
            for key, spin in self.appearance_spins.items():
                spin.blockSignals(True)
                spin.setValue(getattr(cfg, key))
                spin.blockSignals(False)
            self.mode.setCurrentText(cfg.mode)
            self.overlay_layout.setCurrentIndex(
                self.overlay_layout.findData(cfg.overlay_layout)
            )
            self.placement.setCurrentText(cfg.placement)
            self.refresh_microphones()
            self.refresh_displays()
            self.overlay.place()
            self.overlay.update()
            self.persist()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.warn("Could not load preset: " + str(exc))

    def test_microphone(self):
        if self.pipeline or (
            self.microphone_checker and self.microphone_checker.is_alive()
        ):
            return
        if self.microphone.currentData() is None:
            self.warn("Connect and select a microphone first.")
            return
        if not microphone_permission(self, self.test_microphone):
            return
        from app.audio.check import check_microphone

        self.microphone_cancel.clear()
        self.start_button.setEnabled(False)
        self.mic_test_button.setEnabled(False)
        self.mic_test_result.setText("Speak now… checking the selected microphone.")
        device = self.microphone.currentData()

        def run():
            try:
                result = check_microphone(
                    device, self.bridge.event.emit, self.microphone_cancel
                )
            except Exception:
                result = {
                    "message": "Microphone check failed. Check device access and try again."
                }
            self.bridge.event.emit("microphone-check", result)

        self.microphone_checker = threading.Thread(
            target=run, name="LectureLive microphone check", daemon=False
        )
        self.microphone_checker.start()

    def projector_preview(self):
        if self.pipeline:
            self.warn("Finish the lecture before displaying a test caption.")
            return
        from app.captions.state import Caption

        self.overlay.reset()
        self.overlay.place()
        self.overlay.set_caption(
            Caption(
                1,
                0,
                1,
                "Projector preview · captions appear here.",
                "投影预览：字幕将在这里显示。",
                True,
            )
        )
        self.overlay.show()
        self.overlay.lock(False)
        self.lock_button.setText("Lock overlay")
        self.show_button.setText("Hide overlay")

    def reconnect(self):
        if not self.pipeline:
            return
        self.restart_requested = True
        self.retry_button.setEnabled(False)
        self.stop()

    def restart_after_failure(self):
        self.restart_requested = False
        if self.closing:
            return
        self.refresh_microphones()
        if self.wav or self.microphone.findText(self.cfg.microphone) >= 0:
            self.start_stop()
        else:
            self.warn(
                "The selected microphone is still unavailable. Reconnect it, refresh microphones, then start the lecture."
            )

    def show_teaching(self):
        if not self.pipeline:
            self.warn("Start a lecture to use compact teaching controls.")
            return
        if self.teaching is None:
            from app.ui.teaching import TeachingControls

            self.teaching = TeachingControls(self)
        self.teaching.status.setText(self.status.text())
        self.sync_language_controls()
        self.teaching.show()
        self.teaching.raise_()
        self.hide()

    def apply_shortcuts(self):
        from app.system.desktop import parse_shortcut

        lock = self.lock_shortcut_edit.text().strip()
        pause = self.pause_shortcut_edit.text().strip()
        try:
            if parse_shortcut(lock) == parse_shortcut(pause):
                raise ValueError("Lock and pause shortcuts must differ")
        except ValueError as exc:
            self.warn(str(exc))
            return
        old = (self.cfg.lock_shortcut, self.cfg.pause_shortcut)
        self.hotkeys.close()
        candidate = Hotkeys(
            QApplication.instance(), self.toggle_lock, self.pause, lock, pause
        )
        if candidate.errors:
            candidate.close()
            self.hotkeys = Hotkeys(
                QApplication.instance(), self.toggle_lock, self.pause, *old
            )
            self.warn(
                "Shortcut already in use: "
                + ", ".join(candidate.errors)
                + ". Previous shortcuts restored."
            )
            return
        self.hotkeys = candidate
        self.cfg.lock_shortcut = lock
        self.cfg.pause_shortcut = pause
        self.shortcut_label.setText(f"Pause  {pause}     Lock  {lock}")
        self.overlay.update()
        self.persist()

    def recover_transcript(self):
        if self.pipeline:
            self.warn("Finish the lecture before recovering a journal.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Recover transcript journal",
            str(DATA / "transcripts"),
            "Lecture journal (events.jsonl)",
        )
        if not path:
            return
        from app.export.transcript import recover_journal

        try:
            folder, skipped = recover_journal(path, DATA / "transcripts")
            self.open_folder(folder)
            self.warn(
                f"Recovered to a new folder. Incomplete or invalid records skipped: {skipped}."
            )
        except (OSError, ValueError) as exc:
            self.warn("Recovery failed: " + str(exc))

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
        preset_box, preset_form = self.group("LECTURE PRESET")
        preset_row = QHBoxLayout()
        self.preset_choice = QComboBox()
        self.preset_choice.setPlaceholderText("No saved presets yet")
        self.preset_choice.setAccessibleName("Saved lecture presets")
        try:
            self.preset_choice.addItems(sorted(self.presets.read()))
        except (OSError, ValueError):
            self.warn(
                "Saved presets could not be read. Existing files have been retained."
            )
        preset_row.addWidget(self.preset_choice, 1)
        load_preset = QPushButton("Load")
        load_preset.clicked.connect(self.load_preset)
        load_preset.setEnabled(self.preset_choice.count() > 0)
        self.preset_choice.currentIndexChanged.connect(
            lambda index: load_preset.setEnabled(index >= 0)
        )
        save_preset = QPushButton("Save…")
        save_preset.clicked.connect(self.save_preset)
        preset_row.addWidget(load_preset)
        preset_row.addWidget(save_preset)
        preset_form.addLayout(preset_row)
        mic, form = self.group("1 · MICROPHONE")
        row = QHBoxLayout()
        self.microphone = QComboBox()
        self.microphone.setAccessibleName("Microphone")
        row.addWidget(self.microphone, 1)
        refresh = QPushButton("↻")
        refresh.setToolTip("Refresh microphones")
        refresh.setAccessibleName("Refresh microphones")
        refresh.setMaximumWidth(52)
        refresh.clicked.connect(self.refresh_microphones)
        row.addWidget(refresh)
        form.addLayout(row)
        self.meter = QProgressBar()
        self.meter.setRange(0, 100)
        self.meter.setTextVisible(False)
        form.addWidget(self.meter)
        note = QLabel("Your voice stays on this computer. No audio file is saved.")
        note.setObjectName("muted")
        form.addWidget(note)
        self.mic_test_button = QPushButton("Test microphone · 3 seconds")
        self.mic_test_button.clicked.connect(self.test_microphone)
        form.addWidget(self.mic_test_button)
        self.mic_test_result = QLabel("Speak during the check. No audio file is saved.")
        self.mic_test_result.setWordWrap(True)
        form.addWidget(self.mic_test_result)
        left.addWidget(mic)
        captions, form = self.group("2 · CAPTIONS")
        form.addWidget(QLabel("Who is speaking?"))
        self.speaking_language = QComboBox()
        self.speaking_language.setAccessibleName("Speaking language")
        self.speaking_language.addItem("English → 简体中文", "en")
        self.speaking_language.addItem("Mandarin 普通话 → English", "zh")
        self.speaking_language.addItem("Auto · English ↔ Mandarin", "auto")
        self.speaking_language.setCurrentIndex(
            max(0, self.speaking_language.findData(self.cfg.speaking_language))
        )
        self.speaking_language.currentIndexChanged.connect(self.select_language)
        form.addWidget(self.speaking_language)
        self.language_hint = QLabel(
            "Switch between speakers. Wait for Listening before speaking again."
        )
        self.language_hint.setWordWrap(True)
        form.addWidget(self.language_hint)
        self.language_status = QLabel("Auto detects each phrase. Speak one at a time.")
        self.language_status.setWordWrap(True)
        self.language_status.setAccessibleName("Detected speaking language")
        form.addWidget(self.language_status)
        form.addWidget(QLabel("Caption languages"))
        self.mode = QComboBox()
        self.mode.setAccessibleName("Caption languages")
        self.mode.addItems(["Bilingual", "English", "Chinese"])
        self.mode.setCurrentText(self.cfg.mode)
        self.mode.currentTextChanged.connect(self.set_mode)
        form.addWidget(self.mode)
        form.addWidget(QLabel("Speech profile"))
        self.profile = QComboBox()
        self.profile.setAccessibleName("Speech profile")
        for title, key in [
            ("Fast · quicker captions", "fast"),
            ("Balanced · recommended", "balanced"),
        ]:
            if is_x64() and key != "fast":
                continue
            exists = (ROOT / "models/whisper" / key / "config.json").exists()
            self.profile.addItem(
                title if exists or key == "accuracy" else title + " · not installed",
                key,
            )
            self.profile.model().item(self.profile.count() - 1).setEnabled(exists)
        idx = self.profile.findData(self.cfg.profile)
        self.profile.setCurrentIndex(max(0, idx))
        form.addWidget(self.profile)
        form.addWidget(QLabel("Speech recognition"))
        self.recognition_mode = QComboBox()
        self.recognition_mode.setAccessibleName("Speech recognition")
        self.recognition_mode.addItem(
            "Standard · existing speed and behaviour", "standard"
        )
        self.recognition_mode.addItem(
            "Careful · slower; test before teaching", "careful"
        )
        self.recognition_mode.setCurrentIndex(
            max(0, self.recognition_mode.findData(self.cfg.recognition_mode))
        )
        self.recognition_mode.setToolTip(
            "Careful spends more time checking finished phrases. Try it when words are being missed, with any accent."
        )
        form.addWidget(self.recognition_mode)
        self.accelerator = QComboBox()
        self.accelerator.setAccessibleName("Processing hardware")
        for label, key in (
            [
                ("Automatic · Core ML with CPU fallback", "auto"),
                ("CPU · compatibility mode", "cpu"),
                ("Apple Core ML · beta", "coreml"),
            ]
            if is_macos()
            else [
                ("Automatic · checked before captions", "auto"),
                ("CPU · compatibility mode", "cpu"),
                ("GPU · DirectML beta", "gpu"),
                ("Intel NPU · experimental", "intel_npu"),
                ("AMD NPU · experimental", "amd_npu"),
            ]
        ):
            self.accelerator.addItem(label, key)
        self.accelerator.setCurrentIndex(
            max(0, self.accelerator.findData(self.cfg.accelerator))
        )
        if is_x64() or is_macos():
            form.addWidget(QLabel("Processing hardware"))
            form.addWidget(self.accelerator)
            hint = QLabel(
                "Automatic uses Core ML for Fast and CPU for Balanced. Core ML with Balanced is experimental.\nDecoding and translation use CPU. First Core ML use can take several minutes."
                if is_macos()
                else "GPU/NPU accelerates speech encoding. Decoding and translation use CPU.\nFor NPU setup, read the Windows beta guide."
            )
            hint.setWordWrap(True)
            form.addWidget(hint)
        else:
            self.accelerator.hide()
        self.accelerator.currentIndexChanged.connect(self.select_accelerator)
        left.addWidget(captions)
        topic, form = self.group("3 · LECTURE DETAILS · OPTIONAL")
        self.title = QLineEdit()
        self.title.setPlaceholderText("Lecture title (optional)")
        self.title.setText(self.cfg.lecture_title)
        form.addWidget(self.title)
        form.addWidget(QLabel("Subject vocabulary"))
        self.glossary = QComboBox()
        self.glossary.setAccessibleName("Subject vocabulary")
        for path in sorted((ROOT / "glossaries").glob("*.json")):
            self.glossary.addItem(path.stem.replace("_", " ").title(), path.stem)
        self.glossary.setCurrentIndex(max(0, self.glossary.findData(self.cfg.glossary)))
        form.addWidget(self.glossary)
        self.save = QCheckBox("Save text transcripts and subtitles")
        self.save.setChecked(self.cfg.save_transcripts)
        form.addWidget(self.save)
        left.addWidget(topic)
        preset_box.setTitle("SAVED LECTURE PRESETS · OPTIONAL")
        left.addWidget(preset_box)
        self.start_button = QPushButton("Start lecture")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.start_stop)
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause)
        self.compact_button = QPushButton("Teaching controls")
        self.compact_button.clicked.connect(self.show_teaching)
        left.addStretch()
        right = QVBoxLayout()
        welcome = QLabel("Get ready to teach")
        welcome.setObjectName("sectionTitle")
        right.addWidget(welcome)
        steps = QLabel(
            "Choose your microphone and test it. Keep the recommended caption settings, then select Start lecture below."
        )
        steps.setWordWrap(True)
        steps.setObjectName("muted")
        right.addWidget(steps)
        preview, form = self.group("CAPTION PREVIEW")
        from app.languages import caption_labels

        en_label, zh_label = caption_labels(self.cfg.speaking_language)
        self.preview_en_label = QLabel(en_label)
        self.preview_en_label.setObjectName("muted")
        form.addWidget(self.preview_en_label)
        self.preview_en = QLabel("Your words. Understood.")
        self.preview_en.setObjectName("previewEnglish")
        self.preview_en.setWordWrap(True)
        self.preview_en.setFont(
            QFont("Helvetica Neue" if is_macos() else "Segoe UI", 22)
        )
        form.addWidget(self.preview_en)
        self.preview_zh_label = QLabel(zh_label)
        self.preview_zh_label.setObjectName("muted")
        form.addWidget(self.preview_zh_label)
        self.preview_zh = QLabel("让每一句话，都被听懂。")
        self.preview_zh.setObjectName("previewChinese")
        self.preview_zh.setWordWrap(True)
        self.preview_zh.setFont(
            QFont("PingFang SC" if is_macos() else "Microsoft YaHei UI", 20)
        )
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
        terms, form = self.group("TODAY’S VOCABULARY · OPTIONAL")
        self.course_lists = json.loads(
            (ROOT / "assets/co7000-vocabulary.json").read_text(encoding="utf-8")
        )["lists"]
        self.course_vocabulary = QComboBox()
        self.course_vocabulary.setAccessibleName("Course vocabulary list")
        self.course_vocabulary.addItem("Choose a CO7000 week…", None)
        for index, entry in enumerate(self.course_lists):
            self.course_vocabulary.addItem(entry["title"], index)
        self.course_vocabulary.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon
        )
        self.course_vocabulary.setMinimumContentsLength(20)
        form.addWidget(self.course_vocabulary)
        self.use_course_vocabulary = QPushButton("Use this week's terms")
        self.use_course_vocabulary.setToolTip(
            "Replaces Today's vocabulary and selects Project Management. Recognition mode and guidance stay as you set them."
        )
        self.use_course_vocabulary.clicked.connect(self.apply_course_vocabulary)
        form.addWidget(self.use_course_vocabulary)
        self.vocabulary = QPlainTextEdit()
        self.vocabulary.setPlaceholderText(
            "One term per line, for example:\nESP32\nFreeRTOS\ninterrupt service routine"
        )
        self.vocabulary.setPlainText(self.cfg.vocabulary)
        self.vocabulary.setMaximumHeight(140)
        form.addWidget(self.vocabulary)
        self.vocabulary_guidance = QCheckBox(
            "Use these terms to guide speech recognition"
        )
        self.vocabulary_guidance.setChecked(self.cfg.vocabulary_guidance)
        self.vocabulary_guidance.setToolTip(
            "Enter a short, relevant list, most important terms first. Hints can help technical words but may also bias captions."
        )
        form.addWidget(self.vocabulary_guidance)
        guidance_help = QLabel(
            "Put a few relevant technical terms above, one per line. Try Careful recognition if words are missed."
        )
        guidance_help.setWordWrap(True)
        form.addWidget(guidance_help)
        direction_help = QLabel(
            "English vocabulary and CO7000 hints are kept for English turns. They are not applied to Mandarin speech or Mandarin → English translation."
        )
        direction_help.setWordWrap(True)
        form.addWidget(direction_help)
        label = QLabel(
            "Vocabulary guidance is optional. Use only terms relevant to this lecture; save them in a lecture preset."
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

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
        projector_preview = QPushButton("Preview captions on selected display")
        projector_preview.clicked.connect(self.projector_preview)
        form.addRow(projector_preview)
        self.overlay_layout = QComboBox()
        self.overlay_layout.addItem("Rolling · readable projector", "rolling")
        self.overlay_layout.addItem("Compact · latest caption", "compact")
        self.overlay_layout.setCurrentIndex(
            self.overlay_layout.findData(self.cfg.overlay_layout)
        )
        self.overlay_layout.currentIndexChanged.connect(self.change_overlay_layout)
        form.addRow("Caption layout", self.overlay_layout)
        self.placement = QComboBox()
        self.placement.addItems(["Bottom", "Top", "Custom"])
        self.placement.setCurrentText(self.cfg.placement)
        self.placement.currentTextChanged.connect(self.change_placement)
        form.addRow("Placement", self.placement)
        for title, key, minimum, maximum in [
            ("Text size", "font_size", 16, 64),
            ("Backdrop opacity (%)", "opacity", 10, 100),
            ("Overlay width", "width", 400, 4000),
            ("Rolling overlay height", "projector_height", 200, 1200),
            ("Line spacing (%)", "spacing", 100, 180),
        ]:
            spin = QSpinBox()
            spin.setRange(minimum, maximum)
            spin.setValue(getattr(self.cfg, key))
            self.appearance_spins[key] = spin
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
        self.lock_shortcut_edit = QLineEdit(self.cfg.lock_shortcut)
        self.pause_shortcut_edit = QLineEdit(self.cfg.pause_shortcut)
        form.addRow("Lock shortcut", self.lock_shortcut_edit)
        form.addRow("Pause shortcut", self.pause_shortcut_edit)
        apply_shortcuts = QPushButton("Apply shortcuts")
        apply_shortcuts.clicked.connect(self.apply_shortcuts)
        form.addRow(apply_shortcuts)
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
        recover = QPushButton("Recover transcript journal…")
        recover.clicked.connect(self.recover_transcript)
        layout.addWidget(recover)
        return widget

    def show_guide(self):
        from app.ui.help import GuideDialog

        if not getattr(self, "guide_dialog", None):
            self.guide_dialog = GuideDialog(ROOT / "docs", self)
        self.guide_dialog.show()
        self.guide_dialog.raise_()
        self.guide_dialog.activateWindow()

    def about_tab(self):
        from app import __version__
        from app.author import (
            NAME,
            QUALIFICATIONS,
            ROLE,
            COURSES,
            SCHOOL,
            DEPARTMENT,
            UNIVERSITY,
            EMAIL,
            CONTACT,
        )

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        title = QLabel(f"LectureLive {__version__}")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        intro = QLabel(
            "English and Mandarin conversations. Speech and translation processed on your computer."
        )
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)
        card, form = self.group("PROJECT CONTACT")
        for value, style in [
            (NAME, "authorName"),
            (QUALIFICATIONS, "muted"),
            (ROLE, ""),
        ]:
            label = QLabel(value)
            label.setWordWrap(True)
            label.setTextInteractionFlags(
                Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
            )
            if style:
                label.setObjectName(style)
            form.addWidget(label)
        courses = QLabel(
            "Course Leader for:\n" + "\n".join("• " + course for course in COURSES)
        )
        courses.setWordWrap(True)
        courses.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        form.addWidget(courses)
        affiliation = QLabel("\n".join([SCHOOL, DEPARTMENT, UNIVERSITY]))
        affiliation.setWordWrap(True)
        affiliation.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        form.addWidget(affiliation)
        email = QLabel(f'<a href="mailto:{EMAIL}" style="color:#8ce2c9">{EMAIL}</a>')
        email.setTextInteractionFlags(Qt.TextBrowserInteraction)
        email.setOpenExternalLinks(True)
        email.setAccessibleName("Email " + EMAIL)
        email.setToolTip("Open a draft in your email application")
        form.addWidget(email)
        copy = QPushButton("Copy contact details")
        copy.clicked.connect(lambda: QApplication.clipboard().setText(CONTACT))
        form.addWidget(copy)
        layout.addWidget(card)
        privacy, form = self.group("YOUR DATA STAYS LOCAL")
        text = QLabel(
            "No account or cloud translation service is needed. Microphone audio is not recorded. Optional transcripts and saved lecture settings stay on this computer."
        )
        text.setWordWrap(True)
        form.addWidget(text)
        note = QLabel(
            "Preview release: check translations and rehearse with your microphone and projector before teaching. Full classroom acceptance is still pending."
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        form.addWidget(note)
        guide = QPushButton("Open quick-start guide")
        guide.clicked.connect(self.show_guide)
        form.addWidget(guide)
        layout.addWidget(privacy)
        layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

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
                (
                    "Could not list microphones. Check macOS System Settings → Privacy & Security → Microphone."
                    if is_macos()
                    else "Could not list microphones. Check Windows microphone permissions."
                )
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
        self.preview_en_label.setVisible(mode != "Chinese")
        self.preview_zh_label.setVisible(mode != "English")
        self.overlay.update()
        self.persist()

    def change_placement(self, value):
        self.cfg.placement = value
        self.overlay.place()
        self.persist()

    def change_overlay_layout(self, *_):
        self.cfg.overlay_layout = self.overlay_layout.currentData()
        self.overlay.place()
        self.overlay.update()
        self.persist()

    def appearance(self, key, value):
        setattr(self.cfg, key, value)
        if key in {"width", "projector_height"}:
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
        if hasattr(self, "title"):
            self.cfg.lecture_title = self.title.text()
        if hasattr(self, "recognition_mode"):
            self.cfg.recognition_mode = self.recognition_mode.currentData()
        if hasattr(self, "vocabulary_guidance"):
            self.cfg.vocabulary_guidance = self.vocabulary_guidance.isChecked()
        if hasattr(self, "vocabulary"):
            self.cfg.vocabulary = self.vocabulary.toPlainText()
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
                    ROOT
                    / "models/translation"
                    / ("opus" if self.cfg.speaking_language == "en" else "opus-zh-en")
                    / "onnx/encoder_model_quantized.onnx"
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
        if self.microphone_checker and self.microphone_checker.is_alive():
            return
        if self.pipeline:
            self.stop()
            return
        if not self.wav and not microphone_permission(self, self.start_stop):
            return
        self.warning.hide()
        self.retry_button.hide()
        self.cfg.lecture_title = self.title.text()
        self.cfg.vocabulary = self.vocabulary.toPlainText()
        self.cfg.microphone = self.microphone.currentText()
        self.cfg.profile = self.profile.currentData()
        self.cfg.accelerator = self.accelerator.currentData()
        self.cfg.recognition_mode = self.recognition_mode.currentData()
        self.cfg.vocabulary_guidance = self.vocabulary_guidance.isChecked()
        self.cfg.glossary = self.glossary.currentData()
        self.cfg.save_transcripts = self.save.isChecked()
        self.cfg.speaking_language = self.speaking_language.currentData()
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
            model_store=self.model_store,
        )
        self.last_caption = None
        self.transcript_view.clear(self.cfg.save_transcripts)
        self.overlay.reset()
        self.overlay.lock(True)
        self.cfg.locked = True
        self.lock_button.setText("Unlock overlay")
        self.start_button.setText("Stop lecture")
        self.pause_button.setEnabled(True)
        self.mic_test_button.setEnabled(False)
        self.enable_language_controls(False)
        for w in [
            self.microphone,
            self.profile,
            self.accelerator,
            self.recognition_mode,
            self.vocabulary_guidance,
            self.course_vocabulary,
            self.use_course_vocabulary,
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
        self.status.setText("●  Finishing…")
        self.pause_button.setEnabled(False)
        self.start_button.setEnabled(False)
        engine = self.pipeline
        loader = self.loader

        def finish():
            if loader:
                loader.join()
            if self.language_worker:
                self.language_worker.join()
            engine.close()
            self.bridge.event.emit("stopped", None)

        self.closer = threading.Thread(
            target=finish, name="LectureLive shutdown", daemon=False
        )
        self.closer.start()

    def on_event(self, kind, value):
        if kind == "transcript-saving":
            self.transcript_view.set_saving(value)
            return
        if kind == "transcript-entry":
            if self.transcript_view.accept(value):
                self.overlay.preview = False
                self.overlay.update()
            return
        if kind == "microphone-level":
            self.meter.setValue(value)
            return
        if kind == "microphone-check":
            self.mic_test_result.setText(value["message"])
            self.mic_test_button.setEnabled(True)
            self.start_button.setEnabled(True)
            self.meter.setValue(0)
            return
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
                        ("translation", "Translation"),
                        ("vad", "Voice detection"),
                    ]
                )
            )
            self.backend.setText(
                "Verified: " + value.get("backend", "local CPU")
                if value["speech"]
                else "No speech backend passed its check."
            )
            if value["messages"]:
                self.warn(" ".join(value["messages"]))
            if self.closing:
                QTimer.singleShot(50, self.close)
        elif kind == "stopped":
            self.transcript_view.provisional.setText(
                "Lecture finished. History stays here until the next lecture or app exit."
            )
            if self.teaching:
                self.teaching.hide()
                if not self.closing:
                    self.show()
            self.mic_test_button.setEnabled(True)
            self.retry_button.hide()
            self.retry_button.setEnabled(True)
            self.pipeline = None
            self.loader = None
            self.closer = None
            self.language_worker = None
            self.enable_language_controls(True)
            self.status.setText("●  Ready")
            self.start_button.setText("Start lecture")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.pause_button.setText("Pause")
            for w in [
                self.microphone,
                self.profile,
                self.accelerator,
                self.recognition_mode,
                self.vocabulary_guidance,
                self.course_vocabulary,
                self.use_course_vocabulary,
                self.glossary,
                self.save,
                self.vocabulary,
            ]:
                w.setEnabled(True)
            if self.closing:
                self.close()
            elif self.restart_requested:
                QTimer.singleShot(100, self.restart_after_failure)
        elif kind == "language-detection":
            if (
                not self.pipeline
                or value["epoch"] != self.pipeline.epoch
                or self.pipeline.paused.is_set()
                or self.cfg.speaking_language != "auto"
            ):
                return
            language = value["language"]
            if language is None and value["final"]:
                self.transcript_view.provisional.setText(
                    "Speech not transcribed. Select English or Mandarin and repeat."
                )
                self.overlay.display.reject_partial(value["identifier"], value["epoch"])
                self.overlay.partial = self.overlay.display.partial
                en, zh, _ = self.overlay.display.contents(self.cfg.mode)
                self.preview_en.setText(en)
                self.preview_zh.setText(zh)
                self.preview_hint.setText(
                    "Phrase not transcribed; select a language and repeat."
                )
            message = (
                ("Detected: " + ("English" if language == "en" else "Mandarin"))
                if language
                else (
                    "Language unclear — select English or Mandarin and repeat."
                    if value["final"]
                    else "Detecting speaking language…"
                )
            )
            self.language_status.setText(message)
            self.overlay.language_notice = message
            self.overlay.update()
            if self.teaching:
                self.teaching.language_status.setText(message)
        elif kind == "language":
            self.cfg.speaking_language = value
            self.overlay.reset()
            self.overlay.preview = False
            self.last_caption = None
            self.transcript_view.provisional.setText(
                "Speaking language changed. Earlier passages remain above."
            )
            self.preview_en.setText("")
            self.preview_zh.setText("")
            self.preview_hint.setText(
                "Language changed. Wait for Listening, then speak."
            )
            self.sync_language_controls()
            self.persist()
        elif kind == "language-finished":
            self.sync_language_controls()
            if self.pipeline and not self.pipeline.stop_event.is_set():
                self.enable_language_controls(True)
                self.pause_button.setEnabled(True)
        elif kind == "warning":
            self.warn(str(value))
        elif kind == "backend":
            self.backend.setText(str(value))
        elif kind == "transcript":
            self.transcript_path = Path(value)
        elif kind == "state":
            if value != "Listening":
                self.transcript_view.provisional.setText(str(value))
            else:
                self.transcript_view.provisional.setText("Listening…")
            if value in {"Listening", "Paused"} and not self.closer:
                self.enable_language_controls(True)
            if "unavailable" in str(value):
                self.retry_button.show()
            self.status.setText("●  " + str(value))
            if self.teaching:
                self.teaching.status.setText(str(value))
                self.teaching.pause.setText("Resume" if value == "Paused" else "Pause")
                self.teaching.pause.setEnabled(
                    not self.pipeline.stop_event.is_set()
                    and not self.pipeline.switching.is_set()
                    if self.pipeline
                    else False
                )
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
            self.overlay.set_caption(value)
            partial = self.overlay.display.partial
            self.transcript_view.provisional.setText(
                "Unfinished speech · " + partial.source_text
                if partial
                else "Translating…"
                if self.overlay.display.pending
                else "Listening…"
            )
            en, zh, upcoming = self.overlay.display.contents(self.cfg.mode)
            primary = self.overlay.display.primary(self.cfg.mode)
            language = (
                primary.source_language if primary else self.cfg.speaking_language
            )
            from app.languages import caption_labels

            en_label, zh_label = caption_labels(language)
            self.preview_en_label.setText(en_label)
            self.preview_zh_label.setText(zh_label)
            if value.final and (value.translated_text or self.last_caption is None):
                self.last_caption = value
            unavailable = (
                self.overlay.display.pair
                and self.overlay.display.pair.translation_status == "unavailable"
            )
            self.preview_en.setText(
                en
                or (
                    "Translation unavailable" if unavailable else "Translation pending…"
                )
                if language == "zh"
                else en
            )
            self.preview_zh.setText(
                zh
                or (
                    "Translation unavailable — recognised speech continues"
                    if self.overlay.display.pair
                    and self.overlay.display.pair.translation_status == "unavailable"
                    else "Translation pending…"
                    if language == "en"
                    else ""
                )
            )
            self.preview_hint.setText(
                "Next phrase: " + upcoming
                if upcoming
                else "Stable phrase"
                if self.overlay.display.pair
                and self.overlay.display.pair.translated_text
                else "Listening…"
            )

    def tick(self):
        if self.pipeline:
            self.meter.setValue(self.pipeline.level)
            self.diagnostics.setPlainText(
                json.dumps(self.pipeline.diagnostics(), indent=2)
            )
            if self.teaching:
                self.teaching.meter.setValue(self.pipeline.level)
        elif not (self.microphone_checker and self.microphone_checker.is_alive()):
            self.meter.setValue(0)

    def closeEvent(self, event):
        self.closing = True
        if self.microphone_checker and self.microphone_checker.is_alive():
            self.microphone_cancel.set()
            event.ignore()
            QTimer.singleShot(100, self.close)
            return
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
        if self.teaching:
            self.teaching.hide()
        self.model_store.close()
        self.hotkeys.close()
        self.overlay.close()
        self.persist()
        event.accept()
