# Troubleshooting

**Microphone unavailable:** stop the session, reconnect the device, refresh the
microphone list and choose an input. Check Windows microphone access manually if
needed. The tested Surface WASAPI input runs at 48 kHz natively; the application asks
Windows' shared mixer to convert to 16 kHz. Exclusive mode is not used.

**Microphone disappears:** the watchdog pauses caption processing and shows an error.
Stop, refresh and start after reconnection. Physical USB/Bluetooth disconnect tests
are still pending; do not assume every device behaves like the built-in array.

**NPU unavailable:** use the bundled native ARM64 runtime, not an x64 Python. QNN
2.5.0 is a plugin registered with ORT 1.29.0. A context binary compiled for another
chipset is unsuitable. Do not mix in DLLs from an arbitrary older QAIRT SDK. See logs.
The local CPU graph is a separate model; QNN EPContext models cannot execute on CPU.

**Translation missing:** the local `models/translation/opus` assets must include all
three ONNX files, vocab.json, source.spm and configuration. A warning is shown while
English continues. The original OPUS model has limited technical translation quality;
consult the recorded test sentences rather than assuming every fluent output is exact.

**Shortcut does nothing:** another program may own Ctrl+Alt+C or Ctrl+Alt+Space. An
explicit startup warning identifies conflicts; use the on-screen controls.

**Captions hard to read:** increase font size or backdrop opacity, choose a wider
overlay, and shorten spoken phrases. Both languages wrap automatically. Check the
actual projector, not just the Surface screen.

**Transcripts cannot be saved:** check disk space and local directory permissions.
Existing captions continue. English is journaled before translation. The events.jsonl
file can reconstruct finalized English after interruption.

**Application fails before showing a window:** inspect
`%LOCALAPPDATA%/LectureLive/logs/lecturelive.log`. Keep the whole `_internal` directory
beside LectureLive.exe. Do not move only the EXE. No network troubleshooting is needed
for model loading: models must already be on disk.

The build log may report an unresolved `libcdsprpc.dll` dependency for QNN stub
libraries. The final packaged NPU inference test passed on this Surface with its
installed Qualcomm driver. The system driver is still required and is not redistributed
as an arbitrary DLL copied from Windows.
