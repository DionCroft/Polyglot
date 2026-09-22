# Automatic English and Mandarin conversations

Auto is included in the normal LectureLive application. You do not need a separate app,
speech model, account or internet connection. Existing installations keep their manual
speaking-language choice; choose Auto when you want hands-free conversation.

## Start a conversation

1. Select and test the microphone. Both speakers must be audible through that microphone.
2. Choose **Who is speaking? → Auto · English ↔ Mandarin** and leave **Bilingual** selected.
3. Click **Start lecture**. Speak English normally. When a student asks a Mandarin question,
   pause between speakers and let one person speak at a time.
4. Watch **Detected: English** or **Detected: Mandarin**. The displayed caption itself labels
   which language was spoken and which is the translation. Translation follows completed speech.
5. Finish the lecture normally. The same transcript folder contains both speakers.

The selector is also in **Teaching controls**, and Auto can be saved in a lecture preset.
You can switch to either manual language during a lecture. Finish the sentence and wait for
**Listening** after changing the selector. Switching while paused keeps the lecture paused.

## If the language is unclear

Auto waits for more speech before showing a partial caption. For an uncertain completed phrase,
it shows **Language unclear — select English or Mandarin and repeat**. Select the language
manually and ask the speaker to repeat. A very short reply such as “yes”, a name or an acronym
may need manual selection. Speaking a complete question usually provides more evidence.

Uncertain phrases are not silently forced into English or Mandarin. They are marked
**[Not transcribed]** in the bilingual text/VTT and recovery journal. Their audio is not saved.
Single-language text/SRT files contain only recognised speech and completed translations.
The app cannot reconstruct a withheld phrase after the fact; the speaker needs to repeat it.

## What Auto can and cannot establish

Whisper detects the language of each phrase locally. Partial captions need two strong,
consistent growing detections. Final phrases are checked again; disagreement is withheld.
English vocabulary and CO7000 guidance are used only after English is selected. Mandarin
recognition and translation have the same terminology limitations as the manual Mandarin mode.

Auto is intended for **one speaker and one main language per phrase**. It does not identify
speakers or reliably separate overlapping voices, detect every dialect, or guarantee correct
switching within a sentence. French/Spanish negative samples are tested, but that does not
establish rejection of every other language. Model confidence is not a calibrated probability
that a classroom caption is correct.

Detection adds processing and may delay initial captions while enough speech is collected.
Both translation directions are prepared when Auto starts; this can add roughly half a GiB
of RAM compared with English-only operation. No new model download beyond the 0.6 conversation
models is required. Existing acceleration and CPU recovery remain available.

Expanded public-recording, noise, short-speech, native UI and transcript checks are recorded
in the [test report](evidence/auto-language-0.7.md). They are development evidence, not classroom certification.
A rehearsal with your actual microphone, room and consented lecturer/student recordings is
still needed, especially for distant questions, technical vocabulary, names and numbers.
