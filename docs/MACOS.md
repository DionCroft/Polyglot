# LectureLive for Apple Silicon — beta 0.6.0b1

Requires an Apple Silicon Mac (M1 or newer, including M2 MacBook Air) running **macOS 14 Sonoma or later**. Intel Macs and Rosetta are not supported by this build. Native M2 classroom validation is still required. The Windows builds remain available separately.

## Install the ready-made app

1. Open the [Mac beta download page](https://github.com/DionCroft/Polyglot/releases/tag/macos-v0.6.0b1). Under **Assets**, choose **LectureLive-0.6.0b1-macOS-AppleSilicon.dmg** (recommended) or the application ZIP. Do not choose **Source code**. Developer builds are also available from successful **macOS Apple Silicon** runs in **Actions**; those require extracting an outer artifact ZIP and may require signing into GitHub.
2. Open the DMG and drag **LectureLive** onto **Applications**. Alternatively, double-click the inner application ZIP and move **LectureLive.app** to **Applications**. Eject the DMG before starting the installed app.
3. Open **Applications → LectureLive**. This beta is ad-hoc signed and is **not Apple notarised**. If macOS blocks this downloaded beta, open **System Settings → Privacy & Security**, find the message about LectureLive, choose **Open Anyway**, and confirm **Open**. Only approve the copy you obtained from this repository. Your organisation may require IT approval.
4. Choose your microphone and click **Test microphone**. Choose **Allow** when macOS asks for microphone access. If access was denied, turn on **System Settings → Privacy & Security → Microphone → LectureLive**, then quit and reopen LectureLive.
5. Choose **Fast**, leave recognition on **Standard**, and click **Start lecture**. Select **Careful** and try **Balanced** if recognition needs improvement. Use the lecture vocabulary box, subject glossary and CO7000 week lists for technical terms. Save a preset to reuse these choices.
6. Position the caption overlay on your screen or projector, then lock it. Pause with **Control + Option + Space**; lock/unlock with **Control + Option + C**. The screen buttons also work. In shortcut settings, **Ctrl** means Control and **Alt** means Option; Cmd/Command is supported. Change conflicting shortcuts, especially when VoiceOver is enabled.

All speech models, translation in both directions, voice detection, glossaries and course lists are included. Normal use needs no account, Python installation or internet connection. Audio is processed locally. Text transcripts are saved when **Save transcripts** is selected (on by default); turn it off if you do not want saved text. Microphone audio is not recorded. Settings, presets, logs, transcripts and Core ML caches live in `~/Library/Application Support/LectureLive`.

## Lecturer–student conversations

Choose **English → 简体中文** under **Who is speaking?** for your lecture. For a question,
finish your sentence, choose **Mandarin 普通话 → English**, and wait for **Listening** before
the student speaks. The same selector is in **Teaching controls**. Try “请再解释一次。”
(“Please explain again.”). Switch back to English before answering. The captured turn finishes
before the switch; speech during switching is not captured. Both directions stay in one transcript.

This app includes the extra 172.7 MB Mandarin → English model; the older 0.5.0b1 installer does
not. First Mandarin use loads extra model sessions into RAM; one Windows measurement added
about 527 MiB. Mac memory and timings may differ. Translation remains on CPU. Both directions
keep the existing Whisper acceleration and CPU fallback. English vocabulary and CO7000 hints
are preserved for English turns and are not applied to Mandarin. Automatic language detection
is not included. [Full conversation guide and limitations](CONVERSATIONS.md).

## Processing choices and limits

**Automatic** tries Apple Core ML for the Fast speech encoder and falls back to CPU if loading, verification or inference fails. Balanced uses CPU in Automatic mode: Small Core ML compilation exceeded the three-minute limit on the hosted Mac. You can explicitly select **Apple Core ML · beta** to try Small acceleration on your Mac; it retains the same timeout and CPU fallback. **CPU** avoids the accelerator. Both choices retain the selected Fast/Base or Balanced/Small model, vocabulary prompts and Careful decoding. Decoding, translation and voice detection use CPU in both modes. Core ML can partition work across CPU, GPU and Neural Engine; the app verifies Core ML execution but does not claim a particular physical device was used. Initial compilation may take up to three minutes; later launches reuse a local cache. A timed-out inference switches to CPU and retries the phrase.

Balanced uses larger models and more memory. Careful checks more candidate words and can increase caption delay. The fanless M2 Air may slow down during sustained work. Use Fast/Standard first on an 8 GB Mac; close memory-heavy applications. This is guidance, not a measured M2 performance guarantee. Existing accent improvements are retained; the new backend still needs recordings from both lecturers to establish accent accuracy on this hardware.

External microphones, Bluetooth sample-rate conversion, permission denial/recovery, hotkey delivery while another app has focus, full-screen slide overlays, multiple displays, battery use and thermal performance require a physical Mac classroom test. Hosted Apple Silicon CI checks are recorded separately in validation reports; they are not M2 hardware certification.

## Updating or removing the Mac app

Quit LectureLive before replacing the copy in Applications. Keep your previous installer until the update works. Your settings and transcripts stay in your user Library. To remove the app, move LectureLive from Applications to the Bin; this leaves your saved data intact. Only delete `~/Library/Application Support/LectureLive` separately if you also want to remove those settings and transcripts.

If **Open Anyway** is absent or the app is reported as damaged, verify the download against the supplied `SHA256SUMS.txt` or download it again; ask your university IT team if their policy blocks it. Do not disable Gatekeeper globally. If you see **Core ML unavailable**, captions can continue on CPU. Select CPU explicitly if you prefer to skip Core ML compilation. Use **Diagnostics → Open transcripts** to find saved text.

## Build from source (optional, for maintainers)

Install native ARM64 Python 3.11 from python.org on macOS 14+, clone this repository, then run `bash Setup-Mac.command` from Terminal inside the repository. Setup downloads hash-verified dependencies and models; this step needs internet. The resulting `dist/LectureLive.app` runs offline. Allow several GB of free disk space for dependencies, caches and packaging.

To repeat validation and create both distribution formats:

```sh
.venv-macos/bin/python -m scripts.setup_assets --fixtures
.venv-macos/bin/python -m pytest -q
LECTURELIVE_DATA="$PWD/tests/macos-ci-data" .venv-macos/bin/python -m app.main --self-test tests/fixtures/jfk.wav tests/macos-source.json
.venv-macos/bin/python -m scripts.package_macos
```

The packages are written to `dist/macos-release`, with SHA-256 checksums. `ditto` preserves app framework links and executable permissions; do not repackage the app on Windows. Build on macOS: Windows cannot produce or verify the native app.

For a public notarised release, configure a Developer ID Application certificate in the Mac build keychain and set `LECTURELIVE_CODESIGN_IDENTITY` before building. Configure an Apple `notarytool` keychain profile and set `LECTURELIVE_NOTARY_PROFILE` before packaging. The packaging script submits and staples the signed app when that profile is present. These credentials are not included in this repository; the normal CI beta remains ad-hoc signed. Managed Macs may prevent installation of an unnotarised beta.


[Implementation notes and physical M2 acceptance checklist](MACOS_PORT.md).

## Sources for platform behaviour

- [Apple: opening downloaded applications](https://support.apple.com/en-us/102445).
- [ONNX Runtime: Core ML provider and its compute choices](https://onnxruntime.ai/docs/execution-providers/CoreML-ExecutionProvider.html).
- [GitHub: hosted Apple Silicon runner specifications](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- [Qt: microphone permissions](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QMicrophonePermission.html).
