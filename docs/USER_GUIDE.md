# Teaching with LectureLive

1. Open **LectureLive.exe** in the `dist/LectureLive` folder.
2. Select your microphone. The Surface microphone array normally works with the
   WASAPI entry. Audio recording is always off; only captions are generated.
3. Select a subject glossary and optionally type a lecture title. Paste unusual
   spellings into Today's vocabulary, one per line.
4. Press **Start lecture**. A green input meter and Listening status confirm input.
5. Open **Overlay**, choose the projector display, and choose Bottom or Top.
6. Lock the overlay using **Ctrl+Alt+C** so clicks reach PowerPoint or other apps.
7. Open your teaching materials. The controls can stay on the Surface display.

Use **Ctrl+Alt+Space** for an immediate pause. Captions hide and pending display
updates are invalidated. Press it again to resume. Stop lecture closes the input,
finishes already queued translations, and closes transcript files. Closing the
control panel also shuts down all workers.

## Captions and placement

Choose Bilingual, English, or Chinese at any time. English may be provisional while
you speak. Translation happens once a pause or maximum phrase length establishes a
boundary. Short sentences and brief pauses improve reliability.

Show overlay lets you preview placement before teaching. When unlocked, drag the
backdrop to move it; drag its lower-right corner to resize. Font size, line spacing,
width, backdrop opacity and both text colours are adjustable in Overlay. Locking
makes the caption area click-through and prevents it taking keyboard focus.

If a projector disconnects, captions move to an available display. Reconnect and
select the desired display again. The last selected display is remembered.

## Glossaries

Select Electronics, Embedded Systems, Robotics, IoT, Artificial Intelligence, or
General before starting. Exact English terminology activates preferred Chinese
corrections. Vocabulary preserves exact spelling/capitalization; this version does
not acoustically bias Whisper or guess replacements for ordinary words.

Machine translation can omit or mistranslate technical detail. Review your subject's
sample output before class. This development build still needs bilingual quality
sign-off; glossary corrections do not make it a professionally validated translator.

## Transcripts and privacy

Text saving is on by default and can be switched off before a session. **Diagnostics →
Open transcripts** opens the current session. The default location is
`%LOCALAPPDATA%/LectureLive/transcripts`. English, Chinese and bilingual TXT, English
and Chinese SRT, bilingual VTT, and a recovery JSONL journal are written in UTF-8.
Microphone audio is never written to disk by the app. Logs contain timing and errors,
not caption text. Today's vocabulary is held only in memory.

## Offline use

All required models are already in the bundle. Startup never downloads anything.
There is no account, hosted inference, or cloud fallback. Before travel, complete the
Airplane Mode rehearsal in ACCEPTANCE_TESTS.md and copy the recovery package to a
separate drive. The ordinary application does not need internet access.

Starting a lecture automatically locks the overlay. Unlock it with Ctrl+Alt+C only
when you need to move or resize it. A smaller provisional English line can appear
below the previous stable bilingual pair; Chinese does not flicker with each token.

Pause and Stop discard the currently unfinished utterance. Allow a brief sentence-end
pause before stopping if you want its final caption included in the transcript.
