"""Local decoder for Qualcomm's static Whisper encoder / self-attention cache ABI."""

import json
import numpy as np
from app.asr.features import WhisperFeatures
from app.system.inference import session


class QnnWhisper:
    name = "Qualcomm NPU Â· Whisper Base"

    def __init__(self, folder, profile=False):
        self.load_assets(folder)
        self.encoder = session(
            next((folder / "qnn").rglob("encoder.onnx")), True, profile
        )
        self.decoder = session(
            next((folder / "qnn").rglob("decoder.onnx")), True, profile
        )

    def load_assets(self, folder):
        self.cfg = json.loads((folder / "config.json").read_text())
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

    def transcribe(self, audio):
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
        # Force English, transcription, and no timestamps (multilingual Whisper).
        prefix = [50259, 50359, 50363]
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

    def decode(self, result):
        chars = "".join(self.vocab.get(t, "") for t in result if t < 50257)
        return (
            bytes(self.byte_decoder[c] for c in chars)
            .decode("utf-8", errors="replace")
            .strip()
        )
