"""Short microphone level check; samples remain in memory only."""

import threading
import numpy as np
from app.audio.capture import Microphone


def check_microphone(device, emit, cancel=None, seconds=3):
    cancel = cancel or threading.Event()
    count = 0
    energy = 0.0
    peak = 0.0
    clipped = 0
    callbacks = 0

    def frame(data, end):
        nonlocal count, energy, peak, clipped, callbacks
        count += data.size
        energy += float(np.square(data, dtype=np.float64).sum())
        peak = max(peak, float(np.abs(data).max()))
        clipped += int((np.abs(data) >= 0.99).sum())
        callbacks += 1
        emit(
            "microphone-level",
            min(100, int(float(np.sqrt(np.mean(data * data))) * 450)),
        )

    source = Microphone(
        device, frame, lambda message, fatal=False: emit("warning", message)
    )
    try:
        source.start()
        cancel.wait(seconds)
    finally:
        source.close()
    rms = (energy / max(1, count)) ** 0.5
    result = {
        "samples": count,
        "callbacks": callbacks,
        "rms": rms,
        "peak": peak,
        "clipped_fraction": clipped / max(1, count),
        "cancelled": cancel.is_set(),
    }
    result["message"] = (
        "Microphone check cancelled."
        if cancel.is_set()
        else "No audio arrived. Check the selected microphone."
        if count == 0
        else "Audio is clipping. Reduce microphone gain or move farther away."
        if result["clipped_fraction"] > 0.001
        else "Input is very quiet. Speak and check the microphone position."
        if rms < 0.003
        else "Microphone signal received. Input level looks usable."
    )
    return result
