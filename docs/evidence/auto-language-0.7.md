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

| Variant | CPU Base | Snapdragon NPU Small |
|---|---:|---:|
| Full clean | 117/128 | 124/128 |
| One-second excerpt | 34/128 | 55/128 |
| Two-second excerpt | 116/128 | 117/128 |
| 20 dB noise | 113/128 | 121/128 |
| 10 dB noise | 109/128 | 118/128 |

Both runs completed 740 variants. There were zero wrong accepted choices; all 20
French/Spanish examples were rejected in each variant. The remaining supported
phrases were withheld, **not successful captions**. These results measure language
choice only, not word accuracy, technical meaning or translation quality. Related
variants are not independent samples; model scores are not calibrated probabilities.

## Application checks

- 106 regression tests pass on the Windows ARM64 runtime (two POSIX-only skips).
- Manual English output exactly matches the pre-conversation baseline for 36 speech
  cases across CPU Base/QNN Base/QNN Small and Standard/Careful, plus 40 translations.
- Auto tests cover slow translations while speakers alternate, direction-specific
  vocabulary, pause during detection, manual override, missing models, accelerator
  failure/CPU retry, provisional-text retraction and ordered journal recovery.
- Real native Windows UI replay checks both languages, Auto presets, compact controls,
  labelled overlay, manual override and pause-preserving selection. The JFK→Mandarin→JFK
  replay produced eight bilingual pairs and **two withheld short phrases** on QNN Base.
  The withheld English phrase was “ask not”; omitting it changes meaning. The app shows
  an explicit notice and bilingual transcript marker, but a repeat/manual selection
  is needed. This is a concrete reason not to promise complete Auto captions.

Native macOS, rebuilt Windows distributions and sustained replay results are recorded
below as they complete. Windows x64 testing on this machine uses emulation on Snapdragon;
physical Intel/AMD GPU/NPU and physical M2 classroom tests remain outstanding.

## Reproduce

After normal developer setup, use the private Python runtime (or native Mac environment):

```text
python -m scripts.prepare_conversation_fixtures
python -m scripts.prepare_auto_fixtures
python -m pytest -q
python -m scripts.evaluate_auto_language --accelerator cpu --output tests/artifacts/auto-cpu.json
python -m app.main --auto-self-test tests/fixtures tests/artifacts/auto-session.json
python -m app.main --auto-ui-test tests/fixtures tests/artifacts/auto-ui.json
python -m scripts.soak_auto --seconds 600 --profile balanced --output tests/artifacts/auto-soak.json
```

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
