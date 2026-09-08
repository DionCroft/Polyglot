from typing import Protocol
import numpy as np


class SpeechBackend(Protocol):
    name: str

    def transcribe(self, audio: np.ndarray) -> str: ...
