import argparse, json, time, wave
from pathlib import Path
from app.system.offline import enforce_offline

enforce_offline()
import psutil
from app.config.settings import Settings
from app.pipeline import Pipeline

parser = argparse.ArgumentParser()
parser.add_argument("--seconds", type=int, default=600)
parser.add_argument("--noise-snr", type=float)
parser.add_argument("--output", default="")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
target = root / "tests/artifacts/stress.wav"
target.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(root / "tests/fixtures/technical.wav")) as f:
    source = f.readframes(f.getnframes())
if args.noise_snr is not None:
    import numpy as np

    audio = np.frombuffer(source, dtype="<i2").astype(np.float32) / 32768
    rng = np.random.default_rng(20260909)
    noise = rng.standard_normal(len(audio)).astype(np.float32)
    noise *= float(np.sqrt(np.mean(audio * audio))) / (10 ** (args.noise_snr / 20))
    source = (np.clip(audio + noise, -1, 0.9999) * 32768).astype("<i2").tobytes()
with wave.open(str(target), "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(16000)
    remaining = args.seconds * 16000 * 2
    while remaining > 0:
        chunk = source[:remaining]
        f.writeframesraw(chunk)
        remaining -= len(chunk)
counts = {"final_english": 0, "bilingual": 0}
warnings = []
samples = []


def emit(kind, value):
    if kind == "caption" and value.final:
        counts["bilingual" if value.chinese else "final_english"] += 1
    if kind == "warning":
        warnings.append(str(value))


p = Pipeline(
    root,
    root / "tests/artifacts/stress-data",
    Settings(profile="balanced"),
    emit,
    wav=target,
)
p.start()
process = psutil.Process()
start = time.monotonic()
next_sample = start
while p.source and p.source.thread.is_alive():
    now = time.monotonic()
    if now >= next_sample:
        samples.append(
            {
                "elapsed": now - start,
                "rss_mb": process.memory_info().rss / 1048576,
                "threads": process.num_threads(),
                "cpu_percent": process.cpu_percent(),
                **p.diagnostics(),
                "inet_connections": len(process.net_connections(kind="inet")),
                "battery_percent": getattr(psutil.sensors_battery(), "percent", None),
                "power_plugged": getattr(
                    psutil.sensors_battery(), "power_plugged", None
                ),
            }
        )
        (root / f"docs/evidence/stress-{args.seconds}s-progress.json").write_text(
            json.dumps(
                {"counts": counts, "samples": samples, "warnings": warnings}, indent=2
            ),
            encoding="utf-8",
        )
        next_sample = now + 10
    time.sleep(0.2)
time.sleep(2)
p.close()
report = {
    "source": "Real-time synthetic lecture replay",
    "noise_snr_db": args.noise_snr,
    "timing": "Latency includes VAD endpoint delay and downstream inference, relative to final voiced audio",
    "duration_seconds": time.monotonic() - start,
    "counts": counts,
    "samples": samples,
    "warnings": warnings,
    "workers_alive": [t.name for t in p.threads if t.is_alive()],
    "final_metrics": p.diagnostics(),
    "physical_classroom_acceptance": "pending",
}
(root / "docs/evidence" / (args.output or f"stress-{args.seconds}s.json")).write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        {
            "duration": report["duration_seconds"],
            "counts": counts,
            "rss_first_mb": samples[0]["rss_mb"],
            "rss_last_mb": samples[-1]["rss_mb"],
            "workers_alive": report["workers_alive"],
        }
    ),
    flush=True,
)
assert counts["bilingual"] >= max(1, args.seconds // 90)
assert not report["workers_alive"]

assert p.metrics["dropped_audio_chunks"] == 0
assert p.metrics["dropped_phrases"] == 0
assert p.metrics["translation_skips"] == 0
