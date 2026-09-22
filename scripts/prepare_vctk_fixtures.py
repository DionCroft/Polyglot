"""Optional online developer setup; VCTK audio is never bundled with LectureLive."""

import hashlib
import io
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np
from scripts.setup_assets import safe_path


def downsample(data):
    """Fixed 97-tap low-pass FIR then 3:1 decimation, mono PCM16 48 -> 16 kHz."""
    if data.startswith(b"fLaC"):
        # The Viewer calls these audio.wav but currently serves the original FLAC.
        if len(data) < 42 or data[4] & 127 or int.from_bytes(data[5:8], "big") != 34:
            raise ValueError("Expected FLAC STREAMINFO")
        info = int.from_bytes(data[18:26], "big")
        if (info >> 44, ((info >> 41) & 7) + 1, ((info >> 36) & 31) + 1) != (
            48000,
            1,
            16,
        ):
            raise ValueError("Expected VCTK mono 48 kHz PCM16")
        decoder = shutil.which("ffmpeg")
        if not decoder:
            raise RuntimeError(
                "Fixture preparation needs FFmpeg on PATH; the app does not."
            )
        raw = subprocess.run(
            [
                decoder,
                "-nostdin",
                "-v",
                "error",
                "-f",
                "flac",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "pipe:1",
            ],
            input=data,
            capture_output=True,
            check=True,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout
    else:
        with wave.open(io.BytesIO(data)) as reader:
            if (
                reader.getnchannels(),
                reader.getsampwidth(),
                reader.getframerate(),
            ) != (1, 2, 48000):
                raise ValueError("Expected VCTK mono 48 kHz PCM16")
            raw = reader.readframes(reader.getnframes())
    audio = np.frombuffer(raw, dtype="<i2").astype(np.float64)
    if len(audio) < 97:
        raise ValueError("Fixture too short")
    positions = np.arange(-48, 49, dtype=np.float64)
    kernel = 0.3 * np.sinc(0.3 * positions) * np.hamming(97)
    kernel /= kernel.sum()
    filtered = np.convolve(audio, kernel, mode="same")[::3]
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        writer.writeframes(
            np.rint(np.clip(filtered, -32768, 32767)).astype("<i2").tobytes()
        )
    return output.getvalue()


def fetch(url):
    """Bound transient service failures; never retry changed metadata/checksums."""
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code not in {
                429,
                500,
                502,
                503,
                504,
            }:
                raise
            if attempt == 3:
                raise
            delay = 2 ** (attempt + 1)
            if isinstance(error, urllib.error.HTTPError) and error.code == 429:
                header = error.headers.get("Retry-After", "30")
                delay = min(30, max(delay, int(header) if header.isdigit() else 30))
            time.sleep(delay)


def source_rows(source, length=1):
    params = dict(
        dataset=source["dataset"],
        config="default",
        split="train",
        offset=source["row"],
        length=length,
    )
    data = fetch(
        "https://datasets-server.huggingface.co/rows?" + urllib.parse.urlencode(params)
    )
    return {item["row_idx"]: item["row"] for item in json.loads(data)["rows"]}


def download(case, row=None):
    source = case["source"]
    if row is None:
        row = source_rows(source)[source["row"]]
    if (row["speaker_id"], row["text"], row["file"].split("/")[-1], row["accent"]) != (
        case["speaker"],
        case["reference"],
        source["file"],
        case["accent"],
    ):
        raise ValueError("Public speech metadata changed")
    url = row["audio"][0]["src"]
    if "/" + source["revision"] + "/" not in url:
        raise ValueError("Dataset Viewer revision changed; refusing a different test")
    raw = fetch(url)
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError("Source audio checksum mismatch")
    converted = downsample(raw)
    if hashlib.sha256(converted).hexdigest() != case["sha256"]:
        raise ValueError("Converted audio checksum mismatch")
    return converted


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "tests/fixtures/vctk-accent-cases.json").read_text(encoding="utf-8")
    )
    cached_rows = {}
    for case in manifest["cases"]:
        path = safe_path(root, case["path"])
        if (
            path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"]
        ):
            continue
        source = case["source"]
        key = (source["dataset"], source["row"])
        if key not in cached_rows:
            cached_rows.update(
                {
                    (source["dataset"], index): row
                    for index, row in source_rows(source, 100).items()
                }
            )
        data = download(case, cached_rows[key])
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".wav.partial")
        temporary.write_bytes(data)
        temporary.replace(path)
        print("Prepared", case["id"], flush=True)
    print("Verified VCTK accent fixtures. See docs/licenses/vctk-NOTICE.md.")


if __name__ == "__main__":
    main()
