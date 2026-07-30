"""LLMPort — formal Kosmos port for local LLM inference and model management.

Surface locked in by ADR-022 (LLMPort surface expansion) — amends
Kosmos-Build-Spec-v25.md §4.1.

Design rules (per ADR-022):

1. Keyword-only kwargs on all methods.
2. Model management (`list_models`, `pull_model`, `delete_model`) is part
   of the port — Colossus is single-user local-first; model lifecycle is
   a first-class user operation.
3. `is_healthy()` MUST be non-throwing.
4. `generate_stream` is declared as `def` returning `AsyncIterator[str]`
   (not `async def`), because Protocol cannot type an async generator
   directly; this matches the runtime shape of `async def` + `yield`.
5. Plugins depend on this Protocol, never on concrete adapters (ADR-007).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMPort(Protocol):
    """Formal contract for local LLM backends.

    Adapters live under `adapters/llm/<backend>/` and MUST implement this
    Protocol in full. See `adapters/llm/ollama/adapter.py` for the reference
    implementation.
    """

    # ── Inference (non-streaming) ──────────────────────────────────────────

    async def generate(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Single-prompt generation. Returns the full backend response dict."""
        ...

    async def generate_text(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> str:
        """Convenience: return only the generated text string."""
        ...

    async def chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        """Multi-turn chat, non-streaming. Returns the full response dict."""
        ...

    # ── Inference (streaming) ──────────────────────────────────────────────

    def generate_stream(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> AsyncIterator[str]:
        """Stream text deltas from the backend. Yields non-empty content only.

        Declared as `def` (not `async def`) so `Protocol` types the runtime
        shape of an async generator correctly.
        """
        ...

    # ── Embeddings ─────────────────────────────────────────────────────────

    async def embed(
        self,
        *,
        input: str | list[str],
        model: str | None = None,
    ) -> dict[str, Any]:
        """Return embeddings dict for input string or batch of strings."""
        ...

    # ── Model management ───────────────────────────────────────────────────

    async def list_models(self) -> list[dict[str, Any]]:
        """List installed model dicts. Returns raw backend dicts."""
        ...

    async def pull_model(self, *, name: str, insecure: bool = False) -> dict[str, Any]:
        """Download a model. Returns backend pull response."""
        ...

    async def delete_model(self, *, name: str) -> None:
        """Remove a model from the backend."""
        ...

    # ── Health & lifecycle ─────────────────────────────────────────────────

    async def is_healthy(self) -> bool:
        """Non-throwing health probe. MUST return False (not raise) on failure."""
        ...

    async def close(self) -> None:
        """Release any underlying resources (HTTP client, file handles)."""
        ...
