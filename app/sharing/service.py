"""Local history and separately sandboxed inbound HTTP helper lifecycle."""

import json
import logging
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import time

from app.sharing.history import HistoryWriter


def interface_addresses():
    import ipaddress
    import psutil

    found = []
    stats = psutil.net_if_stats()
    for name, addresses in psutil.net_if_addrs().items():
        if not stats.get(name) or not stats[name].isup:
            continue
        for address in addresses:
            try:
                ip = ipaddress.IPv4Address(address.address)
            except ipaddress.AddressValueError:
                continue
            if any(
                ip in ipaddress.ip_network(n)
                for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
            ):
                found.append((name, str(ip)))
    return found


class SharingSession:
    def __init__(self, data, host, *, journal=None):
        root = Path(data) / "phone-sharing"
        root.mkdir(parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix="lecture-", dir=root)
        self.folder = Path(self.directory.name)
        self.host = host
        self.token = secrets.token_urlsafe(32)
        self.history = HistoryWriter(self.folder / "history.sqlite", journal=journal)
        self.process = None
        self.url = ""
        self.error = ""
        self.stopping = False
        self.thread = threading.Thread(
            target=self._start, name="Phone sharing startup", daemon=True
        )

    def start(self):
        self.history.start()
        self.thread.start()

    def capture(self, kind, caption):
        return self.history.submit(kind, caption)

    def state(self, text):
        self.history.submit("meta", ("state", text))

    def _start(self):
        try:
            if not self.history.ready.wait(10) or self.history.error:
                raise RuntimeError(self.history.error or "History startup timed out")
            if self.stopping:
                return
            env = dict(
                os.environ, LECTURELIVE_SHARE_KEY=self.token, PYTHONNOUSERSITE="1"
            )
            if getattr(sys, "frozen", False):
                env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
            command = [sys.executable]
            if not getattr(sys, "frozen", False):
                command += ["-m", "app.main"]
            status = self.folder / "server.json"
            command += [
                "--student-server",
                str(self.history.path),
                self.host,
                str(status),
            ]
            options = (
                {"creationflags": subprocess.CREATE_NO_WINDOW}
                if sys.platform == "win32"
                else {}
            )
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                **options,
            )
            until = time.monotonic() + 10
            while time.monotonic() < until and not self.stopping:
                if status.exists():
                    try:
                        data = json.loads(status.read_text(encoding="utf-8"))
                    except (OSError, ValueError):
                        time.sleep(0.05)
                        continue
                    if not data["ready"]:
                        raise RuntimeError(data.get("error", "Sharing helper failed"))
                    self.url = f"http://{self.host}:{data['port']}/s/{self.token}/"
                    return
                if self.process.poll() is not None:
                    raise RuntimeError("Sharing helper could not start")
                time.sleep(0.05)
            if not self.stopping:
                raise TimeoutError("Sharing helper did not start in time")
        except Exception as exc:
            self.error = str(exc)

    def problem(self):
        if self.error or self.history.error:
            return self.error or self.history.error
        if self.process and self.process.poll() is not None and not self.stopping:
            return "Phone sharing helper stopped. Local captions are still available."
        return ""

    def close(self):
        self.stopping = True
        # Revoke network access promptly, even while buffered history is draining.
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.thread.join(12) if self.thread.is_alive() else None
        if self.process:
            if self.process.stdin:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        self.history.close()
        if not self.history.thread.is_alive():
            try:
                self.directory.cleanup()
            except OSError:
                logging.exception("Phone temporary history cleanup failed")
