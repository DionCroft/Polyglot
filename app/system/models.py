"""One warmed model bundle per control panel; no inference on the UI thread."""

from dataclasses import dataclass
import logging
import threading
import numpy as np
from app.system.architecture import is_x64


@dataclass
class ModelBundle:
    asr: object
    mt: object
    vad: object
    npu: bool
    messages: list
    accelerated: bool = False


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
            if self.bundle is not None:
                close = getattr(self.bundle.asr, "close", None)
                if close:
                    close()
            self.bundle = None

    close = invalidate

    def load(self, profile, force_cpu=False, accelerator="auto"):
        with self.lock:
            if is_x64():
                profile = "fast"
            key = (profile, force_cpu, accelerator)
            if key == self.key and self.bundle is not None:
                return self.bundle
            if profile not in {"fast", "balanced"}:
                raise ValueError("Choose an installed Fast or Balanced speech model.")
            self.invalidate()
            from app.asr.qnn_whisper import QnnWhisper
            from app.asr.cpu_whisper import CpuWhisper
            from app.translation.opus_mt import OpusMT
            from app.audio.vad import SileroVAD

            messages = []
            npu = False
            accelerated = False
            asr = None
            worker = None
            try:
                if force_cpu:
                    raise RuntimeError("Local CPU selected")
                if is_x64():
                    from app.asr.encoder_worker import EncoderWorker
                    from app.system.accelerators import candidates, LABELS

                    for selection in candidates(accelerator):
                        try:
                            worker = EncoderWorker(self.root, selection)
                            asr = CpuWhisper(
                                self.root / "models/whisper/fast", encoder=worker
                            )
                            asr.transcribe(np.zeros(16000, np.float32))
                            asr.name = (
                                LABELS[selection]
                                + " speech encoder + CPU decoder · Beta"
                            )
                            npu = selection.endswith("_npu")
                            accelerated = True
                            break
                        except Exception as exc:
                            if worker is not None:
                                worker.close()
                                worker = None
                            asr = None
                            logging.exception(
                                "Beta accelerator check failed: %s", selection
                            )
                            messages.append(
                                LABELS[selection] + " unavailable: " + str(exc)
                            )
                    if asr is None:
                        raise RuntimeError("Using local CPU")
                else:
                    asr = QnnWhisper(self.root / "models/whisper" / profile)
                    asr.name = "Qualcomm NPU · Whisper " + (
                        "Small FP16" if profile == "balanced" else "Base FP16"
                    )
                # Verify both encoder and decoder, not merely encoder loading.
                if not is_x64():
                    asr.transcribe(np.zeros(16000, np.float32))
                    npu = True
                    accelerated = True
            except Exception:
                if not force_cpu and not is_x64():
                    logging.exception("NPU check failed; using CPU")
                if worker is not None:
                    worker.close()
                npu = accelerated = False
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
            try:
                vad = SileroVAD(self.root / "models/vad/silero_vad.onnx")
                vad.probability(np.zeros(512, np.float32))
                vad.reset()
            except BaseException:
                close = getattr(asr, "close", None)
                if close:
                    close()
                raise
            self.bundle = ModelBundle(asr, mt, vad, npu, messages, accelerated)
            self.key = key
            self.loads += 1
            return self.bundle
