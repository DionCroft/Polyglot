"""Read-only HTTP helper. Runs separately; it never loads speech or translation models."""

import hmac
import ipaddress
import json
import os
from pathlib import Path
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn, TCPServer
from urllib.parse import parse_qs, urlsplit

from app.sharing.history import Database


def local_address(text, *, loopback=False):
    try:
        address = ipaddress.IPv4Address(text)
    except ipaddress.AddressValueError:
        return False
    networks = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
    return (loopback and address.is_loopback) or any(
        address in ipaddress.ip_network(n) for n in networks
    )


def enforce_local_server(host):
    """Allow only inbound IPv4 TCP on the selected local interface; no outbound/DNS."""

    def audit(event, args):
        if event == "socket.__new__":
            if args[1] != socket.AF_INET or args[2] != socket.SOCK_STREAM:
                raise PermissionError("Phone helper only accepts local TCP")
        elif event == "socket.bind":
            if args[1][0] != host:
                raise PermissionError("Unexpected listening interface")
        elif event in {
            "socket.connect",
            "socket.connect_ex",
            "socket.getaddrinfo",
            "socket.gethostbyname",
            "socket.gethostbyaddr",
            "socket.sendto",
            "socket.sendmsg",
        }:
            raise PermissionError("Phone helper cannot make outgoing connections")

    sys.addaudithook(audit)


class LocalServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = False
    request_queue_size = 32

    def __init__(self, address, db, token, assets):
        self.db = Path(db)
        self.token = token
        self.assets = Path(assets)
        self.slots = threading.BoundedSemaphore(32)
        super().__init__(address, Handler)

    def server_bind(self):
        TCPServer.server_bind(self)
        self.server_name = self.server_address[0]
        self.server_port = self.server_address[1]

    def get_request(self):
        request, address = super().get_request()
        request.settimeout(5)
        return request, address

    def process_request(self, request, address):
        if not local_address(address[0], loopback=True) or not self.slots.acquire(
            False
        ):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "LectureLive"
    sys_version = ""

    def log_message(self, *args):
        pass  # Never log the bearer link or caption text.

    def headers_for(self, content_type, length=None, download=False):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        if length is not None:
            self.send_header("Content-Length", str(length))
        else:
            self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.close_connection = True
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
        )
        if download:
            self.send_header(
                "Content-Disposition",
                'attachment; filename="LectureLive-transcript.txt"',
            )
        self.end_headers()
        self.output_started = True

    def do_GET(self):
        self.output_started = False
        try:
            self.respond()
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass
        except Exception:
            if self.output_started:
                self.close_connection = True
                return  # Missing chunk terminator marks an interrupted download.
            # Do not reveal database paths or internals to connected students.
            try:
                self.send_error(
                    503, "Caption history is temporarily unavailable. Please retry."
                )
            except OSError:
                pass

    def respond(self):
        if len(self.path) > 2048:
            self.send_error(414)
            return
        authority = f"{self.server.server_address[0]}:{self.server.server_address[1]}"
        if self.headers.get("Host") != authority:
            self.send_error(403)
            return
        if self.headers.get("Origin") not in {None, "http://" + authority}:
            self.send_error(403)
            return
        if self.headers.get("Sec-Fetch-Site") == "cross-site" and not (
            self.headers.get("Sec-Fetch-Mode") == "navigate"
            and self.headers.get("Sec-Fetch-Dest") == "document"
        ):
            self.send_error(403)
            return
        url = urlsplit(self.path)
        parts = url.path.split("/")
        if (
            len(parts) < 4
            or parts[1] != "s"
            or not hmac.compare_digest(parts[2], self.server.token)
        ):
            self.send_error(404)
            return
        route = "/".join(parts[3:])
        query = parse_qs(url.query, max_num_fields=12)
        if route in {"", "reader.js", "reader.css"}:
            filename = {
                "": "index.html",
                "reader.js": "reader.js",
                "reader.css": "reader.css",
            }[route]
            content_type = {
                "": "text/html; charset=utf-8",
                "reader.js": "text/javascript; charset=utf-8",
                "reader.css": "text/css; charset=utf-8",
            }[route]
            data = (self.server.assets / filename).read_bytes()
            self.headers_for(content_type, len(data))
            self.wfile.write(data)
            return
        if route == "api/page":
            kwargs = {}
            try:
                for key in ("before", "after", "start", "limit", "version"):
                    if key in query:
                        value = int(query[key][0])
                        if value < 0 or value > 2**63 - 1:
                            raise ValueError()
                        kwargs[key] = value
                kwargs["query"] = query.get("q", [""])[0][:120]
            except (ValueError, IndexError):
                self.send_error(400)
                return
            with Database(self.server.db) as db:
                result = db.page(**kwargs)
            data = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.headers_for("application/json; charset=utf-8", len(data))
            self.wfile.write(data)
            return
        if route == "transcript.txt":
            view = query.get("view", ["both"])[0]
            if view not in {"en", "zh", "both"}:
                self.send_error(400)
                return
            with Database(self.server.db) as db:
                self.headers_for("text/plain; charset=utf-8", download=True)
                buffer = bytearray(b"\xef\xbb\xbf")  # Windows Notepad UTF-8.
                for line in db.text_lines(view):
                    buffer.extend(line.encode("utf-8"))
                    if len(buffer) >= 65536:
                        self.chunk(buffer)
                        buffer.clear()
                if buffer:
                    self.chunk(buffer)
                self.wfile.write(b"0\r\n\r\n")
            return
        self.send_error(404)

    def chunk(self, data):
        self.wfile.write(f"{len(data):x}\r\n".encode("ascii"))
        self.wfile.write(data)
        self.wfile.write(b"\r\n")


def parent_input():
    # Windowed PyInstaller executables have sys.stdin=None even with a pipe.
    if sys.stdin is not None:
        return sys.stdin.buffer
    if sys.platform == "win32":
        import ctypes
        import msvcrt
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel.GetStdHandle.restype = wintypes.HANDLE
        handle = kernel.GetStdHandle(wintypes.DWORD(-10).value)
        if not handle or handle == wintypes.HANDLE(-1).value:
            raise OSError("Sharing requires its parent application pipe")
        return os.fdopen(msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY), "rb")
    return os.fdopen(os.dup(0), "rb")


def run(db, host, status_path):
    status = Path(status_path)
    server = None
    try:
        if not local_address(host, loopback=True):
            raise ValueError("Choose a private IPv4 Wi-Fi or Ethernet address")
        token = os.environ.pop("LECTURELIVE_SHARE_KEY", "")
        if len(token) < 32:
            raise ValueError("Missing private sharing key")
        parent = parent_input()
        enforce_local_server(host)
        assets = Path(__file__).resolve().parents[2] / "assets/phone"
        server = LocalServer((host, 0), db, token, assets)
        status.write_text(
            json.dumps({"port": server.server_port, "ready": True}), encoding="utf-8"
        )

        def parent_closed():
            try:
                while parent.read(1):
                    pass
            finally:
                server.shutdown()

        threading.Thread(target=parent_closed, daemon=True).start()
        server.serve_forever(poll_interval=0.15)
        return 0
    except Exception as exc:
        status.write_text(
            json.dumps({"ready": False, "error": str(exc)}), encoding="utf-8"
        )
        return 1
    finally:
        if server:
            server.server_close()
