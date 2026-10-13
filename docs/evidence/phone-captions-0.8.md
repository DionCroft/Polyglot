# Student phone captions — 0.8.0b1 evidence

Date: 2026-10-13. This feature adds a separate optional phone reader. The existing projector, ASR/translation code and settings are unchanged except for a bounded observer of final journal records.

## Investigation before implementation

CaptionDisplay keeps the current pair/pending/partial, not previous paragraphs. The overlay replaces earlier completed text and clips extremely long current captions to the available screen. A regression fixture sends eight long bilingual paragraphs: the overlay retains only the last, while the saved bilingual transcript contains every paragraph unchanged. Thus disappearing display text is not by itself evidence that a translation was lost.

Actual missing speech/translation is still possible through overload, recognition errors, uncertain language decisions or failed translation; the reader preserves the existing notices. No decoder/token limits, segmentation, vocabulary, language thresholds or models were changed. A completed pair means output actually produced by the pipeline, not proof every spoken word was recognised correctly.

## Automated evidence

- Native Windows ARM64: **168 passed, 2 POSIX-only skips**. Includes 22 new sharing regressions plus existing queues, pause/switch/shutdown, translation failure and all six export/recovery tests.
- Windows x64 runtime under ARM emulation: **168 passed, 2 POSIX-only skips**. Physical Intel performance is not measured.
- Native UI real English/Mandarin WAV replay with sharing: all four English-session and two Mandarin-session entries exactly match the saved journal. Pause/switch, old-epoch final records and muted spoken output pass.
- Source native Qt controls: explicit start/off/stop, QR generation, current-journal import, long late translation during pause, new lecture link revocation, history cleanup and fresh empty session all pass.
- Real loopback HTTP: 20 concurrent readers, old/full-history access, TXT streaming, token/Host/Origin/path guards, and distinct main/helper offline policies pass.
- Edge/Chromium mobile emulation: 10,000 bilingual entries initially, 10,002 after updates; at most 120 entries in the DOM. Whole TXT includes every entry and the full long delayed translation. Stable reading anchor (<3 CSS px), no duplicate updated row, Back to live, all language views, size control, whole-history search, eight simultaneous emulated iPhone/Pixel clients, disconnect/reconnect and refresh pass. Clipboard fallback text selection/copy invocation is tested with a mocked browser copy command; physical OS clipboard pasting still needs verification.
- Fixed real-model regression: **36 speech / 40 translation cases exactly match** docs/evidence/spoken-072-english-regression.json, covering CPU Base, QNN Base/Small and Standard/Careful recognition. This is output equivalence on the existing fixtures, not a new human accuracy assessment.
- Long-history load: **25,000 generated bilingual pairs**, all IDs and both text fields retained, with twenty concurrent readers / 3,604 successful HTTP requests and no errors. Queue peaked at 100 events (~206 KiB), submission p99 0.0089 ms; helper RSS stayed 24.3–25.0 MiB across snapshots. This tests disk paging/resource growth, not a 25,000-turn real classroom session.
- Real timed 35.38-second Auto speech with twenty external readers: both native QNN and x64 CPU replays retain all ten timeline entries and recover all six exports exactly. QNN produces eight pairs/two uncertain notices; CPU produces seven pairs/three uncertain notices under the existing thresholds. No dropped audio chunks/phrases, skipped translations, gaps or HTTP errors in either run. 2,565 / 2,668 successful requests respectively. Every shared text/status matches the final journal; no withheld speech is represented as recognised.
- Actual generated Windows QR bitmaps decode into valid session links using test-only jsQR/PNG decoders. A settled native Qt layout fits the entire QR image. Camera scanning is still untested.
- Interrupted-download regression first reproduced the incomplete-file bug; HTTP chunk framing now makes an interrupted TXT transfer fail rather than look complete. Per-entry copy feedback remains visible with the search toolbar collapsed.
- Static network audit allows network imports only in the isolated inbound HTTP helper. Main inference retains Python socket/DNS denial; helper denies outgoing connections/DNS. This is not a native packet trace.

Evidence artifacts are written under tests/artifacts/phone-*. JSON baseline and browser reports are also retained next to this document. Source test commands:

```powershell
runtime/python.exe -m pytest -q
runtime-x64/python.exe -m pytest -q
runtime/python.exe -m scripts.audit_offline
runtime/python.exe -m scripts.check_english_regression --output tests/artifacts/phone-080-english-regression.json --baseline docs/evidence/spoken-072-english-regression.json
# Isolate test preferences first:
$env:LECTURELIVE_DATA = "$PWD/tests/phone-ui-data"
runtime/python.exe -m app.main --phone-self-test tests/artifacts/phone-source-ui.json
runtime/python.exe -m app.main --conversation-ui-test tests/fixtures tests/artifacts/phone-source-conversation-ui.json
# Test-only browser dependency; never included in the application:
npm.cmd install --prefix build/phone-browser --no-audit --no-fund playwright@1.56.1
node scripts/verify_phone_browser.cjs
runtime/python.exe -m scripts.stress_phone_history
runtime/python.exe -m scripts.check_phone_live
runtime-x64/python.exe -m scripts.check_phone_live --cpu
```

The browser harness uses locally installed Microsoft Edge on Windows, generated text fixtures and loopback. Test WAVs use the existing speech fixtures and licence notices. No new speech recordings or models were downloaded for the phone feature.

## Packaging / outstanding checks

Source implementation milestones: `ccc085b` (reader/history/UI) and `dabfe96` (interrupted-download protection). Both were tested and pushed to main. Package code is from `dabfe96`; release documentation is updated separately.

Windows builds: `dist/phone-0.8.0b1/LectureLive/LectureLive.exe` (native ARM64) and `dist/phone-0.8.0b1/LectureLive-x64-Beta/LectureLive-x64-Beta.exe` (x64 under ARM emulation). The initial packages passed all six existing inference/conversation/Auto/UI/voice checks. After the download fix, both rebuilt packages pass native sharing UI/QR/lifecycle, real bilingual UI replay with journal matching, timed Auto replay, and twenty-client HTTP/assets/download/parent-exit tests. Auto replays have zero dropped frames/phrases/skipped translations; uncertainty counts remain honest.

Complete, member-hash-verified Windows ZIPs are in `recovery/` and on the [0.8.0b1 Windows release](https://github.com/DionCroft/Polyglot/releases/tag/windows-v0.8.0b1): ARM64 approximately 1.54 GB; x64 approximately 760 MB. The x64 ZIP includes Launch-CPU.cmd. Both translation models are bundled; the reader needs no additional model download.

Hosted Apple Silicon native CI: [run 38401879185](https://github.com/DionCroft/Polyglot/actions/runs/38401879185) tests/builds the same `dabfe96` code. **170 tests pass with no skips**, plus all nine packaged inference/Cocoa/conversation/Auto/voice/phone checks, including twenty HTTP clients and parent-exit shutdown. Native JSON reports accompany this document. DMG/ZIP packaging and signature verification succeed. macOS 14+ remains the minimum; ad-hoc signed, not notarised. Physical M2 Air behaviour is not established by the hosted runner.

Physical iPhones/Android devices, actual Safari, QR camera scanning, OS clipboard/download handling, campus firewall/device isolation, the i5-1035G1 laptop, an M2 MacBook Air and the expected classroom student count still require testing. Emulated mobile screens and loopback requests do not establish classroom Wi-Fi reliability or performance. No microphone/projector hardware was used for these generated-text tests.

Rehearse with the instructions in [PHONE_CAPTIONS.md](../PHONE_CAPTIONS.md). Privacy: explicit sharing publishes temporary lecture text to holders of a random link over unencrypted trusted-LAN HTTP; stopping does not erase student copies.
