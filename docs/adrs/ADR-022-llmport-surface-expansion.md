# ADR-022 — LLMPort Surface Expansion (spec §4.1 tightening)

**Status:** Ratified v25 (spec amendment)
**Lock-in phase:** Stage 1.2 (LLMPort Protocol formalization)
**Supersedes:** —
**Amends:** Kosmos-Build-Spec-v25.md §4.1 (LLMPort row)

## Context

Kosmos-Build-Spec-v25.md §4.1 declares LLMPort with a three-method contract:

> `LLMPort` → `complete()`, `stream()`, `embed()`

This shape was authored before the donor adapter surface was inventoried. The
Stage 1.1 consolidation (ADR-012, commit `0361d79`) merged three donor Ollama
adapters into `adapters/llm/ollama/`. The consolidated adapter's actual public
surface — which existing donor call-sites in Rigpa-LMS, Forge-OH, PlexClaw, and
axiom depend on — is broader:

- `generate(*, prompt, model?, system?, **options) -> dict`
- `generate_text(*, prompt, model?, system?, **options) -> str`
- `generate_stream(*, prompt, model?, system?, **options) -> AsyncIterator[str]`
- `chat(*, messages, model?, **options) -> dict`
- `embed(*, input, model?) -> dict`
- `list_models() -> list[dict]`
- `pull_model(*, name, insecure=False) -> dict`
- `delete_model(*, name) -> None`
- `is_healthy() -> bool`
- `close() -> None`

If `ports/llm.py` implements only the spec's 3-method surface, all downstream
call-sites (Tektos plugin generation loop, Zetesis research loop, Oikos
finance summarization, kernel `is_healthy` probes, Colossus model management
CLI) would either bypass the port (ADR-007 violation) or force painful
refactoring away from working idioms.

Three surface shapes were evaluated (see this session's discussion):

- **A.** Match the spec verbatim (3 methods). Push everything else into
  adapter-private helpers. Forces downstream refactoring; blocks legitimate
  model-management use cases through the port.
- **B.** Expand the spec to the donor surface. Cheap; matches reality.
- **C.** Split into `LLMPort` + `ModelRegistryPort`. Cleanest boundary but
  adds a 12th port for what is functionally one backend concern (a single
  Ollama process serves both inference and model management), and requires
  another ADR + additional port contract test suite.

## Decision

Adopt **Option B**. Expand LLMPort to the donor-derived surface. Amend
Kosmos-Build-Spec-v25.md §4.1 accordingly.

Formal `LLMPort` Protocol in `ports/llm.py`:

```python
from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class LLMPort(Protocol):
    # ── Inference (non-streaming) ──────────────────────────────────────
    async def generate(
        self, *, prompt: str, model: str | None = None,
        system: str | None = None, **options: Any,
    ) -> dict[str, Any]: ...

    async def generate_text(
        self, *, prompt: str, model: str | None = None,
        system: str | None = None, **options: Any,
    ) -> str: ...

    async def chat(
        self, *, messages: list[dict[str, str]], model: str | None = None,
        **options: Any,
    ) -> dict[str, Any]: ...

    # ── Inference (streaming) ──────────────────────────────────────────
    def generate_stream(
        self, *, prompt: str, model: str | None = None,
        system: str | None = None, **options: Any,
    ) -> AsyncIterator[str]: ...

    # ── Embeddings ─────────────────────────────────────────────────────
    async def embed(
        self, *, input: str | list[str], model: str | None = None,
    ) -> dict[str, Any]: ...

    # ── Model management ───────────────────────────────────────────────
    async def list_models(self) -> list[dict[str, Any]]: ...
    async def pull_model(self, *, name: str, insecure: bool = False) -> dict[str, Any]: ...
    async def delete_model(self, *, name: str) -> None: ...

    # ── Health & lifecycle ─────────────────────────────────────────────
    async def is_healthy(self) -> bool: ...
    async def close(self) -> None: ...
```

Design rules locked in:

1. **Keyword-only kwargs** on all methods (matches Kosmos convention, matches
   `adapters/llm/ollama/adapter.py` as consolidated in Stage 1.1).
2. **`generate_stream` is a coroutine returning `AsyncIterator[str]`** — not
   declared `async def`; `Protocol` cannot type an async generator directly,
   so it is declared as a regular `def` returning an async iterator, matching
   Python's runtime shape for `async def` + `yield`.
3. **Model management is part of the port**, not adapter-private. Rationale:
   Colossus is a single-user local-first system; model lifecycle is a
   first-class user operation, not an ops concern hidden behind an admin API.
4. **`is_healthy()` MUST be non-throwing.** Enforced by contract test.
5. **No streaming variant of `chat`** in Stage 1.2. `generate_stream` covers
   the streaming path via /api/chat internally (adapter detail). If
   multi-turn streaming becomes needed post-Stage-6, add `chat_stream` under a
   minor port version bump (semver rule, spec §4.1).

## Rationale

**Why B over A.** Option A preserves an aspirational spec that no consumer
matches. Every downstream site would either import `OllamaAdapter` directly
(ADR-007 violation) or wrap the 3-method port with adapter-specific extension
methods (which is the same violation dressed up). Rewriting Rigpa/Forge-OH/
PlexClaw/axiom call-sites to fit a 3-method surface produces no isolation
benefit — the extra methods exist because working code needs them.

**Why B over C.** ModelRegistryPort would formalize a distinction that the
runtime does not honor (Ollama is a single process; model management is a
side effect of the same daemon). It adds a 12th port with its own contract
tests, its own singleton, its own adapter directory, and its own fault-injection
target — for functionally one backend. The single-user local-first constraint
(project custom instructions) argues against gratuitous port proliferation.
Adopt C only if Kosmos later grows to support hosted model providers where
inference and registry are separate services.

**Reversibility.** If Kosmos v26 adopts a hosted-inference backend (OpenAI-
compatible remote provider, e.g. via LiteLLM), model management naturally
becomes admin-only and can be extracted into a new `ModelRegistryPort` at that
time. Doing so is a clean subtractive amendment: move `list_models`/
`pull_model`/`delete_model` out of LLMPort, add ModelRegistryPort, keep
inference methods stable. Nothing about Option B blocks that path.

## Consequences

**Spec amendments (this ADR):**
- `docs/Kosmos-Build-Spec-v25.md` §4.1 — LLMPort Contract column expanded from
  `complete()`, `stream()`, `embed()` to the ten-method surface above, with
  footnote referencing ADR-022.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-022 row added.

**Files created:**
- `ports/llm.py` — LLMPort Protocol + type aliases
- `adapters/llm/ollama/test_contract.py` — extended with
  `isinstance(adapter, LLMPort)` runtime-protocol check
- `docs/adrs/ADR-022-llmport-surface-expansion.md` — this file

**Files updated:**
- `adapters/llm/ollama/adapter.py` — no signature changes; only add an
  `LLMPort` binding comment and confirm all methods already match.
- `docs/adrs/README.md` — ADR-022 index row
- `docs/PORTING_LEDGER.md` — Ollama entry updated to reference ADR-022 for
  LLMPort surface definition
- `BUILD_LOG.md` — append ADR-022 entry + Stage 1.2 completion entry

**Downstream stages affected:**
- Stage 1.3 (llama-swap sidecar per ADR-009) — llama-swap adapter must also
  implement the full 10-method surface, OR expose a subset with a
  `NotImplementedError` on unsupported methods and a documented capability
  flag. Sidecar contract to be finalized in Stage 1.3.
- Stage 2 (Tektos plugin) — free to use `chat`, `generate_stream`,
  `list_models` via LLMPort without adapter imports.

**No changes** to ADR-007 (events-only cross-plugin coupling), ADR-008
(MemoryPort), ADR-009 (llama-swap primary), ADR-012 (donor consolidation),
ADR-021 (SearchPort).

## Lock-in phase

Stage 1.2. Contract test in `adapters/llm/ollama/test_contract.py` MUST assert
`isinstance(OllamaAdapter(), LLMPort)` before Stage 1.2 completes.

## References

- `docs/Kosmos-Build-Spec-v25.md` §4.1 (amended by this ADR)
- `docs/Kosmos-Build-Sequence-v25.md` Stage 1.2
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-009-llama-swap-primary.md`
- `docs/adrs/ADR-012-donor-adapter-consolidation.md`
- `docs/adrs/ADR-021-searchport-introduction.md` (same pattern of donor-surface-driven port design)
- Stage 1.1 commit: `0361d79`
