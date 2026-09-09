"""Stage only verified portable models, excluding Qualcomm binaries."""

import json
import shutil
from pathlib import Path
from scripts.setup_assets import safe_path, valid

root = Path(__file__).resolve().parents[1]
for item in json.loads(
    (root / "assets-x64-beta.lock.json").read_text(encoding="utf-8")
)["assets"]:
    source = safe_path(root, item["path"])
    if not valid(source, item):
        raise RuntimeError("Beta model is missing or damaged: " + item["path"])
    target = safe_path(root / "build/beta-assets", item["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
