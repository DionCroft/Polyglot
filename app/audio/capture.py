import threading, time, wave
from pathlib import Path
import numpy as np
import sounddevice as sd
from app.system.architecture import is_macos

RATE = 16000
BLOCK = 512


def microphones():
    devices = sd.query_devices()
    hosts = sd.query_hostapis()
    items = []
    for index, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            host = hosts[d["hostapi"]]["name"]
            if host not in (
                {"Core Audio"} if is_macos() else {"Windows WASAPI", "MME"}
            ):
                continue
            if "Mapper" in d["name"]:
                continue
            items.append((index, d["name"], host))
    return sorted(items, key=lambda i: i[2] != "Windows WASAPI")


class Microphone:
    def __init__(self, device, on_frame, on_error):
        self.device = device
        self.on_frame = on_frame
        self.on_error = on_error
        self.stream = None
        self.origin = 0
        self.frames = 0
        self.last_callback = 0

    def start(self):
        self.frames = 0
        self.origin = time.monotonic()
        self.last_callback = self.origin

        def callback(data, frames, timing, status):
            self.last_callback = time.monotonic()
            if status:
                self.on_error("Audio input overflow; some audio was lost.", False)
            self.frames += frames
            self.on_frame(data[:, 0].copy(), self.frames / RATE)

        try:
            info = sd.query_devices(self.device, "input")
            host = sd.query_hostapis(info["hostapi"])["name"]
            extra = (
                sd.WasapiSettings(auto_convert=True)
                if host == "Windows WASAPI"
                else sd.CoreAudioSettings(
                    change_device_parameters=False, fail_if_conversion_required=False
                )
                if host == "Core Audio"
                else None
            )
            self.stream = sd.InputStream(
                device=self.device,
                samplerate=RATE,
                channels=1,
                dtype="float32",
                blocksize=BLOCK,
                callback=callback,
                extra_settings=extra,
            )
            self.stream.start()
        except Exception as e:
            self.close()
            raise RuntimeError(
                (
                    "Microphone unavailable. Check System Settings → Privacy & Security → Microphone and select another input device."
                    if is_macos()
                    else "Microphone unavailable. Select another input device and try again."
                )
            ) from e

    def close(self):
        if self.stream is not None:
            self.stream.abort()
            self.stream.close()
            self.stream = None


class WavSource:
    """Replay PCM WAV locally with the same cadence as microphone input."""

    def __init__(self, path, on_frame, on_error, on_end):
        self.path = Path(path)
        self.on_frame = on_frame
        self.on_error = on_error
        self.on_end = on_end
        self.stop = threading.Event()
        self.thread = None

    def start(self):
        self.file = wave.open(str(self.path), "rb")
        if self.file.getsampwidth() != 2 or self.file.getframerate() != RATE:
            self.file.close()
            raise ValueError("Test WAV must be 16-bit PCM at 16 kHz (mono or stereo).")
        self.thread = threading.Thread(
            target=self._run, name="WAV replay", daemon=False
        )
        self.thread.start()

    def _run(self):
        count = 0
        origin = time.monotonic()
        try:
            channels = self.file.getnchannels()
            while not self.stop.is_set():
                data = self.file.readframes(BLOCK)
                if not data:
                    break
                frame = (
                    np.frombuffer(data, dtype="<i2")
                    .reshape(-1, channels)
                    .mean(axis=1)
                    .astype(np.float32)
                    / 32768
                )
                frame = np.pad(frame, (0, BLOCK - len(frame)))
                count += BLOCK
                self.on_frame(frame, count / RATE)
                self.stop.wait(max(0, origin + count / RATE - time.monotonic()))
            if not self.stop.is_set():
                for _ in range(20):
                    count += BLOCK
                    self.on_frame(np.zeros(BLOCK, np.float32), count / RATE)
                    self.stop.wait(0.032)
                self.on_end()
        except Exception:
            self.on_error("Could not read the local WAV file.", True)
        finally:
            self.file.close()

    def close(self):
        self.stop.set()
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=2)
