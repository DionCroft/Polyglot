# Improving speech recognition

If LectureLive already works well for you, keep **Speech recognition: Standard** and leave
**Use these terms to guide speech recognition** unticked. These are the existing defaults.
The update adds options you can try for another speaker; it does not switch everyone to a new
recognition model or automatically guess anyone's accent.

Start with the [five-minute check with your colleague](ACCENT_CHECK.md), including
shared CO7000/electronics practice passages and a separate validation passage.
When investigating wrong English words, select **English → Simplified Chinese**
first. Auto's language decision and Whisper's choice of words are different checks.

## Try one change at a time

1. Select the teaching microphone and use **Test microphone**. Resolve a very quiet signal or
   clipping first. Use the same microphone, distance and room when comparing settings.
2. On Snapdragon or Apple Silicon, try **Balanced**. It uses the larger Whisper Small model.
   The local accent measurements below used the Snapdragon NPU. Mac Balanced can use
   CPU fallback and needs a timing check on the teaching Mac. The Intel/AMD x64 beta
   currently uses Whisper Base in its Fast profile.
3. Try **Speech recognition → Careful** on a short, representative lecture passage. It compares
   alternative word sequences for finished phrases; live partial captions remain a single decoding
   path. Compare the actual words, not just whether the sentence sounds plausible.
4. If technical terms are wrong, add a **short list** under **Today's vocabulary**, one term per
   line, and tick **Use these terms to guide speech recognition**. For example:

   ```text
   ESP32
   FreeRTOS
   I2C
   MOSFET
   ```

   Put the most important terms first. Use relevant names and terms, not full sentences,
   instructions, or a whole glossary. This gives the speech model context before it chooses words.
   An unrelated list can make recognition worse. Try hints separately before combining them with
   Careful mode. Untick the box if the model starts favouring words you did not say.
5. Save useful settings in a **lecture preset**. You and your colleague can use different presets.
   Change recognition settings while the lecture is stopped. If the new settings do not help,
   select Standard and untick vocabulary guidance to restore the existing recognition path.

For project-management teaching, use the [CO7000 weekly vocabulary guide](CO7000_VOCABULARY.md).

## What the expanded tests show

The new comparison adds **120 recordings**: 30 each from two Indian-English speakers
and two English speakers from England. Each group has one female and one male voice.
There are 23 sentences shared by all four speakers, plus other read material. These are public
VCTK read recordings, not either lecturer or a classroom recording.

On the tested Snapdragon NPU, **Balanced / Whisper Small with Standard** reduced
Indian-English word errors from **60 to 42 out of 882 words**, compared with
Fast / Whisper Base: **6.80% → 4.76% WER**. Both Indian-English speakers improved.
The English controls also improved, from **35 to 23 errors out of 874 words**
(4.00% → 2.63%). This supports trying the larger model first where available.

**Careful is still a comparison option, not an automatic recommendation.** On Small,
the Indian-English total changed only from 42 to 41 errors. One speaker improved
from 32 to 29, including “A race total” becoming “Aristotle”; the other changed
from 10 to 12, due to “raindrops” becoming “rain drops”. Raw WER counts such formatting
differences too. Artificial noise also produced mixed results. Compare your own
words and caption delay before saving a preset.

No speech model, decoder default, vocabulary rule, audio processing or language
threshold was changed in this testing round. Your existing working settings remain
the baseline. A short relevant vocabulary list can help names, but it can also
worsen other words; a better score on these recordings is not proof of improvement
on your colleague's CO7000 lectures.

The live diagnostic also exposed a useful caution: with hints on, some captions
omitted the very name being prompted. If that happens, turn guidance off and
compare again. The unprompted Standard and Careful replays retained that name.

See the [expanded results and limits](evidence/indian-english-2026-09-23.md).
The [earlier KSP/AWB and synthetic technical comparison](evidence/speech-recognition-2026-09-21.md)
remains available separately; it used different speakers and passages and should
not be combined into an apparent before/after score. Physical Intel/AMD GPU/NPU
and both lecturers' classroom recordings still need validation.

## Speed, memory and hardware

- **Standard:** keeps the previous model and decoder path when guidance is off.
- **Careful:** compares up to three decoding paths for final phrases. This takes more processing
  time and additional decoder-cache memory. It does not guarantee better accuracy. Caption
  delays can grow on slower PCs, so test before a lecture.
- **Vocabulary guidance:** uses the existing local tokenizer and model. It adds a short prompt
  and decoding work. The prompt is bounded to 32 tokens, keeping complete terms in list order;
  long lists are not all used. The tokenizer is loaded only when hints are requested.
- **Balanced versus Fast:** Small is larger and slower than Base. Balanced is already installed
  in the Snapdragon edition. This update does not add a new large download, model, Python
  dependency, or hardware requirement to either Windows edition.
- **Accelerator failure:** CPU fallback preserves your chosen recognition mode and vocabulary.
  Performance and recognition may differ on the smaller CPU model. The backend is shown in
  Diagnostics.

The microphone stream, sample rate, voice-activity threshold and audio features are unchanged.
No blanket noise reduction or gain change was applied without evidence that it would help this
speaker; aggressive processing can discard useful speech detail. The existing microphone test
already checks quiet input and clipping.

## What we need to validate this for both lecturers

Provide 2–5 minutes from **each** speaker, including an ordinary explanation, the same technical
passage, and the words that commonly fail. Use your teaching microphone and a realistic room.
Include an exact written transcript of what was actually said, the incorrect captions, model
profile and processing backend. A mono 16 kHz, 16-bit PCM WAV is supported by the evaluator.
Keep a second short passage aside to check that any later tuning also helps unseen speech.

Record only with the speaker's agreement. LectureLive itself still does not record microphone
audio or upload it. Existing recordings can be evaluated locally; results should be saved under
`tests/artifacts` so private transcripts are not committed accidentally.

The next decision should be based on those paired recordings. Fine-tuning or an accent-specific
model is not justified by the current small proxy set, and it would need more representative,
consented data plus a separate regression set for your speech.

## Developer evaluation

Optional preparation of the public comparison recordings uses the Hugging Face Dataset Viewer
and validates the recorded file checksums. It is separate from ordinary installation and runtime:

```powershell
.\runtime\python.exe -X utf8 -s scripts\prepare_accent_fixtures.py
.\runtime\python.exe -X utf8 -s scripts\evaluate_speech.py --backend balanced --mode standard --output tests/artifacts/standard.json
.\runtime\python.exe -X utf8 -s scripts\evaluate_speech.py --backend balanced --mode careful --output tests/artifacts/careful.json
```

Use `runtime-x64` and `--backend cpu` on the x64 beta. The evaluator accepts `--manifest` for a
local JSON file containing a `cases` list; each case has `id`, `speaker`, `reference`, and `path`
(absolute or relative to the project). Use unique IDs and nonempty English references; split
audio into clips of at most **30 seconds** with matching transcripts. `sha256` is optional for your private files. Use `--vocabulary "ESP32|FreeRTOS|I2C"` to test one fixed vocabulary list; do not supply the reference transcript
as the prompt. WER is aggregated by speaker using substitutions, insertions and deletions over
reference word counts. Raw WER retains spelling/tokenisation differences such as “synthesised”
versus “synthesized” and “I-squared-C” versus “I2C”; it is not a semantic accuracy score.

### Expanded multi-speaker check

The optional VCTK developer fixtures add 120 clips from two Indian-English and two
English speakers from England. Preparation needs internet access and FFmpeg on PATH
to decode the source FLAC files. **Ordinary users do not need FFmpeg or these fixtures.**
Prepared WAVs and evaluation run locally; nothing is uploaded. Source attribution,
revision, hashes and conversion are recorded in the manifest and
[VCTK notice](licenses/vctk-NOTICE.md).

```powershell
.\runtime\python.exe -X utf8 -s -m scripts.prepare_vctk_fixtures
.\runtime\python.exe -X utf8 -s -m scripts.evaluate_speech --manifest tests/fixtures/vctk-accent-cases.json --backend balanced --mode standard --language-check --output tests/artifacts/vctk-standard.json
.\runtime\python.exe -X utf8 -s -m scripts.evaluate_speech --manifest tests/fixtures/vctk-accent-cases.json --backend balanced --mode careful --output tests/artifacts/vctk-careful.json
```

Repeat with `--backend fast` or `--backend cpu` for the installed Base models.
`--variant noise-20dB`, `noise-10dB` or `quiet-12dB` applies a reproducible artificial
stress condition. Use the same variant for both settings. Noise is seeded per clip,
so rearranging the manifest does not change the comparison. These conditions do not
simulate room echoes or other people speaking. `--language-check` reports Auto's
accepted/withheld/wrong decisions separately; WER always covers **all** manual-English
clips. Timing is full-clip speech inference, not live caption latency. The manifest
hash is included in each report to identify the exact comparison set.

## Sources

- [OpenAI Whisper decoding implementation](https://github.com/openai/whisper/blob/main/whisper/decoding.py)
  documents prompts, token suppression and beam search. The app implements these options using
  its existing ONNX backends; it does not add PyTorch or a hosted speech API.
- [OpenAI Whisper model card](https://github.com/openai/whisper/blob/main/model-card.md)
  describes model limitations, including uneven performance across accents.
- [CMU speaker provenance](https://www.cs.cmu.edu/~pmuthuku/publications/thesis/Prasanna_thesis.pdf)
  identifies KSP as Indian and AWB as Scottish; these labels come from the corpus metadata.
- [Public CMU ARCTIC mirror](https://huggingface.co/datasets/MikhailT/cmu-arctic)
  supplies the comparison clips (mirror declares MIT). Dataset revision and individual checksums
  are recorded in `tests/fixtures/accent-cases.json`. Audio files are not redistributed in the app.
