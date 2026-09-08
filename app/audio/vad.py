from collections import deque
from dataclasses import dataclass
import numpy as np
from app.system.inference import session


@dataclass
class AudioPhrase:
    identifier: int
    start: float
    end: float
    audio: np.ndarray
    final: bool


class SileroVAD:
    def __init__(self, path):
        self.model = session(path)
        self.reset()

    def reset(self):
        self.state = np.zeros((2, 1, 128), np.float32)
        self.context = np.zeros((1, 64), np.float32)

    def probability(self, frame):
        block = np.concatenate((self.context, frame.reshape(1, 512)), axis=1)
        prob, self.state = self.model.run(
            None,
            {
                "input": block,
                "state": self.state,
                "sr": np.array(16000, dtype=np.int64),
            },
        )
        self.context = block[:, -64:].copy()
        return float(prob[0, 0])


class Segmenter:
    """32 ms VAD windows, 256 ms pre-roll, 576 ms pause, 9.6 s cap."""

    def __init__(self, vad):
        self.vad = vad
        self.identifier = 0
        self.reset()

    def reset(self):
        self.vad.reset()
        self.pre = deque(maxlen=8)
        self.frames = []
        self.quiet = 0
        self.start = 0
        self.voiced = 0
        self.last_partial = 0

    def push(self, frame, end):
        speech = self.vad.probability(frame) >= 0.5
        if not self.frames:
            if not speech:
                self.pre.append(frame)
                return None
            self.identifier += 1
            self.frames = list(self.pre)
            self.pre.clear()
            self.start = max(0, end - (len(self.frames) + 1) * 0.032)
            self.voiced = 0
            self.last_partial = 0
        self.frames.append(frame)
        self.quiet = 0 if speech else self.quiet + 1
        self.voiced += int(speech)
        final = self.quiet >= 18 or len(self.frames) >= 300
        if final:
            result = self._phrase(end, True) if self.voiced >= 5 else None
            self.frames = []
            self.quiet = 0
            return result
        if len(self.frames) >= 38 and len(self.frames) - self.last_partial >= 38:
            self.last_partial = len(self.frames)
            return self._phrase(end, False)
        return None

    def _phrase(self, end, final):
        return AudioPhrase(
            self.identifier, self.start, end, np.concatenate(self.frames), final
        )

    def finish(self, end):
        result = self._phrase(end, True) if self.frames and self.voiced >= 5 else None
        self.frames = []
        return result
