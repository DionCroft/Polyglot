"""One warmed model bundle per control panel; no inference on the UI thread."""

from dataclasses import dataclass
import logging
import threading
import numpy as np


@dataclass
class ModelBundle:
    asr: object
    mt: object
    vad: object
    npu: bool
    messages: list


class ModelStore:
    def __init__(self, root):
        self.root = root
        self.lock = threading.RLock()
        self.key = None
        self.bundle = None
        self.loads = 0

    def invalidate(self):
        with self.lock:
            self.key = None
            self.bundle = None

    def load(self, profile, force_cpu=False):
        with self.lock:
            key = (profile, force_cpu)
            if key == self.key and self.bundle is not None:
                return self.bundle
            if profile not in {"fast", "balanced"}:
                raise ValueError("Choose an installed Fast or Balanced speech model.")
            self.bundle = None
            self.key = None
            from app.asr.qnn_whisper import QnnWhisper
            from app.asr.cpu_whisper import CpuWhisper
            from app.translation.opus_mt import OpusMT
            from app.audio.vad import SileroVAD

            messages = []
            npu = False
            try:
                if force_cpu:
                    raise RuntimeError("Local CPU selected")
                asr = QnnWhisper(self.root / "models/whisper" / profile)
                asr.name = "Qualcomm NPU · Whisper " + (
                    "Small FP16" if profile == "balanced" else "Base FP16"
                )
                # Verify both encoder and decoder, not merely encoder loading.
                asr.transcribe(np.zeros(16000, np.float32))
                npu = True
            except Exception:
                if not force_cpu:
                    logging.exception("NPU check failed; using CPU")
                asr = CpuWhisper(self.root / "models/whisper/fast")
                asr.transcribe(np.zeros(16000, np.float32))
                messages.append(
                    "Using local CPU Whisper Base; no internet is required."
                )
            try:
                mt = OpusMT(self.root / "models/translation/opus")
                if not mt.translate("Welcome to the lecture."):
                    raise RuntimeError("Empty translation")
            except Exception:
                logging.exception("Local translation check failed")
                mt = None
                messages.append(
                    "Translation unavailable. English captions can continue; repair local translation assets."
                )
            vad = SileroVAD(self.root / "models/vad/silero_vad.onnx")
            vad.probability(np.zeros(512, np.float32))
            vad.reset()
            self.bundle = ModelBundle(asr, mt, vad, npu, messages)
            self.key = key
            self.loads += 1
            return self.bundle
