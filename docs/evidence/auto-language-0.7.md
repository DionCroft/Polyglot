# Auto conversation validation — 0.7.0b1

Auto is part of the main application, with manual English/Mandarin choices retained.
This is development verification, **not classroom certification**. Tests do not replace a
rehearsal with the actual lecturers, student voices, microphone, room and projector.

## Expanded language-identification checks

The frozen manifest selects 60 new Mandarin FLEURS clips, 20 English, 10 French and
10 Spanish. It excludes the three Mandarin clips used for the original prototype.
We also reuse 48 earlier English recordings: 20 public Indian-English, 20 public
Scottish-English and eight synthetic technical clips. Neither lecturer is represented.
Audio and source hashes are checked. See [FLEURS attribution](../licenses/fleurs-NOTICE.md)
and the earlier [speech evaluation](speech-recognition-2026-09-21.md).

Each recording has five variants: full clean speech, the first one/two seconds after
VAD trimming, and deterministic additive Gaussian noise at 20/10 dB SNR. The detector
uses all Whisper language tokens; unsupported languages can win. Noise is not a
recorded classroom, and excerpt duration is not the same as voiced duration.

An initial QNN Base run accepted one wrong one-second Mandarin excerpt as English
(score 0.908, 0.672 seconds voiced). The final policy requires 0.95 for less than
1.2 seconds of voiced speech. **This corpus informed that threshold**, so these
results are not an independent estimate of future accuracy.

Correctly accepted English/Mandarin choices out of 128 supported recordings per variant:

| Variant | CPU Base | QNN Base (policy reanalysis) | QNN Small |
|---|---:|---:|---:|
| Full clean | 117/128 | 123/128 | 124/128 |
| One-second excerpt | 34/128 | 35/128 | 55/128 |
| Two-second excerpt | 116/128 | 117/128 | 117/128 |
| 20 dB noise | 113/128 | 115/128 | 121/128 |
| 10 dB noise | 109/128 | 110/128 | 118/128 |

CPU Base and QNN Small each completed 740 variants using the final policy. QNN Base
reuses the initial run’s recorded choices and applies only the stricter short-phrase score
threshold; its inference was not rerun. This is labelled policy reanalysis in its report. There were zero wrong accepted choices; all 20
French/Spanish examples were rejected in each variant. The remaining supported
phrases were withheld, **not successful captions**. These results measure language
choice only, not word accuracy, technical meaning or translation quality. Related
variants are not independent samples; model scores are not calibrated probabilities.

For the 20 public Indian-English full clips, CPU Base accepted 10 and QNN Small accepted
16; all accepted choices were English. Four/ten withheld clips are still missing content.
These results do not establish performance for the colleague’s own voice. Manual English
mode bypasses language detection and preserves the existing recogniser.

Raw results: [CPU Base](auto-0.7-auto-evaluation-cpu.json),
[QNN Base policy reanalysis](auto-0.7-auto-evaluation-qnn-base-policy.json),
[QNN Small](auto-0.7-auto-evaluation-qnn-small.json).

A separate 24-recording/120-variant x64 DirectML check on the Snapdragon Adreno GPU
accepted 12/12 supported clean clips, 3/12 one-second, 10/12 two-second, 12/12 at
20 dB and 11/12 at 10 dB. No wrong accepted choices; all unsupported clips rejected.
[Raw GPU report](auto-0.7-auto-evaluation-x64-gpu.json). This uses x64 emulation;
it is not physical Intel/AMD evidence.

## Application checks

- 107 regression tests pass on both Windows runtimes (two POSIX-only skips).
- Manual English output exactly matches the pre-conversation baseline for 36 speech
  cases across CPU Base/QNN Base/QNN Small and Standard/Careful, plus 40 translations. [Exact expected outputs](auto-0.7-english-regression.json).
- Auto tests cover slow translations while speakers alternate, direction-specific
  vocabulary, pause during detection, manual override, missing models, accelerator
  failure/CPU retry, provisional-text retraction and ordered journal recovery.
- Real native Windows UI replay checks both languages, Auto presets, compact controls,
  labelled overlay, manual override and pause-preserving selection. The JFK→Mandarin→JFK
  replay produced eight bilingual pairs and **two withheld short phrases** on QNN Base.
  The withheld English phrase was “ask not”; omitting it changes meaning. The app shows
  an explicit notice and bilingual transcript marker, but a repeat/manual selection
  is needed. This is a concrete reason not to promise complete Auto captions.

Both rebuilt Windows editions pass the legacy English/CO7000 self-test, manual conversation
inference/UI, Auto real-time replay and Auto UI checks. Each accelerated Auto replay
produced eight translated pairs and two explicit uncertain phrases, switched en→zh→en,
kept all queues without drops/skips, and recovered exports byte-for-byte. ARM64 uses QNN
Base; x64 uses DirectML on Adreno under emulation. All 42 ARM64 and 29 x64 bundled model
files match their pinned hashes. UI checks include Auto preset, compact selector, labels,
single-language modes, manual override, paused selection and controls at minimum window size.

[ARM64 build checks](auto-0.7-arm64-summary.json) · [x64 build checks](auto-0.7-x64-summary.json) ·
[ARM64 Auto replay](auto-0.7-arm64-auto.json) · [x64 Auto replay](auto-0.7-x64-auto.json) ·
[ARM64 UI](auto-0.7-arm64-auto-ui.json) · [x64 UI](auto-0.7-x64-auto-ui.json).

Native macOS results are recorded below. Windows x64 testing on this machine uses emulation on Snapdragon;
physical Intel/AMD GPU/NPU and physical M2 classroom tests remain outstanding.

## Sustained alternating-speaker replay

A **600-second** real-time replay on QNN Small/Balanced, with recording RMS levels
normalised in test preparation and additive 20 dB noise, completed **133 translated
pairs and 34 language changes**. It retained **34 uncertain-phrase notices** (mostly
the repeated short English “ask not” fragment). No audio chunks, queued phrases or
translations were dropped. Exports recovered byte-for-byte and all pipeline workers
joined on close. This is a functional sustained pass, not complete speech coverage.

Bilingual p95 delay was **2.675 s**, including endpoint delay and inference, measured
from the final voiced audio. Sampled parent RSS ranged **1898–1965 MiB**.
Other development checks ran on the machine, so these are observed run statistics,
not an isolated performance benchmark. Repeating the same three recordings does not
add independent speakers or prove full-lecture thermal/battery stability.
[Full sustained report](auto-0.7-soak-levelled.json).

## Adverse conditions and failed tests

The first 600-second replay at a global 20 dB SNR failed its language-switching criterion:
95 completed pairs, only four language changes, and 53 uncertain phrases, although no
audio chunks/queued phrases/translations were dropped. The source Mandarin recording
was about 31 dB quieter in RMS than JFK (0.00393 versus 0.14210), so the shared noise
floor overwhelmed the Mandarin. [This is retained as a failed test](auto-0.7-soak-unbalanced-failed.json), not relabelled a pass.
It demonstrates why both speakers must be clearly audible at the selected microphone.
A separately labelled replay equalises recording levels *in test preparation* before
adding noise; the application does not apply this gain adjustment.

An x64 forced-CPU real-time replay under ARM emulation also failed to retain both
directions while several development checks ran concurrently. CPU speech took several
seconds per phrase and fell behind. CPU model inference still works, but that observation
is not a real-time CPU acceptance pass. The normal x64 GPU path is checked separately.
A second, lighter-load x64 CPU replay completed seven pairs, three uncertain phrases and
zero queue drops, but its bilingual p95 latency was **12.889 seconds**. It is a functional
CPU pass with unsuitable observed live-caption latency, not a real-time acceptance pass.
[CPU diagnostic](auto-0.7-x64-cpu-diagnostic.json). Native Intel/AMD CPU performance
needs a physical test; these observations apply to x64 emulation on this Snapdragon PC.

## Reproduce

After normal developer setup, use the private Python runtime (or native Mac environment):

```text
python -m scripts.prepare_conversation_fixtures
python -m scripts.prepare_auto_fixtures
python -m pytest -q
python -m scripts.evaluate_auto_language --accelerator cpu --output tests/artifacts/auto-cpu.json
python -m app.main --auto-self-test tests/fixtures tests/artifacts/auto-session.json
python -m app.main --auto-ui-test tests/fixtures tests/artifacts/auto-ui.json
python -m scripts.soak_auto --seconds 600 --profile balanced --normalise-speakers --output tests/artifacts/auto-soak.json
```

Add `--auto-cpu` to the app self-test to force CPU. The UI test uses the normal Automatic
hardware selection. Retain failed reports rather than treating a completed detection
evaluation (`passed: true`) as a classroom accuracy gate.

To repeat the 36/40 exact-output comparison on Windows Snapdragon, run
`python -m scripts.check_english_regression --output tests/artifacts/english-regression.json`.
It uses the committed expected outputs and the previously prepared accent/translation fixtures.

The complete evaluation also requires the earlier accent fixtures. CI uses six FLEURS
clips per language with `--limit 6` and the matching fixture-download limit. Use an isolated
`LECTURELIVE_DATA` folder for UI tests, which save test settings/presets. Downloads occur
only in preparation; application and evaluation enforce the existing offline guard.

## Before relying on it in a classroom

Use the [physical acceptance checklist](../ACCEPTANCE_TESTS.md). Collect a separate,
consented set of actual lecturer and student questions, including Indian-accented English,
Mandarin, CO7000 terms, short replies, negation, dates/numbers and speaker changes. Record
microphone distance and room conditions. A bilingual reviewer should measure wrong language
choices, withheld phrases, word/character errors and preserved meaning independently.
Rehearse a full lecture on the intended hardware, including external microphone, projector,
pause/reconnect, offline startup, sleep/resume and thermal/battery behaviour.

## Windows downloads/builds

The main application code is commit `0d82033`; subsequent commits add verification
reports and documentation. The rebuilt app folders are `dist/LectureLive` (Snapdragon)
and `dist/LectureLive-x64-Beta` (Intel/AMD edition, tested here under emulation).

Local portable ZIPs in `recovery` include the models and updated offline guides:

| Archive | Bytes | Files verified |
|---|---:|---:|
| LectureLive-Windows-ARM64-Beta-0.7.0b1.zip | 1,526,632,481 | 557 |
| LectureLive-Windows-x64-Beta-0.7.0b1.zip | 747,794,782 | 1,334 |

Every ZIP member is hashed against its source file; the ZIP contains `SHA256.json`
and has an adjacent `.zip.sha256` receipt. [Archive receipts](auto-0.7-windows-packages.json).
These large Windows archives are local deliverables, not Git-tracked binaries.
The public Windows installation route remains the main-branch source ZIP and **Setup.cmd**.
The offline guides reflect the evidence available at packaging; this repository report
also records later native Mac and release verification.

## Native Apple Silicon verification

[Native build 35760909426](https://github.com/DionCroft/Polyglot/actions/runs/35760909426)
passed on **macOS 14.8.9 ARM64**, using application commit `0d82033`. All **109 tests**
passed with no skips. The packaged app passed English/CO7000 inference, manual Mandarin
inference and switching, Auto CPU replay, native Cocoa UI, Auto presets and compact
controls, labels and single-language modes, pause/manual override and transcript recovery.
The app signature and microphone-purpose string were verified before DMG/ZIP packaging.

The Auto CPU replay completed seven translated pairs and three uncertain phrases with
no queue drops/skips; bilingual p95 latency was 4.336 s on the hosted runner. The native
Auto UI used the Core ML encoder with CPU decoding and completed eight pairs/two notices.
Core ML Fast executed successfully; Small Core ML preparation timed out and recovered
to CPU, as in the existing Mac edition. This does not identify which physical Apple GPU
or Neural Engine unit was used and is not an M2 Air thermal/battery or classroom test.

The Mac detection evaluation used 24 public recordings (six per language), 120 variants:
12/12 supported clean clips accepted, 4/12 one-second, 11/12 two-second, 12/12 at 20 dB,
and 11/12 at 10 dB. No wrong accepted choices; all unsupported examples were rejected.
Again, withholding is not successful captioning and these clips are not independent
of the development set.

[109-test report](auto-0.7-macos-pytest.xml) ·
[CPU Auto replay](auto-0.7-macos-auto.json) ·
[Native Auto UI](auto-0.7-macos-auto-ui.json) ·
[Mac language evaluation](auto-0.7-macos-auto-evaluation.json) ·
[CPU/Core ML inference and recovery](auto-0.7-macos-packaged.json).
