"""Stage 1.6 Phase 0 — ADR-073 EmbeddingsPort split.

Covers the five decisions locked by ADR-073:

- D1 ``ports.embeddings.EmbeddingsPort`` Protocol is importable
- D2 ``adapters.embeddings.ollama.adapter.OllamaEmbeddingsAdapter`` is importable
  and satisfies the protocol
- D3 ``LLMPort.embed()`` still exists (deprecation window) and emits
  ``DeprecationWarning`` when called on ``OllamaAdapter``
- D4 (Graphiti wiring) is exercised in
  ``adapters/memory/dozerdb/test_graphiti_temporal_index_contract.py``
- D5 ``kernel/app.py`` version bumped to ``6.10.0`` and ``registry.embeddings``
  attribute exists on ``_BootRegistry``

Fast tier — no network.
"""

from __future__ import annotations

import warnings
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from kernel.app import app, registry
from ports.embeddings import EmbeddingsPort


def test_kernel_version_bumped_to_6_10_0() -> None:
    assert app.version == "6.10.0"


def test_boot_registry_has_embeddings_field() -> None:
    # After boot the kernel populates ``registry.embeddings`` (or leaves
    # it None with an ``errors['embeddings']`` entry). Either way the
    # attribute MUST exist so downstream code can reference it safely.
    assert hasattr(registry, "embeddings")


def test_embeddings_port_protocol_importable() -> None:
    from ports.embeddings import (
        EmbeddingDimensionMismatch,
        EmbeddingError,
        EmbeddingsPort,
    )

    assert EmbeddingsPort is not None
    assert issubclass(EmbeddingError, RuntimeError)
    assert issubclass(EmbeddingDimensionMismatch, RuntimeError)


def test_ollama_embeddings_adapter_satisfies_port() -> None:
    from adapters.embeddings.ollama.adapter import OllamaEmbeddingsAdapter

    adapter = OllamaEmbeddingsAdapter(base_url="http://127.0.0.1:11434")
    assert isinstance(adapter, EmbeddingsPort)


def test_llm_port_embed_deprecation_warning(monkeypatch) -> None:
    """OllamaAdapter.embed still works but emits DeprecationWarning."""
    import asyncio

    from adapters.llm.ollama.adapter import OllamaAdapter

    adapter = OllamaAdapter(base_url="http://127.0.0.1:11434")

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {"embeddings": [[0.1, 0.2]]}
    fake_client = MagicMock(spec=httpx.AsyncClient)
    fake_client.post = AsyncMock(return_value=fake_response)
    monkeypatch.setattr(adapter, "_client", fake_client)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        asyncio.run(adapter.embed(input="hello"))

    deprecations = [
        w for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    assert any("ADR-073" in str(w.message) for w in deprecations), (
        f"Expected DeprecationWarning citing ADR-073, got: "
        f"{[str(w.message) for w in deprecations]}"
    )


def test_llama_swap_embed_deprecation_warning(monkeypatch) -> None:
    """LlamaSwapAdapter.embed still works but emits DeprecationWarning."""
    import asyncio

    from adapters.llm.llama_swap.adapter import LlamaSwapAdapter

    adapter = LlamaSwapAdapter(base_url="http://127.0.0.1:8080")

    fake_response = MagicMock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {"data": [{"embedding": [0.1]}]}
    fake_client = MagicMock(spec=httpx.AsyncClient)
    fake_client.post = AsyncMock(return_value=fake_response)
    monkeypatch.setattr(adapter, "_get_client", lambda: fake_client)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        asyncio.run(adapter.embed(input="hello"))

    deprecations = [
        w for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    assert any("ADR-073" in str(w.message) for w in deprecations)


# ADR-075 D1: KosmosGraphitiEmbedder was hard-deleted with the rest of
# the Graphiti wiring. Its bridge-shape test is removed with the class.
