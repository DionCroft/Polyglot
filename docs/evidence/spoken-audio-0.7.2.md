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
speech is intentionally discarded by the existing Pause behavior. Paused overlay
privacy behavior is unchanged and the main caption preview stays readable.

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

Final Windows portable packages and native Apple Silicon build checks are pending
at this milestone. The Windows beta is built separately under `dist/spoken-0.7.2b1`
to preserve the user's running 0.7.1 application. Existing launchers still use the
original `dist` app; open the new executable explicitly for feedback.

Physical speaker/headphone audibility, acoustic feedback, technical pronunciation,
long lectures and native Intel/AMD/M2 hardware require user testing. Automated muted
playback and public-WAV tests do not establish classroom quality.
[Five-minute feedback guide and voice installation](../SPOKEN_AUDIO.md).
