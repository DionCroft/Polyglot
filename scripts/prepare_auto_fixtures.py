"""Setup-only download of attributed, pinned public language-detection fixtures."""

import argparse
import hashlib
import json
import tarfile
import urllib.request
from collections import defaultdict
from pathlib import Path
from scripts.prepare_conversation_fixtures import pcm16
from scripts.setup_assets import safe_path, valid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-per-language", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases = json.loads(
        (root / "tests/fixtures/auto-language-cases.json").read_text(encoding="utf-8")
    )["cases"]
    groups = defaultdict(dict)
    counts = defaultdict(int)
    for case in cases:
        counts[case["language"]] += 1
        if (
            args.limit_per_language
            and counts[case["language"]] > args.limit_per_language
        ):
            continue
        if not valid(safe_path(root, case["path"]), case):
            groups[case["archive_url"]][case["member"]] = case
    for url, missing in groups.items():
        with urllib.request.urlopen(url, timeout=60) as response:
            with tarfile.open(fileobj=response, mode="r|gz") as archive:
                for member in archive:
                    if member.name not in missing or not member.isfile():
                        continue
                    case = missing[member.name]
                    if member.size != case["source_bytes"]:
                        raise ValueError("Fixture size changed")
                    raw = archive.extractfile(member).read()
                    if hashlib.sha256(raw).hexdigest() != case["source_sha256"]:
                        raise ValueError("Fixture source changed")
                    data = pcm16(raw)
                    if hashlib.sha256(data).hexdigest() != case["sha256"]:
                        raise ValueError("Converted fixture changed")
                    target = safe_path(root, case["path"])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    del missing[member.name]
                    if not missing:
                        break
        if missing:
            raise RuntimeError("Missing pinned fixture entries")
    print("Verified automatic-language fixtures")


if __name__ == "__main__":
    main()
