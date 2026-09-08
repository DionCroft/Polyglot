import hashlib, io, json, zipfile
import pytest
from scripts.setup_assets import download, safe_path, install


def item(data, path="models/test.bin"):
    return {
        "path": path,
        "url": "https://example.invalid/pinned/test.bin",
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}


def test_download_resumes_verified_partial(tmp_path):
    data = b"verified model contents"
    record = item(data)
    path = tmp_path / record["path"]
    path.parent.mkdir(parents=True)
    path.with_name(path.name + ".partial").write_bytes(data[:9])

    def open_request(request, timeout):
        assert request.get_header("Range") == "bytes=9-"
        return Response(
            data[9:], 206, {"Content-Range": f"bytes 9-{len(data) - 1}/{len(data)}"}
        )

    assert download(record, tmp_path, open_request).read_bytes() == data


def test_server_ignoring_range_restarts_without_duplicate_bytes(tmp_path):
    data = b"complete data"
    record = item(data)
    p = tmp_path / record["path"]
    p.parent.mkdir(parents=True)
    p.with_name(p.name + ".partial").write_bytes(b"old")
    assert (
        download(record, tmp_path, lambda *a, **k: Response(data)).read_bytes() == data
    )


def test_bad_download_never_replaces_existing_asset(tmp_path, monkeypatch):
    from scripts import setup_assets

    monkeypatch.setattr(setup_assets.time, "sleep", lambda seconds: None)
    record = item(b"correct")
    p = tmp_path / record["path"]
    p.parent.mkdir(parents=True)
    p.write_bytes(b"previous")
    with pytest.raises(ValueError):
        download(record, tmp_path, lambda *a, **k: Response(b"corrupt"))
    assert p.read_bytes() == b"previous"


@pytest.mark.parametrize(
    "path", ["../outside", "/absolute", "C:/escape", "models/../../escape"]
)
def test_asset_path_cannot_escape_root(tmp_path, path):
    with pytest.raises(ValueError):
        safe_path(tmp_path, path)


def test_offline_repair_restores_corrupt_extracted_model(tmp_path):
    data = b"model payload"
    archive = tmp_path / "model.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("encoder.onnx", data)
    record = item(archive.read_bytes(), "model.zip")
    record["extract_to"] = "models/qnn"
    record["members"] = [item(data, "encoder.onnx")]
    manifest = tmp_path / "assets.lock.json"
    manifest.write_text(json.dumps({"version": 1, "assets": [record]}))
    p = tmp_path / "models/qnn/encoder.onnx"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"corrupt")
    assert not install(manifest, tmp_path, verify=True)["passed"]
    assert (
        install(manifest, tmp_path, offline=True)["passed"] and p.read_bytes() == data
    )
    archive.unlink()
    assert install(manifest, tmp_path, verify=True)["passed"]


def test_fully_downloaded_partial_is_installed_without_network(tmp_path):
    data = b"complete pinned file"
    record = item(data)
    p = tmp_path / record["path"]
    p.parent.mkdir(parents=True)
    p.with_name(p.name + ".partial").write_bytes(data)

    def offline(*args, **kwargs):
        raise AssertionError("Network must not be used")

    assert download(record, tmp_path, offline).read_bytes() == data
