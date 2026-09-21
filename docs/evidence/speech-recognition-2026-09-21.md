# Speech recognition verification — 2026-09-21

Versions: ARM64 **0.3.2**, x64 beta **0.4.0b2**. Testing used a Snapdragon X Elite
Surface running Windows 11 ARM64. Paired ASR runs used native ARM64 Python.
Separate x64 UI and accelerator checks used Windows ARM emulation and the Adreno GPU.
Physical Intel/AMD CPU, GPU and NPU verification remains pending.

## Selection and method

No recordings from either actual lecturer were available. Public CMU ARCTIC speakers
KSP (Indian English) and AWB (Scottish English) are limited proxies. Rows 100–119 for
each speaker were selected consecutively before inference; no clips were dropped after
seeing results. Eight pre-existing synthetic electronics clips supplied a technical check.
The two public speakers have different read passages. Every setting was paired on the
same recording, but differences between speakers must not be interpreted as accent effects.

Dataset revision, reference text, source row and SHA-256 are in
[the fixture manifest](../../tests/fixtures/accent-cases.json). The public mirror is
[MikhailT/cmu-arctic](https://huggingface.co/datasets/MikhailT/cmu-arctic) (declared MIT).
[CMU speaker provenance](https://www.cs.cmu.edu/~pmuthuku/publications/thesis/Prasanna_thesis.pdf)
identifies the speakers. Audio is not committed or included in the application.

Baseline source was commit `36208f6c0d308a9e96fc594531e7b44396af315a`.
Word error rate (WER) is aggregate substitutions + deletions + insertions divided by
reference word count, after case/punctuation normalisation. These are raw ASR transcripts,
before glossary spelling correction. British/American spelling and technical tokenisation
differences still count as errors. See [the full per-clip outputs](speech-recognition-2026-09-21.json).

## Results

| Backend / setting | Indian-English (189 words) | Scottish-English (185 words) | Synthetic technical (89 words) |
|---|---:|---:|---:|
| QNN Small / Balanced — Baseline | 4.23% (8 errors) | 2.70% (5 errors) | 6.74% (6 errors) |
| QNN Small / Balanced — New Standard, hints off | 4.23% (8 errors) | 2.70% (5 errors) | 6.74% (6 errors) |
| QNN Small / Balanced — Careful, hints off | 3.17% (6 errors) | 1.62% (3 errors) | 6.74% (6 errors) |
| QNN Small / Balanced — Standard + hints | 5.82% (11 errors) | 3.24% (6 errors) | 4.49% (4 errors) |
| QNN Small / Balanced — Careful + hints | 4.23% (8 errors) | 2.16% (4 errors) | 4.49% (4 errors) |
| QNN Base / Fast — Baseline | 5.29% (10 errors) | 3.24% (6 errors) | 6.74% (6 errors) |
| QNN Base / Fast — New Standard, hints off | 5.29% (10 errors) | 3.24% (6 errors) | 6.74% (6 errors) |
| QNN Base / Fast — Careful, hints off | 7.41% (14 errors) | 2.70% (5 errors) | 6.74% (6 errors) |
| QNN Base / Fast — Standard + hints | 9.52% (18 errors) | 5.41% (10 errors) | 6.74% (6 errors) |
| CPU Base int8 — Baseline | 7.41% (14 errors) | 2.70% (5 errors) | 5.62% (5 errors) |
| CPU Base int8 — New Standard, hints off | 7.41% (14 errors) | 2.70% (5 errors) | 5.62% (5 errors) |
| CPU Base int8 — Careful, hints off | 7.94% (15 errors) | 3.24% (6 errors) | 7.87% (7 errors) |
| CPU Base int8 — Standard + hints | 7.94% (15 errors) | 4.86% (9 errors) | 6.74% (6 errors) |
| CPU Base int8 — Careful + hints | 7.41% (14 errors) | 4.86% (9 errors) | 8.99% (8 errors) |

**Default preservation:** all 48 new Standard transcripts exactly matched baseline text
on each of the three backends (144/144). Both new options remain off by default.

**Careful on Small:** only one clip per public speaker accounts for the improvement.
KSP's “Render Wu” became “rendezvous”; AWB's “the eight” became “they ate”. This is a
two-word-error reduction per group, not a statistically established or classroom-wide gain.
Careful worsened Indian-English results on both Base backends. It must be tested per speaker.

**Vocabulary:** each hints run used the same fixed list:
`ESP32 | I2C | FreeRTOS | interrupt service routine | MOSFET | FPGA | VHDL | PID | neural network`.
Only whole terms within the 32-token prompt budget are used. No reference sentence was
supplied as a prompt. Electronics terms are intentionally unrelated to the public passages:
those runs expose the risk of vocabulary bias. On Small the raw synthetic transcription
“free RTOS” became “FreeRTOS”, but the existing glossary already fixes that spelling in
displayed captions. This does **not** demonstrate a new visible technical-caption gain.
Real technical recordings from the two lecturers are still required.

## Speed and memory

| Balanced setting | Public audio duration | Total inference time | Real-time factor |
|---|---:|---:|---:|
| Baseline | 121.3 s | 17.1 s | 0.14 |
| New Standard, hints off | 121.3 s | 12.7 s | 0.10 |
| Careful, hints off | 121.3 s | 23.5 s | 0.19 |
| Standard + hints | 121.3 s | 26.0 s | 0.21 |
| Careful + hints | 121.3 s | 36.0 s | 0.30 |

Real-time factor is inference time divided by audio duration (lower is faster); it excludes
microphone endpoint delay, translation and UI rendering. These sequential development runs
include cold graph, warm-up and thermal variation. In particular baseline and new Standard
have different timings despite identical decoding code and outputs. Do not treat these as a
controlled benchmark or a promised speed multiplier. Full timings are retained for audit.

Careful uses up to three decoder paths for finished phrases, increasing decoder work and
cache memory; partial captions use one path. The encoder runs once per phrase. Vocabulary
prefill adds up to 32 tokens plus its marker and loads the existing tokenizer lazily. No new
model weights or Python runtime packages are required. Small/Balanced has larger existing
weights and resource requirements than Base/Fast. Peak RAM was not measured; accelerator
memory allocation also depends on the driver. On slower PCs test sustained caption latency.

## Verification and limits

- Unit checks: 69 passed on native ARM64 and 65 under x64 emulation, including project-management acronym/meaning safeguards, tokenizer
  reference vectors, token suppression, decoder context limits, beam alternatives, unchanged
  default dispatch, silence protection and CPU recovery of the chosen settings.
- Six tokenizer vectors match Hugging Face tokenizers 0.22.2 using the existing Whisper
  tokenizer JSON. That reference package was used only for testing, not added to the app.
- Native Qt checks on both runtimes verify preset round-trip, changed hardware selection,
  synthetic lecture/Stop, disabled controls during a lecture and visible minimum-size controls.
  Reports: [ARM64](recognition-ui-arm64.json), [x64](recognition-ui-x64.json).
  The x64 combined-mode replay misrecognised I2C as “iSquadC”; passing a workflow check is
  not an accuracy claim. Base results remain mixed.
- Audio capture, VAD, thresholds and feature extraction are unchanged. Aggressive global
  denoising/gain or accent detection was not introduced without representative evidence.
- No new microphone capture was used. Evaluation invokes the existing offline guards;
  a physical Airplane Mode/native-library packet audit and actual Intel/AMD tests remain open.

Both packaged executables passed the public JFK self-test after rebuilding:
[ARM64 0.3.2](packaged-recognition-arm64.json) and
[x64 beta 0.4.0b2](packaged-recognition-x64.json). ARM64 checked Fast/Balanced QNN and
CPU with Standard and guided decoding. x64 checked CPU and actual DirectML GPU encoding
with both modes. Both checked translation, VAD readiness, all 12 bundled course lists and
the 92-entry subject glossary. Guided silence checks passed on the directly tested CPU/QNN
models. Executable machine headers are ARM64 `0xaa64` and x64 `0x8664`.
These are functional packaged checks, not additional lecturer-accuracy evidence.

## CO7000 course vocabulary

The supplied lecture archive was inspected locally. Twelve weekly lists fit fully within
the prompt budget (11–18 tokens each). The Project Management glossary has 92 entries;
it normalises conservative spelling and acronym variants only when that subject is selected.
Course source decks and assessment documents are not redistributed. The UI selector replaces
the current vocabulary and selects the subject without changing the model or hint/mode choices.

Six newly written synthetic sentences were spoken by Windows **Microsoft Hazel Desktop,
en-GB**. Paired raw WER on Small/Balanced Standard was **4/67 (5.97%)** without hints and
**2/67 (2.99%)** with each week's short list. All improvement came from “prints 2” becoming
“PRINCE2”; the “estimate at completion” error remained. No fuzzy “prints 2” correction was
added to the glossary. These six synthetic clips do not validate Indian-accented English,
and are too small for a general accuracy claim. See [per-clip results](co7000-vocabulary-comparison.json)
and [course instructions and rehearsal passages](../CO7000_VOCABULARY.md).

Reproduce this functional check with `scripts/prepare_course_fixtures.ps1`, then run
`scripts/evaluate_speech.py --manifest tests/fixtures/co7000-cases.json --backend balanced
--mode standard --output tests/artifacts/course-standard.json`. Repeat with `--case-vocabulary`
and a different output path. Generation uses the PC's default Windows voice and preserves
existing WAVs; the local preparation report identifies the voice and which clips were generated.

## Needed next

Obtain 2–5 minutes from each lecturer with their agreement: ordinary explanation, a common
technical passage, failed vocabulary, accurate written references, microphone/room details,
and profile/backend settings. Reserve a separate passage for validation after tuning.
Evaluate both speakers locally with [the guide](../SPEECH_RECOGNITION.md) before changing
their teaching presets. The present public sample does not validate either lecturer's voice.
