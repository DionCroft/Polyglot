import html
from PySide6.QtCore import Qt, QRectF, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QTextDocument, QFont
from PySide6.QtWidgets import QWidget, QApplication
from app.system.desktop import overlay_input
from app.system.architecture import is_macos
from app.captions.display import CaptionDisplay


class Overlay(QWidget):
    moved = Signal()

    def __init__(self, settings):
        super().__init__(
            None,
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus,
        )
        self.settings = settings
        self.display = CaptionDisplay()
        self.caption = None
        self.partial = None
        self.drag = None
        self.preview = True
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMinimumSize(400, 130)
        self.setWindowTitle("LectureLive Captions")
        self.resize(settings.width, settings.height)
        self.place()

    def place(self):
        screens = QApplication.screens()
        screen = next(
            (s for s in screens if s.name() == self.settings.monitor),
            QApplication.primaryScreen(),
        )
        rect = screen.availableGeometry()
        width = min(self.settings.width, rect.width() - 32)
        height = min(self.settings.height, rect.height() - 32)
        self.resize(width, height)
        x = rect.x() + (rect.width() - width) // 2
        y = (
            rect.y() + 30
            if self.settings.placement == "Top"
            else rect.bottom() - height - 28
        )
        if self.settings.placement == "Custom" and self.settings.x != -1:
            x = max(rect.left(), min(self.settings.x, rect.right() - width))
            y = max(rect.top(), min(self.settings.y, rect.bottom() - height))
        self.move(x, y)

    def set_caption(self, caption):
        if not self.display.accept(caption):
            return
        self.caption = self.display.pair
        self.partial = self.display.partial
        self.preview = False
        self.update()

    def reset(self):
        self.display = CaptionDisplay()
        self.caption = None
        self.partial = None
        self.preview = True
        self.update()

    def lock(self, locked):
        self.settings.locked = locked
        if self.isVisible():
            overlay_input(int(self.winId()), locked)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        overlay_input(int(self.winId()), self.settings.locked)

    def _caption_document(self, point_size, width=None):
        en, zh, upcoming = self.display.contents(self.settings.mode)
        if self.preview:
            en = "Your words. Understood."
            zh = "让每一句话，都被听懂。"
        provisional = bool(
            self.display.partial and not self.display.pair and not self.display.pending
        )
        doc = QTextDocument()
        doc.setDefaultFont(
            QFont("PingFang SC" if is_macos() else "Microsoft YaHei UI", point_size)
        )
        doc.setTextWidth((width or self.width()) - 64)
        lines = []
        from app.languages import caption_labels

        primary = self.display.primary(self.settings.mode)
        language = (
            primary.source_language if primary else self.settings.speaking_language
        )
        en_label, zh_label = caption_labels(language)
        if self.settings.mode != "Chinese":
            lines.append(
                f'<p style="margin:0;color:{self.settings.english_color};line-height:{self.settings.spacing}%;"><span style="font-size:12pt;">{en_label}</span><br>{html.escape(en)}{(" …" if provisional and language == "en" else "")}</p>'
            )
        if self.settings.mode != "English" and zh:
            lines.append(
                f'<p style="margin-top:8px;margin-bottom:0;color:{self.settings.chinese_color};line-height:{self.settings.spacing}%;"><span style="font-size:12pt;">{zh_label}</span><br>{html.escape(zh)}{(" …" if provisional and language == "zh" else "")}</p>'
            )
        if upcoming and (
            self.settings.mode == "Bilingual"
            or self.settings.mode == ("English" if language == "en" else "Chinese")
        ):
            lines.append(
                f'<p style="font-size:{max(14, int(point_size * 0.65))}pt;color:#b3c5cb;margin-top:12px;">{html.escape(upcoming)} …</p>'
            )
        notice = getattr(self, "language_notice", "")
        if self.settings.speaking_language == "auto" and notice:
            lines.append(
                f'<p style="font-size:12pt;color:#b3c5cb;">{html.escape(notice)}</p>'
            )
        doc.setHtml("".join(lines))
        return doc

    def _fit_geometry(self, width, desired):
        if self.drag or (desired == self.height() and width == self.width()):
            return
        screen = self.screen().availableGeometry()
        bottom = self.y() + self.height()
        self.resize(width, desired)
        x = max(screen.left(), min(self.x(), screen.right() - width + 1))
        y = (
            max(screen.y(), bottom - desired)
            if self.settings.placement == "Bottom"
            else self.y()
        )
        self.move(x, y)

    def paintEvent(self, event):
        screen = self.screen().availableGeometry()
        max_height = screen.height() - 40
        width = (
            self.width() if self.drag else min(self.settings.width, screen.width() - 32)
        )
        point_size = self.settings.font_size
        doc = self._caption_document(point_size, width)
        while doc.size().height() + 52 > max_height and point_size > 16:
            point_size -= 1
            doc = self._caption_document(point_size, width)
        if doc.size().height() + 52 > max_height:
            width = screen.width() - 32
            doc = self._caption_document(point_size, width)
        desired = min(
            max_height, max(self.settings.height, int(doc.size().height()) + 52)
        )
        if (desired != self.height() or width != self.width()) and not self.drag:
            QTimer.singleShot(0, lambda h=desired, w=width: self._fit_geometry(w, h))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        backdrop = QColor("#10191e")
        backdrop.setAlphaF(self.settings.opacity / 100)
        painter.setBrush(backdrop)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)
        painter.translate(32, 20)
        doc.drawContents(painter, QRectF(0, 0, self.width() - 64, self.height() - 30))
        painter.resetTransform()
        if not self.settings.locked:
            painter.setPen(QColor("#6e8b95"))
            painter.drawText(
                18,
                self.height() - 8,
                "Drag to move · resize ↘ · "
                + getattr(self.settings, "lock_shortcut", "Ctrl+Alt+C")
                + " to lock",
            )
            painter.drawLine(
                self.width() - 20,
                self.height() - 8,
                self.width() - 8,
                self.height() - 20,
            )

    def mousePressEvent(self, event):
        if not self.settings.locked and event.button() == Qt.LeftButton:
            self.drag = (
                event.globalPosition().toPoint(),
                self.geometry(),
                event.position().x() > self.width() - 28
                and event.position().y() > self.height() - 28,
            )

    def mouseMoveEvent(self, event):
        if not self.drag:
            return
        point, rect, resizing = self.drag
        delta = event.globalPosition().toPoint() - point
        if resizing:
            self.resize(
                max(400, rect.width() + delta.x()), max(130, rect.height() + delta.y())
            )
        else:
            self.move(rect.topLeft() + delta)

    def mouseReleaseEvent(self, event):
        if self.drag:
            self.drag = None
            self.settings.x = self.x()
            self.settings.y = self.y()
            self.settings.width = self.width()
            self.settings.height = self.height()
            self.settings.placement = "Custom"
            self.moved.emit()
