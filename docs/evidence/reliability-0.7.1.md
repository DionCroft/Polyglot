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
Packaged Windows and native Mac checks are pending at this implementation milestone.
The native macOS workflow will run on the pushed main commit. Physical Intel/AMD,
M2 Air microphone/thermal/projector and actual lecturer classroom checks remain open.

## Design and trade-offs

The microphone callback only enqueues or counts a drop. Worker/UI diagnostics emit
throttled warnings. The VAD worker finishes usable pre-gap audio, emits a timestamped
AudioGap, and resets before the next captured block. Stop and manual switch barriers
also account for a missing tail. All final speech and markers are drained through the
bounded queue; overload can cause new capture loss, but cannot evict an accepted final.
Pause still discards unfinished speech for privacy.

Each language export advances in chronological order independently. Source captions
and journal entries are immediate; a file may wait behind an earlier translation into
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
