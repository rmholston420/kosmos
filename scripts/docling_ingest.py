"""Kernel runner: ingest one document through docling + DataPort.

Stage 3.10, ADR-044. Wire-up mirrors ``scripts/pier_eval.py``:

* Loads the filesystem :class:`DataPort` adapter rooted at ``--out-root``.
* Calls :func:`plugins.tektos.ingest.ingest_document` with the resolved
  file path.
* Prints the returned :class:`~plugins.tektos.ingest.IngestedDocument`
  fields as JSON on stdout so the caller (Makefile target, ops
  runbook, or Phase-5 bill-tracking plugin) can consume it.

Failure modes exit non-zero with a short human-readable message on
stderr; no partial DataPort envelope is ever emitted (ADR-044 Q4=A).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from adapters.data.filesystem import (
    FilesystemDataAdapter,
    FilesystemStorage,
    SortedJsonCanonicalizer,
)
from plugins.tektos.ingest import (
    DoclingIngestFailure,
    DoclingUnavailableError,
    UnsupportedExtensionError,
    ingest_document,
)
from ports.data import PIITier


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="docling_ingest",
        description=(
            "Ingest one PDF/DOCX/HTML document through docling and persist a "
            "canonical JSON-LD envelope via DataPort (Stage 3.10, ADR-044)."
        ),
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Filesystem path to the source document (.pdf/.docx/.html).",
    )
    parser.add_argument(
        "--out-root",
        default=".ingest-cache/docling",
        help=(
            "DataPort storage root for the resulting canonical envelope. "
            "Default: %(default)s"
        ),
    )
    parser.add_argument(
        "--pii-tier",
        default=PIITier.INTERNAL.value,
        choices=[t.value for t in PIITier],
        help="PII tier for the envelope. Default: %(default)s.",
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    source = Path(args.path).expanduser().resolve()
    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    adapter = FilesystemDataAdapter(
        storage_root=out_root,
        canonicalizer=SortedJsonCanonicalizer(),
        storage=FilesystemStorage(out_root),
    )
    try:
        ingested = await ingest_document(
            source,
            data_port=adapter,
            pii_tier=PIITier(args.pii_tier),
        )
    finally:
        await adapter.close()

    print(
        json.dumps(
            {
                "source_filename": ingested.payload.source_filename,
                "source_extension": ingested.payload.source_extension,
                "source_size_bytes": ingested.payload.source_size_bytes,
                "docling_version": ingested.payload.docling_version,
                "docling_commit": ingested.payload.docling_commit,
                "canonical_hash": ingested.canonical_hash,
                "storage_path": ingested.storage_path,
                "exported_at_iso": ingested.exported_at_iso,
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        return asyncio.run(_run(args))
    except FileNotFoundError as exc:
        print(f"docling_ingest: {exc}", file=sys.stderr)
        return 2
    except UnsupportedExtensionError as exc:
        print(f"docling_ingest: {exc}", file=sys.stderr)
        return 3
    except DoclingUnavailableError as exc:
        print(f"docling_ingest: {exc}", file=sys.stderr)
        return 4
    except DoclingIngestFailure as exc:
        print(f"docling_ingest: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
