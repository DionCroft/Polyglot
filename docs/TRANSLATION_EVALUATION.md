# Translation evaluation

The milestone keeps local Marian/OPUS-MT on ARM64 CPU. It changes beam termination
from stopping at the first four completed hypotheses to a score-based heuristic,
retaining the best completed beams and considering unfinished candidates. Four beams
and length penalty 1.0 remain the defaults; the 1.2 experiment did not improve the
initial eight cases. Generation controls are described in the official documentation:
https://huggingface.co/docs/transformers/main_classes/text_generation

The original obstacle sentence now retains the relationship to the obstacle in the
Chinese output. This is a measured correction, not a sentence-specific replacement.
See `evidence/translation-decoding-comparison.json` for original and revised outputs.

`tests/fixtures/translation-corpus.json` contains 40 authored cases spanning robotics,
electronics, embedded systems, AI, IoT and classroom instructions. References are
DRAFTS pending qualified bilingual review. The automatic checker looks for explicit
concept alternatives; synonyms can fail the check, while semantically incorrect
sentences can pass. Do not describe its score as translation accuracy.

Run `runtime/python.exe scripts/evaluate_translation.py --baseline` in a Git checkout.
The comparison uses the original b2cbed5 decoder and original glossaries against the
new decoder and glossaries. Initial results: original 30/40 concept checks, new 37/40.
These are development cases used to diagnose glossary failures, not an untouched
held-out test. All outputs and timing distributions are in `evidence/translation-expanded.json`.

New terminology corrections apply only when the source contains the corresponding
term and the lecturer selects its domain glossary. They do not translate arbitrary
sentences through templates or invent missing technical facts.

Remaining examples requiring review include overfitting and ambiguous electrical
language. An automated concept match alone does not certify a complete explanation.
The existing M2M100 experiment was slower and inconsistent in the original comparison.
NLLB-200 was considered but is not bundled: its publisher specifies CC-BY-NC and
research-oriented usage rather than production deployment:
https://huggingface.co/facebook/nllb-200-distilled-600M

Before classroom acceptance, collect a separate, consented local lecturer evaluation
set and have a bilingual reviewer judge meaning preservation, negation, numerical
values, units and terminology. No private evaluation speech or transcripts should be
added to the public repository.
