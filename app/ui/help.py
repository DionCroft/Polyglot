"""Readable, offline Markdown help without requiring an external editor."""

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QComboBox, QDialog, QVBoxLayout, QTextBrowser, QPushButton


class GuideDialog(QDialog):
    def __init__(self, docs, parent=None):
        super().__init__(parent)
        self.docs = docs.resolve()
        self.setWindowTitle("LectureLive · Help")
        self.resize(780, 640)
        layout = QVBoxLayout(self)
        self.pages = QComboBox()
        from app.system.architecture import is_macos

        if is_macos():
            self.pages.addItem("Mac installation and first captions", "MACOS.md")
        for label, filename in [
            ("Quick start", "QUICK_START.md"),
            ("English and Mandarin conversations", "CONVERSATIONS.md"),
            ("Automatic language switching", "AUTO_LANGUAGE.md"),
            ("Full user guide", "USER_GUIDE.md"),
            ("Installation help", "INSTALLATION.md"),
            ("Windows Intel/AMD beta", "WINDOWS_BETA.md"),
            ("Improving speech recognition", "SPEECH_RECOGNITION.md"),
            ("CO7000 project-management vocabulary", "CO7000_VOCABULARY.md"),
        ]:
            self.pages.addItem(label, filename)
        self.pages.setAccessibleName("Help topic")
        layout.addWidget(self.pages)
        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)
        self.browser.setOpenExternalLinks(False)
        self.browser.anchorClicked.connect(self.open_link)
        layout.addWidget(self.browser, 1)
        close = QPushButton("Back to LectureLive")
        close.clicked.connect(self.close)
        layout.addWidget(close)
        self.pages.currentIndexChanged.connect(self.load_page)
        self.load_page()

    def load_page(self, *_):
        self.show_document(self.docs / self.pages.currentData())

    def show_document(self, path):
        self.browser.document().setBaseUrl(QUrl.fromLocalFile(str(self.docs) + "/"))
        try:
            self.browser.setMarkdown(path.read_text(encoding="utf-8"))
        except OSError:
            self.browser.setPlainText(
                "This guide is missing. Restore the complete application folder, or read the README included with your download."
            )
        self.browser.verticalScrollBar().setValue(0)

    def open_link(self, url):
        if not url.scheme() and not url.path() and url.fragment():
            self.browser.scrollToAnchor(url.fragment())
        elif url.scheme() in {"https", "mailto"}:
            QDesktopServices.openUrl(url)
        else:
            path = (self.docs / url.path()).resolve() if url.isRelative() else None
            if url.isLocalFile():
                from pathlib import Path

                path = Path(url.toLocalFile()).resolve()
            if path and path.is_relative_to(self.docs) and path.suffix.lower() == ".md":
                self.show_document(path)
