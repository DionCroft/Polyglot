"""Download or verify only the portable macOS model inventory."""

import argparse
import json
from pathlib import Path
from scripts.setup_assets import install


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = install(root / "assets-macos.lock.json", root, args.verify, args.offline)
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
