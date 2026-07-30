"""docling document-ingest harness (Stage 3.10, ADR-044).

Invokes a ``DoclingConverter``-shaped object (real ``docling`` at
runtime; a fake shim in unit tests) against a local file path, then
persists the result through :class:`ports.data.DataPort`.

Design boundaries:

- ADR-007: this module never imports another plugin package.
- ADR-023: no new port; the existing ``DataPort`` surface is reused
  unchanged for the first real consumer.
- ADR-028: every write goes through ``export_canonical`` — the
  non-bypassable port-level guard supplies zero-trust enforcement.
- ADR-044 Q1=A: docling is a **lazy** import, resolved only when the
  real converter is needed. The fast-tier tests supply a
  ``converter_factory`` that never touches ``docling``.
- ADR-044 Q4=A: success writes ``confidence=1.0``; any failure raises
  :class:`DoclingIngestFailure` and writes nothing.
- ADR-044 Q6=A: extension whitelist is enforced **before** the
  converter is invoked, so unsupported inputs never touch docling.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, Protocol

from ports.data import DataPort, PIITier

from .models import DoclingIngestPayload, IngestedDocument
from .policy import (
    DOCLING_DEFAULT_PII_TIER,
    DOCLING_INGEST_PROVENANCE,
    DOCLING_INGEST_RECORD_TYPE,
    DOCLING_SUCCESS_CONFIDENCE,
    DOCLING_UPSTREAM_COMMIT,
    DOCLING_UPSTREAM_PYPI_VERSION,
    require_supported_extension,
)

__all__ = [
    "DoclingConverter",
    "DoclingConverterFactory",
    "DoclingIngestFailure",
    "DoclingUnavailableError",
    "UnsupportedExtensionError",
    "ingest_document",
    "resolve_default_converter_factory",
]


class DoclingUnavailableError(RuntimeError):
    """Raised when the real ``docling`` package cannot be imported.

    Only surfaces when :func:`resolve_default_converter_factory` is
    invoked (i.e. the real path). Fast-tier tests inject their own
    ``converter_factory`` and therefore never hit this path.
    """


class DoclingIngestFailure(RuntimeError):
    """Raised when a converter runs but yields no usable document.

    Distinct from :class:`UnsupportedExtensionError` (a policy gate
    failure). ADR-044 Q4=A locks that this exception aborts ingestion —
    no low-confidence DataPort write is emitted.
    """


class UnsupportedExtensionError(ValueError):
    """Raised when the extension is not in the Stage 3.10 whitelist.

    Subclass of :class:`ValueError` so callers can catch either
    ``ValueError`` (the generic contract of
    :func:`.policy.require_supported_extension`) or the specific
    subclass for finer-grained handling.
    """


class DoclingConverter(Protocol):
    """Duck-typed docling converter surface used by the harness.

    Any object exposing a ``convert(source)`` method whose return value
    exposes ``.document`` (Pydantic v2 ``DoclingDocument`` at runtime)
    satisfies this Protocol. The unit tests supply a fake that returns
    a plain dataclass mirroring the same attribute shape.

    The two attribute reads the harness performs are:

    - ``result.document.export_to_dict()`` → lossless JSON dict
    - ``result.document.export_to_markdown()`` → summary string
    """

    def convert(self, source: str, /) -> Any: ...


#: A zero-arg callable that returns a :class:`DoclingConverter`.
DoclingConverterFactory = Callable[[], DoclingConverter]


def resolve_default_converter_factory() -> DoclingConverterFactory:
    """Return a factory that lazily constructs ``docling.DocumentConverter``.

    Import is deferred until the factory is *called* so the harness
    module remains dep-free at import time — critical for keeping
    ``make stage1-gate`` fast (docling pulls PyTorch etc.).

    Raises:
        DoclingUnavailableError: ``docling`` cannot be imported when
            the factory is invoked.
    """

    def _factory() -> DoclingConverter:
        try:
            from docling.document_converter import (  # type: ignore[import-not-found]
                DocumentConverter,
            )
        except ImportError as exc:  # pragma: no cover — Colossus-only
            raise DoclingUnavailableError(
                "the docling package is not installed. Install with "
                "`.venv/bin/pip install -e '.[ingest]'` on Colossus."
            ) from exc
        return DocumentConverter()

    return _factory


def _resolve_docling_version() -> str:
    """Return the installed ``docling`` version or the locked fallback.

    The harness records whichever wheel actually ran; when docling is
    not importable (fast-tier tests) the locked
    :data:`.policy.DOCLING_UPSTREAM_PYPI_VERSION` is recorded so
    envelopes still carry a stable string.
    """
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover — stdlib
        return DOCLING_UPSTREAM_PYPI_VERSION
    try:
        return version("docling")
    except PackageNotFoundError:
        return DOCLING_UPSTREAM_PYPI_VERSION


def _coerce_document_dict(document: Any) -> dict[str, Any]:
    """Return a plain dict from a docling document-shaped object.

    Real docling exposes ``.export_to_dict()``; fake shims may already
    return a dict. Anything else raises :class:`DoclingIngestFailure`
    (rather than a generic ``AttributeError``) so callers get one
    stable error class.
    """
    if isinstance(document, Mapping):
        return dict(document)
    exporter = getattr(document, "export_to_dict", None)
    if not callable(exporter):
        raise DoclingIngestFailure(
            "docling document has no export_to_dict(); "
            f"got {type(document).__name__}"
        )
    exported = exporter()
    if not isinstance(exported, Mapping):
        raise DoclingIngestFailure(
            "docling export_to_dict() must return a mapping; "
            f"got {type(exported).__name__}"
        )
    return dict(exported)


def _coerce_markdown(document: Any) -> str:
    """Return an ``export_to_markdown`` string or an empty string.

    Missing markdown is treated as ``""`` (some HTML fixtures produce
    empty markdown); an exporter that raises is treated as ingest
    failure.
    """
    exporter = getattr(document, "export_to_markdown", None)
    if not callable(exporter):
        return ""
    rendered = exporter()
    if rendered is None:
        return ""
    if not isinstance(rendered, str):
        raise DoclingIngestFailure(
            "docling export_to_markdown() must return a str; "
            f"got {type(rendered).__name__}"
        )
    return rendered


async def ingest_document(
    path: str | Path,
    *,
    data_port: DataPort,
    converter_factory: DoclingConverterFactory | None = None,
    pii_tier: PIITier = DOCLING_DEFAULT_PII_TIER,
    source_citation: str | None = None,
    attributes: Mapping[str, Any] | None = None,
) -> IngestedDocument:
    """Ingest one document and persist a canonical DataPort envelope.

    Steps:

    1. Resolve + validate ``path`` (must exist; must be a regular file).
    2. Extension policy gate — :func:`.policy.require_supported_extension`.
    3. Build the converter via ``converter_factory`` (defaults to the
       real docling factory; fast-tier tests inject a shim).
    4. Run ``converter.convert(str(path)).document`` and coerce into a
       :class:`DoclingIngestPayload`.
    5. Write through ``data_port.export_canonical`` with locked
       ``record_type`` / ``provenance`` / ``confidence`` /
       ``pii_tier``. Additional caller ``attributes`` merge on top of
       the payload's own attribute projection.

    Args:
        path: Local filesystem path to the source document.
        data_port: A live :class:`DataPort` (or a test double).
        converter_factory: Optional zero-arg factory returning a
            :class:`DoclingConverter`; defaults to the real docling
            factory resolved lazily.
        pii_tier: PII tier for the resulting envelope. Defaults to
            :data:`.policy.DOCLING_DEFAULT_PII_TIER` (``INTERNAL``).
        source_citation: Optional caller-supplied citation string
            recorded on the envelope.
        attributes: Optional caller-supplied attributes merged into the
            envelope ``attributes`` field on top of the payload's own
            attribute projection. Caller keys override.

    Returns:
        The :class:`IngestedDocument` describing the ingested payload
        and the resulting canonical export handle.

    Raises:
        UnsupportedExtensionError: Extension not in the whitelist.
        FileNotFoundError: ``path`` does not exist or is not a file.
        DoclingUnavailableError: Real docling was needed but not
            installed.
        DoclingIngestFailure: Converter ran but produced no usable
            document.
        ValueError: Zero-trust guard rejected the write (should never
            fire because the locked constants satisfy the guard).
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(
            f"docling ingest source must be an existing regular file: {source!s}"
        )
    ext = require_supported_extension(source.suffix)

    factory = converter_factory or resolve_default_converter_factory()
    converter = factory()
    try:
        raw_result = converter.convert(str(source))
    except DoclingIngestFailure:
        raise
    except Exception as exc:
        raise DoclingIngestFailure(
            f"docling.convert() raised {type(exc).__name__}: {exc}"
        ) from exc

    document_obj = getattr(raw_result, "document", None)
    if document_obj is None:
        raise DoclingIngestFailure(
            "docling converter result has no .document attribute; "
            f"got {type(raw_result).__name__}"
        )
    document_dict = _coerce_document_dict(document_obj)
    markdown = _coerce_markdown(document_obj)

    payload = DoclingIngestPayload(
        source_filename=source.name,
        source_extension=ext,
        source_size_bytes=source.stat().st_size,
        docling_version=_resolve_docling_version(),
        docling_commit=DOCLING_UPSTREAM_COMMIT,
        document=document_dict,
        markdown_export=markdown,
    )

    merged_attributes: dict[str, Any] = {
        "source_extension": payload.source_extension,
        "source_size_bytes": payload.source_size_bytes,
        "docling_version": payload.docling_version,
        "docling_commit": payload.docling_commit,
    }
    if attributes:
        merged_attributes.update(dict(attributes))

    handle = await data_port.export_canonical(
        DOCLING_INGEST_RECORD_TYPE,
        payload.to_payload(),
        provenance=DOCLING_INGEST_PROVENANCE,
        confidence=DOCLING_SUCCESS_CONFIDENCE,
        pii_tier=pii_tier,
        source_citation=source_citation,
        attributes=merged_attributes,
    )

    return IngestedDocument(
        payload=payload,
        canonical_hash=handle.canonical_hash,
        storage_path=str(handle.storage_path),
        exported_at_iso=handle.exported_at.isoformat(),
    )
