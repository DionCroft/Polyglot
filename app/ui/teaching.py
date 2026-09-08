from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
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
        self.note = QLabel("Captions stay on the selected display.")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

    def closeEvent(self, event):
        self.owner.show()
        self.owner.raise_()
        event.accept()
