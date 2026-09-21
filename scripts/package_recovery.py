import hashlib, json, zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "recovery"
out.mkdir(exist_ok=True)
archive = out / "LectureLive-Windows-ARM64-Recovery.zip"
files = []
for folder in [
    "dist/LectureLive",
    "app",
    "assets",
    "scripts",
    "docs",
    "glossaries",
    "offline_dependencies/wheels",
]:
    files.extend(
        p
        for p in (root / folder).rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.name != "get-pip.py"
    )
files.extend(
    root / name
    for name in [
        "README.md",
        "Setup.cmd",
        "Launch.cmd",
        "STATUS.md",
        "requirements-lock.txt",
        "LectureLive.pyw",
        "pytest.ini",
        "assets.lock.json",
        "fixtures.lock.json",
        "dependencies.lock.json",
        "offline_dependencies/python-3.11.9-embed-arm64.zip",
    ]
)
files.extend((root / "tests").glob("test_*.py"))
files.extend((root / "tests/fixtures").glob("*.json"))
manifest = {}
with zipfile.ZipFile(
    archive, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True
) as z:
    for p in files:
        name = p.relative_to(root).as_posix()
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        manifest[name] = h.hexdigest()
        z.write(p, name)
    z.writestr("RECOVERY_SHA256.json", json.dumps(manifest, indent=2))
(root / "recovery/RECOVERY_SHA256.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)
print(str(archive), archive.stat().st_size, "bytes", len(files), "files", flush=True)
with zipfile.ZipFile(archive) as z:
    bad = z.testzip()
    if bad:
        raise RuntimeError("Recovery ZIP integrity failed: " + bad)
print("Recovery ZIP CRC integrity verified", flush=True)

with archive.open("rb") as stream:
    archive_digest = hashlib.file_digest(stream, "sha256").hexdigest()
archive.with_suffix(".zip.sha256").write_text(
    archive_digest + "  " + archive.name + "\n", encoding="ascii"
)
print("Archive SHA-256:", archive_digest, flush=True)
