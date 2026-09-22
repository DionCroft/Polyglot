# Expanded accent comparison protocol (23 September 2026)

Baseline: application commit `485428676b7c32ff6a291ce747b23eee36f9ee8d`.
This protocol and the fixture selection were fixed before inference on the new clips.

- First 30 available **mic1** recordings in source row order from each VCTK
  speaker: p248 (Indian, female), p251 (Indian, male), p225 (English, Southern
  England, female), p226 (English, Surrey, male). Do not count mic2 recordings
  as additional speakers or independent examples. Retain every selected clip.
- Public read speech, with shared opening passages and later different texts.
  Report each speaker separately; pooled errors are word-weighted, not an average
  of speaker percentages. Differences cannot be attributed solely to accent.
- Compare existing **Standard** and **Careful** on QNN Base, QNN Small and CPU
  Base. No vocabulary hints for this general read speech. No model training,
  accent classification, language-threshold tuning or decoder retuning on this set.
- Repeat relevant Small comparisons with deterministic per-clip Gaussian noise
  at 20 dB SNR and a quieter-input stress condition. These do not simulate a
  classroom's reverberation, competing voices or microphone response.
- Check Auto final-language decisions separately: report correct English,
  withheld and incorrectly accepted Mandarin. Manual English WER includes all
  clips even if Auto withholds them. Whole-clip detection does not validate
  partial-caption locking or live phrase segmentation.
- Preserve earlier KSP/AWB and technical evidence, plus exact baseline English
  and translation regression checks. Do not report old results as newly run.
- Existing modes are frozen before testing; this is an additional confirmation
  set for those options, **not** held-out validation of Whisper's pretraining.
  The corpus may have appeared in Whisper's training data. If these results
  motivate algorithm changes, obtain a separate unseen-speaker validation set.

Raw WER is punctuation/case-insensitive word edit distance. It retains spelling,
contractions, number/acronym tokenisation and reference-reading differences.
Timing includes per-clip inference, not translation, live scheduling or microphone
latency. Host load and cold starts affect it; report ratios as observations.

The actual lecturers' spontaneous speech, CO7000/electronics terminology and
classroom conditions still need consented representative recordings. No public
speaker should be presented as either lecturer.
