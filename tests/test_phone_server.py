"""Real loopback HTTP requests; no physical classroom LAN/phones implied."""

import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import pytest
from app.captions.state import Caption
from app.sharing.history import Database
from app.sharing.server import LocalServer, local_address


@pytest.fixture
def server(tmp_path):
    path = tmp_path / "history.sqlite"
    with Database(path, write=True) as db:
        for i in range(1, 301):
            db.put(
                "pair",
                Caption(
                    i,
                    i,
                    i + 1,
                    f"English {i}",
                    f"中文 {i}",
                    True,
                    translation_status="complete",
                ),
            )
        db.set_meta("state", "Listening")
    server = LocalServer(
        ("127.0.0.1", 0),
        path,
        "x" * 43,
        Path(__file__).resolve().parents[1] / "assets/phone",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/s/" + server.token + "/"
    yield server, url
    server.shutdown()
    server.server_close()
    thread.join(3)


def read(url, headers=None):
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers or {}), timeout=8
    ) as response:
        return response.read(), response.headers


def test_real_server_late_join_and_txt_include_all_entries(server):
    _, url = server
    data, headers = read(url + "api/page?limit=120")
    page = json.loads(data)
    assert page["count"] == 300 and len(page["entries"]) == 120
    assert page["entries"][0]["identifier"] == 181
    data, headers = read(url + "transcript.txt?view=both")
    text = data.decode("utf-8-sig")
    assert all(
        f"English {i}\n" in text and f"中文 {i}\n" in text for i in range(1, 301)
    )
    assert "attachment" in headers["Content-Disposition"]
    assert headers["Cache-Control"] == "no-store"
    assert "frame-ancestors" in headers["Content-Security-Policy"]
    page = json.loads(read(url + "api/page?q=English%201&limit=40")[0])
    assert page["entries"][0]["identifier"] == 1


def test_twenty_simultaneous_readers_and_refresh(server):
    _, url = server

    def phone(_):
        for _ in range(3):
            page = json.loads(read(url + "api/page?after=0&limit=40")[0])
            assert [c["identifier"] for c in page["entries"]] == list(range(1, 41))
        return True

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        assert all(pool.map(phone, range(20)))


@pytest.mark.parametrize(
    "suffix,headers,status",
    [
        ("../wrong/api/page", {}, 404),
        ("api/page", {"Host": "evil.example"}, 403),
        ("api/page", {"Origin": "http://evil.example"}, 403),
        ("api/page?limit=-3", {}, 400),
        ("../../history.sqlite", {}, 404),
        ("api/page?after=999999999999999999999999", {}, 400),
    ],
)
def test_token_origin_host_and_path_guards(server, suffix, headers, status):
    _, url = server
    with pytest.raises(urllib.error.HTTPError) as error:
        read(url + suffix, headers)
    assert error.value.code == status


def test_private_addresses_and_no_cloud_connections():
    assert local_address("192.168.1.12") and local_address("10.2.3.4")
    assert not any(
        local_address(ip) for ip in ["0.0.0.0", "8.8.8.8", "169.254.2.3", "127.0.0.1"]
    )
    code = """
import socket
from app.sharing.server import enforce_local_server
enforce_local_server('127.0.0.1')
s=socket.socket()
for action in (lambda:s.connect(('8.8.8.8',80)), lambda:socket.getaddrinfo('example.com',80), lambda:s.bind(('0.0.0.0',0))):
    try: action()
    except PermissionError: pass
    else: raise AssertionError('Unexpected network permission')
s.close()
"""
    assert (
        subprocess.run([sys.executable, "-c", code], capture_output=True).returncode
        == 0
    )


def test_model_process_stays_offline():
    code = """
from app.system.offline import enforce_offline
import socket
enforce_offline()
try: socket.socket()
except PermissionError: pass
else: raise AssertionError('Network opened in the speech process')
"""
    assert (
        subprocess.run([sys.executable, "-c", code], capture_output=True).returncode
        == 0
    )
