# Mandarin development fixtures

The three Mandarin samples in `tests/fixtures/mandarin-cases.json` come from
**Google FLEURS**, `cmn_hans_cn`, test split, under **CC-BY-4.0**.

- Dataset, authors and documentation: https://huggingface.co/datasets/google/fleurs
- Reference: FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech,
  Conneau et al., 2022, https://arxiv.org/abs/2205.12446
- Licence: https://creativecommons.org/licenses/by/4.0/
- Pinned revision: `70bb2e84b976b7e960aa89f1c648e09c59f894dd`

LectureLive converts these mono 16 kHz float WAVs to 16-bit PCM for replay. Original
and converted checksums are recorded in the fixture manifest. Selection is the first
three audio entries in the published archive, not a curated accuracy set. They are
public read-speech smoke tests, not lecturer recordings or classroom validation.
Audio is fetched only for development/CI tests and is not included in the teaching app.
