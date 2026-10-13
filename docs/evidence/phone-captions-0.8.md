# Student phone captions — 0.8.0b1 evidence

Date: 2026-10-13. This feature adds a separate optional phone reader. The existing projector, ASR/translation code and settings are unchanged except for a bounded observer of final journal records. The unrelated local whitespace edit in accelerators.py is excluded from these commits.

## Investigation before implementation

CaptionDisplay keeps the current pair/pending/partial, not previous paragraphs. The overlay replaces earlier completed text and clips extremely long current captions to the available screen. A regression fixture sends eight long bilingual paragraphs: the overlay retains only the last, while the saved bilingual transcript contains every paragraph unchanged. Thus disappearing display text is not by itself evidence that a translation was lost.

Actual missing speech/translation is still possible through overload, recognition errors, uncertain language decisions or failed translation; the reader preserves the existing notices. No decoder/token limits, segmentation, vocabulary, language thresholds or models were changed. A completed pair means output actually produced by the pipeline, not proof every spoken word was recognised correctly.

## Automated evidence

- Native Windows ARM64: **167 passed, 2 POSIX-only skips**. Includes 21 new sharing regressions plus existing queues, pause/switch/shutdown, translation failure and all six export/recovery tests.
- Windows x64 runtime under ARM emulation: **167 passed, 2 POSIX-only skips**. Physical Intel performance is not measured.
- Native UI real English/Mandarin WAV replay with sharing: all four English-session and two Mandarin-session entries exactly match the saved journal. Pause/switch, old-epoch final records and muted spoken output pass.
- Source native Qt controls: explicit start/off/stop, QR generation, current-journal import, long late translation during pause, new lecture link revocation, history cleanup and fresh empty session all pass.
- Real loopback HTTP: 20 concurrent readers, old/full-history access, TXT streaming, token/Host/Origin/path guards, and distinct main/helper offline policies pass.
- Edge/Chromium mobile emulation: 10,000 bilingual entries initially, 10,002 after updates; at most 120 entries in the DOM. Whole TXT includes every entry and the full long delayed translation. Stable reading anchor (<3 CSS px), no duplicate updated row, Back to live, all language views, size control, whole-history search, eight simultaneous emulated iPhone/Pixel clients, disconnect/reconnect and refresh pass. Clipboard fallback text selection/copy invocation is tested with a mocked browser copy command; physical OS clipboard pasting still needs verification.
- Fixed real-model regression: **36 speech / 40 translation cases exactly match** docs/evidence/spoken-072-english-regression.json, covering CPU Base, QNN Base/Small and Standard/Careful recognition. This is output equivalence on the existing fixtures, not a new human accuracy assessment.
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
```

The browser harness uses locally installed Microsoft Edge on Windows, generated text fixtures and loopback. Test WAVs use the existing speech fixtures and licence notices. No new speech recordings or models were downloaded for the phone feature.

## Packaging / outstanding checks

Windows x64, frozen ARM64/x64 helper/UI/inference checks and hosted native Apple Silicon CI results are added here as they complete. Available installed releases older than 0.8.0b1 do not have Student phones.

Physical iPhones/Android devices, actual Safari, QR camera scanning, OS clipboard/download handling, campus firewall/device isolation, the i5-1035G1 laptop, an M2 MacBook Air and the expected classroom student count still require testing. Emulated mobile screens and loopback requests do not establish classroom Wi-Fi reliability or performance. No microphone/projector hardware was used for these generated-text tests.

Rehearse with the instructions in [PHONE_CAPTIONS.md](../PHONE_CAPTIONS.md). Privacy: explicit sharing publishes temporary lecture text to holders of a random link over unencrypted trusted-LAN HTTP; stopping does not erase student copies.
