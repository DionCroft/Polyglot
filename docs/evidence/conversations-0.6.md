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
with per-file SHA-256 verification. Native Apple Silicon CI results follow when completed.
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
