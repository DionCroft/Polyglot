"""Create a complete portable beta ZIP and verify every archived member."""

import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "dist/LectureLive-x64-Beta"
if not (source / "LectureLive-x64-Beta.exe").is_file():
    raise RuntimeError("Build the beta first")
out = root / "recovery"
out.mkdir(exist_ok=True)
archive = out / "LectureLive-Windows-x64-Beta-0.6.0b1.zip"
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
