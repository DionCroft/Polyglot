# Model and dependency notices

The app uses local weights; using Whisper does not use an OpenAI API.

| Component | Source / stated license |
|---|---|
| macOS Base/Small ONNX exports | onnx-community/whisper-base and whisper-small; pinned revisions in assets-macos.lock.json; derived from original OpenAI Whisper MIT weights |
| PyObjC / macOS ONNX Runtime | MIT; exact wheel notices collected in the Mac bundle |
| Original Whisper weights/code | OpenAI Whisper, MIT |
| Qualcomm Whisper Base/Small exports | Qualcomm Hugging Face cards identify Apache-2.0 and link the Transformers Apache license; preserve their source notice and original Whisper MIT notice |
| OPUS-MT EN–ZH | Helsinki-NLP card: Apache-2.0; ONNX conversion by onnx-community |
| OPUS-MT ZH–EN | Helsinki-NLP, CC-BY-4.0; ONNX quantisation by Xenova; [attribution and conversion notice](licenses/opus-zh-en-NOTICE.md) |
| Silero VAD | snakers4/silero-vad, MIT (bundled LICENSE) |
| ONNX Runtime / QNN plugin | MIT package notices; retain bundled third-party notices |
| PySide6 / Qt | LGPLv3/GPLv3 or commercial licensing; dynamically linked distribution, preserve notices and users' replacement rights |
| Python | PSF license, included with runtime |
| SentencePiece | Apache-2.0 |
| OpenCC Python reimplementation | Apache-2.0 |
| sounddevice / PortAudio | MIT / PortAudio permissive notices |
| PyInstaller | GPL with bootloader exception; app is not made GPL merely by packaging |

Upstream license text and model cards are archived in `docs/licenses`. Exact model
source revisions and SHA-256 values are recorded separately. Qualcomm's exported
model license pointer is not a blanket license for every separately distributed SDK
or Surface driver. No standalone proprietary SDK or system driver is redistributed.

`docs/evidence/qualcomm-model.py` is research reference source, BSD-3-Clause, not a
runtime dependency. Preserve `qualcomm-reference-BSD.txt` when distributing it.
The public JFK sample is development test material; the deployable app excludes test
recordings. Synthetic technical audio was generated locally using an installed
Windows voice. Audio fixtures are not included in the teaching application bundle.
