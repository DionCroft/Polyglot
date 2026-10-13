"""Synthetic long-lecture/HTTP load test; no speech accuracy or physical LAN claim."""

import concurrent.futures
import json
from pathlib import Path
import statistics
import tempfile
import threading
import time
import urllib.request
import psutil
from app.captions.state import Caption
from app.sharing.history import Database
from app.sharing.service import SharingSession


def run(count=25000):
    main = psutil.Process()
    with tempfile.TemporaryDirectory(prefix="lecturelive-history-load-") as folder:
        session = SharingSession(folder, "127.0.0.1")
        session.start()
        ending = threading.Event()
        timings = []
        errors = []
        reads = [0]
        snapshots = []
        peak_queue = 0
        peak_bytes = 0
        start = time.monotonic()
        try:
            until = start + 15
            while (
                not session.url and not session.problem() and time.monotonic() < until
            ):
                time.sleep(0.01)
            assert session.url, session.problem()
            helper = psutil.Process(session.process.pid)

            def phone(index):
                version = 0
                while not ending.is_set():
                    try:
                        with urllib.request.urlopen(
                            session.url + f"api/page?version={version}&limit=40",
                            timeout=5,
                        ) as response:
                            page = json.load(response)
                        assert len(page.get("entries", [])) <= 40
                        version = page["revision"]
                        reads[0] += 1
                    except Exception as exc:
                        errors.append(type(exc).__name__ + ": " + str(exc))
                    ending.wait(0.1)

            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
                futures = [pool.submit(phone, i) for i in range(20)]
                for i in range(1, count + 1):
                    caption = Caption(
                        i,
                        i * 3,
                        i * 3 + 2,
                        f"Term {i}. Project risk probability and impact. " * 4,
                        f"术语{i}。项目风险的概率和影响。" * 4,
                        True,
                        source_language="en" if i % 2 else "zh",
                        translation_status="complete",
                    )
                    begin = time.perf_counter()
                    assert session.capture("pair", caption), session.problem()
                    timings.append((time.perf_counter() - begin) * 1000)
                    peak_queue = max(peak_queue, session.history.queue.qsize())
                    peak_bytes = max(peak_bytes, session.history.queued_bytes)
                    if i % 100 == 0:
                        assert session.history.flush(10), session.problem()
                    if i in (1000, 5000, 15000, count):
                        snapshots.append(
                            dict(
                                entries=i,
                                writer_rss=main.memory_info().rss,
                                helper_rss=helper.memory_info().rss,
                            )
                        )
                assert session.history.flush(10)
                ending.set()
                for future in futures:
                    future.result()
            ids = []
            with Database(session.history.path) as db:
                after = 0
                while True:
                    rows = db.page(after=after, limit=120)["entries"]
                    if not rows:
                        break
                    assert all(row["english"] and row["chinese"] for row in rows)
                    ids.extend(row["identifier"] for row in rows)
                    after = ids[-1]
                assert ids == list(range(1, count + 1))
                assert db.page(query="Term 1.")["entries"][0]["identifier"] == 1
            assert not errors, errors[:5]
            samples = sorted(timings)
            return dict(
                passed=True,
                generated_caption_pairs=count,
                retained_unique_pairs=len(ids),
                concurrent_clients=20,
                successful_requests=reads[0],
                errors=errors,
                elapsed_seconds=round(time.monotonic() - start, 2),
                queue_peak_events=peak_queue,
                queue_peak_estimated_bytes=peak_bytes,
                submission_p50_ms=round(statistics.median(samples), 4),
                submission_p99_ms=round(samples[int(len(samples) * 0.99)], 4),
                memory_snapshots=snapshots,
                interpretation="Synthetic text over loopback, not real-time classroom, microphone or model latency. Driver RSS includes test measurements; compare helper RSS for the HTTP service.",
            )
        finally:
            ending.set()
            session.close()


if __name__ == "__main__":
    result = run()
    Path("tests/artifacts/phone-load-080.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
