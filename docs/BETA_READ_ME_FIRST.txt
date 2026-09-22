LectureLive - Windows x64 Beta 0.7.0b1

1. Keep this entire folder together, including _internal.
2. Open LectureLive-x64-Beta.exe.
3. Select your microphone and click Test microphone.
4. Leave Processing hardware on Automatic, then click Start lecture.
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
