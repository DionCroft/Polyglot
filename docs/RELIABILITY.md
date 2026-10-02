# Audio loss and transcript recovery — 0.7.1 beta

## If you see Audio was lost

1. Repeat the affected sentence clearly into the selected microphone.
2. Close other demanding applications. If the warning continues, finish the lecture,
   choose **Fast / Standard**, and start a short practice session.
3. Check **Diagnostics → Open transcripts** after finishing. Known missing intervals
   appear as **[Audio lost]** in English, Chinese and bilingual text/subtitle files.

The warning appears in both the main window and **Teaching controls**. Repeated
warnings are limited to one every five seconds so they do not flood the controls.
The app finishes usable speech captured before a detected gap, then starts a new
phrase after it. **Missing audio cannot be recovered** and is never invented.

**Pause** intentionally discards unfinished speech. Audio while paused or while a
manual language switch is in progress is intentionally ignored, not labelled an
input failure. Wait for **Listening** before the next speaker begins.

## Why a saved language file may update a little later

During an Auto conversation, an earlier translation may still be running when the
next person speaks. Live recognised captions and the local journal continue. A
saved English or Chinese file waits for that earlier result before adding later
text, so the question and answer remain in chronological order. Finish the session
and wait for **Finishing…** to complete before reading or sharing the files.

**[Not transcribed]** means Auto could not confidently identify the language; select
English or Mandarin manually and repeat. This differs from **[Audio lost]**, which
means an interval of input audio was missing. Failed translations retain recognised
source text; no translation is invented.

## Recover text after an interrupted session

1. Open **Diagnostics → Open transcripts** and find the session folder.
2. Choose **Recover transcript journal…** and select that folder's `events.jsonl`.
3. Read the newly created recovery folder. The original files are kept.

Recovery restores text and notices already written to the journal. It cannot recover
missing audio, unfinished recognition or an unfinished translation. Old 0.7 journals
remain readable. Gap markers from 0.7.1 need 0.7.1 or later for recovery.

## What changed and what to test before class

There are no new models, model downloads or recognition settings. Offline Whisper,
translation, English/Mandarin selection, Auto thresholds and the pre-rolling overlay
are retained. Existing long-caption display and Auto short-phrase limitations remain.

Buffers remain bounded: 128 audio blocks (about 4.1 seconds), four queued speech
items, four queued translations and at most 32 pending export turns in the live
pipeline. If processing cannot keep up, finishing accepted speech may delay captions;
the app warns about capture loss rather than silently replacing completed phrases.

Before teaching, try English and Mandarin questions with the intended microphone,
check the six saved files, then try Pause/Resume and a manual language switch. Use
Airplane Mode after initial setup. A full lecture rehearsal and native-speaker review
are still required; automated tests do not certify classroom accuracy.
