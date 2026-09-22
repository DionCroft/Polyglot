# Your first lecture

Need to install first? Use the [Windows installation guide](INSTALLATION.md),
[Intel/AMD beta guide](WINDOWS_BETA.md) or [Mac guide](MACOS.md). No programming experience is needed.

LectureLive uses Whisper to recognise English or Mandarin and displays English and Simplified Chinese captions.
You do not need an account. Once setup is complete, speech and translation run on your computer.

## 1. Check your microphone

Connect the microphone you will teach with. In **Lecture**, choose it under **1 · Microphone**.
Select **Test microphone · 3 seconds** and speak. You should see a moving meter and a result.
If it is too quiet, move closer or adjust your microphone, then test again. No audio file is saved.

On Mac, choose **Allow** when asked for microphone access. If it was denied, enable
**System Settings → Privacy & Security → Microphone → LectureLive**, then quit and reopen the app.
On Windows, check **Settings → Privacy & security → Microphone**, including access for desktop apps.

## 2. Keep the recommended settings

Under **2 · Captions**, choose **English → 简体中文** under **Who is speaking?** for an English
lecture. Leave **Bilingual** and **Standard** selected. Use the starting profile below:

| Computer | Speech profile |
|---|---|
| Windows Snapdragon | **Balanced** |
| Windows Intel/AMD beta | **Fast** |
| Apple Silicon Mac | **Fast** |

Leave **Processing hardware** on **Automatic** where it is shown. The lecture title, subject
vocabulary and saved presets are optional. You can come back to these later.

**Save text transcripts and subtitles** is on by default. Untick it before starting if you do not
want saved text. Microphone audio is not recorded.

## 3. Start speaking

Wait for **Ready**, then select **Start lecture** at the bottom. Look for **Listening** and a moving meter.
Speak one or two sentences, with a short natural pause between thoughts. Captions appear in a floating
panel, called the **overlay**. Chinese follows the English after translation finishes.

Try: “The robot uses an ultrasonic sensor to estimate its distance from an obstacle.”

## 4. Use your projector

Open **Overlay**, choose the caption display, and select **Preview captions on selected display**
before starting a lecture. Adjust the text size for the back of the room. Unlock the panel to move it;
lock it to click through to your slides. Starting a lecture locks the overlay automatically.

## 5. Pause or finish

- **Pause** hides captions and discards unfinished speech. Select **Resume** to continue.
- **Stop lecture** finishes already captured speech, saves enabled transcripts, and stops listening.
  Wait while **Finishing…** is shown. Closing the app also finishes the session.
- **Teaching controls** gives you a small floating Pause/Finish panel while your slides are open.

| Action | Windows shortcut | Mac shortcut |
|---|---|---|
| Pause / resume | **Ctrl + Alt + Space** | **Control + Option + Space** |
| Lock / unlock captions | **Ctrl + Alt + C** | **Control + Option + C** |

Change shortcuts under **Overlay** if they conflict with another app, including VoiceOver on Mac.
In Mac shortcut settings, **Ctrl** means Control and **Alt** means Option. The screen buttons also work.

## Take a question in Mandarin

Finish your sentence, choose **Mandarin 普通话 → English** under **Who is speaking?**, and wait
for **Listening** before the student speaks. Try “请再解释一次。” (“Please explain again.”).
Then choose **English → 简体中文** and wait for **Listening** before answering. The selector is
also in **Teaching controls**. Audio during switching is not captured; the previous turn is finished
and saved first. Both directions stay in the same transcript folder.

English vocabulary and CO7000 hints are retained for English turns and are not used in Mandarin.
Read the [conversation guide](CONVERSATIONS.md) for examples and accuracy limitations.

## Find your saved text

Open **Diagnostics → Open transcripts**. Transcripts are available only for sessions where saving
was enabled. Audio is not recorded.

## If something looks wrong

Check the selected microphone and its test result first. If a device disconnects, reconnect it and
use **Reconnect / retry**. If captions lag, try **Fast / Standard** for your next session.
For missing files, close LectureLive and rerun **Setup.cmd** on Windows, or reinstall the Mac app
from the [Mac beta release](https://github.com/DionCroft/Polyglot/releases/tag/macos-v0.6.0b1).

This is a preview release. Review translations and rehearse with your actual microphone and
projector before relying on it in class. Read the [full user guide](USER_GUIDE.md),
[Mac guide](MACOS.md) or [Windows beta guide](WINDOWS_BETA.md) for more help.

## Words being missed?

Keep Standard if it works well for you. Try the optional Careful setting and relevant vocabulary
guidance separately before teaching. See [Improving speech recognition](SPEECH_RECOGNITION.md)
and [CO7000 weekly vocabulary](CO7000_VOCABULARY.md). Save useful choices as a preset for each lecturer.
