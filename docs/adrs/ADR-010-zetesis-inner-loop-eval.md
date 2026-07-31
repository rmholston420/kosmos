> **STATUS AMENDMENT (2026-07-30 22:00 EDT) — Stage 6.4 substrate-tuning arc closure.** ADR-055 ratifies **ODR-post-6.3.9** (commit `05366ac`, tag `stage-6-3-9-complete`) as Zetesis's research inner loop for Stage 6.5 kernel wiring. The Stage 6.3.x tuning arc (sub-stages 6.3.1 → 6.3.9) raised ODR from the Stage 6.2 baseline of 16.7% (3.0 / 18 aggregate) to **89%** (5.33 / 6 agent-rated on 3 Colossus trials at Stage 6.3.9). The Stage 6.2 winner-lock (ODR chosen over AREX-Turbo) still stands unchanged — this is an extension, not a supersession. **AREX-Turbo re-comparison against the tuned ODR is deferred**, filed to `KNOWN_ISSUES.md` as a non-blocking follow-up. The Stage 6.2 rejection reason (AREX completion 0/3 on context-ceiling exhaustion) remains dispositive because structural-finalize (ADR-053) does not address context-ceiling. AREX contender stays wired at `ops/benchmarks/adr_010/harness/arex.py`; vendored `BAAI/AREX-Turbo` inference bundle stays at `vendor/adr_010/arex_inference/`. See ADR-055 for full rationale.
>
> **v25 STATUS:** Ratified v25 · **LOCKED 2026-07-30**. Winner: **Open Deep Research (ODR)** — `langchain-ai/open_deep_research@d337ae3` MIT, served with `qwen2.5:32b-instruct-q4_K_M` on local Ollama via `langchain-mcp` streamable-http against the shared SearXNG substrate. AREX (`BAAI/AREX-Turbo` served on Colossus vLLM) is **REJECTED for Stage 6.2 (Zetesis inner loop)** but retained on the shelf for a future revisit when the Colossus thermal envelope permits sustained bfloat16 attention at extended context. See §Head-to-Head Result (2026-07-30) below.

> **HEAD-TO-HEAD RESULT (2026-07-30):** Six trials on Colossus (RTX 5090 / 128GB RAM), three per contender, identical question (`fixtures/adr_010_question.json` — Neo4j Community vs. DozerDB, 6 canonical facts F1-F6), identical SearXNG substrate. Trials committed at `ops/benchmarks/artifacts/adr-010-2026-07-30/{arex,odr}/`. Blind rating notes in commit body of `stage-6-2-complete`.
>
> | Contender | Completion | Aggregate score | Best trial | Mean latency | Mean source_diversity | Peak VRAM |
> |---|---|---|---|---|---|---|
> | ODR (qwen2.5:32b via Ollama + MCP) | **3/3** | **3.0 / 18 (16.7%)** | trial_03 (1.5/6) | 88.9s | 2.0 | 27.7 GB |
> | AREX-Turbo (vLLM, 32k ctx) | 0/3 | 0.0 / 18 (0.0%) | none | 23.7s | 2.67 | 27.5 GB |
>
> AREX-Turbo consistently exhausted its 32,768-token context ceiling before emitting a `<finish>` tool call — every trial ended with `error=BadRequestError 400 max context length`. Its trajectories showed real research (found `dozerdb.org`, `github.com/DozerDB`, `mindmeld.donnie.in`) with `source_diversity ≥ 3` on 2/3 trials, but no synthesized final answer. A follow-up re-run at 65k context also produced no usable answers (2× visit-tool 404s halted the loop; the third trial aborted mid-run when the RTX 5090 tripped a display-blank thermal event above 85°C). Neither AREX cohort produced a scorable `final_answer`.
>
> ODR's LangChain-graph loop terminated cleanly on all three trials, producing 3-5 KB synthesized reports with grounded citations. Score is low because qwen2.5:32b hallucinated the CE license as "AGPLv3" or "Apache 2.0" in 2/3 trials and refused to commit on plugin-vs-fork in the third; only trial_03 correctly named CE=GPLv3 with a `gnu.org` citation. ODR wins on **completion reliability under the Colossus envelope**, not on absolute answer quality — a substantive improvement pass on the substrate is Stage 6.3 work.
>
> **Decision drivers:**
> 1. Completion rate 3/3 vs. 0/3 is the load-bearing outcome. A research substrate that cannot emit a final answer under the target hardware is not an inner loop.
> 2. Thermal envelope: RTX 5090 on Blackwell SM_120 under sustained bfloat16 attention with 65k KV cache tripped a display-blank thermal event this session. AREX-Turbo requires that envelope to have a fair chance at synthesis. Until Colossus receives thermal remediation (undervolt/fan curve/thermal-pad refresh — separate work, not blocking Stage 6.2), AREX-Turbo cannot be safely run at the context ceiling it needs.
> 3. Integration effort: ODR ships MIT with a public LangChain graph API and works out of the box against any OpenAI-compatible endpoint + MCP server. AREX ships weights (Apache-2.0) but the executor loop was hand-authored fresh from the HF-shipped protocol because the AREX code repo has no LICENSE file. Every future AREX iteration is bespoke maintenance; ODR upgrades are `pip install -U`.
>
> **What this ADR locks:** ODR (langchain-ai/open_deep_research) is the Stage 6.2 Zetesis inner loop substrate. `PORTING_LEDGER.md` promotes it from EVAL-ONLY to VENDORED (MIT); AREX-Turbo moves to REJECTED for Stage 6.2 with a preserved on-shelf note. Stage 6.3 owns substrate tuning (better underlying LLM, prompt-level fact-anchoring, `search_api=NONE`+MCP tuning) to raise the F1-F6 score above the current 16.7% floor.

> **STATUS AMENDMENT (2026-07-30):** Head-to-head eval harness authored and pinned. Contenders:
> - **AREX** — via the vendored `BAAI/AREX-Turbo` inference bundle (Apache-2.0, HF commit `129812742df4a5de27980ed07bda78d9d27c7370`, subpath `inference/`). Served on Colossus via vLLM. Full BrowseComp harness including `update_context` autonomous context compression and `finish` with confidence score. AREX code repo at `github.com/VectorSpaceLab/arex-model` was **not vendored** — repo ships without a LICENSE file, so per `kosmos-port-workflow` license discipline the harness executor was authored fresh from the Apache-2.0 HF-shipped protocol.
> - **Open Deep Research** — via the vendored `langchain-ai/open_deep_research@d337ae32ed4ff8f4c6fbe192ba3bf1b2d6610799` (MIT, EVAL-ONLY per PORTING_LEDGER). Served with `qwen2.5:32b-instruct-q4_K_M` on local Ollama. `search_api=NONE` + MCP tools substitute so ODR sees the same search backend AREX does.
>
> Both contenders route `search` and `visit` through an identical self-hosted **SearXNG** instance (see `ops/benchmarks/adr_010/docker-compose.yml`) so the eval measures loop quality, not search quality. Ground-truth question fixture (`fixtures/adr_010_question.json`) locks 6 canonical facts across Neo4j Community vs. DozerDB (packaging, license, feature deltas) for blind rating.
>
> Six locked metrics per trial: `answer_correctness`, `source_diversity`, `latency_seconds`, `gpu_utilization_peak_pct`, `vram_peak_gb`, `integration_effort_hours` (see `ops/benchmarks/adr_010/metrics.py`). Harness contract-tested in the Perplexity sandbox (17/17 pass); trial execution runs on Colossus. This amendment locks the eval design; winner will be added in a subsequent `LOCKED` amendment once the Colossus run completes.

---

Status: **Ratified v25 · LOCKED 2026-07-30** (winner: Open Deep Research; AREX-Turbo REJECTED for Stage 6.2)

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
- [x] AREX entry added to `PORTING_LEDGER.md` with source URLs (GitHub, both HF checkpoints).
- [x] Head-to-head eval harness authored (`ops/benchmarks/adr_010/`).
- [x] Six trials executed on Colossus (three per contender) with identical SearXNG substrate; artifacts at `ops/benchmarks/artifacts/adr-010-2026-07-30/`.
- [x] Blind rating against `fixtures/adr_010_question.json` canonical facts F1-F6.
- [x] Winner locked in this ADR (ODR); loser rejected (AREX-Turbo) with preserved on-shelf note.
- [x] `PORTING_LEDGER.md` updated: ODR promoted EVAL-ONLY → VENDORED; AREX-Turbo status → REJECTED for Stage 6.2.
- [x] `Kosmos-Build-Spec-v25.md` §17 ADR summary table row updated.
- [x] `adrs/README.md` index row updated.
- [x] Stage 6.2 Definition of Done in `Kosmos-Build-Sequence-v25.md` marked LANDED.
- [x] `BUILD_LOG.md` entry appended.
- [x] `SESSION_HANDOFF.md` overwritten, pointing at Stage 6.3.
