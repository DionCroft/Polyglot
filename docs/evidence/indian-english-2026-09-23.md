# Indian-English speech testing — 23 September 2026

**Practical finding:** try **Balanced / Whisper Small with Standard** first where
available. On the new Snapdragon comparison it reduced combined Indian-English
word errors by 30% relative to Fast / Whisper Base, with improvements for both
Indian-English speakers and both English controls. Careful and vocabulary hints
had mixed results. This is evidence about these public recordings, not a measured
improvement for either lecturer.

This round changes evaluation tools and guidance. **Application speech models,
defaults, decoder code, audio processing, vocabulary corrections and Auto thresholds
remain unchanged from `4854286`.** No additional app download, model memory or
runtime dependency is required to try the existing settings. The published
0.7.0b1 installers remain the release; these tests do not constitute a new release.

## Recordings and method

- 120 new VCTK recordings, 30 per speaker, selected before inference: p248 and
  p251 (Indian English), p225 and p226 (English from Southern England/Surrey).
  Each pair includes one female and one male speaker. Labels are corpus metadata.
- 882 Indian-English reference words and 874 English-control words; 695.12 seconds
  of distinct audio. There are 23 sentences shared by all four speakers: p225's
  available recordings omit sentence 015, so its first 30 available clips include
  033. Other clips include differing newspaper text. No missing clip was invented
  or substituted after evaluation. Both groups read speech outside a classroom.
- 1,440 local full-clip transcriptions: six clean backend/mode combinations,
  four Small noise/quiet comparisons, and two explicitly exploratory hint runs.
  Repeated settings and variants are **not** additional independent recordings.
- [Selection protocol](indian-english-protocol.md), [pinned manifest](../../tests/fixtures/vctk-accent-cases.json),
  [source attribution/licence](../licenses/vctk-NOTICE.md), and
  [every local output, score and changed transcript](indian-english-2026-09-23.json).
  Raw audio is ignored and is not shipped or committed.
- Local hardware: Windows ARM64 Snapdragon X Elite. QNN uses FP16 Base/Small;
  the local CPU test uses Base int8. Models and inference stay offline after setup.
  Report timings are observations under development-machine load, not controlled
  benchmarks or promises about another computer.

WER is word edit distance after lowercasing and punctuation removal. Numbers in
digits versus words, contractions, hyphenation, spelling and word spacing still
count. For example, “raindrops” versus “rain drops” costs two word errors despite
preserving meaning. The corpus reference is the reading script and may differ
from the actual performance. These are not human-rated semantic accuracy scores.
The corpus may have been present in Whisper pretraining; it is new to this app's
comparison, not proven unseen by the model.

## Clean speech on Windows ARM64

Cells show error counts and WER; reference word counts are in the column headings.
Pooled results below are word-weighted.

| Backend and mode | Indian p248 (442 words) | Indian p251 (440 words) | English p225 (429 words) | English p226 (445 words) |
|---|---:|---:|---:|---:|
| QNN Base Standard | 14 / 3.17% | 46 / 10.45% | 21 / 4.90% | 14 / 3.15% |
| QNN Base Careful | 11 / 2.49% | 46 / 10.45% | 17 / 3.96% | 13 / 2.92% |
| QNN Small Standard | 10 / 2.26% | 32 / 7.27% | 13 / 3.03% | 10 / 2.25% |
| QNN Small Careful | 12 / 2.71% | 29 / 6.59% | 12 / 2.80% | 8 / 1.80% |
| CPU Base Standard | 14 / 3.17% | 52 / 11.82% | 24 / 5.59% | 12 / 2.70% |
| CPU Base Careful | 14 / 3.17% | 45 / 10.23% | 21 / 4.90% | 13 / 2.92% |

| Comparison | Indian total / 882 words | English total / 874 words |
|---|---:|---:|
| QNN Base Standard | 60 / 6.80% | 35 / 4.00% |
| QNN Small Standard | 42 / 4.76% | 23 / 2.63% |
| QNN Small Careful | 41 / 4.65% | 20 / 2.29% |

Small Standard is a clearer improvement on this set than switching Small to
Careful. Careful did recover the proper name **Aristotle** from “A race total”
for p251. It also changed some correct text formatting and left substantial
mistakes: “Wednesday” still became “when stay”, and “foretell” became “a fatal”.
Fluent output must not be mistaken for correct output.

Median full-clip inference time was 0.263 seconds for QNN Base Standard,
0.529 for Small Standard and 1.097 for Small Careful. Small's p95 times were
0.784 and 1.976 seconds respectively. These exclude microphone accumulation,
translation and live queueing. Careful's extra paths need more decoder work and
cache memory; memory was not re-profiled in this round. Retain the previous
platform/model memory guidance and rehearse on the actual teaching computer.

## Quieter and noisier speech

Same 120 recordings, fixed per-clip noise seed, unchanged references. Gaussian
noise uses 20 dB SNR; the quiet variant attenuates the whole signal by 12 dB without
adding noise. Neither models room echo, a distant microphone or competing speech.

| Small setting | Indian errors / WER | English errors / WER |
|---|---:|---:|
| Standard, clean | 42 / 4.76% | 23 / 2.63% |
| Careful, clean | 41 / 4.65% | 20 / 2.29% |
| Standard, noise at 20 dB SNR | 56 / 6.35% | 27 / 3.09% |
| Careful, noise at 20 dB SNR | 55 / 6.24% | 22 / 2.52% |
| Standard, 12 dB quieter | 43 / 4.88% | 23 / 2.63% |
| Careful, 12 dB quieter | 40 / 4.54% | 20 / 2.29% |

The aggregate can hide a worse speaker result: with noise, Careful changed p248
from 17 to 22 errors while improving p251 from 39 to 33. These results do not
justify turning Careful on for everyone, adding blanket denoising or applying
automatic gain changes.

## Technical vocabulary: exploratory check

After inspecting the first Small outputs, the fixed list **rainbow, refraction,
reflection, Aristotle** was tried. It relates to the shared science passage;
the unrelated groceries/news clips were retained as controls. No full sentences
or reference transcript were fed into Whisper. Because the list was chosen after
seeing errors, this is an exploratory mechanism check, not independent validation.

| Small mode | Indian errors without → with hints | English errors without → with hints |
|---|---:|---:|
| Standard | 42 → 40 | 23 → 25 |
| Careful | 41 → 39 | 20 → 23 |

Hints improved p251 but worsened p248 and some English controls. Keep short
topic lists optional and saved per lecturer/week. The existing CO7000 lists,
spelling rules and English-only direction support are preserved. Public science
readings and the older synthetic CO7000 examples do **not** validate your
colleague's project-management pronunciation. No guessed sound-alike replacements
were added for risk/issue, assurance/insurance, numbers or other distinct meanings.

Across both accent groups, the 75 science-topic clips stayed at 45 errors with
Standard and 43 with Careful, before/after hints. The 45 out-of-topic clips stayed
at 20 with Standard and worsened from 18 to 19 with Careful. The pooled outcome
hides which individual speakers improved or worsened.

## Real-time pipeline diagnostic

Eight selected clips were replayed at microphone cadence, with one second between
them: 61.63 seconds total and 158 reference words. This deliberately includes
previously observed failures and longer speech; it is not independent validation.
The production VAD, partial/final recognition, translation, queues and transcript
writer all ran, using QNN Small and manual English with the General glossary.

| Setting | Final English errors / WER | Completed bilingual pairs | English / bilingual p95 delay |
|---|---:|---:|---:|
| Standard, hints off | 13 / 8.23% | 10 | 0.889 / 1.179 s |
| Careful, hints off | 10 / 6.33% | 10 | 1.407 / 1.682 s |
| Standard, science hints | 16 / 10.13% | 9 | 1.046 / 1.529 s |

All three runs had **zero audio/phrase drops and zero skipped translations**.
All six text/subtitle export files matched their journal-recovered versions byte
for byte. Pair counts differ because recognition punctuation can change live
phrase boundaries; they do not correspond one-to-one with source files.
These are functional/export passes, not an accuracy or human translation pass.

The prompted replay omitted **Aristotle** at the start of three captions, including
an English control. Some omissions were also present in the full-clip hint run.
This is a measured reason to leave guidance off unless it helps that lecturer's
whole sentences. The unprompted replays retained the name, though Standard still
misrecognised its spelling for one voice. Do not assess hints using only the
aggregate score or assume a longer term list will repair it.

Raw evidence: [Standard](indian-replay-standard.json),
[Careful](indian-replay-careful.json), [Standard with hints](indian-replay-standard-hints.json).
Reproduce using `python -m scripts.evaluate_accent_replay --mode standard --output
tests/artifacts/replay.json`; use `--mode careful` or `--vocabulary
"rainbow|refraction|reflection|Aristotle"` for the alternatives. It uses public
WAVs only, never the microphone. No settings in a lecturer's saved preset are changed.

## Regression checks

- Windows ARM64: **112 passed, two POSIX-only skips**;
  [JUnit evidence](indian-arm64-pytest.xml).
- Windows x64 runtime under ARM emulation: **112 passed, two POSIX-only skips**;
  [JUnit evidence](indian-x64-pytest.xml). This is not physical Intel/AMD validation.
- The existing 36 speech outputs across CPU/Base/Small and 40 English translation
  cases matched the pre-existing baseline exactly on a fresh run;
  [recorded outputs](indian-english-regression.json). The speech subset includes
  earlier KSP/AWB and synthetic technical controls. It is not a fresh run of all
  the older 48-clip experiments.
- Fixture acquisition/conversion is tested for duration, passband/alias rejection,
  checksums and bounded network retries. Noise is paired deterministically per
  case. Both Windows suites and focused lint checks passed.

## Auto remains a separate check

Of 60 clean Indian-English clips, final Auto accepted 53 on QNN Base, 56 on QNN
Small and 50 on CPU Base; it withheld the rest. English controls were accepted
56, 58 and 53 times respectively. On Small, noisy Indian-English acceptance was
52/60 and quiet acceptance 56/60. There were no incorrectly accepted Mandarin
choices in the 600 local final decisions, but withholding a turn is still a miss.

These are whole-clip, VAD-trimmed final decisions, not partial-lock or automatic
conversation tests. The existing broader Mandarin/foreign-language evidence is
in the [Auto report](auto-language-0.7.md). Selecting manual English helps isolate
word errors and prevents an uncertain Auto decision from withholding a lecture turn;
it does not itself repair incorrectly recognised English words.

## Remaining validation

Use the [five-minute lecturer check](../ACCENT_CHECK.md). We still need consented
recordings from both real lecturers, including the same technical passage, their
usual spontaneous explanation, actual incorrect captions and a separate unseen
passage for validation. Record the microphone/distance/room, computer/backend,
profile, recognition mode and exact vocabulary list. Include numbers and negation.

Physical M2 MacBook Air thermal behaviour, physical Intel/AMD acceleration,
room microphones, students speaking from their seats and native-speaker review of
Chinese translation remain outside this check. No classroom-readiness or
accent-wide guarantee follows from these public samples.
