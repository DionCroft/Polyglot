# Teaching with LectureLive 0.6

New to the app? Use the **Quick start** button for the [short guide](QUICK_START.md).

1. On Windows, open **Launch.cmd**, the Start menu shortcut, or the EXE in the complete app folder. On Mac, open **Applications → LectureLive**.
2. Load a saved lecture preset, or select a microphone and subject glossary.
3. Press **Test microphone · 3 seconds**, speak, and check the reported level. This
   creates no recording. A quiet-room result is not an accuracy test of your voice.
4. Enter a title and technical vocabulary. **Save…** stores a named preset locally.
5. In **Overlay**, select the caption display and use **Preview captions on selected
   display**. Check visibility from the back of the room; lock before teaching.
6. Press **Start lecture**. The input meter and Listening status confirm capture.
7. Use **Teaching controls** for a compact floating panel while your slides are open.
   **Full controls** returns to the main window.

The Start/Finish and Pause controls remain visible outside the scrolling preparation
area. Captions automatically lock when a lecture starts.

## Switch between English and Mandarin

Under **Who is speaking?**, choose **English → 简体中文** for the lecturer or **Mandarin
普通话 → English** for a student's question. This is separate from the caption display mode:
leave **Bilingual** selected to show both recognised speech and translation with language labels.
The selector is also in **Teaching controls**. Finish the current sentence, change direction,
and wait for **Listening** before the next speaker starts. Captured speech finishes and is saved
before the switch; audio during switching is not captured. Paused lectures remain paused.
See [conversation examples and limitations](CONVERSATIONS.md).

## Pause, finish and reconnect

**Pause** immediately hides captions and invalidates unfinished speech so private
asides do not appear when you resume. **Stop lecture** stops accepting new audio,
finishes speech already captured, drains recognition and translation, and closes
transcripts. The final bilingual caption remains visible. Closing the app uses the
same finishing sequence. A slow native inference call can delay completion; status
messages explain that local processing is still finishing.

When an input failure is reported, reconnect the microphone and press **Reconnect /
retry**. The old session is finished before another starts. If the saved microphone
is still absent, select and refresh it rather than silently switching to another input.
A runtime NPU error triggers one retry of the same phrase on the local CPU backend.

Default global shortcuts are **Ctrl+Alt+C** for lock and **Ctrl+Alt+Space** for pause. On Mac, these are **Control+Option+C** and **Control+Option+Space**.
Change them under Overlay using Ctrl/Alt/Shift plus a letter, digit, Space or F1–F12.
A conflicting shortcut is rejected and the previous bindings are restored.

## Caption behaviour

Provisional recognised speech appears after agreement between successive hypotheses.
Completed English/Chinese pairs remain together while the next phrase is being translated.
New recognised speech is shown separately underneath. Each language is labelled as spoken
or translated. Translation failures keep the source speech available; old translations are
not presented as the new phrase. A language switch clears captions from the previous turn.

A normal phrase ends after roughly 576 ms of silence. A sentence-ending hypothesis
can shorten that to 320 ms after sufficient speech. Continuous speech still has a
9.6-second bound. Brief natural pauses help translation preserve complete thoughts.

Choose English, Chinese or bilingual display. Drag an unlocked overlay to move it,
and drag its lower-right corner to resize. Text size, width, spacing, opacity and
colours are adjustable. Long content can expand the overlay and reduce its font to
fit the screen; the next short caption restores its normal dimensions.

If a display disappears, the app falls back to an available screen. Reconnect and
select your projector again. Physical projector hot-unplug acceptance remains pending.

## Presets and vocabulary

Presets store title, vocabulary, microphone, glossary, speech profile, caption mode,
appearance and display selection in `%LOCALAPPDATA%/LectureLive/presets.json`.
Global shortcuts remain app preferences when a preset is loaded. Missing or damaged
preset files are reported and retained rather than silently replaced.

English vocabulary preserves recognised spelling. The optional **Use these terms to guide
speech recognition** checkbox also passes a short relevant list to Whisper. English glossary
corrections and CO7000 hints are not applied to Mandarin turns. They remain saved for when you
return to English. Careful and vocabulary guidance can worsen some results; compare a short
passage before teaching. See [speech settings](SPEECH_RECOGNITION.md) and
[translation evaluation](TRANSLATION_EVALUATION.md). Presets also remember the speaking language.

## Transcripts and recovery

Saving is on by default and can be disabled before a lecture. **Diagnostics → Open transcripts**
opens the session folder. Windows Snapdragon uses `%LOCALAPPDATA%/LectureLive`, the x64 beta
uses `%LOCALAPPDATA%/LectureLive Beta`, and Mac uses `~/Library/Application Support/LectureLive`.
Mixed conversations stay in one folder: each language file includes speech in that language
and translations into it. English/Chinese/bilingual TXT, subtitles,
and the UTF-8 `events.jsonl` journal are written incrementally. Saving failures disable
exports and leave captions running.

**Recover transcript journal…** rebuilds exports into a new folder from complete
journal records, skipping invalid or truncated records. The original is preserved.
Microphone samples remain in memory only. Vocabulary and presets are saved locally;
diagnostic logs omit caption text. No private recordings or transcripts are uploaded.

## Offline rehearsal

Ordinary startup never downloads models or contacts hosted inference. Before class,
complete the Airplane Mode, intended-microphone, projector and teaching-length checks
in ACCEPTANCE_TESTS.md. Synthetic tests do not establish real-room accuracy.
