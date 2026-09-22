"""Offline Whisper language scores and a conservative, phrase-local decision policy.

Scores are model probabilities, not calibrated estimates of classroom accuracy.
Never renormalise over English/Chinese alone: an unsupported language must be able
to win. Detection runs without vocabulary prompts or decoder history.
"""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class UncertainTurn:
    identifier: int
    start: float
    end: float
    epoch: int = 0
    reason: str = "Language unclear; select English or Mandarin and repeat."


def language_scores(logits, language_ids):
    values = np.asarray(logits, dtype=np.float64).reshape(-1)
    codes = [code[2:-2] for code in language_ids]
    values = values[list(language_ids.values())]
    if not np.isfinite(values).all():
        raise RuntimeError("Invalid language-detection scores")
    weights = np.exp(values - values.max())
    weights /= weights.sum()
    return dict(zip(codes, map(float, weights)))


def choose_language(scores, voiced_seconds, final=False):
    """Abstain on weak/unsupported evidence. Final phrases can use more context."""
    if voiced_seconds < (0.32 if final else 1.2) or not scores:
        return None
    ranked = sorted(scores.items(), key=lambda item: -item[1])
    language, score = ranked[0]
    other = scores.get("zh" if language == "en" else "en", 0.0)
    if language not in {"en", "zh"} or not np.isfinite(score):
        return None
    minimum = 0.65 if final and voiced_seconds >= 1.2 else 0.95
    ratio = score / max(1e-12, score + other)
    if score < minimum or ratio < (0.98 if final else 0.995):
        return None
    return language


class PhraseLanguage:
    """Two strong growing hypotheses before partial captions; recheck at final.

    An uncertain final is withheld. A final disagreeing with a locked partial is
    withheld as well: this may be mixed speech or an earlier detection error.
    """

    def __init__(self):
        self.key = None
        self.candidate = None
        self.locked = None
        self.last_samples = 0

    def decide(self, key, scores, voiced_seconds, samples, final):
        if key != self.key:
            self.__init__()
            self.key = key
        selected = choose_language(scores, voiced_seconds, final)
        if final:
            return selected if not self.locked or selected == self.locked else None
        if self.locked:
            return self.locked
        if selected and selected == self.candidate and samples > self.last_samples:
            self.locked = selected
        self.candidate = selected
        self.last_samples = samples
        return self.locked
