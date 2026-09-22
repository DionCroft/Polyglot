# Acceptance ledger — LectureLive

Implementation checks and classroom acceptance are separate. The intended teaching
setup is assumed to have a microphone. Tests using the built-in microphone verify
capture here; they do not stand in for a rehearsal with the actual lecture microphone.

## Conversation beta 0.6.0b1

See [conversation verification](evidence/conversations-0.6.md) for current platform results.
The historical checks below remain useful; they are not new Mandarin accuracy evidence.

For a classroom rehearsal, use consented English and Mandarin speakers and:

1. Teach a short English passage with the existing settings and CO7000 week selected.
2. Finish the sentence, switch **Who is speaking?** to Mandarin, and wait for **Listening**.
3. Ask a Mandarin question with a technical term, a number and a negative statement.
   Check the recognised Chinese against the recording and have a bilingual reviewer check
   the English meaning. English CO7000 corrections do not apply to this direction.
4. Switch back to English and answer. Repeat in the compact Teaching controls and while paused.
   Check the microphone and selected profile have stayed the same, and pause remains paused.
5. Finish and open the saved transcript. Verify both speakers, language labels, timestamps,
   source-language text after a translation failure, and the SRT/VTT files.
6. Repeat with airplane mode enabled, your projector and normal question distances.
   Include very short questions, names, dates and mixed English/Chinese speech. Record errors
   and caption delay separately; the automatic tests do not establish language accuracy.

## Earlier automated and local checks

| Area | Evidence |
|---|---|
| Graceful Stop | Regression finishes an utterance with no trailing silence and saves its translation |
| Disk-full/write cleanup | Regression contains both write and cleanup errors; all handles attempted |
| Journal recovery | Truncated final record, torn UTF-8 and non-object records skipped; source preserved |
| Pause privacy | Queued and in-flight recognition invalidated; callback cannot relabel old audio with a new epoch |
| Bilingual continuity | Completed pair retained until replacement; stale results rejected; failures explicit |
| Sentence boundaries | Short pause requires a sentence-ending hypothesis; ongoing speech stays intact |
| NPU runtime recovery | Same phrase retried on CPU in a simulated device-failure regression |
| Presets and shortcuts | Persistence, validation, conflict-safe application and native UI workflow |
| Microphone check | Real three-second RAM-only capture and level assessment; no file recording |
| Compact controls/retry | Actual Qt workflow including simulated disconnected-input retry |
| Readiness reuse | One warmed model bundle reused by lecture startup and restart |
| Asset setup | Real pinned HTTPS download; offline fresh bootstrap/extraction; range/corruption tests |
| Synthetic speech/noise | 24 cases over clean, 20 dB and 10 dB noise; 19.2 s silence produces no phrases |
| Sustained replay | 903 seconds, 161 bilingual captions, zero drops/skips; controlled 20 dB noise |
| Translation evaluation | 40 development cases; concept checks only; human semantic acceptance pending |

Run unit checks with `runtime/python.exe -m pytest -q`. Native tests are separate
scripts described in INSTALLATION.md; they are not accidentally collected by pytest.

## Physical rehearsal still required

Auto checks and remaining limitations are in [the 0.7 evidence report](evidence/auto-language-0.7.md).
Include short English/Mandarin replies, speaker changes, uncertain-phrase notices and manual
override in rehearsal. Withheld phrases count as missed content even when no wrong language
was selected. Test both voices at their actual microphone distances and use bilingual review
to check meaning; language-identification scores alone are not word/translation accuracy.

1. Use the intended lecture microphone and speak real subject material from normal
   teaching positions. Check audience questions, room noise, pacing and accents.
2. Enable Airplane Mode, disconnect any Ethernet/VPN path, and verify startup, both
   languages, pause, finish and reopen. The current automated tests do not toggle radios.
3. Use an application-scoped OS packet/ETW trace for LectureLive and its child processes.
   The Python network guard and zero-socket samples do not prove native DLL silence.
   Do not publish unrelated machine traffic or private transcript contents.
4. Attach the actual projector, check caption readability from the back row, and test
   disconnect/reconnect, display scaling and full-screen PowerPoint click-through.
5. Physically unplug/reconnect the lecture microphone and exercise Reconnect / retry.
   A simulated disconnect is not evidence of this physical test.
6. Rehearse a full lecture on mains and battery, including Windows sleep/resume and
   a lid-close interruption. Record battery state, responsiveness, temperatures if
   available, queue depth and caption latency. Do not equate a 15-minute replay with
   a multi-hour thermal or battery pass.
7. Have a qualified bilingual reviewer inspect a separate real lecturer test set for
   negation, quantities/units, comparisons, terminology and complete meaning.

For an extended automated replay use `scripts/stress_test.py --seconds 7200 --noise-snr 20`.
It records sampled resources, power state, latency percentiles and queue drops. The
replay uses synthetic audio and cannot establish room acoustics or projector behaviour.

The application is not production classroom-approved until these physical and quality
checks are signed off. A hung in-process native driver remains a shutdown limitation.
