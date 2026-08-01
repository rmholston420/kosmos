"""Protocol conformance test for EmbeddingsPort (ADR-073).

Any adapter satisfying ``EmbeddingsPort`` MUST pass this test. Fast tier
— no network, no live Ollama. Uses a stub adapter that returns fixed
vectors so we exercise the Protocol shape, not the backend.
"""

from __future__ import annotations

import asyncio

import pytest

from ports.embeddings import (
    EmbeddingDimensionMismatch,
    EmbeddingError,
    EmbeddingsPort,
)


class _StubEmbeddingsAdapter:
    """Minimal EmbeddingsPort implementation used only for protocol tests."""

    def __init__(self, dim: int = 4) -> None:
        self._dim = dim
        self._closed = False

    async def embed(
        self,
        *,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        if self._closed:
            raise EmbeddingError("closed")
        return [[float(i) for i in range(self._dim)] for _ in texts]

    async def dimensions(self, *, model: str | None = None) -> int:
        return self._dim

    def is_healthy(self) -> bool:
        return not self._closed

    async def close(self) -> None:
        self._closed = True


def test_stub_adapter_satisfies_protocol_runtime_checkable() -> None:
    adapter = _StubEmbeddingsAdapter()
    assert isinstance(adapter, EmbeddingsPort)


def test_embed_returns_one_vector_per_text() -> None:
    adapter = _StubEmbeddingsAdapter(dim=6)
    vectors = asyncio.run(adapter.embed(texts=["a", "b", "c"]))
    assert len(vectors) == 3
    assert all(len(v) == 6 for v in vectors)


def test_embed_empty_list_returns_empty() -> None:
    adapter = _StubEmbeddingsAdapter()

    # ADR-073 does not mandate returning [] on empty input at the port
    # layer — but the Ollama primary adapter does, and consumers rely on
    # that. This test locks the intended behavior for the stub too.
    async def _run() -> list[list[float]]:
        return await adapter.embed(texts=[])

    vectors = asyncio.run(_run())
    # A conforming implementation may either return [] or reject — pin
    # the empty-list behavior since it's the ergonomic choice.
    assert vectors == []


def test_dimensions_matches_embed_output_length() -> None:
    adapter = _StubEmbeddingsAdapter(dim=8)

    async def _run() -> tuple[int, int]:
        declared = await adapter.dimensions()
        vectors = await adapter.embed(texts=["x"])
        return declared, len(vectors[0])

    declared, runtime = asyncio.run(_run())
    assert declared == runtime == 8


def test_is_healthy_never_raises() -> None:
    adapter = _StubEmbeddingsAdapter()
    # is_healthy MUST NOT raise per ADR-023 rule 5.
    assert adapter.is_healthy() is True
    asyncio.run(adapter.close())
    assert adapter.is_healthy() is False


def test_close_is_idempotent() -> None:
    adapter = _StubEmbeddingsAdapter()

    async def _run() -> None:
        await adapter.close()
        await adapter.close()  # second close MUST NOT raise

    asyncio.run(_run())


def test_embed_after_close_raises_embedding_error() -> None:
    adapter = _StubEmbeddingsAdapter()

    async def _run() -> None:
        await adapter.close()
        with pytest.raises(EmbeddingError):
            await adapter.embed(texts=["a"])

    asyncio.run(_run())


def test_dimension_mismatch_exception_shape() -> None:
    # Exception hierarchy contract — callers catch these separately.
    assert issubclass(EmbeddingError, RuntimeError)
    assert issubclass(EmbeddingDimensionMismatch, RuntimeError)
    assert not issubclass(EmbeddingDimensionMismatch, EmbeddingError)
