"""Locked policy constants for the Tektos docling ingest subsystem.

Stage 3.10, ADR-044. Every constant is load-bearing and referenced by
contract tests — do not rename or repoint any of these outside a
superseding ADR.
"""

from __future__ import annotations

from typing import Final

from ports.data import PIITier

__all__ = [
    "DOCLING_DEFAULT_PII_TIER",
    "DOCLING_INGEST_PROVENANCE",
    "DOCLING_INGEST_RECORD_TYPE",
    "DOCLING_MAX_CONFIDENCE",
    "DOCLING_MIN_CONFIDENCE",
    "DOCLING_SUCCESS_CONFIDENCE",
    "DOCLING_SUPPORTED_EXTENSIONS",
    "DOCLING_UPSTREAM_COMMIT",
    "DOCLING_UPSTREAM_LICENSE",
    "DOCLING_UPSTREAM_PACKAGE",
    "DOCLING_UPSTREAM_PYPI_VERSION",
    "DOCLING_UPSTREAM_REPO",
    "confidence_for_ingest",
    "normalize_extension",
    "require_supported_extension",
]

#: Provenance stamped on every DataPort export from the docling harness.
DOCLING_INGEST_PROVENANCE: Final[str] = "tektos-docling-ingest"

#: Canonical DataPort ``record_type`` for every ingested document envelope.
DOCLING_INGEST_RECORD_TYPE: Final[str] = "tektos.ingest.document"

#: Upstream PyPI package name (see ``pyproject.toml [optional-dependencies] ingest``).
DOCLING_UPSTREAM_PACKAGE: Final[str] = "docling"

#: Upstream PyPI version pinned at Stage 3.10 kickoff.
DOCLING_UPSTREAM_PYPI_VERSION: Final[str] = "2.116.0"

#: Upstream GitHub commit SHA locked at Stage 3.10 for ADR-044 audit trail.
DOCLING_UPSTREAM_COMMIT: Final[str] = "ba8251e9cda84bab44cebe3b884119d3f50cb12a"

#: Upstream SPDX license identifier locked for PORTING_LEDGER + audit.
DOCLING_UPSTREAM_LICENSE: Final[str] = "MIT"

#: Upstream repository URL (canonical post org-rename).
DOCLING_UPSTREAM_REPO: Final[str] = "https://github.com/docling-project/docling"

#: Default PII tier for ingested documents (ADR-044 Q3=A).
DOCLING_DEFAULT_PII_TIER: Final[PIITier] = PIITier.INTERNAL

#: DataPort confidence recorded on a successful ingestion (ADR-044 Q4=A).
DOCLING_SUCCESS_CONFIDENCE: Final[float] = 1.0

#: Lower bound of the DataPort confidence range enforced on writes.
DOCLING_MIN_CONFIDENCE: Final[float] = 0.0

#: Upper bound of the DataPort confidence range enforced on writes.
DOCLING_MAX_CONFIDENCE: Final[float] = 1.0

#: Frozen set of input extensions permitted at Stage 3.10 (ADR-044 Q6=A).
#:
#: Extensions are matched **case-insensitively** and stored here as their
#: lowercase form with a leading dot. Widening this set is a follow-up
#: config change with no ADR needed; narrowing requires a superseding
#: ADR because tests key off this exact frozenset.
DOCLING_SUPPORTED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".pdf", ".docx", ".html"}
)


def normalize_extension(extension: str) -> str:
    """Normalize a filename extension for whitelist comparison.

    - Lowercases the extension.
    - Ensures exactly one leading ``.``.

    ``normalize_extension('PDF')`` and ``normalize_extension('.pdf')``
    both return ``'.pdf'``. Non-str inputs raise :class:`TypeError`.
    """
    if not isinstance(extension, str):
        raise TypeError(
            "normalize_extension requires a str, "
            f"got {type(extension).__name__}"
        )
    ext = extension.strip().lower()
    if not ext:
        return ""
    if not ext.startswith("."):
        ext = f".{ext}"
    return ext


def require_supported_extension(extension: str) -> str:
    """Return the normalized extension or raise :class:`ValueError`.

    Fast policy gate used by the harness before ever invoking docling.
    Test doubles rely on this raising ``ValueError`` (not a subclass of
    ``OSError`` or ``RuntimeError``) so the fast-tier tests can assert
    the exception hierarchy independently of the docling package.
    """
    ext = normalize_extension(extension)
    if ext not in DOCLING_SUPPORTED_EXTENSIONS:
        raise ValueError(
            "docling ingest at Stage 3.10 accepts only "
            f"{sorted(DOCLING_SUPPORTED_EXTENSIONS)!r}; got {extension!r}"
        )
    return ext


def confidence_for_ingest(success: bool) -> float:
    """Map an ingest outcome to the DataPort confidence.

    ADR-044 Q4=A locks the mapping: ``True -> 1.0``. ``False`` is
    reserved for future soft-failure ingest modes and currently returns
    ``DOCLING_MIN_CONFIDENCE``; the Stage 3.10 harness raises rather
    than emitting a low-confidence envelope, so the ``False`` branch is
    exercised only in unit tests that pin the mapping.

    Raises:
        TypeError: ``success`` is not a ``bool``.
    """
    if not isinstance(success, bool):
        raise TypeError(
            "confidence_for_ingest requires a bool, "
            f"got {type(success).__name__}"
        )
    return DOCLING_SUCCESS_CONFIDENCE if success else DOCLING_MIN_CONFIDENCE
