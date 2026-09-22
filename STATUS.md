# LectureLive — STATUS

Updated 2026-09-23. Automatic English/Mandarin turns added to the main application.
Production classroom acceptance remains open.

## Auto conversations 0.7.0b1

- **Auto · English ↔ Mandarin** is an optional choice in the main app and Teaching controls. Existing English/manual settings remain unchanged. Whisper detects each phrase offline; both translation directions are prepared before Auto starts.
- Uncertain phrases are withheld, with an on-screen repeat instruction and a bilingual transcript marker. Provisional text is retracted if the final language check disagrees. Manual override remains available.
- 107 regression tests pass per Windows runtime (two POSIX-only skips). Both rebuilt Windows editions pass manual/Auto inference, UI, exports and model-integrity checks. Manual English exactly preserves 36 speech and 40 translation outputs.
- Expanded checks use 148 recordings with short/noisy variants. A level-adjusted 10-minute QNN replay completed 133 translated pairs and 34 automatic switches with no queue drops, but withheld 34 short phrases. Failed uneven-level/noise and overloaded emulated-CPU checks are also recorded. These results do not certify classroom word/translation accuracy.
- [Using Auto](docs/AUTO_LANGUAGE.md) · [Current test/build evidence and remaining checks](docs/evidence/auto-language-0.7.md).

## Previous conversation beta 0.6.0b1

- Manually switch **Who is speaking?** between English → 简体中文 and Mandarin 普通话 → English, including during a lecture. Finish speaking, change the selector, and wait for Listening before the next speaker starts.
- Whisper remains the recogniser. Both offline translation models are included in setup and packaging; the new Mandarin → English files add 172.7 MB. Source and translation have explicit labels and share one mixed-language transcript session.
- Existing English defaults, recognition settings and models are preserved. The selected regression fixtures produced exactly the same 36 English speech outputs and 40 English translation results. English vocabulary/CO7000 guidance remains English-only.
- 92 tests pass on each Windows runtime, with two POSIX-only skips. Mandarin model and UI smoke tests pass on CPU, Qualcomm NPU and emulated x64/DirectML. Both rebuilt Windows executables pass English/Mandarin inference, switching and transcript checks; all bundled model hashes and portable ZIP contents are verified. Native macOS 14.8.9 ARM64 passes 94 tests plus packaged English/Mandarin, switching, exports and Cocoa integration checks; see the evidence report.
- Automatic language detection is not enabled: short questions and mixed-language speech have not been validated. Mandarin recognition and technical translation require native-speaker classroom evaluation.
- [Conversation instructions](docs/CONVERSATIONS.md) · [Tests, measured memory/speed and limitations](docs/evidence/conversations-0.6.md).

## macOS Apple Silicon beta 0.5.0b1

- Native ARM64 `.app`, DMG and ZIP for macOS 14+, with bundled offline models and the existing recognition, translation, presets and CO7000 support.
- Core Audio, user-initiated microphone permissions, Carbon shortcuts and Cocoa overlays. Core ML Fast encoder with CPU fallback; Balanced Automatic uses CPU after Small compilation timed out on native CI.
- 83 tests pass on native macOS; packaged inference, Cocoa UI, static microphone permission integration, signing and architecture checks pass. Windows: 81 tests pass per runtime, both rebuilt executables and UI regressions pass.
- Physical M2 classroom tests and both lecturers' accent recordings remain outstanding. Ad-hoc signed; no Developer ID/notarisation credentials were available. Core ML execution was verified, individual GPU/Neural Engine execution was not.
- [Install the Mac beta](docs/MACOS.md) · [Native measurements and evidence](docs/evidence/macos-2026-09-21.md) · [Platform review and remaining M2 checks](docs/MACOS_PORT.md).

## Optional speech recognition (ARM64 0.3.2 / x64 beta 0.4.0b2)

- Standard with vocabulary guidance off retains the previous decoder and reproduced all
  48 baseline transcripts on each of three backends. Both new options default to off.
- Careful compares up to three paths for finished phrases; explicit vocabulary can now
  guide recognition using the existing local tokenizer. Settings are saved in presets and
  preserved when acceleration fails and the same phrase is retried on CPU.
- On a small public sample, Small/Balanced Careful reduced Indian-English WER from
  4.23% to 3.17% and Scottish-English WER from 2.70% to 1.62%. Base results were mixed;
  irrelevant vocabulary sometimes worsened recognition. Neither lecturer was recorded.
- 69 unit tests pass on both Windows runtimes. Native UI and rebuilt executable self-tests
  pass, including guided CPU/QNN/GPU speech and bundled course vocabulary. No new model,
  package or hardware requirement was introduced. Physical Intel/AMD tests remain open.
- CO7000 includes 12 short weekly hint lists, a 92-term project-management glossary,
  conservative acronym/spelling corrections and an in-app course selector. A synthetic
  six-clip check corrected PRINCE2 with Week 6 hints; lecturer validation is still pending.
- Beginner [speech guide](docs/SPEECH_RECOGNITION.md),
  [full comparison and limits](docs/evidence/speech-recognition-2026-09-21.md).

## Previous Windows x64 beta (0.4.0b1), ARM64 maintenance (0.3.1)

- Separate x64 runtime, immutable model/dependency manifests, installer selection, launcher,
  preferences and portable package. Source setup automatically selects the Windows architecture.
- CPU speech, DirectML GPU speech encoding, experimental Windows ML Intel/AMD NPU adapters.
  CPU remains responsible for decoding, translation and voice detection in the x64 beta.
- NPU provider preparation is an explicit online setup step. Lectures register only prepared,
  fingerprint-checked local libraries and never call the Windows ML download catalog.
- GPU/NPU encoder runs in a private named-pipe worker with bounded initialization/inference.
  Warm-up execution must prove the requested provider ran without CPU fallback. Failure during
  a lecture retries the same phrase on CPU. Settings identify the actual verified backend.
- Beginner [Windows beta guide](docs/WINDOWS_BETA.md), in-app help topic, and separate launchers.

**Hardware scope:** all development checks used a Snapdragon X Elite Surface. x64 CPU ran
under Windows ARM emulation; DirectML actually executed on its Adreno GPU. This is **not**
physical Intel/AMD validation. Intel/AMD GPU compatibility, Intel/AMD NPU model acceptance,
long sessions, native-library network audits and classroom use on those platforms remain pending.

55 tests pass on each architecture, including strict provider trace checks, GPU failure retry,
unavailable NPU fallback and cache disposal. Public JFK audio produced equivalent CPU/GPU
transcripts (punctuation differed). One development run took about 0.78 s on x64 CPU and
0.47 s with GPU encoding after warm-up; this is a single-machine observation, not a benchmark
or a promise of Intel/AMD performance. The native beta UI completed a synthetic lecture without
microphone capture. Pinned x64 dependencies/models passed offline verification and pip check.
See [beta verification evidence](docs/evidence/beta-0.4.md) for packaged checks and limits.

## Interface and installation polish (0.3)

- Numbered microphone/caption/lecture sections; optional presets and vocabulary; keyboard
  focus outlines, accessible input labels, smaller-window support and a custom app icon.
- In-app quick-start, user and installation guides, readable without a Markdown editor.
- About page and README include the professional details supplied by Dr Dion Miroy
  Mariyanayagam, with selectable text, an email link and a copy-contact button.
- Double-click Setup.cmd checks the PC/folder, runs pinned setup/build, writes setup.log,
  and creates a Start menu shortcut. Launch.cmd starts the resulting application.
- Beginner README distinguishes the GitHub source ZIP from a ready-to-run application
  folder; includes requirements, first use, repair, updates and removal instructions.

Verification: 49 regression tests pass (`pytest-0.3.txt`). Native layout/contact/help
checks pass (`polish-0.3.json`); Setup.cmd completes with verified cached assets
(`setup-0.3.json`), and unsupported-PC/incomplete-folder checks pass. The rebuilt
executable passes NPU/CPU/translation self-tests and the native About/Quick start
check (`packaged-self-test-0.3.json`, `packaged-ui-0.3.json`). Fresh online setup
was not repeated; the pinned bootstrap has historical 0.2 evidence.

The existing 0.2 inference and stress results are historical evidence. Physical
classroom acceptance remains pending.

## Implemented improvements

1. **Translation:** score-based beam termination retains the obstacle relationship
   omitted by the baseline; source-gated technical terminology improvements; 40-case
   authored evaluation corpus and original-vs-current comparison. Concept checks
   improve from 30/40 to 37/40 on development cases. Qualified bilingual review and
   a separate real-lecturer evaluation remain necessary.
2. **Reliability:** Stop drains accepted audio and finishes the last utterance before
   translation/export closure. Pause discards unfinished private asides. Export errors
   detach the writer and contain cleanup failures; journal recovery preserves originals.
   A runtime NPU failure retries the same phrase on CPU. Explicit reconnect/retry UI.
3. **Caption continuity:** completed bilingual pair retained while new English waits;
   confirmed provisional prefixes; sentence-aware short pauses; long-caption fitting
   and shrinking; explicit unavailable-translation state. Latency includes endpoint delay.
4. **Teaching workflow:** local named presets and saved vocabulary/title; real microphone
   level check; projector preview; compact floating controls; configurable shortcuts;
   Start/Finish/Pause remain visible outside scrolling preparation controls.
5. **Reproducibility:** pinned model/dependency/fixture manifests with byte counts and
   SHA-256; range-aware temporary downloads, safe extraction and repair; one-command
   ARM64 bootstrap; offline recovery; one warmed model bundle reused across sessions.
6. **Acceptance tooling:** expanded failure/privacy/setup/workflow regressions; 24 noisy
   synthetic speech cases, silence check, microphone capture and extended replay tooling.
   Microphone availability is assumed for the lecture. Physical room/projector checks
   and full teaching-length battery/thermal rehearsal remain separate acceptance items.

## Current architecture

Microphone → bounded queue → Silero VAD → Whisper QNN/CPU → stable caption state →
local OPUS translation → Qt overlay and incremental exports. All inference stays local.
Model readiness verifies encoder AND decoder, translation and VAD away from the UI;
a per-window model store keeps the warmed bundle for the active speech profile.

Native CPython 3.11.9 ARM64; PySide6 6.11.2; ORT 1.29.0; QNN plugin 2.5.0.
Fast is Whisper Base FP16 NPU; Balanced is Whisper Small FP16 NPU. Separate Base int8
CPU graphs provide recovery. Accuracy remains unavailable. M2M100 remains an excluded
experiment. No hosted inference, cloud fallback or microphone recording is introduced.

## Verification evidence

- Unit suite: expanded from 16 to 49 tests; all passed in 0.53 s (`pytest-0.2.txt`).
- `docs/evidence/translation-expanded.json`: 40 development cases and latency distributions.
- `docs/evidence/translation-decoding-comparison.json`: original and revised beam outputs.
- `docs/evidence/workflow-verification.json`: actual native UI, presets, microphone test,
  configurable shortcuts, compact controls, long-caption fitting and retry workflow.
- `docs/evidence/fresh-setup-verification.json`: fresh offline runtime bootstrap and
  archive extraction, followed by real NPU/CPU/translation self-tests.
- `docs/evidence/online-setup-check.json`: actual pinned HTTPS download/checksum verification.
- `docs/evidence/classroom-audio-check.json`: real microphone metrics and synthetic noise checks.
- `docs/evidence/classroom-stress-15min.json`: 903 s at 20 dB noise, 161 bilingual
  captions, zero drops/skips, bilingual p95 1.024 s, clean worker shutdown.
- `docs/evidence/packaged-self-test-0.2.json`: rebuilt ARM64 executable passes both
  NPU profiles, CPU recovery, translation and VAD readiness. Native UI reaches Ready
  and displays version 0.2; see `packaged-ui-0.2.json`.
- `docs/evidence/pipeline.json`: final source replay yields all three bilingual
  sentences and closes every worker after the last runtime refinements.
- Recovery ZIP integrity and relocated restore results are recorded separately under
  `recovery/`; original-release PowerPoint checks remain historical evidence.

## Remaining acceptance and limitations

- Translation concept checks are heuristics; they do not certify full meaning. Overfitting
  terminology and ambiguous technical language still need bilingual review.
- Physical Airplane Mode and application-scoped native packet/ETW audit are pending.
  Python socket guards and process socket samples are not equivalent to OS traffic proof.
- Actual projector hot-unplug, physical microphone unplug/reconnect and real-room
  speech accuracy are pending. The user will have a microphone; this is not a hardware
  procurement blocker.
- Multi-hour lecture, sleep/resume and battery/thermal rehearsal remain pending.
- Native inference remains in-process. A driver call that never returns can delay shutdown;
  status remains responsive but Python cannot safely kill that native thread.
- The build is unsigned. Balanced is FP16, not quantized Small. Accuracy is unavailable.

## Next step

Perform the physical and bilingual rehearsal in `docs/ACCEPTANCE_TESTS.md` before
calling the application production classroom-approved.
