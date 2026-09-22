# LectureLive

**Teach in English. Take questions in Mandarin. Show both languages together.**

LectureLive displays a floating caption panel over your slides, desktop or projector.
It uses **Whisper** for **English → Simplified Chinese** and **Mandarin Chinese → English**
captions, with translation on your computer. English remains the default. After installation,
everyday use needs **no internet connection, account or API key**.

You do not need programming experience. The Mac download is a ready-made app; Windows users
double-click a setup file that prepares everything for them.

![LectureLive captions showing Mandarin speech and its English translation](docs/evidence/auto-overlay-0.7.png)

**New in 0.7.0b1, included in the main application:** choose **Auto · English ↔ Mandarin**
to change direction as speakers take turns. Manual selection remains available and English
remains the default. [Auto guide](docs/AUTO_LANGUAGE.md) · [Test results](docs/evidence/auto-language-0.7.md).

> **Preview/beta software:** rehearse with your teaching microphone and projector before a lecture.
> Captions and translations can contain mistakes. [What has been tested](STATUS.md).

## Start here: choose your computer

| Your computer | Where to start |
|---|---|
| **Windows 11, Snapdragon / ARM64** | [Install on Windows](#install-on-windows). Setup selects the Snapdragon edition. |
| **Windows 11, Intel or AMD / x64** | [Install on Windows](#install-on-windows). Setup selects the Intel/AMD beta. |
| **Apple Silicon Mac: M1 or newer, including M2 MacBook Air** | [Install on Mac](#install-on-mac). Requires **macOS 14 Sonoma or later**. |

**Not sure which computer you have?** On Windows, open **Settings → System → About → System type**.
On a Mac, open **Apple menu → About This Mac** and look for **Chip** and the macOS version.
Intel Macs, Windows 10, 32-bit Windows and Linux are not supported by these builds.

Already installed? Go straight to [your first captions](#your-first-captions).

## Install on Windows

**Before you start:** connect to the internet, plug in your computer and allow at least **15 GB of
free disk space** for setup. Have your teaching microphone available. Setup downloads several GB;
it may take several minutes or longer on a slow connection.

1. Open [the Polyglot repository](https://github.com/DionCroft/Polyglot).
2. Select the green **Code** button, then **Download ZIP**.
3. Find the ZIP in Downloads. Right-click it and select **Extract All…**.
4. Keep the extracted folder somewhere permanent, such as
   `C:\Users\YourName\Documents\LectureLive`. Open the folder containing **Setup.cmd** and this README.
5. Double-click **Setup.cmd**. If file extensions are hidden, it may appear as **Setup** with
   the type **Windows Command Script**. **Run it from the extracted folder, not inside the ZIP.**
6. Keep the setup window open through all three stages. Wait for **SETUP COMPLETE**, then press a key
   to close the window.
7. Double-click **Launch.cmd** in the same folder. You can also use the Start menu shortcut:
   **LectureLive** on Snapdragon, or **LectureLive-x64-Beta** on Intel/AMD.
8. Continue to [your first captions](#your-first-captions).

Setup automatically selects the correct edition and installs its own private Python runtime,
speech models and translation files. You do **not** need to install Python, Git or CUDA yourself,
or type terminal commands. Keep the extracted folder in place: the launcher and models live there.

**Download interrupted or setup stopped?** Run **Setup.cmd** again from the same folder. Verified
downloads are reused and supported downloads resume. Keep **setup.log** from that folder if you need help.

**Windows blocks setup or the app?** These builds are unsigned. Follow your organisation's software
approval process or share the message with IT. Do not disable antivirus or change permanent
PowerShell settings.

GPU acceleration and Intel/AMD NPU options are covered in the [Windows beta guide](docs/WINDOWS_BETA.md).
NPU preparation is optional and experimental; it is not needed to start using captions.
Physical Intel/AMD GPU/NPU validation is still pending.

### If someone gave you a complete Windows app folder

Extract or copy the **whole folder**, then open **LectureLive.exe** (Snapdragon) or
**LectureLive-x64-Beta.exe** (Intel/AMD). Keep the adjacent **_internal** folder: it contains the
models and other files the app needs. A complete copy for your PC needs no initial setup download.
The repository's **Code → Download ZIP** contains source code and needs **Setup.cmd** first.

## Install on Mac

Use an **Apple Silicon Mac running macOS 14 or later**. The conversation Mac beta is **0.7.0b1**.
The DMG download is about **1.22 GB** (ZIP alternative: **1.17 GB**). The speech and both translation models are included; the app runs offline after downloading.

1. [Download LectureLive for Apple Silicon — DMG](https://github.com/DionCroft/Polyglot/releases/download/macos-v0.7.0b1/LectureLive-0.7.0b1-macOS-AppleSilicon.dmg).
   Alternatively, open the [Mac beta release page](https://github.com/DionCroft/Polyglot/releases/tag/macos-v0.7.0b1)
   and choose the **.dmg** under **Assets**. Do not choose **Source code**.
2. Open the downloaded DMG. Drag **LectureLive** onto **Applications**, wait for copying to finish,
   then eject the DMG.
3. Open **Finder → Applications → LectureLive**.
4. This beta is **not Apple notarised**. If macOS blocks it, open **System Settings → Privacy & Security**,
   find the message about LectureLive and choose **Open Anyway**, then confirm **Open**.
   Only approve the copy downloaded from this repository. A managed university Mac may need IT approval.
5. Select your microphone and click **Test microphone · 3 seconds**. Choose **Allow** when macOS asks
   to access the microphone.
6. Continue to [your first captions](#your-first-captions).

If microphone access was denied, open **System Settings → Privacy & Security → Microphone**,
enable **LectureLive**, then quit and reopen the app. If **Open Anyway** is absent or the download
is reported as damaged, see the [Mac installation and troubleshooting guide](docs/MACOS.md).

The first speech-model preparation can take a few minutes. **Automatic** processing has a CPU
fallback if acceleration fails. Native Apple Silicon build checks have passed; a physical M2
classroom test with real microphones and projectors is still needed. The Mac guide explains
performance choices, the ZIP alternative and current limitations.

## Your first captions

1. **Open LectureLive** and wait for **Ready**. Connect the microphone you will teach with.
2. **Select and test your microphone.** Click **Test microphone · 3 seconds** and speak.
   Check that the meter moves and read the test result. If you connect a microphone after opening
   the app, use the refresh button beside the microphone list.
3. **Choose English → 简体中文 under Who is speaking?** Keep **Bilingual** and **Standard** selected.
   Start with the speech profile below. Where
   **Processing hardware** is shown, leave it on **Automatic**. Lecture details and presets are optional.
4. **Choose whether to save text.** **Save text transcripts and subtitles** is on by default.
   Untick it before starting if you do not want saved text. Microphone audio is not recorded.
5. **Click Start lecture.** Speak a sentence and pause briefly. Try:
   “The robot uses an ultrasonic sensor to estimate its distance from an obstacle.”
   Captions appear in the floating panel; Chinese follows after translation finishes.
6. **Pause or finish.** **Pause** hides captions and discards unfinished speech; **Resume** continues.
   **Stop lecture** finishes captured speech and saves text if enabled. Wait for **Finishing…** to end
   before closing the app.

| Computer | Speech profile for your first try |
|---|---|
| Windows Snapdragon | **Balanced** |
| Windows Intel/AMD beta | **Fast** — this edition currently includes only Fast |
| Apple Silicon Mac | **Fast** — particularly for an 8 GB MacBook Air |

**Next time:** use the Windows launcher/Start menu shortcut or **Applications → LectureLive** on Mac.
You do not need to repeat installation. The **Quick start** button opens help inside the app, even offline.

## Show captions with your slides

1. Connect the projector or second display before your rehearsal.
2. Open **Overlay**, choose the **caption display**, then click **Preview captions on selected display**.
3. Adjust the text size and position so the back of the room can read it. Unlock the caption panel
   to move it; lock it to click through to your slides. Starting a lecture locks it automatically.
4. Use **Teaching controls** for a small floating Pause/Finish panel alongside your slides.

| Action | Windows shortcut | Mac shortcut |
|---|---|---|
| Pause / resume | **Ctrl + Alt + Space** | **Control + Option + Space** |
| Lock / unlock captions | **Ctrl + Alt + C** | **Control + Option + C** |

Change shortcuts under **Overlay** if another app uses them. On Mac, the settings use **Ctrl** for
Control and **Alt** for Option; VoiceOver may use these combinations. The on-screen buttons also work.
Test captions over your actual slide presentation, including full-screen mode, before teaching.

## Let students ask questions in Mandarin

For hands-free conversation, choose **Who is speaking? → Auto · English ↔ Mandarin**, keep
**Bilingual** selected, and start the lecture. Finish your English sentence, then let the student
ask their Mandarin question. Pause briefly between speakers. Both must be audible through the
selected microphone. Watch **Detected: English** or **Detected: Mandarin**. No selector changes
are needed between accepted turns. The same option is in **Teaching controls**.

**If you see Language unclear**, select English or Mandarin manually and ask the speaker to repeat.
Short replies, names and acronyms are harder to detect. Auto can withhold a phrase, including
meaningful words; the bilingual transcript marks it **[Not transcribed]**. A complete question
usually provides more evidence. Use manual mode if Auto repeatedly misses short exchanges.

To select the language manually during the same lecture:

1. Finish your English sentence and choose **Mandarin 普通话 → English** under **Who is speaking?**.
2. Wait for **Listening**. The app finishes the captured turn before changing language;
   anything spoken during **Switching language…** is not captured.
3. Let the student ask their question, for example **“请再解释一次。”** (“Please explain again.”).
4. Read the English translation beside the recognised Simplified Chinese. Each line is labelled
   **spoken** or **translation**.
5. Choose **English → 简体中文**, wait for **Listening**, then answer in English.

Keep **Bilingual** selected to show both languages. Only one person should speak at a time.
Your microphone, projector, shortcuts and transcript folder stay the same. Switching while paused
keeps the lecture paused. Saved presets remember the speaking language; older presets use English.

Auto is designed for one speaker and one main language per phrase. It does not reliably separate
overlapping voices or switches within a sentence. Expanded public speech, noise and software checks
are documented in the [Auto test report](docs/evidence/auto-language-0.7.md). **Classroom validation
with your microphone and both lecturers is still needed.** Language detection does not guarantee
correct words or translation; Mandarin homophones, dates and technical terms still need review.

The additional offline translation model adds **172.7 MB** to setup and packaging. It loads on the
first Mandarin turn, or when preparing Auto, then stays cached. One Snapdragon test measured about **527 MiB extra RAM**
when loading it; other computers can differ. It can add caption delay and first-switch preparation
time. Windows setup includes it automatically; install the **0.7.0b1** Mac build to obtain it on Mac.
The older Mac **0.5.0b1** does not have conversation support.

## Improve missed words and use CO7000 vocabulary

Keep **Standard** and vocabulary guidance off if recognition already works well for you.
Try changes while the lecture is stopped, using a short passage and your usual microphone:

1. Choose **English → Simplified Chinese** when comparing English words, and test your microphone.
   On Snapdragon or Apple Silicon, try **Balanced** for the larger Whisper model.
2. Start with **Standard**, then compare it with **Speech recognition → Careful**.
   Careful checks more possible word sequences, can be slower and does not help every speaker.
3. For technical words, enter a short relevant list under **Today's vocabulary**, one term per line,
   then tick **Use these terms to guide speech recognition**.
4. For **CO7000**, choose the week and click **Use this week's terms**. This replaces the current list
   and selects **Project Management**. Save any custom list as a preset first. Tick vocabulary guidance
   separately if you want to use the terms as speech hints.
5. Compare the captions, then save useful choices as a **lecture preset**. Each lecturer can have
   their own preset. Return to Standard and untick guidance if a change makes recognition worse.

Careful and vocabulary hints do not guarantee better accent recognition; results were mixed with
the smaller Fast model. Balanced and Careful can increase memory use and caption delay.
[Speech settings and measured results](docs/SPEECH_RECOGNITION.md) ·
[Five-minute check with your colleague](docs/ACCENT_CHECK.md) ·
[CO7000 weekly vocabulary guide](docs/CO7000_VOCABULARY.md).

**Expanded accent testing:** 120 additional public recordings support trying Balanced first.
On the tested Snapdragon, it reduced Indian-English word errors from 6.80% to 4.76%
compared with Fast; the English controls improved too. Hints sometimes omitted a spoken
name, so check the whole sentence before keeping them on. These are public speakers,
not your colleagues; [read the results and limitations](docs/evidence/indian-english-2026-09-23.md).

English vocabulary, glossary corrections and CO7000 hints are preserved when switching, but are
**not applied to Mandarin turns**. There is no reviewed reverse CO7000 glossary yet. For example,
**关键路径** may translate as “key route” instead of “critical path”. See the
[conversation guide](docs/CONVERSATIONS.md) for direction-specific limitations.

## Help with common problems

| What you see | What to do |
|---|---|
| Windows setup stops during a download | Check internet and disk space, close LectureLive, then rerun **Setup.cmd** in the same folder. Read **setup.log** if it stops again. |
| Launch says the app is not ready | Run **Setup.cmd** and wait for **SETUP COMPLETE**. |
| Windows microphone has no moving meter | Select the correct input, refresh and retest. Open **Settings → Privacy & security → Microphone** and enable microphone access, including access for desktop apps. |
| Mac microphone is unavailable | Enable **System Settings → Privacy & Security → Microphone → LectureLive**, then quit and reopen the app. |
| A microphone disconnects | Reconnect it and use **Reconnect / retry**. If needed, stop the lecture, refresh the microphone list and select it again. |
| English appears but Chinese does not | Select **Bilingual** and read any warning. For missing files, close the app and rerun Windows setup, or reinstall the Mac app from the release download. |
| Captions are slow | Try **Fast / Standard** for the next session, close heavy applications and pause naturally between sentences. |
| Mandarin speech produces incorrect captions | Check **Who is speaking?** is set to **Mandarin 普通话 → English** and wait for **Listening** before speaking. Speak one language at a time. |
| Auto says Language unclear | Choose the language manually and repeat the complete sentence. Read [Auto help](docs/AUTO_LANGUAGE.md). |
| Switching says the Mandarin model is missing | Close the app and rerun the current Windows **Setup.cmd**, or install the 0.7.0b1 Mac app. The previous speaking language is retained. |
| An accelerator check fails or takes too long | On Mac or the Intel/AMD beta, stop the lecture and select **CPU** under Processing hardware. See the platform guide for details. |
| Captions are on the wrong screen | Open **Overlay** and select the projector or preferred caption display. |
| You want your saved text | Open **Diagnostics → Open transcripts**. Text is saved only when the transcript option is enabled. |

More help: [Quick start](docs/QUICK_START.md) · [User guide](docs/USER_GUIDE.md) ·
[English and Mandarin conversations](docs/CONVERSATIONS.md) ·
[Mac guide](docs/MACOS.md) · [Windows beta guide](docs/WINDOWS_BETA.md) ·
[Windows installation and repair](docs/INSTALLATION.md) · [Windows offline recovery](docs/OFFLINE_SETUP.md).

## Updates, saved data and removal

**Update Windows:** close LectureLive, download and extract the new source ZIP into a new folder,
then run its **Setup.cmd**. Keep your previous working copy until the new one works. The Start menu
shortcut will point to the new copy.

**Update Mac:** quit LectureLive, download the new Mac installer and replace LectureLive in
**Applications**. Keep your previous installer until the update works.

Settings, presets and saved text are stored separately from the app. Back up important transcripts
before updating. **Diagnostics → Open transcripts** is the easiest way to find saved text.

| Edition | Personal data folder |
|---|---|
| Windows Snapdragon | `%LOCALAPPDATA%\LectureLive` |
| Windows Intel/AMD beta | `%LOCALAPPDATA%\LectureLive Beta` |
| Mac | `~/Library/Application Support/LectureLive` |

To open a Windows path, press **Windows + R**, paste the path and press Enter. On Mac, use
**Finder → Go → Go to Folder…** and paste the path.

**Remove Windows:** close the app, delete its extracted application/setup folder and remove its
Start menu shortcut. **Remove Mac:** quit the app and move LectureLive from Applications to the Bin.
These steps leave personal data intact. Only delete the matching data folder above if you also
want to permanently remove settings, presets and transcripts.

## Project contact

**Dr Dion Miroy Mariyanayagam BEng (Hons) PGCert FHEA PhD MIET CEng**

Senior Lecturer of Electronic and Embedded Systems

Course Leader for:

- BEng (Hons) Computer Systems Engineering and Robotics
- BEng (Hons) Electronics Engineering and IoT
- MSc Robotics with AI

School of Computing and Digital Media

Department of Communications Technology and Mathematics

London Metropolitan University

**Email:** [d.mariyanayagam@londonmet.ac.uk](mailto:d.mariyanayagam@londonmet.ac.uk)

These details are also available under **About** in the application.

## For developers

The sections above cover normal installation and teaching. The repository also contains source,
glossaries, pinned setup manifests, documentation and synthetic/public test evidence. Large models,
runtimes, executables, recordings and private transcripts are excluded from Git.

For Windows development, use the private ARM64 runtime created by setup (replace `runtime` with
`runtime-x64` for the Intel/AMD beta):

```powershell
.\runtime\python.exe -m pytest -q
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -VerifyOnly
```

For Mac development and packaging, follow [Build from source](docs/MACOS.md#build-from-source-optional-for-maintainers).

[Architecture](docs/ARCHITECTURE.md) · [Model licences](docs/MODEL_LICENSES.md) ·
[Translation evaluation](docs/TRANSLATION_EVALUATION.md) · [Acceptance checklist](docs/ACCEPTANCE_TESTS.md).
