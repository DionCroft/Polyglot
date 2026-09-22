"""Local decoder for Qualcomm's static Whisper encoder / self-attention cache ABI."""

import json
import numpy as np
from app.asr.features import WhisperFeatures
from app.system.inference import session


class QnnWhisper:
    name = "Qualcomm NPU · Whisper Base"

    def __init__(self, folder, profile=False):
        self.load_assets(folder)
        self.encoder = session(
            next((folder / "qnn").rglob("encoder.onnx")), True, profile
        )
        self.decoder = session(
            next((folder / "qnn").rglob("decoder.onnx")), True, profile
        )

    def load_assets(self, folder):
        from app.asr.decoding import RecognitionOptions

        self.recognition = RecognitionOptions(folder)
        self.final_pass = True
        self.cfg = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        self.features = WhisperFeatures(folder / "preprocessor_config.json")
        vocab = json.loads((folder / "tokenizer.json").read_text(encoding="utf-8"))[
            "model"
        ]["vocab"]
        self.vocab = {i: s for s, i in vocab.items()}
        bs = list(range(33, 127)) + list(range(161, 173)) + list(range(174, 256))
        cs = bs[:]
        extra = 0
        for b in range(256):
            if b not in bs:
                bs.append(b)
                cs.append(256 + extra)
                extra += 1
        self.byte_decoder = dict(zip(map(chr, cs), bs))

    def configure_recognition(self, mode="standard", vocabulary="", language="en"):
        self.recognition.configure(mode, vocabulary, language)

    def transcribe(self, audio):
        if self.recognition.enabled:
            return self._transcribe_guided(audio)
        return self._transcribe_standard(audio)

    def _transcribe_standard(self, audio):
        cross = self.encoder.run(
            None,
            {
                self.encoder.get_inputs()[0].name: self.features(audio).astype(
                    np.float16
                )
            },
        )
        inputs = self.decoder.get_inputs()
        dtype = {
            "tensor(float)": np.float32,
            "tensor(int32)": np.int32,
            "tensor(int64)": np.int64,
            "tensor(float16)": np.float16,
        }
        feed = {i.name: np.zeros(i.shape, dtype=dtype[i.type]) for i in inputs}
        # ABI: token, mask, self k/v per layer, cross k/v per layer, position.
        layers = self.cfg["decoder_layers"]
        for i, value in zip(inputs[2 + layers * 2 : -1], cross, strict=True):
            feed[i.name] = value
        mask_name = inputs[1].name
        length = feed[mask_name].shape[-1]
        feed[mask_name].fill(-100)
        token = self.cfg["decoder_start_token_id"]
        # Force the selected language, transcription, and no timestamps.
        prefix = [self.recognition.language_token, 50359, 50363]
        result = []
        for n in range(length - 1):
            feed[inputs[0].name].fill(token)
            feed[inputs[-1].name].fill(n)
            feed[mask_name][..., length - n - 1] = 0
            out = self.decoder.run(None, feed)
            token = prefix[n] if n < len(prefix) else int(np.argmax(out[0]))
            if token == self.cfg["eos_token_id"]:
                break
            result.append(token)
            for i, value in zip(inputs[2 : 2 + layers * 2], out[1:], strict=True):
                feed[i.name] = value
        return self.decode(result)

    def _transcribe_guided(self, audio):
        from app.asr.decoding import search

        audio = np.asarray(audio, dtype=np.float32)
        if not audio.size or float(np.max(np.abs(audio))) < 1e-6:
            return ""
        cross = self.encoder.run(
            None,
            {
                self.encoder.get_inputs()[0].name: self.features(audio).astype(
                    np.float16
                )
            },
        )
        inputs = self.decoder.get_inputs()
        dtype = {
            "tensor(float)": np.float32,
            "tensor(int32)": np.int32,
            "tensor(int64)": np.int64,
            "tensor(float16)": np.float16,
        }
        feed = {i.name: np.zeros(i.shape, dtype=dtype[i.type]) for i in inputs}
        layers = self.cfg["decoder_layers"]
        for info, value in zip(inputs[2 + layers * 2 : -1], cross, strict=True):
            feed[info.name] = value
        cache_names = [i.name for i in inputs[2 : 2 + layers * 2]]
        initial = tuple(feed[name] for name in cache_names)
        length = feed[inputs[1].name].shape[-1]

        def step(token, position, cache):
            feed[inputs[0].name].fill(token)
            feed[inputs[-1].name].fill(position)
            feed[inputs[1].name].fill(-100)
            feed[inputs[1].name][..., length - position - 1 :] = 0
            for name, value in zip(
                cache_names, initial if cache is None else cache, strict=True
            ):
                feed[name] = value
            out = self.decoder.run(None, feed)
            return out[0], tuple(out[1:])

        width = 3 if self.recognition.mode == "careful" and self.final_pass else 1
        return self.decode(search(step, self.recognition, length - 1, width))

    def decode(self, result):
        chars = "".join(self.vocab.get(t, "") for t in result if t < 50257)
        return (
            bytes(self.byte_decoder[c] for c in chars)
            .decode("utf-8", errors="replace")
            .strip()
        )
