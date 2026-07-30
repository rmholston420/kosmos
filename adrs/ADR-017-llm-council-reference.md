# ADR-017 — Karpathy `llm-council` as Synedrion Design-Pattern Reference (Not Vendored)

**Status:** Ratified · **Lock-in phase:** Phase 6.4

## Context

Synedrion (multi-agent coordination) needs a pattern for structured multi-model deliberation: multiple LLM "voices" vote or debate a decision, then a synthesizer produces the final action. karpathy/`llm-council` demonstrates this pattern minimally and effectively.

## Decision

Treat `karpathy/llm-council` as a **design reference only**. Do **not** vendor the code.

- Synedrion implements council-pattern voting/deliberation natively, using Kosmos's LLMPort and EventBusPort.
- Council roles, voting weight, and synthesis policy are Kosmos-defined; the shape of the interaction is informed by llm-council.

## Rationale

- llm-council is a minimal notebook-style repo — vendoring would import stylistic overhead without meaningful code reuse.
- Native Synedrion implementation stays within LLMPort/EventBusPort contracts (no direct LLM calls or side-channels).
- Design pattern is small enough to re-derive; reference is enough.

## Consequences

- PORTING_LEDGER lists llm-council under "Design References — Do Not Vendor".
- If a future need emerges for llm-council-style code beyond patterns (e.g., specific prompt templates), revisit with a new ADR.

## Lock-in phase

Phase 6.4 — Synedrion council-pattern implementation.

## References

- PORTING_LEDGER: karpathy/llm-council (DESIGN REFERENCE)
- ADR-011 (a2a-sdk transport for Synedrion messages)
