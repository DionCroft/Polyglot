"""Core ML in a bounded child process, using inherited pipes (no sockets)."""

import hashlib
import json
import os
from pathlib import Path
import select
import struct
import subprocess
import sys
import time
import numpy as np

PROVIDER = "CoreMLExecutionProvider"
ENCODERS = {
    "fast": "a9f3b752833b49e880dec91ee5b6d936112be7c3ea07c221024ba493439f46fe",
    "balanced": "b37cd6625dc36f9178ec7539a1876b9680ea26a910097e092be39dc766320c7b",
}
MAX_FRAME = 1500 * 768 * 4


def transfer(fd, size, deadline, data=None):
    """Both directions have deadlines; a wedged native provider cannot block UI shutdown."""
    output = bytearray()
    offset = 0
    while offset < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Core ML worker timed out; switching to CPU")
        readable, writable, _ = select.select(
            [fd] if data is None else [],
            [fd] if data is not None else [],
            [],
            remaining,
        )
        if not readable and not writable:
            raise TimeoutError("Core ML worker timed out; switching to CPU")
        if data is None:
            chunk = os.read(fd, min(size - offset, 65536))
            if not chunk:
                raise EOFError("Core ML worker stopped")
            output.extend(chunk)
            offset += len(chunk)
        else:
            offset += os.write(fd, data[offset : offset + 4096])
    return bytes(output)


def send(fd, data, deadline):
    if len(data) > MAX_FRAME:
        raise ValueError("Oversized Core ML message")
    packet = struct.pack("!I", len(data)) + data
    transfer(fd, len(packet), deadline, packet)


def receive(fd, deadline, limit=MAX_FRAME):
    size = struct.unpack("!I", transfer(fd, 4, deadline))[0]
    if size > limit:
        raise ValueError("Oversized Core ML response")
    return transfer(fd, size, deadline)


def verify_trace(events):
    providers = sorted(
        {
            event.get("args", {}).get("provider")
            for event in events
            if event.get("cat") == "Node" and event.get("args", {}).get("provider")
        }
    )
    if PROVIDER not in providers:
        raise RuntimeError("Core ML did not execute any encoder nodes")
    return providers


class MacEncoder:
    def __init__(self, folder):
        if sys.platform != "darwin":
            raise RuntimeError("Core ML requires native macOS")
        self.process = None
        self.read_fd = self.write_fd = None
        self.width = json.loads((folder / "config.json").read_text())["d_model"]
        read_fd, child_write = os.pipe()
        child_read, write_fd = os.pipe()
        self.read_fd, self.write_fd = read_fd, write_fd
        command = [sys.executable]
        if not getattr(sys, "frozen", False):
            command += ["-m", "app.main"]
        command += [
            "--mac-encoder-worker",
            str(folder),
            str(child_read),
            str(child_write),
        ]
        env = dict(os.environ)
        # A frozen worker is a separate app instance, not a multiprocessing fork.
        if getattr(sys, "frozen", False):
            env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
        try:
            self.process = subprocess.Popen(
                command,
                pass_fds=(child_read, child_write),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except BaseException:
            self.close()
            raise
        finally:
            os.close(child_read)
            os.close(child_write)
        try:
            self.details = json.loads(receive(read_fd, time.monotonic() + 180, 32768))
            if not self.details.get("ready"):
                raise RuntimeError(self.details.get("error", "Core ML unavailable"))
        except BaseException:
            self.close()
            raise

    def run(self, outputs, feed):
        features = np.asarray(feed["input_features"], dtype="<f4")
        if features.shape != (1, 80, 3000) or not np.isfinite(features).all():
            raise ValueError("Invalid encoder input")
        try:
            deadline = time.monotonic() + 30
            send(self.write_fd, features.tobytes(), deadline)
            data = receive(self.read_fd, deadline)
            if len(data) != 1500 * self.width * 4:
                raise ValueError("Invalid Core ML output size")
            result = np.frombuffer(data, dtype="<f4").reshape(1, 1500, self.width)
            if not np.isfinite(result).all():
                raise ValueError("Non-finite Core ML output")
            return [result]
        except BaseException:
            self.close()
            raise

    def close(self):
        for key in ("write_fd", "read_fd"):
            fd = getattr(self, key, None)
            if fd is not None:
                os.close(fd)
                setattr(self, key, None)
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
            self.process = None


def create_encoder(folder):
    import platform
    import tempfile
    import onnxruntime as ort
    from app.config.settings import DATA

    ort.disable_telemetry_events()
    path = folder / "accelerated/encoder_model.onnx"
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != ENCODERS.get(folder.name):
        raise ValueError("Core ML model is damaged; reinstall LectureLive")
    if PROVIDER not in ort.get_available_providers():
        raise RuntimeError("This runtime does not provide Core ML")
    cache_key = hashlib.sha256(
        (digest + ort.__version__ + platform.mac_ver()[0]).encode()
    ).hexdigest()
    cache = DATA / "cache/coreml" / cache_key
    cache.mkdir(parents=True, exist_ok=True)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    for name, size in (
        ("batch_size", 1),
        ("feature_size", 80),
        ("encoder_sequence_length", 3000),
    ):
        options.add_free_dimension_override_by_name(name, size)
    options.enable_profiling = True
    with tempfile.TemporaryDirectory(prefix="verify-", dir=cache) as traces:
        options.profile_file_prefix = str(Path(traces) / "encoder")
        session = ort.InferenceSession(
            str(path),
            options,
            providers=[
                (
                    PROVIDER,
                    {
                        "ModelFormat": "MLProgram",
                        "MLComputeUnits": "ALL",
                        "RequireStaticInputShapes": "1",
                        "EnableOnSubgraphs": "0",
                        "ModelCacheDirectory": str(cache),
                    },
                ),
                "CPUExecutionProvider",
            ],
        )
        session.run(None, {"input_features": np.zeros((1, 80, 3000), np.float32)})
        trace = Path(session.end_profiling())
        providers = verify_trace(json.loads(trace.read_text()))
    return session, {
        "ready": True,
        "providers": providers,
        "runtime": ort.__version__,
        "compute_units": "ALL",
        "device": "Selected by macOS; GPU/ANE not individually verified",
    }


def run_worker(folder, read_fd, write_fd):
    read_fd, write_fd = int(read_fd), int(write_fd)
    try:
        try:
            encoder, details = create_encoder(Path(folder))
        except Exception as exc:
            send(
                write_fd,
                json.dumps({"ready": False, "error": str(exc)[:2000]}).encode(),
                time.monotonic() + 5,
            )
            return 1
        send(write_fd, json.dumps(details).encode(), time.monotonic() + 5)
        while True:
            # Idle workers wait for the owning process; EOF ends the child immediately.
            data = receive(read_fd, time.monotonic() + 86400, 80 * 3000 * 4)
            if len(data) != 80 * 3000 * 4:
                raise ValueError("Invalid feature frame")
            features = np.frombuffer(data, dtype="<f4").reshape(1, 80, 3000)
            output = np.asarray(
                encoder.run(None, {"input_features": features})[0], dtype="<f4"
            )
            send(write_fd, output.tobytes(), time.monotonic() + 30)
    except (EOFError, BrokenPipeError):
        return 0
    finally:
        os.close(read_fd)
        os.close(write_fd)
