import html
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QTextDocument, QFont
from PySide6.QtWidgets import QWidget, QApplication
from app.system.windows import overlay_input


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
        if caption.final:
            if self.caption and (caption.epoch, caption.identifier) < (
                self.caption.epoch,
                self.caption.identifier,
            ):
                return
            self.caption = caption
            if self.partial and (self.partial.epoch, self.partial.identifier) <= (
                caption.epoch,
                caption.identifier,
            ):
                self.partial = None
        else:
            if self.caption and (caption.epoch, caption.identifier) <= (
                self.caption.epoch,
                self.caption.identifier,
            ):
                return
            self.partial = caption
        self.preview = False
        self.update()

    def reset(self):
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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        backdrop = QColor("#10191e")
        backdrop.setAlphaF(self.settings.opacity / 100)
        painter.setBrush(backdrop)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)
        if self.caption:
            en = self.caption.english
            zh = self.caption.chinese
            provisional = not self.caption.final
        elif self.partial:
            en = self.partial.english
            zh = ""
            provisional = True
        else:
            en = "Your words. Understood."
            zh = "让每一句话，都被听懂。"
            provisional = False
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Microsoft YaHei UI", self.settings.font_size))
        doc.setTextWidth(self.width() - 64)
        lines = []
        if self.settings.mode != "Chinese":
            lines.append(
                f'<p style="margin:0;color:{self.settings.english_color};line-height:{self.settings.spacing}%;">{html.escape(en)}{(" …" if provisional else "")}</p>'
            )
        if self.settings.mode != "English" and zh:
            lines.append(
                f'<p style="margin-top:8px;margin-bottom:0;color:{self.settings.chinese_color};line-height:{self.settings.spacing}%;">{html.escape(zh)}</p>'
            )
        if self.caption and self.partial and self.settings.mode != "Chinese":
            lines.append(
                f'<p style="font-size:{max(14, int(self.settings.font_size * 0.65))}pt;color:#b3c5cb;margin-top:12px;">{html.escape(self.partial.english)} …</p>'
            )
        doc.setHtml("".join(lines))
        desired = int(doc.size().height()) + 52
        # Expand for real content rather than silently clipping a long Chinese sentence.
        screen = self.screen().availableGeometry()
        if desired > self.height() and desired < screen.height() - 40:
            bottom = self.y() + self.height()
            self.resize(self.width(), desired)
            if self.settings.placement == "Bottom":
                self.move(self.x(), max(screen.y(), bottom - desired))
        painter.translate(32, 20)
        doc.drawContents(painter, QRectF(0, 0, self.width() - 64, self.height() - 30))
        painter.resetTransform()
        if not self.settings.locked:
            painter.setPen(QColor("#6e8b95"))
            painter.drawText(
                18, self.height() - 8, "Drag to move · resize ↘ · Ctrl+Alt+C to lock"
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
