import numpy as np
from app.asr.qnn_whisper import QnnWhisper
from app.system.inference import session


class CpuWhisper(QnnWhisper):
    name = "Local CPU · Whisper Base int8"

    def __init__(self, folder, encoder=None):
        self.load_assets(folder)
        self.encoder = (
            encoder
            if encoder is not None
            else session(folder / "cpu/encoder_model_quantized.onnx")
        )
        self.decoder = session(folder / "cpu/decoder_model_quantized.onnx")
        self.past = session(folder / "cpu/decoder_with_past_model_quantized.onnx")

    def transcribe(self, audio):
        hidden = self.encoder.run(None, {"input_features": self.features(audio)})[0]
        cache = {}
        result = []
        token = self.cfg["decoder_start_token_id"]
        for n in range(192):
            decoder = self.decoder if n == 0 else self.past
            feed = {
                "input_ids": np.array([[token]], dtype=np.int64),
                "encoder_hidden_states": hidden,
                **cache,
            }
            out = decoder.run(
                None, {i.name: feed[i.name] for i in decoder.get_inputs()}
            )
            token = [50259, 50359, 50363][n] if n < 3 else int(np.argmax(out[0][0, -1]))
            if token == 50257:
                break
            result.append(token)
            for info, value in zip(decoder.get_outputs()[1:], out[1:]):
                cache[info.name.replace("present.", "past_key_values.")] = value
        return self.decode(result)

    def close(self):
        close = getattr(self.encoder, "close", None)
        if close:
            close()
