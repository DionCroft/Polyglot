# macOS port: implementation and validation boundaries

The macOS beta is a native ARM64 Python/Qt Cocoa application. The `.app` includes its runtime, native libraries and pinned model files. It does not run the Windows executable or use Rosetta. Its minimum version is macOS 14, matching the pinned ONNX Runtime ARM64 wheel. Windows dependency locks, launchers and model manifests remain separate.

## Windows dependencies and their Mac replacements

| Area | Existing Windows implementation | Apple Silicon implementation |
|---|---|---|
| Microphones | WASAPI/MME, WASAPI format conversion | Core Audio with conversion to the existing mono 16 kHz pipeline |
| Permission | Windows privacy settings | Qt's static Darwin microphone permission plugin, Info.plist usage description, user-initiated permission request |
| Global shortcuts | Win32 RegisterHotKey | Carbon RegisterEventHotKey; Control/Option and Cmd aliases; no keylogging or Accessibility permission |
| Overlay | Win32 extended window styles | Cocoa NSWindow ignoresMouseEvents, floating level, all-Spaces/full-screen auxiliary flags |
| Hardware inference | Qualcomm QNN or DirectML/Windows ML | ONNX Runtime Core ML encoder; CPU decoder/translation/VAD; CPU fallback |
| Worker isolation | Windows named pipe, CREATE_NO_WINDOW | Private inherited POSIX pipes, bounded reads/writes, process termination on failure |
| Preferences/cache | LOCALAPPDATA | User Library/Application Support/LectureLive; no writes into the signed bundle |
| Packaging | Windows PyInstaller EXE/folder | Native macOS PyInstaller ARM64 BUNDLE; ad-hoc or Developer ID signing; ditto ZIP and hdiutil DMG |

Core ML must execute encoder nodes during a traced warm-up before the app labels it active. The trace may include CPU partitions. It cannot establish that the Neural Engine or GPU performed any particular work; Apple chooses the compute device. Encoder startup has a 180-second limit and each inference a 30-second limit. CPU fallback retains Base/Small selection, Careful mode, vocabulary prompts and the same audio phrase. Python runtime networking remains disabled in the parent and child; the worker does not open sockets or write microphone audio.

The Mac build adds portable ONNX Small weights alongside Base. It reuses the original OpenAI tokenizer and preprocessing assets, including the existing mel filter bank. Translation, segmentation, caption stabilisation, transcript exports, 12 CO7000 lists and the 92-term project-management glossary use shared application code. The optional recognition improvements are unchanged. All model downloads are a setup/build step and are verified by byte count and SHA-256; ordinary launches use bundled models.

## Physical M2 acceptance still required

Hosted Apple Silicon tests cover native execution and packaging, but do not replace this classroom check:

1. On an M2 MacBook Air running macOS 14 or newer, install the downloaded DMG in Applications. Verify Finder launch, Gatekeeper handling and reopening after quitting. Record macOS version, RAM and power mode.
2. Allow the first microphone request, test the built-in input, then deny/re-enable permission through System Settings and retest. Repeat with the lecturer's actual USB or Bluetooth microphone; disconnect and reconnect it during captions.
3. Deliver a 30-minute lecture with Fast/Standard, then compare Balanced/Careful. Record caption delay, memory, fanless thermal slowdown and battery impact. Record the displayed backend; distinguish verified Core ML execution from an actual ANE/GPU measurement.
4. Test pause and lock shortcuts while PowerPoint or Keynote has focus. Move captions between the Mac screen and projector, test full-screen presentation and Spaces, unlock/drag/relock, and disconnect the projector. Check that locked captions pass mouse clicks through.
5. Disconnect Wi-Fi and wired networking and repeat recognition, Chinese translation, presets, CO7000 terms and text export. Audit native-library network activity separately if an institutional offline assurance report is required; Python socket blocking alone does not prove every native library is silent.
6. With permission, record each lecturer reading the same representative technical and project-management passages, plus spontaneous speech using the teaching microphone. Supply corrected reference text. Compare Standard/Careful and Base/Small for both British- and Indian-accented English; the JFK smoke test does not measure their accent accuracy.

No attached physical Mac, M2 microphone/projector setup, lecturer recordings or Apple Developer ID/notarisation credentials were available on the Windows development host. Signing and notarisation hooks are provided for a maintainer with those credentials; the distributed CI beta remains ad-hoc signed.
