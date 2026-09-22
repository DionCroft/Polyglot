"""Bounded English vocabulary prompting and deterministic local beam search.

Uses the existing Whisper tokenizer/model assets, with no runtime dependencies/downloads.
The Standard path remains in the original backend methods for compatibility.
"""

import json
import unicodedata
import numpy as np


def pieces(text):
    """Whisper/GPT-2 ByteLevel pre-tokenization using Unicode categories, without regex wheels."""

    def kind(char):
        if char.isspace():
            return "space"
        category = unicodedata.category(char)[0]
        return category if category in {"L", "N"} else "punct"

    i = 0
    while i < len(text):
        contraction = next(
            (
                x
                for x in ("'s", "'t", "'re", "'ve", "'m", "'ll", "'d")
                if text.startswith(x, i)
            ),
            None,
        )
        if contraction:
            yield contraction
            i += len(contraction)
            continue
        start = i
        if text[i] == " " and i + 1 < len(text) and not text[i + 1].isspace():
            i += 1
        category = kind(text[i])
        i += 1
        while i < len(text) and kind(text[i]) == category:
            i += 1
        if category == "space" and i < len(text) and i - start > 1:
            # The greedy whitespace alternative leaves the final space for the next token.
            i -= 1
        yield text[start:i]


class WhisperTokenizer:
    def __init__(self, path):
        data = json.loads(path.read_text(encoding="utf-8"))["model"]
        self.vocab = data["vocab"]
        self.ranks = {
            tuple(x.split(" ")) if isinstance(x, str) else tuple(x): n
            for n, x in enumerate(data["merges"])
        }
        values = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
        chars = values[:]
        for value in range(256):
            if value not in values:
                values.append(value)
                chars.append(256 + sum(x >= 256 for x in chars))
        self.byte_encoder = dict(zip(values, map(chr, chars)))

    def _encode_piece(self, piece):
        parts = [self.byte_encoder[x] for x in piece.encode("utf-8")]
        while len(parts) > 1:
            pair = min(
                zip(parts, parts[1:]), key=lambda x: self.ranks.get(x, float("inf"))
            )
            if pair not in self.ranks:
                break
            merged = []
            i = 0
            while i < len(parts):
                if i + 1 < len(parts) and (parts[i], parts[i + 1]) == pair:
                    merged.append(parts[i] + parts[i + 1])
                    i += 2
                else:
                    merged.append(parts[i])
                    i += 1
            parts = merged
        return tuple(self.vocab[x] for x in parts)

    def encode(self, text):
        return [token for piece in pieces(text) for token in self._encode_piece(piece)]

    def vocabulary_tokens(self, vocabulary, limit=32):
        terms = []
        seen = set()
        tokens = []
        for raw in vocabulary.splitlines()[:100]:
            term = " ".join(unicodedata.normalize("NFC", raw).split())[:100]
            if not term or term.casefold() in seen:
                continue
            seen.add(term.casefold())
            proposed = self.encode(" " + ", ".join(terms + [term]))
            if len(proposed) > limit:
                break
            terms.append(term)
            tokens = proposed
        return tokens


class RecognitionOptions:
    def __init__(self, folder):
        self.folder = folder
        self.generation = json.loads(
            (folder / "generation_config.json").read_text(encoding="utf-8")
        )
        self.tokenizer = None
        self.configure("standard", "")

    def configure(self, mode, vocabulary, language="en"):
        from app.languages import validate_language

        self.language = validate_language(language)
        if mode not in {"standard", "careful"}:
            raise ValueError("Unknown recognition mode")
        self.mode = mode
        self.prompt = []
        if vocabulary.strip():
            if self.tokenizer is None:
                self.tokenizer = WhisperTokenizer(self.folder / "tokenizer.json")
            self.prompt = self.tokenizer.vocabulary_tokens(vocabulary)

    @property
    def enabled(self):
        return self.mode == "careful" or bool(self.prompt)

    @property
    def prefix(self):
        prefix = [50258, self.language_token, 50359, 50363]
        return [50361, *self.prompt, *prefix] if self.prompt else prefix

    @property
    def language_token(self):
        return 50259 if self.language == "en" else 50260

    def filtered(self, logits, first):
        values = np.asarray(logits, dtype=np.float64).reshape(-1).copy()
        # Permit ordinary text and end-of-text only; no timestamps/language/task leakage.
        values[50258:] = -np.inf
        blocked = list(self.generation.get("suppress_tokens", []))
        if first:
            blocked += self.generation.get("begin_suppress_tokens", [])
        blocked = [x for x in blocked if 0 <= x < len(values)]
        values[blocked] = -np.inf
        values[np.isnan(values)] = -np.inf
        if not np.isfinite(values).any():
            raise RuntimeError("Decoder returned no usable text scores")
        maximum = np.max(values)
        values -= maximum + np.log(np.exp(values - maximum).sum())
        return values


def search(step, options, max_positions, beam_size=3):
    """step(token, position, immutable_cache) -> logits, new_cache; encoder reused once."""
    prefix = options.prefix
    if len(prefix) + 1 >= max_positions:
        raise ValueError("Vocabulary exceeds decoder context")
    state = None
    for position, token in enumerate(prefix):
        logits, state = step(token, position, state)
    active = [((), 0.0, state, logits)]
    finished = {}
    max_new = max_positions - len(prefix)
    for index in range(max_new):
        candidates = []
        for tokens, score, cache, scores in active:
            probs = options.filtered(scores, not tokens)
            count = min(beam_size + 1, len(probs))
            ids = np.argpartition(-probs, count - 1)[:count]
            ids = sorted(ids, key=lambda token: (-probs[token], int(token)))
            for token in ids:
                if np.isfinite(probs[token]):
                    candidates.append(
                        (tokens + (int(token),), score + float(probs[token]), cache)
                    )
        candidates.sort(key=lambda x: (-x[1], x[0]))
        selected = []
        for tokens, score, cache in candidates:
            if tokens[-1] == 50257:
                finished[tokens[:-1]] = score
            else:
                selected.append((tokens, score, cache))
            if len(selected) == beam_size:
                break
        if len(finished) >= beam_size or not selected:
            break
        if index == max_new - 1:
            active = [(t, s, c, None) for t, s, c in selected]
            break
        active = []
        for tokens, score, cache in selected:
            logits, next_cache = step(tokens[-1], len(prefix) + index, cache)
            active.append((tokens, score, next_cache, logits))
    # Prefer completed candidates; use an unfinished path only if none completed.
    if not finished:
        finished = {tokens: score for tokens, score, _, _ in active}
    return (
        list(max(finished, key=lambda tokens: finished[tokens] / max(1, len(tokens))))
        if finished
        else []
    )
