"""Create a portable Windows ZIP and verify every archived member (default: x64)."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--architecture", choices=("ARM64", "x64"), default="x64")
architecture = parser.parse_args().architecture
app_name = "LectureLive" if architecture == "ARM64" else "LectureLive-x64-Beta"
source = root / "dist" / app_name
if not (source / (app_name + ".exe")).is_file():
    raise RuntimeError("Build the beta first")
out = root / "recovery"
out.mkdir(exist_ok=True)
archive = out / f"LectureLive-Windows-{architecture}-Beta-0.7.0b1.zip"
partial = archive.with_suffix(".zip.partial")
manifest = {}
with zipfile.ZipFile(
    partial, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True
) as z:
    for path in sorted(source.rglob("*")):
        if path.is_file():
            name = path.relative_to(source.parent).as_posix()
            with path.open("rb") as stream:
                manifest[name] = hashlib.file_digest(stream, "sha256").hexdigest()
            z.write(path, name)
    z.writestr("SHA256.json", json.dumps(manifest, indent=2))
with zipfile.ZipFile(partial) as z:
    for name, expected in manifest.items():
        with z.open(name) as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                raise RuntimeError("Archive verification failed: " + name)
partial.replace(archive)
with archive.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
archive.with_suffix(".zip.sha256").write_text(
    digest + "  " + archive.name + "\n", encoding="ascii"
)
print(
    json.dumps(
        {
            "archive": str(archive),
            "bytes": archive.stat().st_size,
            "files": len(manifest),
            "sha256": digest,
            "verified": True,
        }
    )
)
