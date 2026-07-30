"""Frozen models for the Tektos docling ingest subsystem.

Stage 3.10, ADR-044. All value objects are immutable and JSON-friendly
so a docling ingest payload can round-trip through
:meth:`ports.data.DataPort.export_canonical` without custom encoders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["DoclingIngestPayload", "IngestedDocument"]


@dataclass(frozen=True, slots=True)
class DoclingIngestPayload:
    """The DataPort payload for one ingested document.

    Only primitives / dicts / lists appear here so
    :func:`json.dumps(sort_keys=True)` (the fast-tier canonicalizer test
    double at ``adapters.data.filesystem.SortedJsonCanonicalizer``) can
    stably serialize the envelope.

    Field mapping:

    - :attr:`source_filename` — basename of the source document
      (e.g. ``sample.pdf``). Full paths are deliberately omitted so
      envelopes never leak host-local storage layout.
    - :attr:`source_extension` — lowercase extension with leading dot
      (e.g. ``".pdf"``); one of :data:`.policy.DOCLING_SUPPORTED_EXTENSIONS`.
    - :attr:`source_size_bytes` — byte-count of the source file at
      ingest time; recorded for downstream integrity checks.
    - :attr:`docling_version` — resolved ``docling`` package version
      string, e.g. ``"2.116.0"``.
    - :attr:`docling_commit` — the upstream commit SHA locked in
      :mod:`.policy` (recorded for audit even when a PyPI wheel is
      what actually ran).
    - :attr:`document` — the lossless docling JSON returned by
      ``DoclingDocument.export_to_dict()``. Kept opaque here; the
      Stage 3.10 test surface only asserts key presence, not schema.
    - :attr:`markdown_export` — a small ``export_to_markdown()`` string
      captured for cheap downstream summarization; may be ``""`` when
      docling emits an empty markdown (e.g. tiny HTML fixtures).
    """

    source_filename: str
    source_extension: str
    source_size_bytes: int
    docling_version: str
    docling_commit: str
    document: dict[str, Any]
    markdown_export: str

    def to_payload(self) -> dict[str, Any]:
        """Project this payload into a DataPort-ready dict.

        The returned mapping is what actually appears under the envelope
        ``payload`` key. Callers must not mutate the return value; a
        fresh copy is produced on every call so tests can freely mutate
        without corrupting the frozen dataclass.
        """
        return {
            "source_filename": self.source_filename,
            "source_extension": self.source_extension,
            "source_size_bytes": self.source_size_bytes,
            "docling_version": self.docling_version,
            "docling_commit": self.docling_commit,
            "document": dict(self.document),
            "markdown_export": self.markdown_export,
        }


@dataclass(frozen=True, slots=True)
class IngestedDocument:
    """A wrapped :class:`DoclingIngestPayload` + resulting DataPort handle.

    Returned by :func:`.harness.ingest_document`. Attributes ride along
    on the envelope's ``attributes`` field (not the ``payload``) so
    downstream code can filter by them without reading the potentially
    large docling JSON body.
    """

    payload: DoclingIngestPayload
    canonical_hash: str
    storage_path: str
    exported_at_iso: str

    def to_attributes(self) -> dict[str, Any]:
        """DataPort ``attributes`` projection.

        Only compact, filterable fields go here — the heavyweight
        docling document JSON stays in ``payload``.
        """
        return {
            "source_filename": self.payload.source_filename,
            "source_extension": self.payload.source_extension,
            "source_size_bytes": self.payload.source_size_bytes,
            "docling_version": self.payload.docling_version,
            "docling_commit": self.payload.docling_commit,
        }
