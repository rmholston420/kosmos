"""SuttaCentral Bilara humanities corpus (Stage 4.5 · ADR-050).

Humanities-KB substrate: CIDOC-CRM–aligned Buddhist canonical text ingest
from `github.com/suttacentral/bilara-data` (translations CC0, Mahasangiti
Pali root public domain). One MemoryPort record per upstream translation
file plus the mirrored Pali root file, at a pinned commit SHA, with typed
cross-reference edges materialized between root ↔ translation and
translation ↔ translator actor (E21_Person).

**Not code-vendored** per ADR-008 — this is content-only ingest into
MemoryPort. No upstream code is imported at runtime; the fixture JSONL
is the boundary. Regenerate via
``scripts/ingest_humanities.py --sha <SHA>``.

Stage 4.5 slice: Bhikkhu Sujato's English translations of three
Khuddaka Nikaya publications (scpub7 Dhammapada, scpub19 Khuddakapatha,
scpub86 Cariyapitaka) plus the mirrored Pali root under
``root/pli/ms/sutta/kn/{dhp,kp,cp}/`` — 70 translation files + 70 root
files + 1 actor record = 141 records, 140 CIDOC-CRM typed edges
(``P73_is_translation_of`` + ``P94_was_created_by``).

Owner at Stage 4.5: adapter-side (this subpackage). Relocates into
`plugins/gnosis/humanities/canonical_kb/` when the Gnosis plugin lands
at Phase 3 (ADR-002 + ADR-016).
"""

from __future__ import annotations

from .humanities_bilara import (
    CORPUS,
    SOURCE_COMMIT,
    UPSTREAM_LICENSE_ROOT,
    UPSTREAM_LICENSE_TRANSLATION,
    UPSTREAM_URL,
    load_corpus,
    load_facts_and_edges,
)

__all__ = [
    "CORPUS",
    "SOURCE_COMMIT",
    "UPSTREAM_LICENSE_ROOT",
    "UPSTREAM_LICENSE_TRANSLATION",
    "UPSTREAM_URL",
    "load_corpus",
    "load_facts_and_edges",
]
