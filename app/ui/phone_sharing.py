"""Lecturer controls for explicit, per-lecture local sharing."""

import threading
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from app.config.settings import DATA
from app.sharing.service import SharingSession, interface_addresses


class PhoneSharing(QScrollArea):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.session = None
        self.cleaner = None
        self.has_lecture = False
        self.shown_url = ""
        self.setWidgetResizable(True)
        body = QWidget()
        self.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(20, 18, 20, 18)
        title = QLabel("Captions on students’ phones")
        title.setStyleSheet("font-size:23px;font-weight:600")
        layout.addWidget(title)
        intro = QLabel(
            "Share this lecture over the same Wi-Fi or Ethernet network. Students scan the QR code to read, scroll back, search and download the bilingual text."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        row = QHBoxLayout()
        self.address = QComboBox()
        self.address.setAccessibleName("Classroom network address")
        row.addWidget(self.address, 1)
        refresh = QPushButton("Refresh networks")
        refresh.clicked.connect(self.refresh)
        row.addWidget(refresh)
        layout.addLayout(row)
        buttons = QHBoxLayout()
        self.start = QPushButton("Start sharing")
        self.stop = QPushButton("Stop sharing")
        self.stop.setEnabled(False)
        self.start.clicked.connect(lambda: self.start_sharing())
        self.stop.clicked.connect(self.stop_sharing)
        buttons.addWidget(self.start)
        buttons.addWidget(self.stop)
        layout.addLayout(buttons)
        self.status = QLabel("Sharing is off. No student link is active.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.qr = QLabel()
        self.qr.setAlignment(Qt.AlignCenter)
        self.qr.setAccessibleName("Scan this QR code to open the shared lecture")
        layout.addWidget(self.qr)
        self.link = QLineEdit()
        self.link.setReadOnly(True)
        self.link.setPlaceholderText("Your private classroom link appears here")
        self.link.setAccessibleName("Student caption link")
        layout.addWidget(self.link)
        actions = QHBoxLayout()
        self.copy = QPushButton("Copy link")
        self.preview = QPushButton("Open student view")
        help_button = QPushButton("Connection help")
        self.copy.clicked.connect(
            lambda: QApplication.clipboard().setText(self.link.text())
        )
        self.preview.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(self.link.text()))
        )
        help_button.clicked.connect(self.help)
        for button in (self.copy, self.preview, help_button):
            actions.addWidget(button)
        self.copy.setEnabled(False)
        self.preview.setEnabled(False)
        layout.addLayout(actions)
        note = QLabel(
            "Sharing is optional and starts off. Anyone with this link on the network can read and download the shared text. Use trusted classroom Wi-Fi. Sharing stores a temporary text history even if normal transcript saving is off; Stop sharing removes that temporary history. Students keep any copies they downloaded."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        fallback = QLabel(
            "Phones cannot connect? Use the same network, check that this address is your Wi-Fi/Ethernet adapter, and ask university IT about device isolation or the app’s firewall permission. No internet connection or account is needed."
        )
        fallback.setWordWrap(True)
        layout.addWidget(fallback)
        layout.addStretch()
        self.refresh()

    def refresh(self):
        selected = self.address.currentData()
        self.address.clear()
        for name, ip in interface_addresses():
            self.address.addItem(name + " · " + ip, ip)
        if self.address.findData(selected) >= 0:
            self.address.setCurrentIndex(self.address.findData(selected))
        self.start.setEnabled(
            bool(self.address.count()) and self.session is None and not self.cleaner
        )
        if not self.address.count() and self.session is None:
            self.status.setText(
                "Connect to a private Wi-Fi or Ethernet network, then choose Refresh networks."
            )

    def help(self):
        self.owner.show_guide()
        self.owner.guide_dialog.pages.setCurrentIndex(
            self.owner.guide_dialog.pages.findData("PHONE_CAPTIONS.md")
        )

    def capture(self, kind, caption):
        # Called by the ASR/translation workers: bounded queue only, no Qt or disk work.
        session = self.session
        if session is not None:
            session.capture(kind, caption)

    def start_sharing(self, host=None):
        if self.session or self.cleaner:
            return
        host = host or self.address.currentData()
        if not host:
            return
        try:
            session = SharingSession(DATA, host)
            pipeline = self.owner.pipeline
            self.has_lecture = pipeline is not None
            if pipeline:
                # Snapshot after all earlier export writes, then attach live records.
                with pipeline.export_lock:
                    if pipeline.export:
                        journal = pipeline.export.folder / "events.jsonl"
                        session.history.journal = (journal, journal.stat().st_size)
                    self.session = session
            else:
                self.session = session
            session.start()
            session.state(
                "Listening"
                if pipeline and not pipeline.paused.is_set()
                else "Paused"
                if pipeline
                else "Waiting for lecture"
            )
            self.start.setEnabled(False)
            self.stop.setEnabled(True)
            self.address.setEnabled(False)
            self.status.setText("Preparing your private classroom link…")
        except Exception as exc:
            self.stop_sharing()
            self.status.setText("Sharing could not start: " + str(exc))

    def stop_sharing(self):
        session = self.session
        self.session = None
        self.shown_url = ""
        self.link.clear()
        self.qr.clear()
        self.copy.setEnabled(False)
        self.preview.setEnabled(False)
        self.stop.setEnabled(False)
        self.status.setText(
            "Sharing stopped. The link is no longer active; downloaded or already received text stays on students’ devices."
        )
        self.address.setEnabled(True)
        if session:
            session.stopping = True
            if session.process and session.process.poll() is None:
                session.process.terminate()
            self.cleaner = threading.Thread(
                target=session.close, name="Phone sharing cleanup", daemon=False
            )
            self.cleaner.start()
        else:
            self.start.setEnabled(bool(self.address.count()) and not self.cleaner)

    def begin_lecture(self):
        if self.session and self.has_lecture:
            self.stop_sharing()
            self.status.setText(
                "Previous sharing stopped for the new lecture. Choose Start sharing for a new private link."
            )
        elif self.session:
            self.has_lecture = True
            self.session.state("Loading local models…")

    def state(self, value):
        if self.session:
            self.session.state(str(value))

    def tick(self):
        if self.cleaner and not self.cleaner.is_alive():
            self.cleaner = None
            self.start.setEnabled(bool(self.address.count()) and self.session is None)
        if not self.session:
            return
        problem = self.session.problem()
        if problem:
            self.stop_sharing()
            self.status.setText(problem)
            self.owner.warn(problem)
            return
        url = self.session.url
        if url and url != self.shown_url:
            from app.vendor.qrcodegen import QrCode

            code = QrCode.encode_text(url, QrCode.Ecc.MEDIUM)
            size = code.get_size()
            scale = 6
            image = QImage((size + 8) * scale, (size + 8) * scale, QImage.Format_RGB32)
            image.fill(Qt.white)
            from PySide6.QtGui import QPainter

            painter = QPainter(image)
            for y in range(size):
                for x in range(size):
                    if code.get_module(x, y):
                        painter.fillRect(
                            (x + 4) * scale, (y + 4) * scale, scale, scale, Qt.black
                        )
            painter.end()
            self.qr.setPixmap(QPixmap.fromImage(image))
            self.shown_url = url
            self.link.setText(url)
            self.copy.setEnabled(True)
            self.preview.setEnabled(True)
            self.status.setText(
                "Sharing is on. Students on the same network can scan this code. Keep LectureLive open while they read or download."
            )

    def shutdown(self):
        if self.session:
            self.stop_sharing()
        return not (self.cleaner and self.cleaner.is_alive())
