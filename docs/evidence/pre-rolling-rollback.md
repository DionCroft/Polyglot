# Restored pre-rolling version — 27 September 2026

The application is restored to **0.7.0b1 at `03e7973`**, the last commit before the
rolling reader and projector features. Rollback commit: `cd84704`. Git history is
preserved. The application, tests, build scripts and workflow were compared with
that baseline and matched exactly before adding these documentation reports.

The original latest-caption overlay is restored. The rolling reader, Back to live,
search/copy interface and queued projector playback are removed. Saved transcripts,
English/Mandarin switching, Auto, offline operation, microphone selection, shortcuts,
presets and vocabulary/CO7000 support remain as they were in the earlier version.

## Translation findings

The rolling commits did not change speech/translation inference code, models or model
locks. They changed presentation and added transcript notifications to the pipeline.
Queuing/independent scrolling can affect timing and which part of a passage is visible;
that is not proof of a translation-model regression. The rolling display tests measured
visible text coverage, not native-speaker translation quality.

A fresh run of 36 speech cases and 40 English-to-Chinese translation cases exactly matches
the established pre-rolling results. It also matches the recorded rolling-era fixed
fixture outputs. This does not rule out errors on other speech or vocabulary. To explain
a particular mistranslation, a representative utterance and its recognised/translated
text are needed.

Check **Who is speaking? → English → 简体中文** for English speech. Manually selecting
Mandarin makes Whisper expect Mandarin; the wrong speaking language can cause incorrect
recognition and translation. Keep the desired language selected when loading presets.
Careful decoding and vocabulary hints retain the earlier behaviour and are optional.

## Verification and use

- Both Windows runtimes pass **112 tests**, with two POSIX-only skips each; x64 is tested
  under Windows ARM emulation. Syntax and diff checks pass.
- Fresh Windows ARM64 and x64 EXEs are built. Their embedded version is **0.7.0b1**, and
  inspection confirms the rolling reader/projector modules are absent. EXE SHA-256 hashes
  are recorded in `rollback-executables.json`.
- Both rebuilt EXEs pass offline English/Mandarin WAV conversation checks, including
  manual and paused switching, labels, a single transcript folder and minimum controls.
- The published [Mac 0.7 installer](https://github.com/DionCroft/Polyglot/releases/tag/macos-v0.7.0b1)
  has matching application code, dependency lock and bundle specification. Reuse that
  tested installer; no new Mac build or physical hardware test was performed for this
  rollback. The rollback commit skips redundant CI for this identical native application.

Reopen **Launch.cmd** for the restored local Windows app. For an installed Mac copy of
0.8, quit LectureLive and install the 0.7 app from the linked release using the usual
[Mac instructions](../MACOS.md). Saved settings remain readable; unknown rolling options
are ignored by 0.7. Test sessions use isolated data folders. These checks do not establish
classroom translation quality or replace a rehearsal with the teaching microphone.
