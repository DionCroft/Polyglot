"""Request macOS microphone access on the GUI thread, only after a user action."""

from app.system.architecture import is_macos


def microphone_permission(window, resume):
    if not is_macos():
        return True
    from PySide6.QtCore import QMicrophonePermission, Qt, QTimer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    permission = QMicrophonePermission()
    status = app.checkPermission(permission)
    if status == Qt.PermissionStatus.Granted:
        return True
    if status == Qt.PermissionStatus.Denied:
        window.warn(
            "Microphone access is off. Open System Settings → Privacy & Security → Microphone, enable LectureLive, then try again."
        )
        return False
    if getattr(window, "microphone_permission_pending", False):
        return False
    window.microphone_permission_pending = True

    def finished(result):
        window.microphone_permission_pending = False
        if getattr(window, "closing", False):
            return
        if result.status() == Qt.PermissionStatus.Granted:
            QTimer.singleShot(0, resume)
        else:
            window.warn(
                "Microphone access was not granted. Enable LectureLive in System Settings → Privacy & Security → Microphone."
            )

    app.requestPermission(permission, window, finished)
    return False
