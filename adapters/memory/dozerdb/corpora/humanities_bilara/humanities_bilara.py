"""Bilara humanities corpus loader (Stage 4.5 · ADR-050).

Reads JSONL from ``$KOSMOS_HUMANITIES_BILARA_PATH`` when set; otherwise
falls back to the committed ``fixtures/humanities_bilara.jsonl`` (one
row per upstream translation file, its mirrored Pali root file, and
each referenced translator actor at a pinned upstream SHA of
`github.com/suttacentral/bilara-data`). The env-path form lets
Colossus point at a re-ingested fixture from a newer SHA without
shipping a new adapter release.

Each JSONL line MUST have the CorpusFact fields (``event_id``,
``subject``, ``predicate``, ``object``, ``as_of``, ``provenance``,
``confidence``) plus an ``attributes`` dict that carries at minimum:
- ``source_commit`` — pinned SHA it was ingested from
- ``license`` — SPDX identifier (``CC0-1.0`` for translations and
  actor metadata, ``public-domain`` for the Mahasangiti Pali root)
- ``references`` — list of typed CIDOC-CRM edge dicts (kind
  ``P73_is_translation_of``, ``P94_was_created_by``, etc.), each with
  ``target_event_id`` + optional ``target_path`` + ``anchor_text``

Text-carrying records (root + translation) additionally carry ``body``
(the concatenated segment text) and ``segment_count``. Actor records
(subject namespace ``bilara/actor/*``) omit ``body`` — they exist to
make ``P94_was_created_by`` edges resolvable inside the corpus.

Cross-reference edges are lifted out of each fact's ``attributes`` and
materialized as :class:`CorpusEdge` records on the corpus so the
contract layer can assert typed-link retrieval without introspecting
attribute payloads.

Temporal queries: every fact carries the same ``as_of`` (the upstream
commit-authored date), so the tiered temporal probes are trivial — one
early cutoff (all facts forbidden) and one at-or-after cutoff (all
facts eligible), mirroring Stage 4.4 Superpowers.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..models import Corpus, CorpusEdge, CorpusFact, TemporalQuery

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "humanities_bilara.jsonl"
_ENV_VAR = "KOSMOS_HUMANITIES_BILARA_PATH"

# Publish the pinned coordinates for ADR / BUILD_LOG / test parity.
UPSTREAM_LICENSE_TRANSLATION = "CC0-1.0"
UPSTREAM_LICENSE_ROOT = "public-domain"  # Mahasangiti edition
UPSTREAM_URL = "https://github.com/suttacentral/bilara-data"

# Subject-namespace prefixes used by the ingest CLI.
_ACTOR_PREFIX = "bilara/actor/"
_ROOT_PREFIX = "bilara/root/"
_TRANSLATION_PREFIX = "bilara/translation/"

# Required attribute keys for body-carrying (root/translation) records.
_REQUIRED_BODY_KEYS = ("body", "source_commit", "license")
# Required attribute keys for actor records (no body).
_REQUIRED_ACTOR_KEYS = ("source_commit", "license", "author_uid")


def _resolve_source() -> Path:
    env = os.getenv(_ENV_VAR)
    if env:
        p = Path(env).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"{_ENV_VAR}={env!r} does not resolve to a file")
        return p
    return _FIXTURE_PATH


def _parse_line(raw: str, lineno: int) -> CorpusFact:
    try:
        row = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"line {lineno}: invalid JSON: {exc}") from exc
    required = {
        "event_id",
        "subject",
        "predicate",
        "object",
        "as_of",
        "provenance",
        "confidence",
    }
    missing = required - row.keys()
    if missing:
        raise ValueError(f"line {lineno}: missing fields {sorted(missing)}")
    as_of = datetime.fromisoformat(row["as_of"])
    if as_of.tzinfo is None:
        raise ValueError(f"line {lineno}: as_of {row['as_of']!r} is not timezone-aware")
    attrs = dict(row.get("attributes", {}))
    subject = row["subject"]
    # Zero-trust: Stage 4.5 fixtures MUST carry the provenance triple.
    if subject.startswith(_ACTOR_PREFIX):
        required_keys = _REQUIRED_ACTOR_KEYS
    elif subject.startswith(_ROOT_PREFIX) or subject.startswith(_TRANSLATION_PREFIX):
        required_keys = _REQUIRED_BODY_KEYS
    else:
        raise ValueError(
            f"line {lineno}: unknown subject namespace {subject!r} "
            f"(expected one of bilara/actor/, bilara/root/, bilara/translation/)"
        )
    for key in required_keys:
        if key not in attrs:
            raise ValueError(
                f"line {lineno}: attributes missing required key {key!r}"
            )
    return CorpusFact(
        event_id=row["event_id"],
        subject=subject,
        predicate=row["predicate"],
        object_=row["object"],
        as_of=as_of,
        provenance=row["provenance"],
        confidence=float(row["confidence"]),
        attributes=attrs,
    )


def _edges_from_facts(facts: tuple[CorpusFact, ...]) -> tuple[CorpusEdge, ...]:
    """Materialize typed cross-reference edges from fact attributes."""
    known = {f.event_id for f in facts}
    out: list[CorpusEdge] = []
    for f in facts:
        refs = f.attributes.get("references") or []
        for ref in refs:
            kind = ref.get("kind") or "references"
            dst = ref.get("target_event_id")
            if dst not in known:
                # Skip edges whose target isn't present at this SHA;
                # the ingest CLI is expected to prune these, but the
                # loader tolerates a mismatched fixture rather than
                # blowing up.
                continue
            attrs = {
                "target_path": ref.get("target_path"),
                "anchor_text": ref.get("anchor_text"),
            }
            out.append(
                CorpusEdge(
                    src_event_id=f.event_id,
                    kind=kind,
                    dst_event_id=dst,
                    attributes={k: v for k, v in attrs.items() if v is not None},
                )
            )
    return tuple(out)


def load_facts(source: Path | None = None) -> tuple[CorpusFact, ...]:
    """Load facts from JSONL. Empty lines are skipped."""
    src = source or _resolve_source()
    facts: list[CorpusFact] = []
    with src.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            facts.append(_parse_line(stripped, lineno))
    return tuple(facts)


def load_facts_and_edges(
    source: Path | None = None,
) -> tuple[tuple[CorpusFact, ...], tuple[CorpusEdge, ...]]:
    """Load facts + typed cross-reference edges together."""
    facts = load_facts(source)
    return facts, _edges_from_facts(facts)


def _default_queries(facts: tuple[CorpusFact, ...]) -> tuple[TemporalQuery, ...]:
    """Two-point temporal probe: before-ingest and at-ingest.

    All Bilara facts share the same ``as_of`` (the pinned commit's
    authored date), so a mid cutoff is not meaningful. The load-bearing
    assertion is that the early-cutoff query rejects every fact.
    """
    if not facts:
        return ()
    sorted_facts = sorted(facts, key=lambda f: f.as_of)
    earliest = sorted_facts[0].as_of
    latest = sorted_facts[-1].as_of
    all_ids = frozenset(f.event_id for f in sorted_facts)
    before = earliest - timedelta(days=1)
    return (
        TemporalQuery(
            query="Buddhist canonical texts and their translations",
            as_of=before,
            expected_event_ids=frozenset(),
            forbidden_event_ids=all_ids,
        ),
        TemporalQuery(
            query="Buddhist canonical texts and their translations",
            as_of=latest,
            expected_event_ids=frozenset(),
            forbidden_event_ids=frozenset(),
        ),
    )


def load_corpus(source: Path | None = None) -> Corpus:
    facts, edges = load_facts_and_edges(source)
    queries = _default_queries(facts)
    return Corpus(
        name="humanities-bilara",
        facts=facts,
        queries=queries,
        edges=edges,
    )


def _default_corpus() -> Corpus:
    return load_corpus(_FIXTURE_PATH)


CORPUS = _default_corpus()
SOURCE_COMMIT: str = (
    CORPUS.facts[0].attributes.get("source_commit", "") if CORPUS.facts else ""
)

# Silence unused-import lints in some tooling.
_ = timezone
