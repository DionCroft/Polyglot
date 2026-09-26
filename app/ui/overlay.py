import html
import time
from PySide6.QtCore import Qt, QRectF, Signal, QTimer
from PySide6.QtGui import QColor, QPainter, QTextDocument, QFont, QFontMetricsF
from PySide6.QtWidgets import QWidget, QApplication
from app.system.desktop import overlay_input
from app.system.architecture import is_macos
from app.captions.display import CaptionDisplay
from app.captions.state import Caption
from app.ui.projector import RollingProjector


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
        self.projector = RollingProjector()
        if history:
            for entry in history.entries.values():
                self.projector.accept(entry)
        self.roll_timer = QTimer(self)
        self.roll_timer.setInterval(50)
        self.roll_timer.timeout.connect(self._roll_tick)
        self.last_tick = time.monotonic()
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

    def enqueue(self, entry):
        self.projector.accept(entry)
        self.preview = False
        self.update()

    def _roll_tick(self):
        now = time.monotonic()
        elapsed = min(0.1, max(0, now - self.last_tick))
        self.last_tick = now
        if (
            self.settings.overlay_layout == "rolling"
            and self.isVisible()
            and not self.preview
        ):
            self.projector.prepare(self.width() - 48, self.height() - 88, self.settings)
            self.projector.advance(elapsed, self.settings.projector_line_ms / 1000)
            self.update()

    def _paint_rolling(self):
        screen = self.screen().availableGeometry()
        width = (
            self.width() if self.drag else min(self.settings.width, screen.width() - 32)
        )
        font = QFont(
            "PingFang SC" if is_macos() else "Microsoft YaHei UI",
            self.settings.font_size,
        )
        # Even a small panel must fit one complete line at the chosen font size.
        minimum = int(QFontMetricsF(font).height() * self.settings.spacing / 100) + 96
        desired = self.height() if self.drag else self.settings.projector_height
        height = min(max(minimum, desired), screen.height() - 40)
        if (width, height) != (self.width(), self.height()):
            QTimer.singleShot(0, lambda: self._fit_geometry(width, height))
        viewport = QRectF(24, 44, self.width() - 48, self.height() - 88)
        player = self.projector
        if self.preview:
            # Preview does not become part of the lecture queue.
            player = RollingProjector()
            player.accept(
                self.display.pending
                or self.display.pair
                or Caption(
                    0, 0, 0, "Your words. Understood.", "让每一句话，都被听懂。", True
                )
            )
        player.prepare(viewport.width(), viewport.height(), self.settings)
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
        count = max(1, len(player.columns))
        column_width = (viewport.width() - 24 * (count - 1)) / count
        for index, (lang, column) in enumerate(player.columns.items()):
            x = viewport.left() + index * (column_width + 24)
            painter.setPen(QColor("#c6d9e2"))
            painter.drawText(
                QRectF(x, 9, column_width, 30),
                Qt.AlignVCenter,
                painter.fontMetrics().elidedText(
                    player.labels[lang], Qt.ElideRight, int(column_width)
                ),
            )
            visible = column.visible_lines()
            if not visible:
                continue
            # Clip at the last complete line, never halfway through the next one.
            visible_height = visible[-1].bottom - column.offset
            painter.save()
            painter.setClipRect(QRectF(x, viewport.top(), column_width, visible_height))
            painter.translate(x, viewport.top() - column.offset)
            column.document.drawContents(
                painter, QRectF(0, column.offset, column_width, visible_height)
            )
            painter.restore()
        player.drawn = True
        progress = " · ".join(
            ("EN" if lang == "en" else "中文" if lang == "zh" else "Notice")
            + f" {column.index + 1}–{column.index + len(column.visible_lines())}/{len(column.lines)}"
            for lang, column in player.columns.items()
        )
        footer = (f"{player.backlog} waiting · " if player.backlog else "") + progress
        notice = getattr(self, "language_notice", "")
        if self.settings.speaking_language == "auto" and notice:
            footer = (
                (f"{player.backlog} waiting · " if player.backlog else "")
                + notice
                + " · "
                + progress
            )
        if player.waiting:
            footer += " · Waiting for translation"
        elif not footer:
            footer = "Waiting for speech"
        if not self.settings.locked:
            footer += " · Drag / resize · lock before teaching"
        painter.setPen(QColor("#b3c5cb"))
        painter.drawText(
            24,
            self.height() - 14,
            painter.fontMetrics().elidedText(footer, Qt.ElideRight, self.width() - 48),
        )
        painter.end()

    def set_caption(self, caption):
        if not self.display.accept(caption):
            return
        self.caption = self.display.pair
        self.partial = self.display.partial
        self.preview = False
        self.update()

    def reset(self, *, new_session=False):
        if new_session:
            self.projector = RollingProjector()
        self.display = CaptionDisplay()
        self.caption = None
        self.partial = None
        self.preview = self.projector.current is None
        self.update()

    def lock(self, locked):
        self.settings.locked = locked
        if self.isVisible():
            overlay_input(int(self.winId()), locked)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        overlay_input(int(self.winId()), self.settings.locked)
        self.last_tick = time.monotonic()
        self.roll_timer.start()

    def hideEvent(self, event):
        self.roll_timer.stop()
        self.projector.drawn = False
        super().hideEvent(event)

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
