import numpy as np
from app.asr.qnn_whisper import QnnWhisper
from app.system.inference import session


class CpuWhisper(QnnWhisper):
    name = "Local CPU · Whisper Base int8"

    def __init__(self, folder, encoder=None):
        self.load_assets(folder)
        self.name = "Local CPU · Whisper " + (
            "Small int8" if self.cfg["d_model"] == 768 else "Base int8"
        )
        self.encoder = (
            encoder
            if encoder is not None
            else session(folder / "cpu/encoder_model_quantized.onnx")
        )
        self.decoder = session(folder / "cpu/decoder_model_quantized.onnx")
        self.past = session(folder / "cpu/decoder_with_past_model_quantized.onnx")

    def _transcribe_standard(self, audio):
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
            token = (
                [self.recognition.language_token, 50359, 50363][n]
                if n < 3
                else int(np.argmax(out[0][0, -1]))
            )
            if token == 50257:
                break
            result.append(token)
            for info, value in zip(decoder.get_outputs()[1:], out[1:]):
                cache[info.name.replace("present.", "past_key_values.")] = value
        return self.decode(result)

    def detect_language(self, audio):
        from app.asr.language_detection import language_scores

        hidden = self.encoder.run(None, {"input_features": self.features(audio)})[0]
        feed = {
            "input_ids": np.array([[self.cfg["decoder_start_token_id"]]], np.int64),
            "encoder_hidden_states": hidden,
        }
        logits = self.decoder.run(
            None, {i.name: feed[i.name] for i in self.decoder.get_inputs()}
        )[0][0, -1]
        return language_scores(logits, self.recognition.generation["lang_to_id"])

    def _transcribe_guided(self, audio):
        from app.asr.decoding import search

        audio = np.asarray(audio, dtype=np.float32)
        if not audio.size or float(np.max(np.abs(audio))) < 1e-6:
            return ""
        hidden = self.encoder.run(None, {"input_features": self.features(audio)})[0]

        def step(token, position, cache):
            decoder = self.decoder if cache is None else self.past
            feed = {
                "input_ids": np.array([[token]], dtype=np.int64),
                "encoder_hidden_states": hidden,
                **(cache or {}),
            }
            out = decoder.run(
                None, {i.name: feed[i.name] for i in decoder.get_inputs()}
            )
            updated = dict(cache or {})
            for info, value in zip(decoder.get_outputs()[1:], out[1:]):
                updated[info.name.replace("present.", "past_key_values.")] = value
            return out[0][0, -1], updated

        width = 3 if self.recognition.mode == "careful" and self.final_pass else 1
        return self.decode(search(step, self.recognition, 192, width))

    def close(self):
        close = getattr(self.encoder, "close", None)
        if close:
            close()
