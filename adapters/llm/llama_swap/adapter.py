"""LlamaSwapAdapter — LLMPort adapter for the llama-swap sidecar.

Vendored per ADR-009 (llama-swap primary sidecar) — Stage 1.3.
Implements the LLMPort Protocol (ADR-022) against llama-swap's
OpenAI-compatible HTTP API.

llama-swap is an external Go daemon (github.com/mostlygeek/llama-swap,
MIT). This adapter speaks its endpoints only; no Go source is vendored.

Design notes:

- Uses OpenAI-compatible endpoints: `/v1/completions`, `/v1/chat/completions`,
  `/v1/embeddings`, `/v1/models`.
- `is_healthy` probes `/health` (llama-swap-native) and MUST NOT raise
  (ADR-022 rule 3).
- `pull_model` / `delete_model` raise `NotImplementedError` — llama-swap
  does not manage weights; models are declared in llama-swap's `config.yaml`
  and served by upstream inference processes (llama.cpp, vllm, etc.).
  Documented capability subset per ADR-022 Consequences §Downstream stages.
- Keyword-only kwargs on all methods (ADR-022 rule 1).
- Single reusable `httpx.AsyncClient` (consistent with OllamaAdapter).
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx


DEFAULT_BASE_URL = "http://127.0.0.1:8080"
DEFAULT_MODEL = "qwen3:14b-q8_0"
DEFAULT_TIMEOUT_S = 300.0


class LlamaSwapAdapter:
    """HTTP-client adapter for the llama-swap sidecar.

    Satisfies the LLMPort Protocol (see `ports/llm.py`). Contract test in
    `test_contract.py` asserts `isinstance(LlamaSwapAdapter(), LLMPort)` at
    runtime.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._base_url = (
            base_url
            or os.environ.get("KOSMOS_LLAMA_SWAP_BASE_URL")
            or DEFAULT_BASE_URL
        ).rstrip("/")
        self._default_model = (
            default_model
            or os.environ.get("KOSMOS_LLAMA_SWAP_DEFAULT_MODEL")
            or DEFAULT_MODEL
        )
        self._timeout = httpx.Timeout(timeout_s, connect=10.0)
        self._client: httpx.AsyncClient | None = None

    # ── internal ───────────────────────────────────────────────────────────

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                follow_redirects=True,
            )
        return self._client

    def _resolve_model(self, model: str | None) -> str:
        return model or self._default_model

    # ── Inference (non-streaming) ──────────────────────────────────────────

    async def generate(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "prompt": prompt,
            "stream": False,
        }
        if system is not None:
            # OpenAI /v1/completions has no `system`; encode it as prefix.
            payload["prompt"] = f"{system}\n\n{prompt}"
        payload.update(options)
        client = self._get_client()
        response = await client.post("/v1/completions", json=payload)
        response.raise_for_status()
        return response.json()

    async def generate_text(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> str:
        result = await self.generate(
            prompt=prompt, model=model, system=system, **options
        )
        try:
            return result["choices"][0]["text"]
        except (KeyError, IndexError, TypeError):
            return ""

    async def chat(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None = None,
        **options: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "messages": messages,
            "stream": False,
        }
        payload.update(options)
        client = self._get_client()
        response = await client.post("/v1/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()

    # ── Inference (streaming) ──────────────────────────────────────────────

    async def generate_stream(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "prompt": prompt,
            "stream": True,
        }
        if system is not None:
            payload["prompt"] = f"{system}\n\n{prompt}"
        payload.update(options)
        client = self._get_client()
        async with client.stream("POST", "/v1/completions", json=payload) as response:
            response.raise_for_status()
            async for raw_line in response.aiter_lines():
                if not raw_line:
                    continue
                # OpenAI SSE frames: "data: {json}\n\n" and "data: [DONE]\n\n"
                if raw_line.startswith("data:"):
                    data = raw_line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    try:
                        text = obj["choices"][0].get("text") or ""
                    except (KeyError, IndexError, TypeError):
                        text = ""
                    if text:
                        yield text

    # ── Embeddings ─────────────────────────────────────────────────────────

    async def embed(
        self,
        *,
        input: str | list[str],
        model: str | None = None,
    ) -> dict[str, Any]:
        """POST /v1/embeddings via llama-swap.

        .. deprecated:: ADR-073 (Ratified v25 2026-08-01)
           Use ``ports.embeddings.EmbeddingsPort`` instead.
        """
        import warnings

        warnings.warn(
            "LlamaSwapAdapter.embed() is deprecated per ADR-073. "
            "Use EmbeddingsPort (adapters.embeddings.ollama).",
            DeprecationWarning,
            stacklevel=2,
        )
        payload: dict[str, Any] = {
            "model": self._resolve_model(model),
            "input": input,
        }
        client = self._get_client()
        response = await client.post("/v1/embeddings", json=payload)
        response.raise_for_status()
        return response.json()

    # ── Model management ───────────────────────────────────────────────────

    async def list_models(self) -> list[dict[str, Any]]:
        """List models declared in llama-swap's config.yaml (via /v1/models)."""
        client = self._get_client()
        response = await client.get("/v1/models")
        response.raise_for_status()
        payload = response.json()
        # OpenAI-shape: {"object":"list","data":[{...}, ...]}
        data = payload.get("data", []) if isinstance(payload, dict) else []
        return list(data) if isinstance(data, list) else []

    async def pull_model(self, *, name: str, insecure: bool = False) -> dict[str, Any]:
        """Not supported.

        llama-swap does not manage weights; models are declared statically in
        `config.yaml` and served by upstream inference processes. Managing
        weights out-of-band is the operator's responsibility (or delegated
        to the underlying backend like Ollama when llama-swap fronts it).
        Documented capability subset per ADR-022 Consequences §Downstream stages.
        """
        raise NotImplementedError(
            "llama-swap does not manage model weights; declare models in "
            "llama-swap config.yaml (see ADR-009). Use OllamaAdapter for "
            "runtime pull semantics."
        )

    async def delete_model(self, *, name: str) -> None:
        """Not supported. See `pull_model` docstring."""
        raise NotImplementedError(
            "llama-swap does not manage model weights; remove entries from "
            "llama-swap config.yaml instead (see ADR-009)."
        )

    # ── Health & lifecycle ─────────────────────────────────────────────────

    async def is_healthy(self) -> bool:
        """Probe `/health` (llama-swap-native). Non-throwing per ADR-022 rule 3."""
        try:
            client = self._get_client()
            response = await client.get("/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None


# ── module-level singleton ────────────────────────────────────────────────

_singleton: LlamaSwapAdapter | None = None


def get_llama_swap_adapter() -> LlamaSwapAdapter:
    global _singleton
    if _singleton is None:
        _singleton = LlamaSwapAdapter()
    return _singleton


async def close_llama_swap_adapter() -> None:
    global _singleton
    if _singleton is not None:
        await _singleton.close()
        _singleton = None
