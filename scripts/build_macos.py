"""Run on macOS 14+ ARM64 after setup; produces a self-contained app."""

import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
from scripts.setup_assets import safe_path, valid

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != "darwin" or platform.machine() != "arm64":
        raise SystemExit("Build on an Apple Silicon Mac with native ARM64 Python 3.11.")
    if sys.version_info[:2] != (3, 11) or int(platform.mac_ver()[0].split(".")[0]) < 14:
        raise SystemExit("Build requires Python 3.11 and macOS 14 or later.")
    os.chdir(ROOT)
    stage = ROOT / "build/macos-assets"
    for item in json.loads((ROOT / "assets-macos.lock.json").read_text())["assets"]:
        source = safe_path(ROOT, item["path"])
        if not valid(source, item):
            raise RuntimeError("Missing/damaged model: " + item["path"])
        target = safe_path(stage, item["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if not valid(target, item):
            if target.exists():
                target.unlink()
            # Same-volume hard links avoid an extra copy of 1+ GB of immutable weights.
            try:
                os.link(source, target)
            except OSError:
                shutil.copy2(source, target)
    # Preserve notices shipped in the exact wheels used to produce this bundle.
    import importlib.metadata
    import hashlib

    notices = ROOT / "build/macos-licenses"
    notices.mkdir(parents=True, exist_ok=True)
    for distribution in importlib.metadata.distributions():
        for file in distribution.files or []:
            if any(
                word in file.name.lower() for word in ("license", "copying", "notice")
            ):
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    suffix = hashlib.sha256(str(file).encode()).hexdigest()[:8]
                    target = notices / (
                        distribution.metadata["Name"] + "-" + suffix + "-" + file.name
                    )
                    shutil.copy2(source, target)
    icons = ROOT / "build/LectureLive.iconset"
    icons.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            target = icons / f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(size * scale),
                    str(size * scale),
                    "assets/lecturelive.png",
                    "--out",
                    str(target),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
    subprocess.run(
        ["iconutil", "-c", "icns", str(icons), "-o", "build/LectureLive.icns"],
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--noconfirm", "LectureLive-macOS.spec"],
        check=True,
    )
    subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", "dist/LectureLive.app"],
        check=True,
    )
    arch = subprocess.check_output(
        ["lipo", "-archs", "dist/LectureLive.app/Contents/MacOS/LectureLive"], text=True
    ).strip()
    if arch != "arm64":
        raise RuntimeError("Expected native arm64 app, found: " + arch)
    print(
        "Verified native ARM64 bundle. Signing identity: "
        + (os.environ.get("LECTURELIVE_CODESIGN_IDENTITY") or "ad-hoc (not notarised)")
    )


if __name__ == "__main__":
    main()
