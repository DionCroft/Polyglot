"""Optional ONLINE developer setup for the checksum-pinned public accent fixtures."""

import hashlib, json, urllib.parse, urllib.request
from pathlib import Path
from scripts.setup_assets import safe_path


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "tests/fixtures/accent-cases.json").read_text(encoding="utf-8")
    )
    for case in manifest["cases"]:
        source = case.get("source")
        if not source:
            continue  # Existing synthetic fixtures have their own setup script.
        path = safe_path(root, case["path"])
        if (
            path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == case["sha256"]
        ):
            continue
        params = urllib.parse.urlencode(
            dict(
                dataset=source["dataset"],
                config=source["config"],
                split=source["split"],
                offset=source["row"],
                length=1,
            )
        )
        with urllib.request.urlopen(
            "https://datasets-server.huggingface.co/rows?" + params, timeout=60
        ) as response:
            row = json.load(response)["rows"][0]["row"]
        if row["text"] != case["reference"] or row["file"] != source["file"]:
            raise ValueError(
                "Public fixture metadata changed; refusing an incomparable test"
            )
        with urllib.request.urlopen(row["audio"][0]["src"], timeout=60) as response:
            payload = response.read()
        if hashlib.sha256(payload).hexdigest() != case["sha256"]:
            raise ValueError("Public fixture checksum mismatch")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".wav.partial")
        temporary.write_bytes(payload)
        temporary.replace(path)
        print("Prepared", case["id"], flush=True)
    print("Public accent fixtures verified. No lecturer audio has been uploaded.")


if __name__ == "__main__":
    main()
