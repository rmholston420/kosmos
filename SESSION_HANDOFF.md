# Kosmos Session Handoff — 2026-07-30 20:12 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.3.8 **COMPLETE** (Phase 6 · ADR-010 ODR contender wrapper). Tag `stage-6-3-8-complete` on origin/main.
- **Plugin / kernel component:** ADR-010 ODR benchmark harness (`ops/benchmarks/adr_010/`)
- **Port(s) in progress:** none — harness-internal work only

## Completed this session
- Deep-research pass on RAG hallucination mitigation. Report at `research_6_3_7b.md`.
- Reverted 6.3.7b regex-sweep draft (research-informed rejection).
- Shipped Stage 6.3.8 structural finalize (new `structural_finalize.py` module, shim 9 in `odr.py`, CLI flag, 19 new tests). Whole-repo pytest 1180 → 1199 passed / 19 skipped.
- Authored ADR-053 (Ratified v25) + ADR README row.
- Colossus 3-trial 6.3.8 verification: **structural_finalize outcome=ok all 3, blind F1–F6 mean 5.67 / 6** (baseline 4.17; 6.3.7 was 2.94).
- Tagged `stage-6-3-8-complete` on origin/main.
- BUILD_LOG + DEBUG_LOG updated with regression + fix + lock-in entries.

## Remaining before current Definition of Done
- **6.3.8 DoD is met.** Nothing outstanding for this stage.

## Open questions / awaiting user answer
- **Next stage direction:** ADR-010 resolution path from here is either (a) run the head-to-head vs AREX-Turbo now that ODR is stable, or (b) address the F4 AGPL-rationale gap + F5 minor overreach observed in the 6.3.8 blind rating with a targeted prompt / notes tweak before the head-to-head. User's call — neither is spec-forcing.

## Residual observations (candidates for future stages, not 6.3.8 blockers)
1. **F4 rubric-detail-loss:** AGPL-network-copyleft rationale absent from all 3 trials. Fix would be a small notes-enrichment or prompt hint, not a structural change.
2. **F5 rubric-orphan overreach:** trials 02/03 each added one URL-cited claim outside canonical facts (external cloud services / negated telemetry). Allow-list gate correctly retained them because they had valid URLs; not fabrication but detail-drift.
3. **Sources-block cosmetic:** renderer emits `[N] {label}: {url}` where writer sometimes puts a numeric/bracketed citation number in `label`, yielding `[1] (2):` / `[1] [4]:`. Track as KNOWN_ISSUES.
4. **Silent-fail shims (not new):** `rubric_critique` reported `no_fenced_output` and `cove` reported `insufficient_claims` on every trial — shims 6/7 are running but their inner LLM outputs don't match expected fences. Structural finalize covered the gap. Worth investigating in a small follow-up stage.

## Exact next action
Ask user which of these to pursue next:
- **A.** Run ADR-010 head-to-head (ODR vs AREX-Turbo) with 6.3.8-stable ODR — the point of the entire Phase-6 stream.
- **B.** Ship a 6.3.9 mini-stage: fix F4 notes-enrichment + sources-block cosmetic + investigate rubric_critique/cove silent-fail before head-to-head.
- **C.** Something else.
