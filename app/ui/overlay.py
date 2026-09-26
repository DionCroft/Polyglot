import html
from PySide6.QtCore import Qt, QRectF, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QTextDocument, QFont
from PySide6.QtWidgets import QWidget, QApplication
from app.system.desktop import overlay_input
from app.system.architecture import is_macos
from app.captions.display import CaptionDisplay
from app.captions.state import Caption


class Overlay(QWidget):
    moved = Signal()

    def __init__(self, settings, history=None):
        super().__init__(
            None,
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus,
        )
        self.settings = settings
        self.history = history
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
        height = min(self.target_height(), rect.height() - 32)
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

    def target_height(self):
        return (
            self.settings.projector_height
            if self.settings.overlay_layout == "rolling"
            else self.settings.height
        )

    def _rolling_document(self, width, max_height=None):
        """A shared table keeps both languages on the same chronological row."""
        doc = QTextDocument()
        doc.setDocumentMargin(0)
        doc.setDefaultFont(
            QFont(
                "PingFang SC" if is_macos() else "Microsoft YaHei UI",
                self.settings.font_size,
            )
        )
        doc.setTextWidth(width)
        entries = self.history.recent(4) if self.history else []
        if not entries:
            current = self.display.pending or self.display.pair
            if current:
                entries = [current]
            elif self.preview:
                entries = [
                    Caption(
                        0,
                        0,
                        0,
                        "Your words. Understood.",
                        "让每一句话，都被听懂。",
                        True,
                    )
                ]
        languages = (
            ["en", "zh"]
            if self.settings.mode == "Bilingual"
            else ["en" if self.settings.mode == "English" else "zh"]
        )
        rows = []
        for entry in entries:
            if not isinstance(entry, Caption):
                rows.append(
                    f'<tr><td colspan="{len(languages)}"><p style="font-size:14pt;color:#ffd59b;margin-bottom:16px">'
                    f"Speech not transcribed · {html.escape(entry.reason)}</p></td></tr>"
                )
                continue
            cells = []
            for language in languages:
                if isinstance(entry, Caption):
                    source = entry.source_language == language
                    text = entry.english if language == "en" else entry.chinese
                    text = text or (
                        "Translation unavailable"
                        if entry.translation_status == "unavailable"
                        else "Translating…"
                    )
                    label = "Spoken" if source else "Translation"
                colour = (
                    self.settings.english_color
                    if language == "en"
                    else self.settings.chinese_color
                )
                cells.append(
                    f'<td width="{100 // len(languages)}%" valign="top"><p style="color:{colour};line-height:{self.settings.spacing}%;margin-bottom:16px"><span style="font-size:12pt">{label}</span><br>{html.escape(text)}</p></td>'
                )
            rows.append("<tr>" + "".join(cells) + "</tr>")
        doc.trimmed = False
        while True:
            doc.setHtml(
                '<table width="100%" cellspacing="14" cellpadding="0">'
                + "".join(rows)
                + "</table>"
            )
            if (
                max_height is None
                or doc.size().height() <= max_height
                or len(rows) <= 1
            ):
                break
            rows.pop(0)
            doc.trimmed = True
        return doc

    def _paint_rolling(self):
        screen = self.screen().availableGeometry()
        width = (
            self.width() if self.drag else min(self.settings.width, screen.width() - 32)
        )
        height = (
            self.height()
            if self.drag
            else min(self.settings.projector_height, screen.height() - 40)
        )
        if (width, height) != (self.width(), self.height()) and not self.drag:
            QTimer.singleShot(0, lambda: self._fit_geometry(width, height))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        backdrop = QColor("#10191e")
        backdrop.setAlphaF(self.settings.opacity / 100)
        painter.setBrush(backdrop)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 16, 16)
        painter.setFont(
            QFont("PingFang SC" if is_macos() else "Microsoft YaHei UI", 12)
        )
        painter.setPen(QColor("#c6d9e2"))
        painter.drawText(
            30, 27, "简体中文" if self.settings.mode == "Chinese" else "English"
        )
        if self.settings.mode == "Bilingual":
            painter.drawText(self.width() // 2 + 7, 27, "简体中文")
        viewport = QRectF(24, 38, self.width() - 48, self.height() - 82)
        doc = self._rolling_document(self.width() - 48, viewport.height())
        offset = max(0, doc.size().height() - viewport.height())
        painter.save()
        inset = 0
        if offset:
            block = doc.begin()
            while block.isValid():
                top = doc.documentLayout().blockBoundingRect(block).top()
                layout = block.layout()
                for index in range(layout.lineCount()):
                    line = layout.lineAt(index)
                    start = top + line.y()
                    end = start + line.height()
                    if start < offset < end:
                        inset = max(inset, end - offset)
                block = block.next()
        painter.setClipRect(viewport.adjusted(0, inset, 0, 0))
        painter.translate(viewport.left(), viewport.top() - offset)
        doc.drawContents(painter)
        painter.restore()
        if not self.settings.locked:
            footer = "Drag to move · resize ↘ · lock before teaching"
        else:
            footer = (
                "Earlier text ↑ · full history in Transcript"
                if offset or doc.trimmed
                else "Rolling captions · full history in Transcript"
            )
            if self.settings.speaking_language == "auto" and getattr(
                self, "language_notice", ""
            ):
                footer = self.language_notice
        painter.setPen(QColor("#b3c5cb"))
        painter.drawText(30, self.height() - 14, footer)
        painter.end()

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
        if self.settings.overlay_layout == "rolling":
            self._paint_rolling()
            return
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
            if self.settings.overlay_layout == "rolling":
                self.settings.projector_height = self.height()
            else:
                self.settings.height = self.height()
            self.settings.placement = "Custom"
            self.moved.emit()
