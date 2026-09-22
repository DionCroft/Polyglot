import json
import numpy as np
import sentencepiece as spm
from app.system.inference import session


class OpusMT:
    name = "OPUS-MT EN → ZH · local CPU"

    def __init__(
        self,
        folder,
        beams=4,
        length_penalty=1.0,
        early_stopping=False,
        source_language="en",
    ):
        from opencc import OpenCC
        from app.languages import validate_language

        self.source_language = validate_language(source_language)
        self.name = (
            "OPUS-MT "
            + ("EN → ZH" if source_language == "en" else "ZH → EN")
            + " · local CPU"
        )
        self.beams = beams
        self.length_penalty = length_penalty
        self.early_stopping = early_stopping
        self.simplify = OpenCC("t2s")
        self.cfg = json.loads((folder / "config.json").read_text())
        self.vocab = json.loads((folder / "vocab.json").read_text(encoding="utf-8"))
        self.reverse = {i: s for s, i in self.vocab.items()}
        self.source = spm.SentencePieceProcessor(model_file=str(folder / "source.spm"))
        self.encoder = session(folder / "onnx/encoder_model_quantized.onnx")
        self.decoder = session(folder / "onnx/decoder_model_quantized.onnx")
        self.past = session(folder / "onnx/decoder_with_past_model_quantized.onnx")

    def encode(self, text):
        return (
            ([self.vocab[">>cmn_Hans<<"]] if self.source_language == "en" else [])
            + [self.vocab.get(p, 1) for p in self.source.encode(text, out_type=str)]
            + [0]
        )

    def translate(self, text):
        if not text.strip():
            return ""
        ids = self.encode(text)
        if len(ids) > 500:
            raise ValueError(
                "Phrase exceeds translation model limit; use shorter segments."
            )
        ids = np.array([ids], dtype=np.int64)
        mask = np.ones_like(ids)
        hidden = self.encoder.run(None, {"input_ids": ids, "attention_mask": mask})[0]
        beams = self.beams
        eos = self.cfg["eos_token_id"]
        pad = self.cfg["pad_token_id"]
        active = [[]]
        scores = np.array([0.0])
        cache = {}
        finished = []
        next_ids = np.array([[self.cfg["decoder_start_token_id"]]], dtype=np.int64)
        for step in range(192):
            decoder = self.decoder if step == 0 else self.past
            feed = {
                "input_ids": next_ids,
                "encoder_attention_mask": np.repeat(mask, len(active), axis=0),
                "encoder_hidden_states": np.repeat(hidden, len(active), axis=0),
                **cache,
            }
            out = decoder.run(
                None, {i.name: feed[i.name] for i in decoder.get_inputs()}
            )
            logits = out[0][:, -1].astype(np.float64)
            logits[:, pad] = -np.inf
            if step == 0 and hasattr(self, "target_id"):
                forced = logits[:, self.target_id].copy()
                logits[:] = -np.inf
                logits[:, self.target_id] = forced
            logits -= logits.max(axis=1, keepdims=True)
            probabilities = logits - np.log(np.exp(logits).sum(axis=1, keepdims=True))
            combined = probabilities + scores[:, None]
            flat = combined.ravel()
            top = np.argpartition(flat, -min(beams * 2, len(flat)))[-beams * 2 :]
            top = top[np.argsort(flat[top])[::-1]]
            parents = []
            tokens = []
            new_active = []
            new_scores = []
            for rank, index in enumerate(top):
                parent, token = divmod(int(index), combined.shape[1])
                sequence = active[parent] + [token]
                score = float(flat[index])
                if not np.isfinite(score):
                    continue
                if token == eos:
                    if rank < beams:
                        finished.append(
                            (
                                score / (max(1, len(sequence)) ** self.length_penalty),
                                sequence,
                            )
                        )
                elif len(new_active) < beams:
                    parents.append(parent)
                    tokens.append(token)
                    new_active.append(sequence)
                    new_scores.append(score)
            finished = sorted(finished, key=lambda item: item[0], reverse=True)[:beams]
            if len(finished) >= beams:
                best_live = max(new_scores, default=-np.inf) / (
                    (step + 1) ** self.length_penalty
                )
                if self.early_stopping or best_live <= finished[-1][0]:
                    break
            if not new_active:
                break
            cache = {k: v[parents] for k, v in cache.items()}
            for info, value in zip(decoder.get_outputs()[1:], out[1:]):
                cache[info.name.replace("present.", "past_key_values.")] = value[
                    parents
                ]
            active = new_active
            scores = np.array(new_scores)
            next_ids = np.array(tokens, dtype=np.int64)[:, None]
        if not finished:
            raise RuntimeError(
                "Translation did not reach a sentence ending within its token limit."
            )
        result = max(finished, key=lambda item: item[0])[1]
        text = (
            "".join(
                self.reverse.get(i, "")
                for i in result
                if i != eos and i != getattr(self, "target_id", -1)
            )
            .replace("▁", " ")
            .strip()
        )
        return self.simplify.convert(text) if self.source_language == "en" else text
