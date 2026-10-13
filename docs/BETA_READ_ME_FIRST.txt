LectureLive - Windows x64 Beta 0.7.2b1

1. Keep this entire folder together, including _internal.
2. On an Intel i5-1035G1 / 16 GB laptop, open Launch-CPU.cmd.
   INSTALL-INTEL.md has the first-use guide. Other PCs can open LectureLive-x64-Beta.exe.
3. Select your microphone and click Test microphone.
4. For the CPU launcher, keep Fast / Standard / CPU; then click Start lecture.
   With the normal EXE, Automatic remains available. No NPU preparation is needed for i5-1035G1.
5. Choose English -> Chinese under Who is speaking? and pause naturally between sentences.
   For a student question choose Mandarin -> English, wait for Listening, then let them speak.
   Switch back to English before answering. Audio during switching is not captured.
   Both directions stay in one transcript folder. English vocabulary/CO7000 hints apply only
   to English turns. Both translation models are included; Mandarin support is a beta.
6. For hands-free turns, choose Auto under Who is speaking? and keep Bilingual selected.
   Pause between speakers. If Language unclear appears, choose the language manually
   and repeat the complete sentence. Short replies may be withheld and marked in
   the bilingual transcript. Open Quick start > Automatic language switching.
7. Stop lecture and wait for the last caption to finish saving.

CPU captions and compatible DirectML GPU acceleration are available to try.
Intel/AMD NPU support is experimental and needs separate preparation on this PC.
Open Quick start > Windows Intel/AMD beta for the complete guide and test status.
GPU/NPU accelerates the speech encoder; decoding and translation stay on CPU.
The app falls back to CPU if an accelerator fails verification.

This build has been tested under x64 emulation on a Snapdragon Surface, including
real DirectML execution on Adreno. Physical Intel/AMD GPU and NPU tests are pending.
Use your actual classroom microphone and projector for a practice run first.

Preferences and transcripts: %LOCALAPPDATA%\LectureLive Beta
Contact: Dr Dion Miroy Mariyanayagam, d.mariyanayagam@londonmet.ac.uk

Words being missed? Open Quick start > Improving speech recognition.
Standard recognition keeps the previous behaviour. Careful and vocabulary hints
are optional and should be tested with each speaker before teaching.

RELIABILITY UPDATE 0.7.2b1
If Audio was lost appears, repeat the sentence. Captured speech before a gap is
retained where usable, but missing audio cannot be recovered. Close heavy apps;
if warnings repeat, finish the session and try Fast / Standard.
All saved text/subtitles mark known audio gaps as [Audio lost]. Language files
wait for earlier translations to keep the conversation in chronological order.
Quick start > Audio loss and transcript recovery explains warnings and recovery.

OPTIONAL SPOKEN AUDIO
Open Spoken audio, choose On demand, wait for a translation and click Speak last translation.
Listening pauses during speaker playback. Press Resume afterwards. Ctrl+Alt+S speaks/stops.
Automatic audio is for headphones only. Audio starts Off each time you open the app.
Missing English/Mandarin voices can be installed in Windows Speech settings.
See Help > Spoken translations and voice setup for instructions and a feedback checklist.

STUDENT PHONE CAPTIONS (0.8.0b1+)
Open Student phones, select the trusted classroom network, then Start sharing.
Students scan the QR code on the same Wi-Fi to read, scroll back, search, copy
and download bilingual captions. No internet or account is needed.
Stop sharing closes the private link. Anyone with the link on your network
can read the shared text; local HTTP is not encrypted.
Use Connection help for full instructions, privacy and Wi-Fi troubleshooting.
