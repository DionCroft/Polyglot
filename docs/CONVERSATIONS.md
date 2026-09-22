# English and Mandarin conversations

LectureLive uses Whisper and local translation for **English → Simplified Chinese** and
**Mandarin Chinese → English**. Internet is needed only for initial setup. English remains the
default, with the same models, Standard/Careful choices and vocabulary settings.

## A lecturer and student conversation

1. Select your teaching microphone, test it, and leave **Bilingual** selected.
2. Under **Who is speaking?**, choose **English → 简体中文**. Click **Start lecture**.
3. Teach normally. For example: “The critical path determines the shortest project duration.”
4. When a student has a question, finish your sentence and choose **Mandarin 普通话 → English**.
   The same selector is available in **Teaching controls** alongside your slides.
5. Wait for **Listening** before the student speaks. Previously captured speech is finished and
   saved first. Audio spoken during **Switching language…** is not captured.
6. The student can ask: “请再解释一次。” (“Please explain again.”)
7. Choose **English → 简体中文**, wait for **Listening**, then answer in English.
8. Click **Stop lecture** at the end and wait for finishing to complete.

The caption panel labels **spoken** text and **translation**. English and Simplified Chinese
remain in their usual colours. Whisper's Mandarin transcription is normalised to Simplified
Chinese. **English** and **Chinese** display modes still select the language you want to show;
use **Bilingual** to see both. Only one person should speak at a time.

Switching keeps the microphone, lecture title, projector, shortcuts and transcript folder.
Switching while paused keeps the lecture paused. A missing translation model leaves the previous
speaking language selected and shows a warning. Settings and saved presets remember the speaking
language; presets from older versions continue to select English.

## Vocabulary and accuracy

English subject glossaries, custom vocabulary and CO7000 weekly lists remain available for
English turns. They are retained when you switch to Mandarin, but are **not applied to Mandarin
speech or Mandarin → English translation**. This avoids feeding English-only pronunciation
corrections and translation rules into a Chinese question. Mandarin custom hints and a reviewed
reverse CO7000 glossary are not included in this release. Careful recognition can still be tried.

Rehearse actual questions. For example, the reverse translation model may render **关键路径** as
“key route” rather than the project-management term “critical path”. It can also make errors
with names, numbers, negation and mixed English/Chinese sentences. These need bilingual review.

## Automatic switching

In the same selector, choose **Auto · English ↔ Mandarin** for hands-free turns. Keep **Bilingual**
selected. Finish speaking, pause briefly, and let the next speaker use the microphone. Auto
detects each phrase locally and chooses its translation direction without pausing capture.
Manual English/Mandarin choices remain available; only changing the selector manually has
the switching pause described above.

If **Language unclear** appears, choose the language manually and repeat the sentence. Very short
replies and mixed/overlapping speech are harder to detect. Uncertain phrases are withheld and
marked **[Not transcribed]** in the bilingual transcript/VTT and journal; single-language
files omit them. The audio is not stored for later recovery. [Auto guide and limits](AUTO_LANGUAGE.md).

## Setup, memory and speed

Windows setup and the Mac app include an additional **172,673,277 bytes (172.7 MB / 164.7 MiB)**
of pinned, checksum-verified Mandarin → English translation assets. Existing English assets are
unchanged. Windows users update using **Setup.cmd**; Mac users install the new conversation build.
Older Mac beta 0.5.0b1 does not include this feature.

The extra translation model loads on the first Mandarin turn (or when Auto prepares both directions) and is retained until the speech
model bundle is replaced or the app closes, so subsequent switches can reuse it. Its download
size is not its RAM requirement: model sessions, working buffers and decoder caches need extra
memory. Translation runs on CPU in both directions. Whisper uses the existing platform
acceleration and CPU fallback; a failed accelerator retains the selected speaking language.
Balanced and Careful can increase latency. Auto adds a detection pass and may wait for more speech.
Wait for **Listening** after changing the selector manually.

On the Snapdragon test machine, loading and warming the reverse model took about **0.63 s**
and increased process RAM by about **527 MiB**. Eight short questions took **0.076–0.155 s**
each to translate after warm-up. These are translation-only timings, not microphone-to-caption
latency or Mac/Intel/AMD promises. Segmentation, speech recognition and any queued work add delay.
[Detailed verification and limits](evidence/conversations-0.6.md).

On the hosted Apple Silicon test runner, reverse-model load/warm-up took **1.27 s**,
added about **516 MiB** of RAM, and warmed translations took **0.19–0.38 s**.
CPU recognition was faster than Core ML on these three short test recordings;
try **Processing hardware → CPU** if Automatic feels slower on your Mac.
This is not a physical M2 benchmark. The English recognition settings are unchanged.

## Saved conversations

**Save text transcripts and subtitles** is on by default. Open **Diagnostics → Open transcripts**.
One lecture folder contains the whole conversation:

- **English Transcript.txt / English.srt:** English speech and English translations of Mandarin.
- **Chinese Transcript.txt / Chinese.srt:** Mandarin speech and Chinese translations of English.
- **Bilingual Transcript.txt:** both languages, labelled as spoken or translated.
- **Bilingual.vtt:** both languages for subtitle players.
- **events.jsonl:** a recoverable journal with each turn's source language and timestamps.

If translation fails, the recognised speech is still saved. Microphone audio is never recorded.
The journal recovery tool can read both older English-only journals and new mixed conversations.

See the [README](https://github.com/DionCroft/Polyglot#readme) for installation and the
[speech-recognition guide](SPEECH_RECOGNITION.md) for existing accent comparisons.
