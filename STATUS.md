# LectureLive — STATUS

Updated 2026-09-08. **Working native ARM64 development build. Production acceptance remains open.**

## Implemented and exercised

- Native CPython 3.11.9 ARM64, Qt/PySide6 6.11.2, ORT 1.29.0 + QNN 2.5.0.
- Fast (Whisper Base) and default Balanced (Whisper Small FP16) actually run on the
  Snapdragon X Elite NPU. Strict-provider ONNX profiling contains QNN kernels.
- Separate Whisper Base int8 CPU recovery; simulated unavailable NPU tested.
- Surface WASAPI microphone capture with shared Windows 48 kHz → 16 kHz conversion.
- Local Silero VAD, bounded worker queues, provisional English, final-phrase translation,
  retained stable pairs, source-conditioned glossary corrections and vocabulary spelling.
- Local OPUS-MT four-beam translation with explicit Mandarin Simplified prefix and OpenCC.
- Native Qt control panel and overlay: transparency, topmost, non-activation, click-through,
  drag/resize, monitor choice, modes, font/colour/spacing/opacity and local preferences.
- Global lock shortcut tested while PowerPoint had focus. A click through the locked
  caption rectangle advanced a real PowerPoint slideshow; captions remained visible.
- Text exports and recovery journal; bounded pending translation results maintain cue order.
- Runtime Python networking guard; ONNX telemetry explicitly disabled; static audit clean.
- Missing translation: English continues. Device-open failure and worker cleanup tested.
- Background startup inference checks; packaged EXE self-test and recovery scripts.
- Native PyInstaller EXE built; PE machine 0xAA64. Packaged self-test passed all NPU/CPU/VAD/translation checks; its first UI run loaded Small on the
  NPU and captured live microphone input; closing joined its workers.
- 16 core regression tests and Qt integration checks pass (see evidence).

## Measured performance

Public 11-second speech sample: Base NPU 0.242 s, Small NPU 0.543 s,
Base ARM64 CPU 0.633 s. These are observed individual runs, not guarantees.

Ten-minute real-time technical replay: 107 bilingual pairs;
zero dropped audio/phrases/translation skips; all workers joined. After the first
minute RSS ranged 1365.3–1423.6 MB,
ending 1365.7 MB. Sampled audio queue peaked at
1, ASR at 0,
translation at 0. All sampled process
TCP/UDP connection counts were zero. See `docs/evidence/stress-10min.json`.
This run preceded the final language-prefix and subtitle-order refinements; the final
source has a separate shorter regression run and packaged inference test.

## Current architecture

Audio → bounded queue → Silero VAD → Whisper QNN/CPU worker → explicit stabiliser →
bounded local translation worker → caption state/Qt overlay + incremental UTF-8 exports.
Setup networking lives only in scripts. No hosted inference or cloud fallback exists.
The experimental M2M100 adapter/model remains in development for comparison but is
excluded from the teaching bundle: it was slower and not consistently more accurate.

## Known issues / acceptance still required

- Physical Airplane Mode test and application-scoped native packet/ETW trace are pending.
  Socket snapshots and a Python guard do not prove every native DLL makes no requests.
- Only one display was available. Real projector selection/disconnection remains pending.
- Physical USB/Bluetooth microphone unplug/reconnect tests remain pending.
- Multi-hour thermal/battery and real lecturer speech accuracy tests remain pending.
- OPUS translation can omit detail or mistranslate terminology. Eight actual comparison
  sentences are saved in `docs/evidence/translation-comparison.json`; qualified bilingual
  review is still required. Glossaries correct observed terms, not arbitrary mistranslations.
- Balanced uses the verified FP16 Small artifact; no quantized Small claim is made.
- Accuracy profile is visibly unavailable. No untested large model is advertised as ready.
- Build is unsigned. Audio recording is intentionally not implemented. Hotkeys are fixed.

## Next implementation / validation step

Review technical translations with the lecturer, improve or replace the local translator
where necessary, then complete the physical acceptance checklist. Do not call the project
complete or travel-ready until `docs/ACCEPTANCE_TESTS.md` is fully signed off.

Final-source 90-second regression: 17 bilingual pairs, zero drops, all workers joined.
The packaged self-test measured Base NPU 0.297 s, Small NPU 0.599 s, and CPU 0.823 s
on the 11-second sample. Different background load explains variation; no hard latency
guarantee is claimed.

The full eight-sentence synthetic speech benchmark is in
`docs/evidence/technical-benchmark.json`. FreeRTOS split-word recognition is handled
by an explicit selected-glossary alias. The robotics translation still omits the
obstacle relationship; this is an unresolved quality issue, not a passing semantic test.

Release candidate verification: the final rebuilt executable passed its own local
self-test (`docs/evidence/packaged-self-test-final.json`), and 16 regression tests pass.
Recovery archive generation and CRC/checksum validation are recorded separately.

Recovery validation passed: a fresh extraction matched all 634 payload checksums,
restored the ARM64 development runtime from included wheels with no index access,
passed `pip check`, and ran NPU/CPU/VAD/translation self-tests from the relocated
executable. See `docs/evidence/recovery-verification.json`.
