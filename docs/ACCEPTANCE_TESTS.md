# Acceptance ledger

A partial pass is not a completed acceptance test. Keep final teaching approval open.

| Requirement | Evidence / status |
|---|---|
| Native Windows ARM64 | Verified CPython, packages; packaged EXE PE header verification is recorded by build script |
| Real NPU speech | PASS: Base and Small transcribed local WAV; strict-QNN profile contains QNN kernels |
| Local CPU speech recovery | PASS: Base int8 transcribed same WAV; simulated missing QNN startup tested separately |
| Microphone capture | PASS: built-in array, WASAPI shared conversion, 3-second sample held only in RAM |
| Live phrase pipeline | PASS: real-time technical WAV, stable EN/ZH and UTF-8 exports |
| UI responsiveness/pause/shutdown | PASS: automated Qt harness delivers translated caption, hides on pause, joins workers |
| Native overlay flags | PASS: topmost/noactivate/click-through flags checked; actual PowerPoint test recorded separately |
| PowerPoint click-through | PASS: real PowerPoint slideshow click-through + Ctrl+Alt+C, see evidence/powerpoint-test.json |
| Projector / display hot-unplug | PENDING: only one physical display was available during automated checks |
| Physical microphone disconnect / USB / Bluetooth | PENDING: do not equate simulated failure with unplugging hardware |
| Airplane Mode | PENDING: machine radios were not disabled during development |
| Network audit | Python audit guard blocks sockets; runtime source audited; process TCP/UDP snapshots during stress sampled zero sockets if report confirms. OS packet/ETW trace still PENDING |
| Ten-minute stress | PASS: 107 bilingual pairs, zero drops, workers joined; evidence/stress-10min.json |
| Multi-hour thermal/resource test | PENDING |
| Technical Chinese quality | REVIEW REQUIRED: baseline OPUS can omit/mistranslate detail |

## Physical rehearsal before travel

1. Enable Airplane Mode manually; disconnect Ethernet/VPN if applicable. Launch the
   packaged EXE, speak the technical sentences, and confirm both languages work.
2. Use Windows packet/ETW tracing or an approved network monitor to observe the
   LectureLive process and child processes. Verify no external requests while loading,
   listening, translating, pausing and stopping. A zero-socket snapshot alone is not a
   packet audit. Save only application-specific evidence.
3. Start a PowerPoint slideshow, show captions at bottom, lock them, and click within
   their rectangle. Slides must still advance; captions must remain visible.
4. Attach the projector. Keep controls on Surface and overlay on the projector. Unplug
   it, verify fallback, reconnect and reselect.
5. Test USB/Bluetooth microphones and unplug while listening; confirm clear errors and
   recovery via Stop → refresh → Start.
6. Run a full teaching-length session on battery and power. Record responsiveness,
   temperatures, memory, queue depth, latency, and transcript integrity.

Do not mark the project complete until these physical checks and quality review pass.
