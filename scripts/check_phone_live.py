"""Real offline Auto speech with twenty external loopback caption readers."""

import argparse
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.request


def worker(folder, cpu):
    from app.system.offline import enforce_offline

    enforce_offline()
    from app.config.settings import Settings, ROOT
    from app.pipeline import Pipeline
    from app.sharing.service import SharingSession
    from app.sharing.history import Database
    from app.system.auto_self_test import conversation_wav, verify_exports

    sharing = SharingSession(folder, "127.0.0.1")
    sharing.start()
    pipeline = None
    result = {"passed": False, "real_microphone": False, "physical_wifi": False}
    try:
        until = time.monotonic() + 20
        while not sharing.url and not sharing.problem() and time.monotonic() < until:
            time.sleep(0.02)
        assert sharing.url, sharing.problem()
        (folder / "connection.json").write_text(json.dumps({"url": sharing.url}))
        wav = folder / "conversation.wav"
        duration = conversation_wav(ROOT / "tests/fixtures", wav)
        pipeline = Pipeline(
            ROOT,
            folder,
            Settings(
                speaking_language="auto",
                profile="fast",
                accelerator="cpu" if cpu else "auto",
            ),
            lambda *a: None,
            wav=str(wav),
            force_cpu=cpu,
            caption_sink=sharing.capture,
        )
        pipeline.start()
        assert pipeline.started and pipeline.source is not None
        journal_folder = pipeline.export.folder
        pipeline.source.thread.join(duration + 90)
        assert not pipeline.source.thread.is_alive()
        pipeline.close()
        assert sharing.history.flush(), sharing.problem()
        records = {}
        for line in (
            (journal_folder / "events.jsonl").read_text(encoding="utf-8").splitlines()
        ):
            record = json.loads(line)
            records[record["identifier"]] = record
        with Database(sharing.history.path) as db:
            rows = db.page(after=0, limit=120)["entries"]
            assert len(rows) == len(records) and rows
            assert [r["identifier"] for r in rows] == sorted(records)
            for row in rows:
                original = records[row["identifier"]]
                for key in (
                    "english",
                    "chinese",
                    "source_language",
                    "translation_status",
                ):
                    if key in original:
                        assert row[key] == original[key], (row, original)
            assert {"en", "zh"} <= {
                r["source_language"] for r in rows if r["kind"] == "caption"
            }
        assert all(
            pipeline.metrics[k] == 0
            for k in (
                "dropped_audio_chunks",
                "dropped_phrases",
                "translation_skips",
                "audio_gaps",
            )
        ), pipeline.metrics
        exports = verify_exports(journal_folder)
        result.update(
            passed=True,
            backend=pipeline.asr.name,
            audio_seconds=duration,
            matched_history_entries=len(rows),
            metrics=pipeline.metrics,
            exports=exports,
        )
        sharing.state("Lecture ended")
        # Let each reader observe the last source/translation updates.
        time.sleep(2)
    finally:
        if pipeline is not None:
            pipeline.close()
        (folder / "history-ended").touch()
        sharing.close()
        (folder / "worker.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )


def run(cpu=False):
    root = Path(__file__).resolve().parents[1]
    label = "cpu" if cpu else "npu"
    folder = root / f"tests/phone-live-{label}-data"
    folder.mkdir(parents=True, exist_ok=True)
    # Each attempt is isolated and has a new token, database and coordinator file.
    import tempfile

    attempt = Path(tempfile.mkdtemp(prefix="run-", dir=folder))
    child = subprocess.Popen(
        [
            sys.executable,
            "-X",
            "utf8",
            "-m",
            "scripts.check_phone_live",
            "--worker",
            str(attempt),
            *(["--cpu"] if cpu else []),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    done = threading.Event()
    errors = []
    counts = []
    try:
        end = time.monotonic() + 30
        while not (attempt / "connection.json").exists() and time.monotonic() < end:
            assert child.poll() is None, "Speech worker failed to start"
            time.sleep(0.02)
        url = json.loads((attempt / "connection.json").read_text())["url"]

        def phone(index):
            reads = 0
            while not done.is_set():
                try:
                    with urllib.request.urlopen(
                        url + "api/page?limit=120", timeout=5
                    ) as response:
                        page = json.load(response)
                    ids = [row["identifier"] for row in page["entries"]]
                    assert ids == sorted(set(ids))
                    reads += 1
                except Exception as exc:
                    if child.poll() is None and not (attempt / "worker.json").exists():
                        # Closing the helper marks the end; ignore only that final teardown.
                        if not (attempt / "history-ended").exists():
                            errors.append(str(exc))
                done.wait(0.3)
            counts.append(reads)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(phone, i) for i in range(20)]
            assert child.wait(timeout=240) == 0, "Real speech worker failed"
            done.set()
            for f in futures:
                f.result()
        result = json.loads((attempt / "worker.json").read_text(encoding="utf-8"))
        assert result["passed"], result
        assert not errors, errors
        result.update(
            concurrent_readers=20,
            successful_http_requests=sum(counts),
            reader_counts=counts,
            lecture_connection_errors=errors,
            environment="Windows source runtime; microphone replaced by timed local WAV; HTTP over loopback",
        )
        Path(f"tests/artifacts/phone-live-{label}-080.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, indent=2))
    finally:
        done.set()
        if child.poll() is None:
            child.kill()
            child.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()
    worker(args.worker, args.cpu) if args.worker else run(args.cpu)
