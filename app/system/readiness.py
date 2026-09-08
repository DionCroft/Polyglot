"""Actual local startup inference checks, always run away from the UI thread."""

import logging
import numpy as np
from app.system.inference import session
from app.audio.vad import SileroVAD
from app.translation.opus_mt import OpusMT

log = logging.getLogger(__name__)


def check(root, profile):
    result = {
        "speech": False,
        "translation": False,
        "vad": False,
        "npu": False,
        "messages": [],
    }
    try:
        path = next((root / "models/whisper" / profile / "qnn").rglob("encoder.onnx"))
        model = session(path, True)
        model.run(
            None, {model.get_inputs()[0].name: np.zeros((1, 80, 3000), np.float16)}
        )
        result["speech"] = True
        result["npu"] = True
    except Exception:
        log.exception("Startup NPU check failed; checking CPU model")
        try:
            model = session(
                root / "models/whisper/fast/cpu/encoder_model_quantized.onnx"
            )
            model.run(None, {"input_features": np.zeros((1, 80, 3000), np.float32)})
            result["speech"] = True
            result["messages"].append(
                "NPU unavailable; local CPU speech recovery is ready."
            )
        except Exception:
            result["messages"].append(
                "Speech model check failed. See local logs and installation guide."
            )
    try:
        vad = SileroVAD(root / "models/vad/silero_vad.onnx")
        vad.probability(np.zeros(512, np.float32))
        result["vad"] = True
    except Exception:
        log.exception("Startup VAD check failed")
        result["messages"].append("Voice detection model is missing or could not run.")
    try:
        translator = OpusMT(root / "models/translation/opus")
        text = translator.translate("Welcome to the lecture.")
        if not text:
            raise RuntimeError("Empty test translation")
        result["translation"] = True
    except Exception:
        log.exception("Startup translation check failed")
        result["messages"].append(
            "Translation model check failed. English can continue."
        )
    return result
