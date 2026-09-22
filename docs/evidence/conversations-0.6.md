# Conversation beta 0.6.0b1 verification

This release adds manual English/Mandarin switching and offline Mandarin → English
translation. Mandarin is a beta feature; these checks do not certify classroom accuracy.

## English regression comparison

Baseline: `be7d66a`, before implementation. On the same Snapdragon X Elite computer,
36 English speech outputs matched exactly after the change: six existing public/synthetic
clips × Standard/Careful × CPU Base, QNN Base and QNN Small. All 40 existing authored
English translation cases also matched exactly, both raw output and glossary-adjusted captions.
These comparisons cover the selected fixtures, not every speaker or possible sentence.

## Automated behaviour and Windows source checks

- 92 tests passed on native Windows ARM64 and on the Windows x64 runtime under ARM emulation;
  two POSIX-only tests were skipped on each.
- New tests cover direction-specific prefixes, old preset defaults, new preset round trips,
  mixed-language TXT/SRT/VTT saving and journal recovery, pending Mandarin display, source-only
  saving after a translation failure, and Mandarin CPU recovery without English vocabulary hints.
- Threaded pipeline tests cover three turns in one transcript, monotonic IDs, draining a slow
  translation before switching, rejecting transition audio, paused switching, and a missing reverse
  model leaving English selected. Existing pause/stop, export failure and offline guards pass.
- The native Windows UI verified compact/main selector synchronisation, a Mandarin preset,
  switching during a lecture, paused switching, overlay labels, minimum-window controls,
  a real Mandarin WAV lecture and saved English translations. No microphone was recorded.

## Mandarin speech smoke samples

Three public FLEURS Mandarin test recordings (32.52 seconds total) were selected as the first
three WAV entries in the pinned archive. References and original/PCM-converted hashes are in
`tests/fixtures/mandarin-cases.json`; [attribution](../licenses/fleurs-NOTICE.md).
These are unrelated read-speech samples, not student questions or representative classroom audio.
Punctuation/space-insensitive character counts retain numbers and letters without semantic normalisation.

| Windows ARM64 backend | Character edits / reference characters | Inference time per complete clip |
|---|---|---|
| Whisper Base CPU | 8 / 81 | 0.425–0.486 s |
| Whisper Base Qualcomm NPU | 10 / 81 | 0.170–0.223 s |
| Whisper Small Qualcomm NPU | 15 / 81 | 0.431–0.585 s |

Errors included 篇章 becoming a homophone and incorrect years in the bridge example. Small did
not outperform Base on this tiny sample. This is insufficient evidence to rank models generally.
Careful and silence checks also ran. Each backend returned to its exact initial English JFK
transcription after switching Mandarin → English. x64 CPU and Adreno DirectML checks also passed
under ARM emulation; they do not establish behaviour on physical Intel/AMD hardware.

## Reverse translation and memory

Eight authored Mandarin questions produced English locally. They include project risk, robotics,
negation, dates, a voltage and a formula. No qualified bilingual review has been completed.
Examples: 请再解释一次。 → “Please explain again.”; 这个电路的电压是五伏。 →
“The voltage of this circuit is five volts.” The project-management term 关键路径 became
“key route”; 安全问题 became “security issues”. Domain meaning therefore needs review.

Additional model inventory: **172,673,277 bytes** in eight files, identical across all three
platform manifests. Existing English files retain their original pinned hashes.
On the native ARM64 development run, reverse-model load plus warm-up took **0.633 s**;
process RSS increased by **553,062,400 bytes / 527.4 MiB**. Eight translation calls took
**0.076–0.155 s** after warm-up. These are single-run, translation-only observations, not
end-to-end caption latency. Speech recognition, VAD boundaries and queued work add time.
Model sessions remain cached; different hosts and memory pressure may change these figures.

## Platform and release status

Both Windows executables were rebuilt from `2370b05`. Packaged English inference,
Mandarin/reverse translation, native UI switching and transcript checks passed on ARM64
and under x64 emulation. All 42 ARM64 and 29 x64 bundled model files matched their pinned
hashes; each includes the eight reverse-translation assets. Portable ZIPs are prepared
with per-file SHA-256 verification.

Native Apple Silicon [build 35744753297](https://github.com/DionCroft/Polyglot/actions/runs/35744753297)
passed on **macOS 14.8.9 ARM64**, using the same `2370b05` application code. **94 tests passed**
with no skips. The packaged `.app` passed English CPU/Core ML inference, the nine Mandarin
speech cases, reverse translation, English language round trips, native Cocoa controls,
live/paused switching, mixed transcript saving, CO7000 presets, overlay click-through flags,
shortcut registration, linked microphone permission handling, architecture and signature checks.
Microphone permission delivery and global shortcut delivery to a real lecturer were not tested.

| Hosted Apple Silicon backend | Character edits / reference characters | Inference time per complete Mandarin clip |
|---|---|---|
| Whisper Base CPU | 7 / 81 | 1.215–1.301 s |
| Whisper Base Core ML encoder + CPU decoder | 10 / 81 | 1.541–1.855 s |
| Whisper Small CPU | 14 / 81 | 2.843–3.368 s |

Core ML Fast executed successfully, but was slower than CPU on these complete clips.
Explicit Small Core ML again exceeded the three-minute worker limit and recovered on CPU;
Balanced Automatic already uses CPU. These hosted-runner results do not predict M2 classroom
performance or identify whether Core ML ran on a GPU or Neural Engine.
The reverse-model load/warm-up took **1.274 s** and added **541,409,280 bytes / 516.3 MiB**
to process RSS. Eight warmed translations took **0.189–0.380 s**. Native-speaker review
remains pending; the nine non-empty Chinese outputs are functional checks, not accuracy passes.

Native evidence: [94-test report](macos-0.6-macos-pytest.xml),
[English and acceleration](macos-0.6-macos-packaged.json),
[Mandarin and reverse translation](macos-0.6-macos-conversations.json),
[conversation controls/exports](macos-0.6-macos-conversation-ui.json),
[Cocoa integration](macos-0.6-macos-ui.json).

Physical M2 microphone/permissions, projector/full-screen delivery, global shortcut delivery,
thermal/battery behaviour and physical Intel/AMD GPU/NPU acceptance remain pending.
OS-level network checks for native libraries and long classroom sessions remain pending.
Python runtime socket creation stays blocked during every app/self-test launch.

Raw evidence: [exact English before/after](conversations-0.6-english-regression.json),
[ARM64 model checks](packaged-arm64-conversations-0.6.json),
[ARM64 controls and exports](packaged-arm64-conversation-ui-0.6.json),
[x64 model checks](packaged-x64-conversations-0.6.json),
[x64 controls and exports](packaged-x64-conversation-ui-0.6.json),
[bundled model hashes](packaged-models-0.6.json).
The [overlay screenshot](conversation-overlay-0.6.png) uses an explicit UI text fixture;
it is a layout check, not an audio accuracy result.

## Installable builds

| Package | Bytes | Availability |
|---|---|---|
| Windows ARM64 portable ZIP | 1,526,351,003 | `recovery/LectureLive-Windows-ARM64-Beta-0.6.0b1.zip` in the maintainer workspace |
| Windows x64 portable ZIP | 747,513,708 | `recovery/LectureLive-Windows-x64-Beta-0.6.0b1.zip` in the maintainer workspace |
| Apple Silicon DMG | 1,220,030,579 | [Public Mac beta release](https://github.com/DionCroft/Polyglot/releases/tag/macos-v0.6.0b1) |
| Apple Silicon ZIP | 1,172,642,186 | Same public release |

The [package record](conversations-0.6-packages.json) contains exact SHA-256 hashes.
Windows packaging verified each archived member against its source hash (530 ARM64 files,
1,307 x64 files). Both executables were tested before packaging. Their documentation was
refreshed after native Mac validation; executable code is unchanged from `2370b05`.
Windows archives are local deliverables, not GitHub release assets; colleagues can use
the beginner `Setup.cmd` route or receive a complete portable ZIP from the maintainer.

The [Mac publisher](https://github.com/DionCroft/Polyglot/actions/runs/35746510015)
verified both native artifact checksums before publication; the public GitHub asset digests
match `SHA256SUMS.txt`. Release tag `macos-v0.6.0b1` points to tested commit `2370b05`.
Minimum macOS is 14, Apple Silicon only. The app is ad-hoc signed, not notarised.
Physical M2 hardware, native-speaker classroom recordings, physical Intel/AMD acceleration
and application-scoped OS network tracing remain outstanding as described above.

## Reproduce

Setup the app normally, then fetch developer fixtures using
`python -m scripts.setup_assets --fixtures` and `python -m scripts.prepare_conversation_fixtures`.
With the platform's private runtime, run `python -m pytest -q`, then:

```text
python -m app.main --conversation-self-test tests/fixtures tests/artifacts/conversations.json
python -m app.main --conversation-ui-test tests/fixtures tests/artifacts/conversation-ui.json
```

Set `LECTURELIVE_DATA` to an isolated test folder before GUI tests; they save test preferences
and transcripts. Packaged executables accept the same switches. Never test against a live
lecture session. For native-speaker validation, obtain consented English and Mandarin recordings
of real lecturer–student turns, with exact transcripts, technical terms, names, numbers, negation,
short questions and realistic microphone distances. Include mixed-language examples to document limits.
