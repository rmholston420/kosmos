"""Tektos docling document-ingestion subsystem (Stage 3.10, ADR-044).

Public surface — everything else is implementation detail. Keep this
import graph flat so ADR-007 AST guard tests never grow false positives.
"""

from __future__ import annotations

from .harness import (
    DoclingIngestFailure,
    DoclingUnavailableError,
    UnsupportedExtensionError,
    ingest_document,
)
from .models import DoclingIngestPayload, IngestedDocument
from .policy import (
    DOCLING_DEFAULT_PII_TIER,
    DOCLING_INGEST_PROVENANCE,
    DOCLING_INGEST_RECORD_TYPE,
    DOCLING_MAX_CONFIDENCE,
    DOCLING_MIN_CONFIDENCE,
    DOCLING_SUCCESS_CONFIDENCE,
    DOCLING_SUPPORTED_EXTENSIONS,
    DOCLING_UPSTREAM_COMMIT,
    DOCLING_UPSTREAM_LICENSE,
    DOCLING_UPSTREAM_PACKAGE,
    DOCLING_UPSTREAM_PYPI_VERSION,
    DOCLING_UPSTREAM_REPO,
    confidence_for_ingest,
    normalize_extension,
    require_supported_extension,
)

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
    "DoclingIngestFailure",
    "DoclingIngestPayload",
    "DoclingUnavailableError",
    "IngestedDocument",
    "UnsupportedExtensionError",
    "confidence_for_ingest",
    "ingest_document",
    "normalize_extension",
    "require_supported_extension",
]
