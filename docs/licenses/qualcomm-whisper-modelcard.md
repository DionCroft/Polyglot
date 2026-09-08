---
library_name: pytorch
license: apache-2.0
tags:
- foundation
- android
pipeline_tag: automatic-speech-recognition

---

![](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/web-assets/model_demo.png)

# Whisper-Base: Optimized for Qualcomm Devices

HuggingFace Whisper-Base ASR (Automatic Speech Recognition) model is a state-of-the-art system designed for transcribing spoken language into written text. This model is based on the transformer architecture and has been optimized for edge inference by replacing Multi-Head Attention (MHA) with Single-Head Attention (SHA) and linear layers with convolutional (conv) layers. It exhibits robust performance in realistic, noisy environments, making it highly reliable for real-world applications. Specifically, it excels in long-form transcription, capable of accurately transcribing audio clips up to 30 seconds long. Time to the first token is the encoder's latency, while time to each additional token is decoder's latency, where we assume a max decoded length specified below.

This is based on the implementation of Whisper-Base found [here](https://github.com/huggingface/transformers/tree/v4.42.3/src/transformers/models/whisper).
This repository contains pre-exported model files optimized for Qualcomm® devices. You can use the [Qualcomm® AI Hub Models](https://github.com/qualcomm/ai-hub-models/blob/v0.61.0/src/qai_hub_models/models/whisper_base) library to export with custom configurations. More details on model performance across various devices, can be found [here](#performance-summary).

Qualcomm AI Hub Models uses [Qualcomm AI Hub Workbench](https://workbench.aihub.qualcomm.com) to compile, profile, and evaluate this model. [Sign up](https://myaccount.qualcomm.com/signup) to run these models on a hosted Qualcomm® device.

## Deploying Whisper-Base on-device

This model is compatible with the Qualcomm Voice AI SDK. Download the SDK from the [Qualcomm Package Manager](https://qpm.qualcomm.com/#/main/tools/details/VoiceAI_ASR) to deploy this model on-device.
## Getting Started
There are two ways to deploy this model on your device:

### Option 1: Download Pre-Exported Models

Below are pre-exported model assets ready for deployment.

| Runtime | Precision | Chipset | SDK Versions | Download |
|---|---|---|---|---|
| PRECOMPILED_QNN_ONNX | float | Snapdragon® X2 Elite | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_snapdragon_x2_elite.zip)
| PRECOMPILED_QNN_ONNX | float | Snapdragon® X Elite | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_snapdragon_x_elite.zip)
| PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Gen 3 Mobile | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_snapdragon_8gen3.zip)
| PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Gen 1 Mobile | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_snapdragon_8gen1.zip)
| PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-8275 | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_qcs8275.zip)
| PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_qcs8550_proxy.zip)
| PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-9075 | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_qcs9075.zip)
| PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Elite Mobile | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_snapdragon_8_elite_for_galaxy.zip)
| PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Elite Gen 5 Mobile | QAIRT 2.45, ONNX Runtime 1.27.1 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-precompiled_qnn_onnx-float-qualcomm_snapdragon_8_elite_gen5_for_galaxy.zip)
| QNN_CONTEXT_BINARY | float | Snapdragon® X2 Elite | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_snapdragon_x2_elite.zip)
| QNN_CONTEXT_BINARY | float | Snapdragon® X Elite | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_snapdragon_x_elite.zip)
| QNN_CONTEXT_BINARY | float | Snapdragon® 8 Gen 3 Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_snapdragon_8gen3.zip)
| QNN_CONTEXT_BINARY | float | Snapdragon® 8 Gen 1 Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_snapdragon_8gen1.zip)
| QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-8275 | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_qcs8275.zip)
| QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_qcs8550_proxy.zip)
| QNN_CONTEXT_BINARY | float | Qualcomm® SA8775P | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_sa8775p.zip)
| QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-9075 | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_qcs9075.zip)
| QNN_CONTEXT_BINARY | float | Qualcomm® SA7255P | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_sa7255p.zip)
| QNN_CONTEXT_BINARY | float | Qualcomm® SA8295P | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_sa8295p.zip)
| QNN_CONTEXT_BINARY | float | Snapdragon® 8 Elite Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_snapdragon_8_elite_for_galaxy.zip)
| QNN_CONTEXT_BINARY | float | Snapdragon® 8 Elite Gen 5 Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-qnn_context_binary-float-qualcomm_snapdragon_8_elite_gen5_for_galaxy.zip)
| VOICE_AI | float | Snapdragon® X2 Elite | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_snapdragon_x2_elite.zip)
| VOICE_AI | float | Snapdragon® X Elite | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_snapdragon_x_elite.zip)
| VOICE_AI | float | Snapdragon® 8 Gen 3 Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_snapdragon_8gen3.zip)
| VOICE_AI | float | Snapdragon® 8 Gen 1 Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_snapdragon_8gen1.zip)
| VOICE_AI | float | Qualcomm® Dragonwing™ IQ-8275 | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_qcs8275.zip)
| VOICE_AI | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_qcs8550_proxy.zip)
| VOICE_AI | float | Qualcomm® SA8775P | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_sa8775p.zip)
| VOICE_AI | float | Qualcomm® Dragonwing™ IQ-9075 | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_qcs9075.zip)
| VOICE_AI | float | Qualcomm® SA7255P | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_sa7255p.zip)
| VOICE_AI | float | Qualcomm® SA8295P | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_sa8295p.zip)
| VOICE_AI | float | Snapdragon® 8 Elite Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_snapdragon_8_elite_for_galaxy.zip)
| VOICE_AI | float | Snapdragon® 8 Elite Gen 5 Mobile | QAIRT 2.45 | [Download](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/whisper_base/releases/v0.61.0/whisper_base-voice_ai-float-qualcomm_snapdragon_8_elite_gen5_for_galaxy.zip)

For more device-specific assets and performance metrics, visit **[Whisper-Base on Qualcomm® AI Hub](https://aihub.qualcomm.com/models/whisper_base)**.


### Option 2: Export with Custom Configurations

Use the [Qualcomm® AI Hub Models](https://github.com/qualcomm/ai-hub-models/blob/v0.61.0/src/qai_hub_models/models/whisper_base) Python library to compile and export the model with your own:
- Custom weights (e.g., fine-tuned checkpoints)
- Custom input shapes
- Target device and runtime configurations

This option is ideal if you need to customize the model beyond the default configuration provided here.

See our repository for [Whisper-Base on GitHub](https://github.com/qualcomm/ai-hub-models/blob/v0.61.0/src/qai_hub_models/models/whisper_base) for usage instructions.

## Model Details

**Model Type:** Model_use_case.speech_recognition

**Model Stats:**
- Input resolution: 80x3000 (30 seconds audio)
- Max decoded sequence length: 200 tokens
- Model checkpoint: openai/whisper-base
- Model size (decoder) (float): 187 MB
- Model size (encoder) (float): 90.7 MB
- Number of parameters (decoder): 48.9M
- Number of parameters (encoder): 23.7M

## Performance Summary
| Model | Runtime | Precision | Chipset | Inference Time (ms) | Peak Memory Range (MB) | Primary Compute Unit
|---|---|---|---|---|---|---
| decoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® X2 Elite | 2.355 ms | 20 - 20 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® X Elite | 3.744 ms | 126 - 126 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Gen 3 Mobile | 3.485 ms | 0 - 13 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Gen 1 Mobile | 5.254 ms | 25 - 40 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-8275 | 5.659 ms | 20 - 43 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | 4.325 ms | 20 - 22 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® QCS8450 | 5.254 ms | 25 - 40 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-9075 | 5.198 ms | 20 - 43 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-X7181 | 3.744 ms | 126 - 126 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ Q-8750 | 2.896 ms | 16 - 23 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Elite Mobile | 2.896 ms | 16 - 23 MB | NPU
| decoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Elite Gen 5 Mobile | 2.69 ms | 23 - 30 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Snapdragon® X2 Elite | 2.877 ms | 20 - 20 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Snapdragon® X Elite | 3.763 ms | 20 - 20 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Gen 3 Mobile | 3.417 ms | 16 - 24 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Gen 1 Mobile | 5.159 ms | 19 - 28 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-8275 | 5.398 ms | 20 - 45 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-8275 | 7.19 ms | 20 - 30 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | 4.189 ms | 20 - 21 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8775P | 5.236 ms | 20 - 30 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8650P | 5.236 ms | 20 - 30 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8255P | 5.236 ms | 20 - 30 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® QCS8450 | 5.159 ms | 19 - 28 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-9075 | 5.113 ms | 22 - 46 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-X7181 | 3.763 ms | 20 - 20 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ Q-8750 | 2.822 ms | 0 - 9 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA7255P | 7.19 ms | 20 - 30 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8295P | 5.31 ms | 18 - 23 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Elite Mobile | 2.822 ms | 0 - 9 MB | NPU
| decoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Elite Gen 5 Mobile | 2.668 ms | 20 - 29 MB | NPU
| decoder | VOICE_AI | float | Snapdragon® X2 Elite | 2.978 ms | 20 - 20 MB | NPU
| decoder | VOICE_AI | float | Snapdragon® X Elite | 3.909 ms | 20 - 20 MB | NPU
| decoder | VOICE_AI | float | Snapdragon® 8 Gen 3 Mobile | 3.435 ms | 1 - 8 MB | NPU
| decoder | VOICE_AI | float | Snapdragon® 8 Gen 1 Mobile | 5.137 ms | 20 - 28 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-8275 | 5.44 ms | 20 - 45 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-8275 | 7.406 ms | 20 - 28 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | 4.184 ms | 19 - 20 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® SA8775P | 5.311 ms | 20 - 30 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® SA8650P | 5.311 ms | 20 - 30 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® SA8255P | 5.311 ms | 20 - 30 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® QCS8450 | 5.137 ms | 20 - 28 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-9075 | 5.112 ms | 20 - 44 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-X7181 | 3.909 ms | 20 - 20 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® Dragonwing™ Q-8750 | 2.858 ms | 0 - 9 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® SA7255P | 7.406 ms | 20 - 28 MB | NPU
| decoder | VOICE_AI | float | Qualcomm® SA8295P | 5.216 ms | 18 - 23 MB | NPU
| decoder | VOICE_AI | float | Snapdragon® 8 Elite Mobile | 2.858 ms | 0 - 9 MB | NPU
| decoder | VOICE_AI | float | Snapdragon® 8 Elite Gen 5 Mobile | 2.668 ms | 20 - 30 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® X2 Elite | 22.517 ms | 67 - 67 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® X Elite | 48.984 ms | 66 - 66 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Gen 3 Mobile | 36.297 ms | 41 - 48 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Gen 1 Mobile | 95.477 ms | 38 - 53 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-8275 | 57.412 ms | 37 - 41 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | 48.137 ms | 8 - 57 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® QCS8450 | 95.477 ms | 38 - 53 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-9075 | 56.123 ms | 42 - 45 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ IQ-X7181 | 48.984 ms | 66 - 66 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Qualcomm® Dragonwing™ Q-8750 | 25.428 ms | 39 - 46 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Elite Mobile | 25.428 ms | 39 - 46 MB | NPU
| encoder | PRECOMPILED_QNN_ONNX | float | Snapdragon® 8 Elite Gen 5 Mobile | 22.113 ms | 38 - 45 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Snapdragon® X2 Elite | 22.876 ms | 0 - 0 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Snapdragon® X Elite | 49.129 ms | 0 - 0 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Gen 3 Mobile | 35.959 ms | 1 - 8 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Gen 1 Mobile | 95.742 ms | 1 - 10 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-8275 | 57.053 ms | 0 - 21 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-8275 | 142.302 ms | 1 - 10 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | 47.885 ms | 1 - 6 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8775P | 54.868 ms | 1 - 10 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8650P | 54.868 ms | 1 - 10 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8255P | 54.868 ms | 1 - 10 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® QCS8450 | 95.742 ms | 1 - 10 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-9075 | 55.801 ms | 2 - 22 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ IQ-X7181 | 49.129 ms | 0 - 0 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® Dragonwing™ Q-8750 | 25.927 ms | 1 - 13 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA7255P | 142.302 ms | 1 - 10 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Qualcomm® SA8295P | 68.883 ms | 0 - 6 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Elite Mobile | 25.927 ms | 1 - 13 MB | NPU
| encoder | QNN_CONTEXT_BINARY | float | Snapdragon® 8 Elite Gen 5 Mobile | 21.99 ms | 1 - 9 MB | NPU
| encoder | VOICE_AI | float | Snapdragon® X2 Elite | 22.846 ms | 0 - 0 MB | NPU
| encoder | VOICE_AI | float | Snapdragon® X Elite | 49.577 ms | 0 - 0 MB | NPU
| encoder | VOICE_AI | float | Snapdragon® 8 Gen 3 Mobile | 36.127 ms | 1 - 8 MB | NPU
| encoder | VOICE_AI | float | Snapdragon® 8 Gen 1 Mobile | 95.132 ms | 0 - 9 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-8275 | 56.813 ms | 0 - 21 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-8275 | 142.251 ms | 1 - 10 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® Dragonwing™ QCS8550 (Proxy) | 47.884 ms | 1 - 3 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® SA8775P | 55.027 ms | 1 - 10 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® SA8650P | 55.027 ms | 1 - 10 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® SA8255P | 55.027 ms | 1 - 10 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® QCS8450 | 95.132 ms | 0 - 9 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-9075 | 55.533 ms | 0 - 20 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® Dragonwing™ IQ-X7181 | 49.577 ms | 0 - 0 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® Dragonwing™ Q-8750 | 25.823 ms | 1 - 10 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® SA7255P | 142.251 ms | 1 - 10 MB | NPU
| encoder | VOICE_AI | float | Qualcomm® SA8295P | 68.788 ms | 0 - 6 MB | NPU
| encoder | VOICE_AI | float | Snapdragon® 8 Elite Mobile | 25.823 ms | 1 - 10 MB | NPU
| encoder | VOICE_AI | float | Snapdragon® 8 Elite Gen 5 Mobile | 22.044 ms | 1 - 9 MB | NPU

## License
* The license for the original implementation of Whisper-Base can be found
  [here](https://github.com/huggingface/transformers/blob/v4.42.3/LICENSE).

## References
* [Robust Speech Recognition via Large-Scale Weak Supervision](https://cdn.openai.com/papers/whisper.pdf)
* [Source Model Implementation](https://github.com/huggingface/transformers/tree/v4.42.3/src/transformers/models/whisper)

## Community
* Join [our AI Hub Slack community](https://aihub.qualcomm.com/community/slack) to collaborate, post questions and learn more about on-device AI.
* For questions or feedback please [reach out to us](mailto:ai-hub-support@qti.qualcomm.com).
