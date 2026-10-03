# Spoken translations — first test

Spoken audio is optional and starts **Off** each time you open LectureLive. Captions,
Whisper, translation models and saved transcripts are unchanged. System voices run
locally; a missing English or Mandarin voice needs a one-time installation first.

## Try it with laptop speakers

1. Open **Spoken audio**, choose **On demand · pauses listening**, then check the
   installed voices. Start with volume 30 and normal speed (0).
2. Start a lecture, speak one complete sentence, and wait for its translation.
3. Click **Speak last translation** (also in Teaching controls), or press
   **Ctrl+Alt+S**. On Mac this means Control + Option + S.
4. Listening pauses to avoid transcribing the computer's own voice. Wait until the
   audio finishes, then press **Resume** before the next person speaks.

English input produces Mandarin audio; Mandarin input produces English audio.
The button reads the last completed translation, not a provisional caption.
Finish your sentence first: Pause discards unfinished speech. The main caption
preview remains readable; Pause hides the projector overlay as usual. If a voice is
missing, listening is not paused just to report the missing voice.

**Stop audio**, or the same shortcut during playback, stops and clears queued audio.
Stopping audio changes automatic playback back to On demand. You can change the
shortcut under **Overlay → Speak / Stop shortcut → Apply shortcuts**.

## Automatic playback with headphones

Select **Automatic · headphones only** and tick the headphone confirmation. This
confirmation is required again for each new lecture. Only completed translations
that arrive after enabling automatic playback are spoken. Captions keep running.
Do not use this with loudspeakers: there is no acoustic echo cancellation, and the
microphone can recognise and translate playback again. Stop audio before unplugging
headphones or changing the system output device. Choose that device in Windows or
macOS sound settings; this beta uses the default system output.

Pause, resume, manual language switching, stopping and closing clear pending audio.
Automatic language changes within a conversation select the appropriate target voice.
Playback keeps at most one active phrase and two waiting phrases. Queued audio older
than 20 seconds is skipped with a notice; captions and saved text are kept. Text over
800 characters is not read live or silently shortened. A playback error or two-minute
timeout stops automatic audio while caption processing continues.

## Install a missing voice

### Windows 11

Open **Settings → Time & language → Speech → Manage voices → Add voices**. Add
**English** and **Chinese (Simplified, China)** as needed. On systems that show language
options instead, use **Language & region → Chinese (Simplified, China) → Language
options → Text-to-speech**. University computers may require IT to install these.
Return to LectureLive and click **Refresh installed voices**. If the new voice is
still absent, quit and reopen the app. Only installed Microsoft system voices exposed
by the speech engine are listed; installing a Narrator-only voice may not expose it
here. No registry changes or cloud account are required.

### Apple Silicon Mac

Open **System Settings → Accessibility → Spoken Content** (called **Read & Speak**
on newer macOS versions). Open the system voice options and download an English and
a Mandarin Chinese voice. Return to LectureLive and click **Refresh installed voices**;
restart the app if necessary. Voice names and quality differ between operating systems.

The app does not download voices during a lecture. Check playback in Airplane Mode
after installation. Voice generation is additional CPU work; measured classroom delay
and technical pronunciation still need testing on your machine. No extra Whisper or
translation models are needed.

## Send useful feedback

Try: **English → Chinese:** “The project risk register lists the probability and
impact of each risk.” Then **Mandarin → English:** “请解释一下项目的风险。”

Tell us your computer, voice name, playback mode, speakers/headphones, the caption
that appeared, what sounded wrong, and whether Pause, Resume or Stop behaved as
expected. Start with a five-minute rehearsal; do not enable automatic loudspeaker
playback during a class. Technical acronyms and proper names may sound different
from their spelling. Audio repeats translation mistakes; it does not correct them.
No microphone recording or generated audio export is added by this feature.
