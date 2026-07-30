# ADR-009 — llama-swap as LLMPort Primary Sidecar (with router-mode fallback)

**Status:** Ratified v25 (contingent on Stage 1.7 benchmark) · **Lock-in phase:** Stage 1

## Context

Colossus has one physical GPU (RTX 5090, 32 GB VRAM). Kosmos plugins invoke different models for different tasks — coding (larger context, tool-following), research (retrieval-heavy), governance (small guardrail models), background jobs. Loading all models simultaneously exceeds VRAM. Cold-loading on demand is slow.

Two viable architectures:

- **llama-swap sidecar** — external process manages model residency; API calls specify the desired model; llama-swap swaps as needed.
- **Router-mode** — a single llama.cpp / vLLM / router process holds one model; model switching happens by process restart or in-process load.

## Decision

**Primary:** llama-swap. **Fallback:** router-mode, kept as a working alternate.

- LLMPort adapter wraps llama-swap by default.
- Priority queue for GPU access, ranked:
  1. Phrouros anomaly (algedonic — jumps queue)
  2. Active Tektos task (user-facing)
  3. Synedrion / Zetesis background work

- **Model-swap SLO** (measured on Colossus at Stage 1.7):
  - **Cold-load target: < 8 s**
  - **Warm-swap target: < 2 s**

- **Contingent adoption:** If llama-swap on Colossus fails these SLOs, LLMPort adapter switches to router-mode; this ADR is amended, decision recorded in BUILD_LOG.md with benchmark artifact.

## Rationale

- **llama-swap advantages** — process isolation per model, clean crash recovery, well-defined API surface, easier priority-queue integration.
- **Router-mode risk** — restart-based swap defeats the SLO; in-process swap on some backends is fragile at high memory pressure.
- **Contingency preserves progress** — if primary fails, we do not stop the build; we swap adapters (LLMPort abstraction was designed for this).

## Consequences

- Stage 1.7 gate is a real measurement, not a rubber-stamp. Benchmark artifact is required to lock the ADR.
- LLMPort's priority-queue hook must be adapter-agnostic (works for both llama-swap and router-mode).
- Model quantization choices (GGUF vs. exl2 vs. AWQ) are made per model in `ops/model-selection.md`; not part of this ADR.

## Open items

- None. Contingency is defined; benchmark is scheduled at Stage 1.7.

## Lock-in phase

Stage 1.3 (adapter wire-up) → Stage 1.7 (SLO benchmark) → status `LOCKED` or `AMENDED (router-mode)`.

## References

- Spec §11 (Hardware Portability)
- PORTING_LEDGER: llama-swap, llama.cpp (for router fallback)
