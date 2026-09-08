# LectureLive 0.2 — STATUS

Updated 2026-09-09. Six-part improvement milestone implemented and native executable verified.
Production classroom acceptance remains open.

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
