"""LectureLive desktop entry point. No model downloads or network setup here."""

import sys
from app.system.offline import enforce_offline


def main():
    enforce_offline()
    if "--encoder-worker" in sys.argv:
        from app.asr.encoder_worker import run_worker

        index = sys.argv.index("--encoder-worker")
        return run_worker(*sys.argv[index + 1 : index + 4])
    if "--mac-encoder-worker" in sys.argv:
        from app.asr.macos_encoder import run_worker

        index = sys.argv.index("--mac-encoder-worker")
        return run_worker(*sys.argv[index + 1 : index + 4])
    if "--mac-ui-test" in sys.argv:
        from app.system.macos_ui_test import run

        return run(sys.argv[sys.argv.index("--mac-ui-test") + 1])
    from app.config.settings import DATA
    from app.utils.logging import configure

    configure(DATA / "logs")
    if "--conversation-ui-test" in sys.argv:
        from app.system.conversation_ui_test import run

        index = sys.argv.index("--conversation-ui-test")
        return run(sys.argv[index + 1], sys.argv[index + 2])
    if "--conversation-self-test" in sys.argv:
        from app.system.conversation_self_test import run
        from app.config.settings import ROOT

        index = sys.argv.index("--conversation-self-test")
        return run(ROOT, sys.argv[index + 1], sys.argv[index + 2])
    if "--self-test" in sys.argv:
        from app.system.self_test import run
        from app.config.settings import ROOT

        index = sys.argv.index("--self-test")
        return run(ROOT, sys.argv[index + 1], sys.argv[index + 2])
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QLockFile

    app = QApplication(sys.argv)
    app.setApplicationName("LectureLive")
    from app import __version__

    app.setApplicationVersion(__version__)
    app.setOrganizationName("LectureLive")
    DATA.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(DATA / "lecturelive.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(None, "LectureLive", "LectureLive is already running.")
        return 0
    from app.ui.main_window import MainWindow

    try:
        window = MainWindow()
        window.show()
    except Exception:
        import logging

        logging.exception("Desktop initialization failed")
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(
            None,
            "LectureLive could not start",
            "Please check the local log folder: " + str(DATA / "logs"),
        )
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
