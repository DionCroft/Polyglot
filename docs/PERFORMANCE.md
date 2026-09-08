# Performance measurements

Hardware: Snapdragon X1E80100, Windows 11 build 26200 (25H2), ARM64.
These are local measurements, not latency guarantees.

| Test | Observed time |
|---|---:|
| Whisper Base NPU, public 11 s JFK sample | 0.242 s |
| Whisper Small NPU, same sample | 0.543 s |
| Whisper Base int8 ARM64 CPU, same sample | 0.633 s |
| Original greedy OPUS translation, short technical sentence | 0.050 s |
| Four-beam OPUS, three technical sentences, before final language-prefix adjustment | 0.061–0.103 s |

Strict-QNN session configuration disabled CPU fallback; ONNX profiling showed
`QNNExecutionProvider` kernels. Provider enumeration alone was not used as proof.
The decoder's exported ABI is FP16 with static 200-token cache length. The tested
Balanced artifact is FP16 Small, not an int8 Small model; this difference from the
preferred quantized profile is explicit.

In version 0.2 provisional requests occur about every 0.768 seconds, with visible text
requiring prefix agreement across two hypotheses. Final boundaries use 576 ms of
silence, shortened to 320 ms when a sentence-ending hypothesis is available after
sufficient speech. Pre-roll is 256 ms; the maximum window remains 9.6 seconds.

Final caption latency now references the last voiced sample, so VAD endpoint delay
is included along with downstream inference. Provisional latency references its latest
sample endpoint. Diagnostics report rolling p95 values over up to 2048 observations;
these are not word-aligned latency measurements. Older reports used segment endpoints
and should not be compared directly with the new latency numbers.

See `evidence/first-inference.json`, `pipeline.json`, `stress-test.json` (once complete)
and `technical-benchmark.json`. The ten-minute stress test uses a real-time WAV replay;
it is not a substitute for a multi-hour thermal test with a lecturer and projector.
NPU utilization percentage and thermal sensors were not instrumented.

Translation quality is a known limitation: the old OPUS model can omit details and
mistranslate domain terms. Source-conditioned glossary corrections are narrow. A
bilingual lecturer must review the technical sample set before production use.

## Final packaged and regression evidence

`evidence/packaged-self-test.json`: all startup checks passed inside LectureLive.exe;
Base NPU 0.297 s, Small NPU 0.599 s, CPU 0.823 s, short translation 0.107 s.
`stress-10min.json`: 107 bilingual pairs, zero drops, queue maxima audio 1 / ASR 0 /
translation 0 in samples; final RSS 1365.7 MB; no worker threads left alive.
`stress-90s.json`: 17 bilingual pairs from the final pipeline refinements, no drops.

`technical-benchmark.json` records all eight requested example sentences. WER is a
simple word edit distance and counts equivalent I-squared-C / I2C and UK/US spelling
variants as differences; it is not a human-rated accuracy score. That baseline robot sentence omitted a relationship. Version 0.2 preserves it in the
decoder comparison; broader human semantic acceptance remains open.
M2M100 took roughly 0.95–2.21 s and introduced other term errors; it is not shipped.

## Version 0.2 evaluation

The 40-case development comparison improved from 30 to 37 automatic concept checks.
Measured translation p95 was about 0.09 seconds in that run. This is neither a human
accuracy percentage nor a held-out evaluation; see TRANSLATION_EVALUATION.md.

`evidence/workflow-verification.json` records model-bundle reuse and actual UI flows.
`evidence/fresh-setup-verification.json` records a new offline runtime/model installation.
`evidence/classroom-audio-check.json` contains 24 synthetic speech/noise outputs and
microphone-level diagnostics. `classroom-stress-15min.json` records the sustained noisy
replay: 903 seconds, 161 bilingual captions, zero audio/phrase drops or translation
skips. Final rolling bilingual p95 was 1.024 s (English 0.779 s). RSS ranged from
1370.9 to 1427.5 MB and ended at 1375.8 MB; all worker threads exited. Some development checks and setup I/O ran concurrently; timing
is observed performance under that load, not a guarantee.

The final 0.2 executable self-test measured Fast NPU 0.229 s, Balanced NPU
0.517 s, CPU 0.607 s and short translation 0.062 s. All startup checks passed.
A short final source replay verified the callback/privacy and unavailable-caption
refinements made after the extended replay started; all three pairs completed.
