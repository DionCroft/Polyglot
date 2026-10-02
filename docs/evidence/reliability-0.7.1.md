# Reliability update 0.7.1b1 — 3 October 2026

Base: pre-rolling main `3b6c4f5`. No speech/translation models, inference settings,
Auto thresholds, presets or overlay layout changed. An unrelated local whitespace
edit in `app/system/accelerators.py` is excluded from the commits.

## Regression-first verification

Before production edits, five new cases failed: lost pre-gap speech, missing overflow
warning, out-of-order separate exports in both initial directions, and a missing
trailing gap on stop. After implementation, 126 tests pass on Windows ARM64 and on
Windows x64 under ARM emulation; two POSIX-only tests skip in each environment.
The additional cases use stub inference and real processing threads where applicable.
They cover actual bounded-queue overflow, midstream/trailing gaps, manual/Auto routing,
switch barriers, intentional pause, delayed translation, failed/uncertain turns,
shutdown and byte-identical recovery of all six text/subtitle exports. A stalled
translation test verifies the live export reorder-buffer bound.

The real local CPU Base, QNN Base and QNN Small comparison exactly matches all
36 English speech cases and 40 English-to-Chinese translation cases in the prior
baseline. This verifies unchanged fixed outputs, not native-speaker quality.

The native Windows source UI replay passed English/Mandarin audio, manual and paused
switching, minimum controls, saved transcripts and warning forwarding into Teaching
controls. An initial UI assertion was raced by a queued WAV-finished notice; the check
now verifies synchronous forwarding before processing unrelated notifications.
Both final Windows packages pass the five checks described below. Native Mac release
verification is recorded separately below. Physical Intel/AMD, M2 Air microphone/thermal/
projector and actual lecturer classroom checks remain open.

## Design and trade-offs

The microphone callback only enqueues or counts a drop. Worker/UI diagnostics emit
throttled warnings. The VAD worker finishes usable pre-gap audio, emits a timestamped
AudioGap, and resets before the next captured block. Stop and manual switch barriers
also account for a missing tail. All final speech and markers are drained through the
bounded queue; overload can cause new capture loss, but cannot evict an accepted final.
Pause still discards unfinished speech for privacy.

Each language export advances in chronological order independently. During normal
processing, source captions and journal entries are immediate; a file may wait behind an earlier translation into
that language. The live pipeline limits pending export turns to 32. Gap and uncertain
markers are saved in all six files and understood by journal recovery. Missing
translations remain absent rather than being invented. The models need no extra disk
space; bookkeeping is bounded and does not require another inference model.

## Warning layout follow-up

Visual inspection of the source UI found a long warning could be clipped in Teaching
controls. The panel now sizes the label to its wrapped content and expands as needed.
A second native Windows UI replay passed, asserting both full warning height and a
visible Finish lecture button; the saved image was visually inspected.
[UI report](reliability-071-warning-ui.json) · [Verified warning image](reliability-071-teaching-warning.png).

A further failing regression reproduced Stop occurring during the callback's meter
calculation. The last-capture timestamp now advances only after the Stop/Pause check,
so this intentionally rejected frame does not create a false trailing audio-gap
marker. The complete suite then passed 126 tests on both Windows runtimes (two
POSIX-only skips each). This change does not alter any model or decode settings.

## Final Windows packages

Built from `8718fbb86d3fe9b3fd0c0dde1b4eee9cd6ddea61`, including the stop/callback
regression fix and full Teaching warning layout. The only excluded working-tree
change is the unrelated whitespace edit noted above. The embedded app version is
`0.7.1b1` in both executables.

| Check | Windows ARM64 | Windows x64 |
|---|---|---|
| Complete regression suite | 126 passed, 2 POSIX skips | 126 passed, 2 POSIX skips |
| Offline English/CO7000 packaged self-test | Passed | Passed |
| Mandarin recognition and both translation directions | Passed | Passed |
| Manual/paused switching and complete warning UI | Passed | Passed |
| Auto conversation and Auto UI replay | Passed | Passed |
| Bundled model/dependency member hashes | 42 verified | 29 verified |
| All six exports: chronology and byte-identical recovery | 4 sessions | 4 sessions |

Windows ARM64 ran natively on a Snapdragon X Elite Surface with CPU/Qualcomm NPU
checks. x64 ran under Windows ARM emulation; DirectML executed on its Adreno GPU.
These results do not establish physical Intel/AMD GPU or NPU compatibility.

Each final Auto replay produced eight completed pairs in English → Mandarin →
English order and two uncertain-language notices. No audio blocks, final phrases
or translations were dropped in these normal-speed replays. The deliberate overflow,
delayed/failed translation and stop/pause/switch cases use controlled regression
fixtures and stub inference. Public recordings and WAV injection do not test a real
microphone, classroom acoustics or either lecturer's speech.

All English/Chinese/bilingual TXT, both SRT and bilingual VTT files were independently
checked for chronological timestamps and byte-identical journal recovery across
eight packaged sessions. The regression suite additionally checks gap and uncertain
markers, delayed and failed translations, and an interrupted journal.

[Final Windows summary and executable hashes](reliability-071-windows-summary.json)
· [ARM64 suite](reliability-071-arm64.xml) · [x64 suite](reliability-071-x64.xml)
· [Unchanged 36-speech / 40-translation outputs](reliability-071-english-regression.json).

The final executable locations are `dist/LectureLive/LectureLive.exe` and
`dist/LectureLive-x64-Beta/LectureLive-x64-Beta.exe`. Keep each adjacent `_internal`
folder. Both portable ZIPs were verified against every archived member's SHA-256:

| Portable archive under `recovery/` | Size (decimal) | Verified files |
|---|---|---|
| `LectureLive-Windows-ARM64-Beta-0.7.1b1.zip` | 1.527 GB | 599 |
| `LectureLive-Windows-x64-Beta-0.7.1b1.zip` | 748.3 MB | 1,376 |

Each has an adjacent `.zip.sha256`; its internal `SHA256.json` lists member hashes.
[ARM64 receipt](reliability-071-arm64-zip.json) · [x64 receipt](reliability-071-x64-zip.json).
The archives include documentation from their tested build commit; this report on
GitHub records the subsequent final package verification.

## Native Apple Silicon build

[Build 37041298927](https://github.com/DionCroft/Polyglot/actions/runs/37041298927)
completed successfully for the same tested commit on native macOS 14.8.9 ARM64:
**128 tests passed, no skips**. The pinned dependencies/models passed offline
verification and the configured Ruff checks passed.

The packaged app passed English/CO7000 inference, both conversation directions,
manual/paused switching, Auto and native Cocoa UI checks. The full loss warning and
Finish lecture control fit in the Mac Teaching panel; its saved screenshot was also
visually inspected. Native shortcuts, overlay flags, permission-handler integration,
strict code-signature verification and DMG/ZIP creation passed. Permission integration
is not evidence of physical microphone capture or the first-install user prompt.

Whisper Base executed with CPU and Core ML. Requested Small Core ML compilation
again timed out and successfully fell back to CPU, as in the existing Mac edition;
this update does not change that behavior. Core ML ran, but individual GPU/Neural
Engine execution was not verified. These checks use a hosted Apple Silicon runner,
not a physical M2 MacBook Air classroom setup.

The CPU Auto replay completed seven pairs and withheld three uncertain phrases; the
Auto UI replay completed eight pairs and withheld two. Both retained English →
Mandarin → English direction order and journal recovery with no capture/translation
queue drops in the CPU replay. This differs by inference backend and short phrase;
no Auto thresholds were adjusted.

A separate 120-case public-speech language check accepted no wrong language in this
small sample. It accepted all 12 supported-language clean clips, but only 4 of 12
one-second variants. Other-language clips were withheld. This measures language
routing, not transcription/translation correctness, and reinforces the need for
manual selection when brief questions are withheld.

[Native suite](reliability-071-macos-pytest.xml) ·
[CPU/Core ML and fallback](reliability-071-macos-packaged.json) ·
[Conversation checks](reliability-071-macos-conversations.json) ·
[Auto replay](reliability-071-macos-auto.json) ·
[Language routing](reliability-071-macos-auto-evaluation.json) ·
[Warning screenshot](reliability-071-macos-teaching-warning.png).

The Mac app requires **Apple Silicon and macOS 14 or later**. It is ad-hoc signed,
not Developer ID signed or Apple notarised. [Publication run 37043421583](https://github.com/DionCroft/Polyglot/actions/runs/37043421583)
completed successfully. The [published 0.7.1b1 Mac release](https://github.com/DionCroft/Polyglot/releases/tag/macos-v0.7.1b1)
contains the DMG (1.220 GB), ZIP (1.173 GB), installation guide and checksums. Its tag
resolves to the exact tested build commit. Both published installer SHA-256 digests
match the native build's checksum file. See the [publication receipt](reliability-071-macos-release.json),
[checksums](reliability-071-macos-SHA256SUMS.txt), and [Mac installation guide](../MACOS.md).

## Before teaching

1. Extract the correct complete Windows ZIP, or install the Mac DMG, and confirm
   **About → 0.7.1b1**. Select and test the actual teaching microphone.
2. In English mode, speak a short course paragraph. Then switch manually to Mandarin
   for a question and back to English for the answer. Wait for **Listening** between
   manual switches. Try Auto separately and repeat any withheld short question.
3. Pause/resume and finish the session. Check that all six text/subtitle files follow
   the question/answer order. Use **Recover transcript journal…** on this practice
   session and compare the new recovery folder with the originals.
4. Rehearse a full lesson with the projector, after initial setup in Airplane Mode.
   If **Audio was lost** appears, repeat the sentence and close demanding apps; if it
   persists, finish and retry with Fast/Standard. A known gap is marked **[Audio lost]**;
   missing audio cannot be recovered. Do not overload a live class deliberately.

Native-speaker review of English/Mandarin technical vocabulary and recordings of both
lecturers are still needed to judge classroom word and translation accuracy. The
pre-rolling overlay retains its existing long-caption display limits.
