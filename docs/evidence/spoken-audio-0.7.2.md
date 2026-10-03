# Spoken translations 0.7.2b1 — 3 October 2026

The pre-rolling app, offline Whisper, translation models, inference defaults, Auto
thresholds, presets and CO7000 vocabulary are retained. Audio is an optional UI-side
consumer of completed translations. No microphone recording or audio export is added.
The unrelated local whitespace edit in `app/system/accelerators.py` is excluded.

## First tested milestone

- Windows ARM64: 139 tests passed, two POSIX-only skips.
- Windows x64 under ARM emulation: 139 passed, two skips.
- Thirteen new controller/voice/settings tests cover completed-only output,
  both directions, duplicate/late captions, bounded/expired queues, long-text
  refusal, cancellation, delayed callbacks, missing/wrong-language voices,
  playback errors/timeouts, disabled output and old settings.
- Native Windows source UI verifies that saved Auto does not start playback on
  opening, automatic mode needs headphone confirmation, on-demand speech pauses
  listening, and Pause/Resume, language switching, Stop and shutdown clear audio.
- Real WinRT English playback at zero volume completes; stopping and immediately
  starting another utterance succeeds. No human listening judgment is implied.
- A real Mandarin WAV replay is recognised and translated, then its completed
  English translation is played through WinRT at zero volume. Listening pauses and
  resumes correctly. Existing conversation, transcript and caption UI checks pass.
- This PC lists Microsoft George, Hazel and Susan (en_GB). No Mandarin voice is
  installed, so actual Mandarin output remains pending here; its direction/control
  tests use a fake voice engine. The app explains how to install a system voice.

[ARM64 tests](spoken-072-arm64.xml) · [x64 tests](spoken-072-x64.xml) ·
[Native voice and controlled UI checks](spoken-072-source.json) ·
[Real pipeline and caption UI](spoken-072-conversation-ui.json).

## Playback behavior

Audio starts Off whenever the app opens or a preset is loaded. On-demand speech
prepares the target voice before pausing listening, so a missing voice does not
pause capture unnecessarily. The user presses Resume after playback; unfinished
speech is intentionally discarded by the existing Pause behavior. The microphone pause
used for playback keeps completed captions visible. The normal privacy Pause still
hides the overlay, including when audio is requested from an already paused session.

Automatic output requires a headphone confirmation for every lecture. There is no
acoustic echo cancellation. It uses the default system output device; stop audio
before unplugging headphones. Automatic output can keep listening with headphones.
The queue holds one active phrase and at most two waiting phrases, expires waiting
items after 20 seconds, and reports skipped audio without altering captions or text
exports. Utterances over 800 characters are refused rather than silently truncated;
a two-minute timeout/error suspends automatic audio. Stop audio switches to On demand.

Installed Windows/macOS system voices are used; no new inference models are bundled
or downloaded during lectures. Voice availability, pronunciation and speed vary by
computer. Missing/removed voices cannot silently fall back to the wrong language.
Cantonese locales are not offered as Mandarin.

## Delivery status and remaining checks

Both final Windows portable packages and the published Apple Silicon app pass the
checks below. Real listening quality and physical classroom checks remain open. The Windows beta is built separately under `dist/spoken-0.7.2b1`
to preserve the user's running 0.7.1 application. Existing launchers still use the
original `dist` app; open the new executable explicitly for feedback.

Physical speaker/headphone audibility, acoustic feedback, technical pronunciation,
long lectures and native Intel/AMD/M2 hardware require user testing. Automated muted
playback and public-WAV tests do not establish classroom quality.
[Five-minute feedback guide and voice installation](../SPOKEN_AUDIO.md).

## Caption visibility polish

A follow-up native UI check verifies that the microphone pause used by on-demand
speech keeps completed captions visible. Explicit privacy Pause still hides them,
and speaking a translation while already privately paused does not reveal them.
The real Mandarin-to-English pipeline/playback check and all 139 Windows ARM64
regression tests pass after this adjustment.

## Final Windows builds

Built from `e5df9c7f9fbf3e8c5483438ee84ca02ed27518ff`. Both editions pass all six
packaged checks: native speech-output/control tests, English/CO7000 inference,
Mandarin and both translation directions, the real caption/voice UI test,
Auto conversations and Auto UI. The compiled version is verified as 0.7.2b1.

The final checks verify 42 bundled model/dependency members for ARM64 and 29 for
x64 against the locked hashes. All six text/subtitle files preserve chronological
order and recover byte-for-byte across four packaged sessions per edition. The
existing 36 speech and 40 English-to-Chinese outputs exactly match 0.7.1.

- [Packaged Windows summary and EXE hashes](spoken-072-windows-summary.json)
- [ARM64 speech output](spoken-072-arm64-speech.json) / [real pipeline](spoken-072-arm64-conversation-ui.json)
- [x64 speech output](spoken-072-x64-speech.json) / [real pipeline](spoken-072-x64-conversation-ui.json)
- [Exact speech/translation baseline](spoken-072-english-regression.json)

The verified ZIPs under `recovery/` are:

| Archive | Decimal size | Verified members |
|---|---|---|
| `LectureLive-Windows-ARM64-Beta-0.7.2b1.zip` | 1.537 GB | 675 |
| `LectureLive-Windows-x64-Beta-0.7.2b1.zip` | 759.2 MB | 1,452 |

Each has a `.zip.sha256` companion and internal per-file `SHA256.json`.
[ARM64 receipt](spoken-072-arm64-zip.json) / [x64 receipt](spoken-072-x64-zip.json).
The archives contain documentation from the tested code commit; this report on GitHub
records final results collected after packaging.

On the development PC, open `dist/spoken-0.7.2b1/LectureLive/LectureLive.exe` after
closing the currently running LectureLive. For x64, use the corresponding
`LectureLive-x64-Beta` folder/executable. Keep `_internal` next to the executable.
The normal launchers still select the original app. Its 0.7.1 ARM64 executable hash
was checked and is unchanged; no running process was terminated.

## Real automatic-voice replay

Two native Windows ARM64 source replays used the real Mandarin recognition and
translation pipeline plus the real WinRT English voice, at volume zero. Each input
was a 34.14-second sequence made from three repetitions of the public Mandarin test
clip with silence between them. Tests used rate 0 and rate -50.

Each run completed six caption pairs and six spoken utterances, in order, with at
most one waiting utterance. Neither run dropped audio blocks, phrases or translations;
no playback was skipped or expired. All six exports recovered byte-for-byte. Separate
controlled unit tests force queue overflow, expiry and voice timeout/error paths.

[Replay results and timing/queue metrics](spoken-072-live-auto.json).
To reproduce from the repository root with the prepared test WAVs, set
`LECTURELIVE_DATA` to a dedicated test folder and run
`python -m scripts.check_spoken_audio_replay` using the project's native runtime.
The script refuses to run without an explicit data folder and uses muted output.
This is a short functional concurrency check, not an audible or classroom benchmark.

## Native Apple Silicon and published Mac installers

[Build 37091675387](https://github.com/DionCroft/Polyglot/actions/runs/37091675387)
passed on native hosted macOS 14.8.9 ARM64: **141 tests, zero skips**. The packaged
Darwin speech engine completed **English and Mandarin** playback at zero volume,
plus native stop/reuse and the controlled UI lifecycle tests. Mandarin voices were
installed on this runner (including Yu-shu, Li-Mu and Tingting for zh_CN); unlike the
Windows development PC, both real voice directions were available here.

The real Mandarin transcription/translation → English speech path passed. Completed
captions stayed visible for playback; explicit privacy Pause continued to hide them.
All three global shortcuts registered, and existing native overlay, microphone
permission integration, conversation/Auto and minimum-control checks passed. The
new speech-control screenshot was visually inspected.

CPU and Base/Core ML recognition passed. Requested Small/Core ML preparation timed
out and successfully fell back to CPU, as in the existing Mac edition. Individual
GPU/Neural Engine execution and a physical M2 Air classroom were not verified.

[Native suite](spoken-072-macos-pytest.xml) ·
[Real English/Mandarin voice checks](spoken-072-macos-spoken-audio.json) ·
[Real caption-to-voice path](spoken-072-macos-conversation-ui.json) ·
[Recogniser/fallback checks](spoken-072-macos-packaged.json) ·
[Verified speech UI image](spoken-072-macos-ui.png).

[Publish run 37092728590](https://github.com/DionCroft/Polyglot/actions/runs/37092728590)
verified and published the exact native-build installers. The tag resolves to
`e5df9c7f9fbf3e8c5483438ee84ca02ed27518ff`; both uploaded asset digests match the
native build's SHA-256 checksums. The [0.7.2b1 Mac release](https://github.com/DionCroft/Polyglot/releases/tag/macos-v0.7.2b1)
contains a 1.221 GB DMG, 1.174 GB ZIP, INSTALL-MAC.md and SHA256SUMS.txt.
[Publication receipt](spoken-072-macos-release.json) ·
[Installer checksums](spoken-072-macos-SHA256SUMS.txt).

The app requires Apple Silicon and macOS 14 or later. It is ad-hoc signed and not
Apple notarised. System voices are supplied by the operating system; missing voices
need a one-time download and are not bundled in the installers. Speech generation
was checked with muted output: **no human listening or physical microphone/feedback
claim is made**. Physical Intel/AMD, M2 Air, projector/acoustic and long-session
acceptance remain open for user feedback.
