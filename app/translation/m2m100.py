import json
import sentencepiece as spm
from opencc import OpenCC
from app.translation.opus_mt import OpusMT
from app.system.inference import session


class M2M100(OpusMT):
    name = "M2M100 · local ARM64 CPU"

    def __init__(self, folder):
        self.beams = 4
        self.length_penalty = 1.0
        self.early_stopping = False
        self.cfg = json.loads((folder / "config.json").read_text())
        self.vocab = json.loads((folder / "vocab.json").read_text(encoding="utf-8"))
        self.reverse = {i: s for s, i in self.vocab.items()}
        tokens = json.loads((folder / "tokenizer.json").read_text(encoding="utf-8"))[
            "added_tokens"
        ]
        self.source_id = next(t["id"] for t in tokens if t["content"] == "__en__")
        self.target_id = next(t["id"] for t in tokens if t["content"] == "__zh__")
        self.source = spm.SentencePieceProcessor(
            model_file=str(folder / "sentencepiece.bpe.model")
        )
        self.simplify = OpenCC("t2s")
        self.encoder = session(folder / "onnx/encoder_model_quantized.onnx")
        self.decoder = session(folder / "onnx/decoder_model_quantized.onnx")
        self.past = session(folder / "onnx/decoder_with_past_model_quantized.onnx")

    def encode(self, text):
        return (
            [self.source_id]
            + [self.vocab.get(p, 3) for p in self.source.encode(text, out_type=str)]
            + [self.cfg["eos_token_id"]]
        )
