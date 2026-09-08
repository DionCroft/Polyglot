import json
import numpy as np


class WhisperFeatures:
    def __init__(self, config_path):
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        self.filters = np.asarray(cfg["mel_filters"], dtype=np.float32)
        self.window = np.hanning(401)[:-1].astype(np.float32)

    def __call__(self, audio):
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)[:480000]
        audio = np.pad(audio, (0, 480000 - len(audio)))
        audio = np.pad(audio, (200, 200), mode="reflect")
        frames = np.lib.stride_tricks.sliding_window_view(audio, 400)[::160]
        power = np.abs(np.fft.rfft(frames * self.window, axis=-1)) ** 2
        mel = self.filters @ power[:-1].T
        log = np.log10(np.maximum(mel, 1e-10))
        log = np.maximum(log, log.max() - 8.0)
        return ((log + 4.0) / 4.0)[None].astype(np.float32)
