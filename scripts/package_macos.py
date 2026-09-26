"""Package a tested bundle without losing framework links or executable permissions."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys


def main():
    if sys.platform != "darwin":
        raise SystemExit("Package on macOS.")
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    app = root / "dist/LectureLive.app"
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
    release = root / "dist/macos-release"
    release.mkdir(parents=True, exist_ok=True)
    name = "LectureLive-0.8.0b1-macOS-AppleSilicon"
    archive = release / (name + ".zip")
    image = release / (name + ".dmg")
    # Notarisation is optional and only uses a preconfigured local keychain profile.
    profile = os.environ.get("LECTURELIVE_NOTARY_PROFILE")
    if profile:
        if not os.environ.get("LECTURELIVE_CODESIGN_IDENTITY"):
            raise RuntimeError("Notarisation requires a Developer ID signed build")
        submission = root / "build/notarisation.zip"
        subprocess.run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(app),
                str(submission),
            ],
            check=True,
        )
        subprocess.run(
            [
                "xcrun",
                "notarytool",
                "submit",
                str(submission),
                "--keychain-profile",
                profile,
                "--wait",
            ],
            check=True,
        )
        subprocess.run(["xcrun", "stapler", "staple", str(app)], check=True)
        subprocess.run(["xcrun", "stapler", "validate", str(app)], check=True)
    subprocess.run(
        [
            "ditto",
            "-c",
            "-k",
            "--sequesterRsrc",
            "--keepParent",
            str(app),
            str(archive),
        ],
        check=True,
    )
    stage = root / "build/dmg-stage"
    stage.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ditto", str(app), str(stage / "LectureLive.app")], check=True)
    applications = stage / "Applications"
    if not applications.is_symlink():
        applications.symlink_to("/Applications", target_is_directory=True)
    (stage / "READ ME FIRST.txt").write_text(
        (root / "docs/MACOS.md").read_text(), encoding="utf-8"
    )
    subprocess.run(
        [
            "hdiutil",
            "create",
            "-ov",
            "-volname",
            "LectureLive",
            "-srcfolder",
            str(stage),
            "-format",
            "UDZO",
            str(image),
        ],
        check=True,
    )
    (release / "INSTALL-MAC.md").write_text(
        (root / "docs/MACOS.md").read_text(), encoding="utf-8"
    )
    lines = []
    for artifact in (archive, image):
        with artifact.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        lines.append(digest + "  " + artifact.name)
    (release / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
