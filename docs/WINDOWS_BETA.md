# Windows Intel/AMD beta

LectureLive 0.6.0 beta 1 includes a Windows x64 edition with English and Mandarin conversations. You can try it on Intel or AMD PCs.
The existing Snapdragon ARM64 edition remains available. macOS, Linux and 32-bit Windows
are outside this release.

## What is ready to try?

| Processing option | What it does | Validation status |
|---|---|---|
| CPU | Runs speech, Chinese translation and voice detection locally | x64 runtime tested under Windows ARM emulation; physical Intel/AMD testing pending |
| GPU (DirectML) | Runs the Whisper Base speech encoder on a compatible Windows GPU; decoding and translation stay on CPU | Real DirectML execution verified on Adreno; Intel/AMD GPU testing pending |
| Intel NPU | Tries a prepared Windows ML OpenVINO provider on an actual NPU device | Experimental integration; physical hardware/model acceptance pending |
| AMD NPU | Tries a prepared Windows ML Vitis AI provider on an actual NPU device | Experimental integration; physical hardware/model acceptance pending |

An Intel or AMD processor does not necessarily have an NPU. NPU selection is only accepted
when a matching device loads the model and its execution trace confirms accelerated work.
Unsupported models or drivers fall back to CPU. There is no guaranteed speed improvement:
compare caption speed on your own PC. This beta uses the **Fast / Whisper Base** speech model.

## Install the beta — no programming needed

1. Use Windows 11 on a 64-bit Intel or AMD PC. Keep Windows and your manufacturer's graphics
   drivers up to date. Use Windows 11 24H2 or later if you want to try an NPU.
2. Download the repository ZIP and **Extract All**, as shown in the main README.
3. Open the extracted folder and double-click **Setup.cmd**. It detects your Windows architecture.
   On an Intel/AMD PC it installs the x64 beta. **Setup-Beta.cmd** explicitly selects the beta.
4. Wait for **SETUP COMPLETE**. Setup uses its own private Python installation; no account or
   developer tools are needed. Keep internet connected during this first setup and allow about
   15 GB of free space for downloads, models and build files.
5. Double-click **Launch-Beta.cmd** (or **Launch.cmd** on an Intel/AMD PC). The Start menu
   shortcut is **LectureLive-x64-Beta**. Keep the extracted folder in place.
6. Connect your teaching microphone. Select it and use **Test microphone**. Leave processing
   hardware on **Automatic** and start a short practice lecture.
7. Read **Diagnostics** to see the actual verified backend. CPU is a valid working result.

A complete ready-to-run beta folder contains **LectureLive-x64-Beta.exe** and **_internal**.
Keep both together. Copying that whole folder needs no Python installation or initial model
download for CPU/GPU use. The source ZIP from GitHub needs setup first.

## Taking Mandarin questions

The current setup includes the additional **172.7 MB** Mandarin → English model. Update by
closing the app and running the current **Setup.cmd** or **Setup-Beta.cmd**. CPU and GPU
speech paths use the same Whisper Base model for both languages. NPU hardware support remains
experimental. The reverse translator runs on CPU and loads on the first Mandarin turn.

Use **Who is speaking? → Mandarin 普通话 → English**, wait for **Listening**, then let the
student speak. Return to **English → 简体中文** to answer. English-only CO7000/vocabulary
hints are retained but not applied to Mandarin. [Conversation guide](CONVERSATIONS.md).

## Improving speech recognition

See [Improving speech recognition](SPEECH_RECOGNITION.md) for the optional Careful mode,
vocabulary guidance and the measured limitations of these options on Whisper Base.
Standard remains the default. No new model downloads are required.

## Optional Intel/AMD NPU preparation

GPU and CPU captions do not require this step. Preparation is **online**; lectures remain offline.

1. Install the NPU driver recommended by your PC manufacturer. Check that the PC actually has
   an Intel or AMD NPU. A CPU brand alone is not sufficient.
2. Install the official [Windows App Runtime 2.3 x64 installer](https://aka.ms/windowsappsdk/2.3/2.3.1/windowsappruntimeinstall-x64.exe)
   if it is not already installed. Follow Microsoft's installer prompts or ask university IT.
3. Close LectureLive, then double-click **Prepare-Acceleration.cmd** in the source/setup folder.
   This uses Microsoft's Windows ML catalog to prepare compatible NPU providers for this PC.
   Wait for the results. If none are found, keep using CPU or GPU.
4. Start LectureLive again. Choose **Intel NPU** or **AMD NPU** under **Processing hardware**.
   The first model check can take up to three minutes. Actual inference must pass before the
   app labels the encoder as NPU accelerated. If the check fails, the warning explains why
   and the app uses CPU captions.
5. Re-run preparation after a provider/driver update, or on a different PC. Prepared NPU
   libraries are specific to the Windows user and PC; they are not a portable part of the ZIP.

NPU support is experimental. The pinned FP32 Whisper encoder may be rejected by a vendor
provider. This beta handles that rejection, but it does not yet certify this model for Intel
or AMD NPU hardware. Do not rely on NPU availability until the app passes on your own PC.

## How fallback and privacy work

Automatic selection tries prepared Intel/AMD NPUs, then DirectML GPU, then CPU. Selecting an
individual accelerator tries only that accelerator before CPU. The encoder runs in a separate
process with a 180-second setup limit and a 30-second inference limit. A failure can delay a
caption until that timeout; the same phrase is then retried on CPU. Use CPU mode if your driver
is unreliable. Change hardware while the lecture is stopped.

The app never prepares/downloads providers during a lecture. Runtime CPU fallback is disabled
inside the accelerated encoder session; a synthetic warm-up trace must show the requested
provider and no CPU nodes. The decoder, translation and voice detection intentionally use CPU.
Microphone features travel through an authenticated local Windows named pipe, not a network
socket or audio file. Native vendor libraries still need an OS-level network audit on each new
platform before making stronger offline guarantees.

Beta preferences, logs and text transcripts are stored separately in
`%LOCALAPPDATA%\LectureLive Beta`. The ARM64 edition uses `%LOCALAPPDATA%\LectureLive`.

## If something goes wrong

| Problem | Next step |
|---|---|
| NPU unavailable | Check the driver/runtime, run preparation, then inspect Diagnostics. CPU/GPU remain usable. |
| Provider changed or checksum mismatch | Close the app and re-run Prepare-Acceleration.cmd on this PC. |
| Slow or failed GPU check | Update the graphics driver or choose CPU for the next lecture. |
| Setup stopped | Read setup.log and re-run Setup.cmd in the same folder. Verified downloads are reused. |
| Beta app missing | Run Setup-Beta.cmd, then Launch-Beta.cmd. |
| Windows blocks the unsigned application | Follow your organisation's software approval process. Do not disable antivirus. |

Before teaching, test a five-minute recording-free lecture with your actual microphone and
projector. Check caption accuracy, final transcript saving, pause/resume and Stop. To report a
problem, include Windows version, CPU/GPU/NPU models, driver versions, chosen processing
option and the actual backend in Diagnostics. Review logs before sharing personal information.

## Implementation references

The beta pins Windows ML Python bindings 2.3.0 and their required ONNX Runtime Windows ML
1.25.2.202605110140 wheel. GPU uses the bundled DirectML provider. NPU preparation uses the
Windows ML catalog, then runtime registration uses a locally cached, SHA-256 checked library.

- [Microsoft ONNX Runtime DirectML provider](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html)
- [OpenVINO provider and NPU options](https://onnxruntime.ai/docs/execution-providers/OpenVINO-ExecutionProvider.html)
- [AMD Windows ML provider integration](https://ryzenai.docs.amd.com/projects/WinML/en/latest/winml_ep.html)
- [AMD Windows ML requirements](https://ryzenai.docs.amd.com/projects/WinML/en/latest/installation.html)
