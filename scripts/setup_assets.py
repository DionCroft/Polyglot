"""Setup-only HTTPS downloads and verification; never imported by the app."""

import argparse, hashlib, json, time, urllib.request, zipfile
from pathlib import Path, PurePosixPath


def safe_path(root, relative):
    root = Path(root).resolve()
    posix = PurePosixPath(relative.replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts or ":" in str(posix):
        raise ValueError("Unsafe asset path")
    candidate = root.joinpath(*posix.parts)
    if not candidate.resolve().is_relative_to(root):
        raise ValueError("Asset path escaped root")
    return candidate


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def valid(path, item):
    return (
        path.is_file()
        and path.stat().st_size == item["bytes"]
        and digest(path) == item["sha256"]
    )


def download(item, root, opener=urllib.request.urlopen):
    path = safe_path(root, item["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if valid(path, item):
        return path
    part = safe_path(root, item["path"] + ".partial")
    if valid(part, item):
        part.replace(path)
        return path
    if not item["url"].startswith("https://"):
        raise ValueError("Asset URL must use HTTPS")
    # Resume only immutable artifacts and always verify the complete final digest.
    for attempt in range(3):
        offset = part.stat().st_size if part.exists() else 0
        if offset >= item["bytes"]:
            part.unlink()
            offset = 0
        request = urllib.request.Request(
            item["url"],
            headers={
                "User-Agent": "LectureLive-Setup/1",
                **({"Range": f"bytes={offset}-"} if offset else {}),
            },
        )
        try:
            with opener(request, timeout=45) as response:
                partial = response.status == 206
                if partial and not response.headers.get("Content-Range", "").startswith(
                    f"bytes {offset}-"
                ):
                    raise ValueError("Unexpected resume range")
                with part.open("ab" if partial and offset else "wb") as output:
                    while chunk := response.read(1024 * 1024):
                        if output.tell() + len(chunk) > item["bytes"]:
                            raise ValueError("Asset exceeded its pinned byte count")
                        output.write(chunk)
            if valid(part, item):
                part.replace(path)
                return path
            part.unlink()
            raise ValueError("Downloaded asset checksum mismatch: " + item["path"])
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(min(2**attempt, 4))
    raise RuntimeError("Download failed")


def archive_ready(root, item):
    if not item.get("members"):
        return False
    folder = safe_path(root, item["extract_to"])
    return all(
        valid(safe_path(folder, member["path"]), member) for member in item["members"]
    )


def extract_verified(archive, root, item):
    folder = safe_path(root, item["extract_to"])
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for member in item["members"]:
            target = safe_path(folder, member["path"])
            if valid(target, member):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            part = target.with_name(target.name + ".partial")
            with source.open(member["path"]) as incoming, part.open("wb") as outgoing:
                while chunk := incoming.read(1024 * 1024):
                    outgoing.write(chunk)
            if not valid(part, member):
                part.unlink()
                raise ValueError("Extracted model failed checksum")
            part.replace(target)


def install(manifest, root, verify=False, offline=False):
    manifest = json.loads(Path(manifest).read_text(encoding="utf-8"))
    if manifest.get("version") != 1:
        raise ValueError("Unsupported manifest version")
    bad = []
    checked = 0
    for item in manifest["assets"]:
        path = safe_path(root, item["path"])
        if item.get("members") and archive_ready(root, item):
            checked += len(item["members"])
            continue
        if verify:
            if item.get("members") or not valid(path, item):
                bad.append(item["path"])
            else:
                checked += 1
            continue
        if not valid(path, item):
            if offline:
                raise FileNotFoundError(
                    "Offline asset missing or damaged: " + item["path"]
                )
            print("Fetching", item["path"], flush=True)
            download(item, root)
        if item.get("members"):
            extract_verified(path, root, item)
        checked += len(item.get("members", [])) or 1
    return {"checked_files": checked, "missing_or_damaged": bad, "passed": not bad}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--dependencies", action="store_true")
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    root = args.root or Path(__file__).resolve().parents[1]
    result = install(
        root
        / (
            "dependencies.lock.json"
            if args.dependencies
            else "fixtures.lock.json"
            if args.fixtures
            else "assets.lock.json"
        ),
        root,
        args.verify,
        args.offline,
    )
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
