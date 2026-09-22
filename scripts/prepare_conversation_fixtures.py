"""Setup-only: three attributed FLEURS smoke samples, pinned independently of models."""

import hashlib
import io
import json
from pathlib import Path
import struct
import tarfile
import urllib.request
import wave

import numpy as np


def pcm16(data):
    """Convert the pinned mono 16 kHz IEEE-float WAVs; reject any other format."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Expected RIFF WAV")
    position, samples, fmt = 12, None, None
    while position + 8 <= len(data):
        tag, size = struct.unpack_from("<4sI", data, position)
        block = data[position + 8 : position + 8 + size]
        if len(block) != size:
            raise ValueError("Truncated WAV")
        if tag == b"fmt ":
            fmt = struct.unpack_from("<HHIIHH", block)
        elif tag == b"data":
            samples = block
        position += 8 + size + size % 2
    if fmt != (3, 1, 16000, 64000, 4, 32) or samples is None:
        raise ValueError("Expected mono 16 kHz float32 fixture")
    audio = np.frombuffer(samples, dtype="<f4")
    if not np.isfinite(audio).all():
        raise ValueError("Non-finite audio")
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        writer.writeframes(
            np.rint(np.clip(audio * 32768, -32768, 32767)).astype("<i2").tobytes()
        )
    return output.getvalue()


def main():
    from scripts.setup_assets import safe_path, valid

    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "tests/fixtures/mandarin-cases.json").read_text(encoding="utf-8")
    )
    missing = {
        c["member"]: c
        for c in manifest["cases"]
        if not valid(safe_path(root, c["path"]), c)
    }
    if not missing:
        print("Verified all Mandarin smoke fixtures")
        return
    with urllib.request.urlopen(manifest["archive_url"], timeout=60) as response:
        with tarfile.open(fileobj=response, mode="r|gz") as archive:
            for member in archive:
                if member.name not in missing or not member.isfile():
                    continue
                case = missing[member.name]
                if member.size != case["source_bytes"]:
                    raise ValueError("Fixture byte count changed")
                data = archive.extractfile(member).read()
                if hashlib.sha256(data).hexdigest() != case["source_sha256"]:
                    raise ValueError("Fixture source checksum changed")
                converted = pcm16(data)
                if hashlib.sha256(converted).hexdigest() != case["sha256"]:
                    raise ValueError("Converted fixture checksum changed")
                target = safe_path(root, case["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(converted)
                del missing[member.name]
                print("Verified", case["id"], flush=True)
                if not missing:
                    break
    if missing:
        raise RuntimeError("Archive is missing expected Mandarin fixtures")


if __name__ == "__main__":
    main()
