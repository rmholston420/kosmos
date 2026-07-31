"""ZetesisLLMStub — Protocol-conformant LLMPort stub (ADR-056 sub-slice 2).

Every method raises NotImplementedError. Sub-slice 3+ replaces or swaps
in a real LLMPort adapter (llama-swap or ollama) at plugin construction.
"""

from __future__ import annotations

from typing import Any, AsyncIterator


class ZetesisLLMStub:
    """Minimal LLMPort stub. All methods raise NotImplementedError."""

    _MSG = "ZetesisLLMStub is a sub-slice-2 skeleton; wire a real LLMPort."

    async def generate(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError(self._MSG)

    async def generate_text(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> str:
        raise NotImplementedError(self._MSG)

    async def chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError(self._MSG)

    def generate_stream(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> AsyncIterator[str]:
        raise NotImplementedError(self._MSG)

    async def embed(
        self,
        *,
        input: str | list[str],
        model: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError(self._MSG)

    async def list_models(self) -> list[dict[str, Any]]:
        raise NotImplementedError(self._MSG)

    async def pull_model(self, *, name: str, insecure: bool = False) -> dict[str, Any]:
        raise NotImplementedError(self._MSG)

    async def delete_model(self, *, name: str) -> None:
        raise NotImplementedError(self._MSG)

    async def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
