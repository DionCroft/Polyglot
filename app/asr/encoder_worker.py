"""Bound accelerator driver work in a persistent, private Windows named pipe worker.

No sockets, audio files, model downloads, or vendor messages on the protocol channel.
"""

import json
import os
import subprocess
import sys
import threading
import uuid
from multiprocessing.connection import Listener, Client
from pathlib import Path
import numpy as np


class EncoderWorker:
    def __init__(self, root, selection, startup_timeout=180, inference_timeout=30):
        self.process = None
        self.connection = None
        self.listener = None
        self.lock = threading.RLock()
        self.inference_timeout = inference_timeout
        self.selection = selection
        address = r"\\.\pipe\LectureLive-" + uuid.uuid4().hex
        # Authentication is exchanged through a private inherited environment, not the command line.
        secret = os.urandom(32)
        env = dict(os.environ, LECTURELIVE_PIPE_KEY=secret.hex(), PYTHONNOUSERSITE="1")
        command = [sys.executable]
        if not getattr(sys, "frozen", False):
            command += ["-m", "app.main"]
        command += ["--encoder-worker", address, str(root), selection]
        self.listener = Listener(address, family="AF_PIPE", authkey=secret)
        accepted = threading.Event()
        errors = []

        def accept():
            try:
                self.connection = self.listener.accept()
            except Exception as exc:
                errors.append(exc)
            finally:
                accepted.set()

        threading.Thread(target=accept, daemon=True).start()
        try:
            self.process = subprocess.Popen(
                command,
                env=env,
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if not accepted.wait(15) or errors:
                raise RuntimeError("Accelerator worker could not start")
            if not self.connection.poll(startup_timeout):
                raise TimeoutError(
                    "Accelerator preparation timed out; CPU captions remain available"
                )
            status = json.loads(self.connection.recv_bytes(16384))
            if not status.get("ready"):
                raise RuntimeError(status.get("error", "Accelerator check failed"))
            self.provider = status["provider"]
        except BaseException:
            self.close()
            raise

    def run(self, outputs, feed):
        features = np.asarray(feed["input_features"], dtype=np.float32)
        if features.shape != (1, 80, 3000) or not np.isfinite(features).all():
            raise ValueError("Invalid speech encoder input")
        with self.lock:
            try:
                self.connection.send_bytes(features.tobytes())
                if not self.connection.poll(self.inference_timeout):
                    raise TimeoutError("Accelerator did not finish this phrase")
                payload = self.connection.recv_bytes(1 * 1500 * 512 * 4)
                if len(payload) != 1 * 1500 * 512 * 4:
                    raise RuntimeError("Accelerator returned an invalid result")
                hidden = (
                    np.frombuffer(payload, dtype=np.float32)
                    .reshape(1, 1500, 512)
                    .copy()
                )
                if not np.isfinite(hidden).all():
                    raise RuntimeError("Accelerator returned non-finite values")
                return [hidden]
            except BaseException:
                self.close()
                raise

    def close(self):
        with self.lock:
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
                self.process = None
            if self.connection is not None:
                self.connection.close()
                self.connection = None
            if self.listener is not None:
                self.listener.close()
                self.listener = None


def run_worker(address, root, selection):
    from app.system.accelerators import create_encoder, verify_trace, PROVIDERS
    from app.config.settings import DATA

    connection = Client(
        address,
        family="AF_PIPE",
        authkey=bytes.fromhex(os.environ.pop("LECTURELIVE_PIPE_KEY")),
    )
    session = runtime = None
    try:
        trace_dir = DATA / "logs" / ("accelerator-" + uuid.uuid4().hex)
        trace_dir.mkdir(parents=True, exist_ok=True)
        session, runtime = create_encoder(
            Path(root) / "models/whisper/fast/accelerated/encoder_model.onnx",
            selection,
            trace_dir,
        )
        warm = session.run(
            None, {"input_features": np.zeros((1, 80, 3000), np.float32)}
        )[0]
        if warm.shape != (1, 1500, 512) or not np.isfinite(warm).all():
            raise RuntimeError("Encoder warm-up output is invalid")
        trace = Path(session.end_profiling())
        verify_trace(
            json.loads(trace.read_text(encoding="utf-8")), PROVIDERS[selection]
        )
        # Profiling covers synthetic silence only and is removed after verification.
        trace.unlink()
        trace_dir.rmdir()
        connection.send_bytes(
            json.dumps({"ready": True, "provider": PROVIDERS[selection]}).encode()
        )
        while True:
            payload = connection.recv_bytes(80 * 3000 * 4)
            features = np.frombuffer(payload, dtype=np.float32).reshape(1, 80, 3000)
            hidden = session.run(None, {"input_features": features})[0]
            connection.send_bytes(np.asarray(hidden, dtype=np.float32).tobytes())
    except (EOFError, BrokenPipeError):
        pass
    except Exception as exc:
        try:
            connection.send_bytes(
                json.dumps({"ready": False, "error": str(exc)[:8000]}).encode()
            )
        except (OSError, EOFError):
            pass
    finally:
        connection.close()
        del session
        if runtime is not None:
            runtime()
    return 0
