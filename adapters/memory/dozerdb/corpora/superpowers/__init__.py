"""Superpowers KB corpus (Stage 4.4 · ADR-049).

Personal-KB substrate: Superpowers methodology skills
(`github.com/obra/superpowers`, MIT) ingested as one MemoryPort record
per upstream `skills/*/*.md` file at a pinned commit SHA. Includes
typed cross-reference edges parsed from inline Markdown links between
sibling files.

**Not code-vendored** per ADR-008 — this is content-only ingest into
MemoryPort. No upstream Python or Markdown is imported at runtime; the
fixture JSONL is the boundary. Regenerate via
``scripts/ingest_superpowers.py --sha <SHA>``.

Owner at Stage 4.4: adapter-side (this subpackage). Relocates into
`plugins/gnosis/humanities/personal_kb/` when the Gnosis plugin lands
at Phase 3 (ADR-002 + ADR-016).
"""

from __future__ import annotations

from .superpowers import (
    CORPUS,
    SOURCE_COMMIT,
    UPSTREAM_LICENSE,
    UPSTREAM_URL,
    load_corpus,
    load_facts_and_edges,
)

__all__ = [
    "CORPUS",
    "SOURCE_COMMIT",
    "UPSTREAM_LICENSE",
    "UPSTREAM_URL",
    "load_corpus",
    "load_facts_and_edges",
]
