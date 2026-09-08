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

English provisional requests occur approximately every 1.216 seconds of speech.
Final phrases use 576 ms of silence, 256 ms pre-roll and a 9.6-second maximum window.
The displayed English latency metric measures time after the audio chunk endpoint;
it does not include all speech duration. Bilingual latency has the same endpoint
reference. Pause-boundary detection adds its own delay. These are not word-aligned
latencies or formal WER/BLEU benchmarks.

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
variants as differences; it is not a human-rated accuracy score. The robot sentence's
Chinese output omits a relationship, so semantic acceptance is still open.
M2M100 took roughly 0.95–2.21 s and introduced other term errors; it is not shipped.
