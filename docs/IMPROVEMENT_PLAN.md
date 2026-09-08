# LectureLive improvement goal

Implementation milestone: 2026-09-09. Microphone availability is assumed for the intended lecture setup.

1. Translation: expand a technical evaluation corpus, measure current output and test local decoding/model improvements; retain honest bilingual-review status.
2. Reliability: drain accepted speech on Stop, isolate export failures, recover journals, test interruption and failure paths.
3. Captions: retain completed bilingual pairs until replacements are ready, stabilise provisional text and improve pause/sentence boundaries.
4. Teaching workflow: save lecture presets, offer a microphone check and projector preview, compact controls and configurable global shortcuts.
5. Setup: publish pinned verified asset manifests, resumable download/repair/bootstrap tooling and reuse warmed models.
6. Acceptance: automate reproducible microphone, noise, latency, long-session, failure and interface checks; provide a physical projector/room rehearsal checklist.

Implementation and automated testing are distinct from production classroom acceptance. Real lecturer/bilingual review and actual projector/room tests must not be fabricated.

All six implementation areas are complete. The rebuilt native ARM64 0.2 executable
passes model self-tests and a desktop interface check. The unit suite passes 49 tests;
a 15-minute noisy replay produces 161 bilingual captions without drops or skipped
translations. Translation concept checks improve from 30/40 to 37/40 on development
cases, with human semantic review still pending.

The recovery archive is regenerated from this milestone; its separate verification
report records archive integrity and relocated offline restoration. Physical rehearsal
items remain in ACCEPTANCE_TESTS.md. No lecture recordings or private transcripts
are included in the GitHub source publication.
