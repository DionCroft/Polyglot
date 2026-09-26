# Rolling transcript validation — 26 September 2026

Application milestone: `4c2d01f` (0.8.0b1). Speech models, decoding settings,
vocabulary rules, CO7000 terms, automatic language thresholds and export formats
were not changed. No additional model download is needed.

## What changed

- An in-memory session history receives committed source text and translation
  events independently of whether disk saving is enabled. Epoch changes no longer
  erase reading history. Late translations replace their own passage in place.
- The Transcript tab supports live following, scrollback, a new-passage count,
  bilingual case-insensitive search with wraparound, text selection and copying.
  Selecting or searching text holds the reading position; Back to live restores following.
- A rolling projector layout uses the selected fixed font size and aligned language
  columns. Whole older passages leave the panel when necessary. An oversized latest
  passage can extend above the visible area; full text remains in the reader.
  Compact caption mode retains its previous rendering.
- The reader and its document retain at most 10,000 complete passages, with an
  explicit notice after eviction. Saved exports retain the complete session.

## Verified locally

- **Windows ARM64:** 127 tests pass, with two POSIX-only skips.
- **Windows x64 under ARM emulation:** 127 tests pass, with the same skips.
- Actual Qt tests cover 1,440 passages over a **simulated two-hour timeline**, source
  followed by translation, manual epoch changes, missing translation, explicit uncertain
  gaps, duplicate rejection, retention and exact journal recovery. This is an accelerated
  event replay, not a two-hour microphone soak or a new accent-accuracy benchmark.
- Scroll anchoring is checked while a much longer translation arrives above the
  viewport. Copying recognised source text survives its translation arriving, including
  text containing non-BMP Unicode. Hidden tabs and window resizing retain live following.
- Native Windows EXE checks exercise the reader, search/copy, late translations,
  uncertain-partial retraction, minimum 860 × 640 window, fixed projector font,
  offline help, click-through/no-activation flags and clearing temporary history.
- The real WAV conversation UI test uses offline Whisper/translation, manual language
  switching, a switch while paused, one transcript folder, saved subtitles and Mandarin
  recognition. It checks functional completion, not human-rated Chinese accuracy.
- **English regression:** all 36 fixed speech outputs and 40 translation outputs match
  the previous baseline exactly on the local Snapdragon system.

Machine-readable reports and synthetic screenshots accompany this document. Clipboard
tests use fixture text; no lecturer recordings, personal transcripts or microphone audio
are included in the evidence.

## Windows distributions

Built locally from `4c2d01f`. Each portable ZIP is re-read and every archived file's
SHA-256 is checked against its manifest; a separate whole-archive SHA-256 file is included
next to the ZIP. No new model downloads or hardware requirements were introduced.

| Edition | Archive in the project's `recovery` folder | Size |
|---|---|---:|
| Windows ARM64 / Snapdragon | `LectureLive-Windows-ARM64-Beta-0.8.0b1.zip` | 1,527,052,771 bytes |
| Windows x64 / Intel and AMD | `LectureLive-Windows-x64-Beta-0.8.0b1.zip` | 748,217,519 bytes |

Extract the entire ZIP and open the EXE inside its application folder. Keep `_internal`
beside the EXE. Existing source installations can open the rebuilt app with **Launch.cmd**.
The archive reports are `rolling-arm64-package.json` and `rolling-x64-package.json`.

Native Apple Silicon validation is tracked in
[build 36252250715](https://github.com/DionCroft/Polyglot/actions/runs/36252250715).
At the Windows evidence milestone its unit tests and `.app` build passed; packaged
inference/UI checks and DMG/ZIP production were still running. The published 0.7.0b1
Mac download does not include the rolling transcript.

## Remaining classroom checks

- Physical Intel/AMD hardware, an M2 MacBook Air, actual teaching microphones and
  projectors still need a rehearsal. Hosted native Mac results are separate from these.
- Check viewing distance, projector scaling/contrast, moving between monitors and
  a full lecture with the intended vocabulary and both speakers.
- Auto detection can still withhold ambiguous or very short speech. The new reader
  makes those gaps visible; it does not make language detection or word confidence stronger.
- History is temporary when saving is off and clears at the next lecture or app exit.
  Copy it before leaving if needed. Search/copy cover retained passages only.

See [beginner instructions](../TRANSCRIPT.md) and [classroom acceptance checks](../ACCEPTANCE_TESTS.md).
