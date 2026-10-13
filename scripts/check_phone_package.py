"""Real HTTP smoke check of a packaged helper; no physical LAN implied."""

import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import urllib.request
from app.captions.state import Caption
from app.sharing.history import Database


def run(executable):
    with tempfile.TemporaryDirectory(prefix="lecturelive-phone-test-") as tmp:
        root = Path(tmp)
        db = root / "history.sqlite"
        status = root / "status.json"
        token = secrets.token_urlsafe(32)
        with Database(db, write=True) as history:
            history.put(
                "pair",
                Caption(
                    1,
                    0,
                    2,
                    "Complete English",
                    "完整中文",
                    True,
                    translation_status="complete",
                ),
            )
        child = subprocess.Popen(
            [
                str(Path(executable).resolve()),
                "--student-server",
                str(db),
                "127.0.0.1",
                str(status),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=dict(
                os.environ,
                LECTURELIVE_SHARE_KEY=token,
                PYINSTALLER_RESET_ENVIRONMENT="1",
            ),
        )
        try:
            deadline = time.monotonic() + 30
            while not status.exists() and time.monotonic() < deadline:
                assert child.poll() is None, "Packaged helper exited"
                time.sleep(0.05)
            state = json.loads(status.read_text(encoding="utf-8"))
            assert state["ready"], state
            url = f"http://127.0.0.1:{state['port']}/s/{token}/"

            def read(route):
                with urllib.request.urlopen(url + route, timeout=8) as response:
                    return response.read().decode("utf-8-sig")

            for route in ("", "reader.js", "reader.css"):
                assert len(read(route)) > 100
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
                for text in pool.map(read, ["api/page"] * 20):
                    assert json.loads(text)["entries"][0]["chinese"] == "完整中文"
            assert "Complete English" in read("transcript.txt?view=both")
            child.stdin.close()
            assert child.wait(timeout=8) == 0, (
                "Helper must stop when parent pipe closes"
            )
            return {
                "passed": True,
                "packaged_assets": True,
                "simultaneous_clients": 20,
                "parent_exit_stops_server": True,
                "physical_wifi": False,
            }
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable")
    parser.add_argument("report")
    args = parser.parse_args()
    result = run(args.executable)
    Path(args.report).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
