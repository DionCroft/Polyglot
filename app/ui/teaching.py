from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QComboBox,
)


class TeachingControls(QDialog):
    def __init__(self, owner):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setStyleSheet(owner.styleSheet())
        self.owner = owner
        self.setWindowTitle("LectureLive · Teaching controls")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        self.status = QLabel("Listening")
        layout.addWidget(self.status)
        self.warning = QLabel(owner.warning.text())
        self.warning.setObjectName("warning")
        self.warning.setWordWrap(True)
        self.warning.setMaximumWidth(520)
        self.warning.setVisible(not owner.warning.isHidden())
        layout.addWidget(self.warning)
        layout.addWidget(QLabel("Who is speaking?"))
        self.language = QComboBox()
        self.language.setAccessibleName("Speaking language")
        self.language.addItem("English → 简体中文", "en")
        self.language.addItem("Mandarin 普通话 → English", "zh")
        self.language.addItem("Auto · English ↔ Mandarin", "auto")
        self.language.setCurrentIndex(
            self.language.findData(owner.cfg.speaking_language)
        )
        self.language.currentIndexChanged.connect(
            lambda: owner.speaking_language.setCurrentIndex(
                owner.speaking_language.findData(self.language.currentData())
            )
        )
        self.language.setEnabled(owner.speaking_language.isEnabled())
        layout.addWidget(self.language)
        self.language_status = QLabel(owner.language_status.text())
        self.language_status.setWordWrap(True)
        self.language_status.setVisible(owner.cfg.speaking_language == "auto")
        layout.addWidget(self.language_status)
        self.meter = QProgressBar()
        self.meter.setRange(0, 100)
        self.meter.setTextVisible(False)
        layout.addWidget(self.meter)
        row = QHBoxLayout()
        layout.addLayout(row)
        self.pause = QPushButton("Pause")
        self.pause.clicked.connect(owner.pause)
        row.addWidget(self.pause)
        self.stop = QPushButton("Finish lecture")
        self.stop.clicked.connect(owner.stop)
        row.addWidget(self.stop)
        show = QPushButton("Full controls")
        show.clicked.connect(self.close)
        layout.addWidget(show)
        self.note = QLabel(
            "Choose Auto for conversation, or select the speaking language manually. Pause briefly between speakers. Captions stay on the selected display."
        )
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

    def show_warning(self, message):
        self.warning.setText(message)
        self.warning.setVisible(bool(message))
        self.layout().activate()
        self._fit_warning()
        self.adjustSize()

    def _fit_warning(self):
        if not self.warning.isHidden():
            height = self.warning.heightForWidth(self.warning.width())
            if height > 0:
                self.warning.setMinimumHeight(height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_warning()

    def closeEvent(self, event):
        self.owner.show()
        self.owner.raise_()
        event.accept()
