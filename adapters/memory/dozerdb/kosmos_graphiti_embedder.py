"""adapters.memory.dozerdb.kosmos_graphiti_embedder — Graphiti bridge (ADR-073).

Thin wrapper that adapts our ``EmbeddingsPort`` into the ``EmbedderClient``
shape Graphiti expects, so ``GraphitiTemporalIndex`` can drop the inline
``OpenAIEmbedderConfig(api_key="ollama-not-used", ...)`` shim.

Graphiti's ``EmbedderClient`` protocol (per graphiti-core, upstream):

    class EmbedderClient(ABC):
        @abstractmethod
        async def create(
            self,
            input_data: str | list[str],
        ) -> list[float] | list[list[float]]:
            ...

We satisfy this by routing through ``EmbeddingsPort.embed`` and unwrapping
the single-input case so Graphiti's callers get the shape they expect.

References:
    - ADR-073 D4
    - `ports/embeddings.py`
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ports.embeddings import EmbeddingsPort


class KosmosGraphitiEmbedder:
    """Bridge ``EmbeddingsPort`` → Graphiti ``EmbedderClient``.

    Not a subclass of Graphiti's abstract base because Graphiti is
    lazy-imported inside ``GraphitiTemporalIndex`` (fast tier isolation).
    Duck-typing suffices — Graphiti calls ``embedder.create(input_data)``.
    """

    def __init__(self, embeddings: EmbeddingsPort, *, model: str | None = None) -> None:
        self._embeddings = embeddings
        self._model = model

    async def create(
        self,
        input_data: str | list[str],
    ) -> list[float] | list[list[float]]:
        """Graphiti-shaped embed call.

        Preserves the input-vs-batch return shape convention Graphiti
        assumes: single ``str`` → single vector, ``list[str]`` → batch.
        """
        if isinstance(input_data, str):
            vectors = await self._embeddings.embed(
                texts=[input_data],
                model=self._model,
            )
            return vectors[0]
        vectors = await self._embeddings.embed(
            texts=list(input_data),
            model=self._model,
        )
        return vectors
