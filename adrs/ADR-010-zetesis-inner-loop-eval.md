> **v25 STATUS:** OPEN — sole surviving unresolved ADR. Head-to-head evaluation of **AREX** vs. **LangChain Open Deep Research** as Zetesis inner loop must run **immediately before Phase 6.2**. Selection criteria: answer correctness (blind-rated), source diversity, latency, GPU utilization on Colossus, integration effort. Benchmark artifact required at `ops/benchmarks/adr-010-<date>.md`. Winner locked; loser rejected in PORTING_LEDGER.

---

Status: Proposed (Tier-2 ADR ratification required per Kosmos v20 ADR practice, since this touches PORTING_LEDGER.md and the Zetesis scope entry)

## Context
Kosmos v20's Build Philosophy mandates continuous re-verification: each future build stage must check whether a newly-matured OSS project has obviated a planned bespoke component before that component is built. Zetesis (Phase 6, System-1 research plugin) is currently scoped to extract Rigpa-LMS's existing PLAN→SEARCH→SYNTHESIZE→VALIDATE→CRITIQUE→DELIVER→ARGUE pipeline, plus `uia-research-agent`'s credibility-scoring/citation-audit utilities, as a bespoke build.

BAAI released AREX (July 2026, arxiv.org/abs/2607.21461) — an open-weight family of Recursively Self-Improving (RSI) deep-research agents. AREX alternates an inner research loop (evidence gathering, provisional answer construction) with an outer self-improvement loop (constraint-wise audit, unresolved-claim detection, targeted follow-up research), and includes a learned `update_context` tool that autonomously compresses growing interaction history into a compact state preserving verified evidence and unresolved constraints — without an external summarizer model. Two open checkpoints ship: AREX-Turbo (4B dense) and AREX-Base (122B-A10B MoE, 10B activated). Both outperform comparable-scale baselines on BrowseComp, GAIA, WideSearch, DeepSearchQA, and HLE.

## Decision
Log AREX as a **"To Confirm"** vendor-before-build candidate in `PORTING_LEDGER.md`, targeting two Kosmos scope entries:

1. **Zetesis core research loop** — AREX's inner/outer loop architecture is a trained, working implementation of the same verify-then-refine pattern Zetesis's VALIDATE/CRITIQUE stages and claim-argument graph are designed to perform. Evaluate replacing (or wrapping) the bespoke Zetesis loop with an AREX checkpoint once Zetesis's build turn arrives in Rollout Plan Phase 6.
2. **Kernel Context Budget Manager** — AREX's `update_context` mechanism is architecturally close to the Context Budget Manager's working-memory summarization and JSON-vs-TOON measurement responsibilities. Evaluate AREX's context-compression approach as a reference (not necessarily a direct port, since the Context Budget Manager is a shared kernel service, not model-specific) when the Context Budget Manager's summarization strategy is next revisited.

This does not change current build sequencing. Zetesis remains Phase 6; the Context Budget Manager remains a Phase 3 kernel deliverable. This ADR only registers AREX as a known, evaluated candidate so it is not independently reinvented when either component's build turn arrives.

## Requirements Before Tier-2 Promotion
Per existing v20 governance, AREX must clear the same gates as any other vendored LLM component before adoption:

- **License verification**: confirm SPDX identifier for both AREX-Turbo and AREX-Base weights/code (GitHub: VectorSpaceLab/arex-model; HF: BAAI/AREX-Base, BAAI/AREX-Turbo, cfli/AREX-Turbo) and log in `MODEL_LICENSE_LEDGER.md`.
- **CUDA/Blackwell validation**: run both checkpoints through the same Colossus-specific golden-dataset eval harness and RTX 5090 (CUDA 13 nightly wheel) compatibility check already required for gpt-oss/Mistral Small 3.6, recorded in `CUDA_REQUIREMENTS.md`.
- **VRAM/hot-swap fit**: AREX-Turbo (4B) is a straightforward llama-swap-managed resident model. AREX-Base (122B-A10B MoE, 10B activated) requires validating CPU-offloaded MoE-layer feasibility within Colossus's 128GB system RAM budget alongside existing model-swap SLO targets (cold-load 8s, warm-swap 2s) before it can be considered for the priority-queue rotation.
- **Bus-factor flag**: as a newly released single-org (BAAI) research artifact with no long adoption history, AREX is flagged for bus-factor/upstream-health monitoring from first adoption, same treatment as llama-swap and DozerDB in v20.
- **Fixture/contract-test parity**: if adopted, AREX must pass the same contract-test and fault-injection gates as any Zetesis component before Tier-2 promotion, per the standing rule that no vendored component skips chaos testing.

## Rationale
1. Vendor-before-build discipline: a trained, benchmarked open-weight model solving the exact inner/outer verification-loop problem Zetesis is scoped to hand-build is precisely the case v20's continuous re-verification rule anticipates.
2. Ablation evidence reported for AREX shows disabling the outer loop and autonomous context update drops long-horizon accuracy by roughly 23 points — validating (not just inspiring) Kosmos's existing design choice to give the Context Budget Manager first-class, kernel-level ownership of context compression rather than treating it as an incidental utility.
3. No sequencing disruption: because Zetesis is Phase 6 and the Context Budget Manager's initial implementation is already Phase 3, this ADR adds an evaluation candidate without pulling any work forward or blocking current phases.

## Definition of Done
- AREX entry added to `PORTING_LEDGER.md` with source URLs (GitHub, both HF checkpoints), status "To Confirm", and this ADR referenced as rationale.
- Zetesis's Rollout Plan Phase 6 scope entry amended with a cross-reference note: "Evaluate AREX (see ADR) before finalizing bespoke research-loop build."
- Context Budget Manager's Phase 3 scope entry amended with a cross-reference note: "Reference AREX's autonomous context-update approach during summarization-strategy design (see ADR)."
- No live code changes required for this ADR to be considered "done" — it is a registration/tracking action only, gated for full Tier-2 promotion at the point either component is actually built or swapped.
