# Public VCTK evaluation recordings

Yamagishi, Junichi; Veaux, Christophe; MacDonald, Kirsten (2019).
**CSTR VCTK Corpus: English Multi-speaker Corpus for CSTR Voice Cloning Toolkit
(version 0.92)**. University of Edinburgh, Centre for Speech Technology Research.
[Dataset and attribution](https://doi.org/10.7488/ds/2645).

Licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
The [publisher's metadata](https://datashare.ed.ac.uk/items/30e7453c-9ea8-48b4-8e18-f96d0dc62928/full)
identifies the licence. No endorsement of LectureLive by the authors or speakers is implied.

Our optional developer benchmark uses a subset from the
[sanchit-gandhi/vctk mirror](https://huggingface.co/datasets/sanchit-gandhi/vctk),
revision `73ef4ee7d49a6fed4ea1efd65f82b4c95faeb9de`. Speaker accent, region and
gender labels are the corpus metadata, not inferred from names or voices.
`tests/fixtures/vctk-accent-cases.json` records references, row IDs, original
filenames and original/converted SHA-256 checksums.

Changes: the original mono 48 kHz, 16-bit recordings are decoded from FLAC,
low-pass filtered with a fixed 97-tap Hamming-windowed sinc, downsampled to
16 kHz and rounded to PCM16. Optional noise/quiet variants are created in memory
by the evaluation script; they are artificial stress conditions.

Audio remains in ignored developer fixtures. It is not included in the app,
installers or Git repository. Public reference excerpts and benchmark outputs
are retained for reproducibility. No lecturer recordings are uploaded.
