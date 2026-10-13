# Intel laptop: install and try LectureLive

This guide targets **Windows 11, Intel Core i5-1035G1, 16 GB RAM, 64-bit Windows**.
Use the **Windows x64** app. The Snapdragon/ARM64 and Mac apps are different downloads.
The processor and memory are suitable for trying the existing Whisper Base CPU path;
caption delay and sustained classroom performance still need testing on your laptop.

## Download the complete app

1. Open the [Windows Intel CPU release](https://github.com/DionCroft/Polyglot/releases/tag/windows-v0.8.0b1).
2. Under **Assets**, download **LectureLive-Windows-x64-Beta-0.8.0b1.zip**.
   Do not select **Source code**. The complete app is about 760 MB to download.
3. Right-click the downloaded ZIP and choose **Extract All**. Allow at least **4 GB**
   of free space for the ZIP, extracted application and working files.
4. Move the extracted **LectureLive-x64-Beta** folder to a permanent place, for example
   **Documents\LectureLive**. Keep **_internal** and every other file beside the EXE.
5. Close any older LectureLive, then double-click **Launch-CPU.cmd** inside this folder.
   With file extensions hidden, look for **Launch-CPU**, type **Windows Command Script**.
   Run it from the extracted folder, not from inside the ZIP.
6. Wait for the initial model check, then follow the first test below.

No Python, Git, CUDA, NPU drivers, administrator installation or new model download
is needed for this complete app. University policy may still require IT approval.
The app is unsigned; if Windows blocks it, ask IT to approve the repository's build.
Do not disable antivirus. English and Chinese system voices are separate optional
Windows downloads if you want spoken translations.

Already using the source/setup version? Update the source, run **Setup-Beta.cmd**,
then use **Launch-CPU.cmd** from the source folder. Source setup needs internet and
about 15 GB of free space. It builds the same x64 app.

## Your first five-minute test

1. Plug the laptop into power and close heavy background apps. Use your teaching microphone.
2. Select it in LectureLive, click **Test microphone**, and check the meter.
   If access is denied, open **Settings → Privacy & security → Microphone** and allow
   microphone access, including access for desktop apps.
3. Check **Fast**, **Standard**, **CPU**, **Bilingual** and **English → 简体中文**.
   Leave spoken audio Off for this first caption test.
4. Click **Start lecture**. Say: “The project risk register records the probability
   and impact of each risk.” Pause briefly between complete sentences.
5. Check that English appears and Chinese follows. Open **Diagnostics**: the verified
   backend should say **Local CPU · Whisper Base int8**.
6. Try **Pause**, **Resume**, then **Mandarin → English** for a question such as
   “请解释一下项目的风险。” Wait for Listening before speaking after a switch.
7. Stop the lecture and open the saved transcript folder. Check both languages and
   their order. Preferences and transcripts live in **%LOCALAPPDATA%\LectureLive Beta**.

The CPU launcher selects Fast and CPU **before** checking models, even if the last
session saved GPU or NPU. It does not reset your microphone, language, lecture presets,
CO7000 vocabulary or voice choices. Audio still starts Off. The normal controls can
save CPU as your preference; you can change processing hardware while stopped.
A saved lecture preset can also change processing hardware, so check CPU after loading one.

## Speed and optional features

- Start with manual language selection and Standard recognition. Auto language detection
  and Careful recognition do extra work; test them after the basic captions keep up.
- The i5-1035G1 has four CPU cores/eight threads and Intel UHD graphics. It is an older
  Intel generation without the Intel NPU required by LectureLive's NPU option.
  **Do not run NPU preparation for this processor.**
- GPU/DirectML remains optional. Its speed and driver compatibility on this laptop have
  not been verified. CPU startup skips accelerator probing; it does not guarantee CPU
  will be faster than a working GPU. Keep CPU for the first rehearsal.
- The existing int8 Whisper Base, both translation models, offline captions, overlays,
  shortcuts, transcripts and vocabulary support are retained. No smaller or less accurate
  replacement model is introduced. Sixteen GB is reasonable for this configuration, but
  leave memory available for LectureLive while running your slides.
- For audio, use **Spoken audio → On demand**. It pauses listening while speaking; press
  Resume afterwards. Install missing Windows voices using the [spoken-audio guide](SPOKEN_AUDIO.md).
  Automatic spoken output requires headphones.
- Touch can operate the normal controls; this is the same desktop layout, not a new
  tablet interface. Physical touch/projector behavior still needs a rehearsal.

If captions fall increasingly behind or **Audio was lost** appears, stop and repeat
missing content. Close heavy apps, stay plugged in and use Fast / Standard / CPU.
The app cannot recover uncaptured audio. Finish with a **15–20 minute rehearsal with
PowerPoint and your projector**, checking caption delay, heat and any warnings.

## What has actually been tested?

This is **LectureLive 0.7.2b1, Intel CPU package revision 1**. The feature version is
unchanged; the extra launcher, startup selection and installation guide are new.
The package uses the existing Windows x64 speech/translation models. Our development
PC is a Snapdragon: x64 execution here is **Windows emulation**, not an i5 benchmark.
No claim is made that your laptop or its microphone/GPU/touchscreen has been tested.
See the [Intel package test report](evidence/intel-cpu-2026-10-12.md) for current results.

For feedback, send the selected and verified backend, whether delays grow, any warning,
and a sentence/caption example. Device ID and Windows Product ID are not needed.

Processor reference: [Intel i5-1035G1 specifications](https://www.intel.com/content/www/us/en/products/compare.html?productIds=196603).

## Optional student phone captions (0.8.0b1+)

Open **Student phones → Start sharing**, choose your classroom Wi-Fi/Ethernet address, and show the QR code. Students on the same trusted local network can scroll back through bilingual captions, search/copy and download the full text. Internet access and accounts are not needed. **Stop sharing** closes the link. Previous 0.7.x downloads do not include this feature. Follow the [phone caption guide](PHONE_CAPTIONS.md), including privacy and firewall/Wi-Fi advice, before teaching.
