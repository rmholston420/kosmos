"""Rigpa export corpus loader (Stage 4.2).

Reads JSONL from `$KOSMOS_RIGPA_EXPORT_PATH` when set; otherwise falls
back to the committed `fixtures/rigpa_sample.jsonl` (20 events spanning
2024-05 → 2024-12). The env-path form lets Colossus point at a real
Rigpa-LMS export dump without shipping user data through the repo.

Each JSONL line MUST have:
- ``event_id`` (str)
- ``subject`` / ``predicate`` / ``object`` (str)
- ``as_of`` (ISO-8601 with tz)
- ``provenance`` (str)
- ``confidence`` (float in (0.0, 1.0])
- ``attributes`` (dict, optional)

Time-slice queries assert that only events at or before their `as_of`
cutoff appear.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .models import Corpus, CorpusFact, TemporalQuery

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "rigpa_sample.jsonl"
_ENV_VAR = "KOSMOS_RIGPA_EXPORT_PATH"


def _resolve_source() -> Path:
    env = os.getenv(_ENV_VAR)
    if env:
        p = Path(env).expanduser()
        if not p.is_file():
            raise FileNotFoundError(
                f"{_ENV_VAR}={env!r} does not resolve to a file"
            )
        return p
    return _FIXTURE_PATH


def _parse_line(raw: str, lineno: int) -> CorpusFact:
    try:
        row = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"line {lineno}: invalid JSON: {exc}") from exc
    required = {"event_id", "subject", "predicate", "object", "as_of", "provenance", "confidence"}
    missing = required - row.keys()
    if missing:
        raise ValueError(f"line {lineno}: missing fields {sorted(missing)}")
    as_of = datetime.fromisoformat(row["as_of"])
    if as_of.tzinfo is None:
        raise ValueError(f"line {lineno}: as_of {row['as_of']!r} is not timezone-aware")
    return CorpusFact(
        event_id=row["event_id"],
        subject=row["subject"],
        predicate=row["predicate"],
        object_=row["object"],
        as_of=as_of,
        provenance=row["provenance"],
        confidence=float(row["confidence"]),
        attributes=dict(row.get("attributes", {})),
    )


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


def _default_queries(facts: tuple[CorpusFact, ...]) -> tuple[TemporalQuery, ...]:
    """Time-slice queries derived from the loaded fact timeline.

    - Early cutoff (before any fact) → all facts forbidden, none expected.
    - Mid cutoff → facts at/before cutoff expected, later forbidden.
    - Late cutoff (after all facts) → all facts eligible; hits may be
      empty when Graphiti's semantic search returns nothing for the
      short generic query, so the mid-cutoff assertion is the
      load-bearing one.
    """
    if not facts:
        return ()
    sorted_facts = sorted(facts, key=lambda f: f.as_of)
    earliest = sorted_facts[0].as_of
    latest = sorted_facts[-1].as_of
    # Bisect cleanly by list index rather than trusting `datetime`
    # arithmetic on years/months.
    mid_idx = len(sorted_facts) // 2
    mid_cutoff = sorted_facts[mid_idx].as_of
    at_or_before_mid = frozenset(f.event_id for f in sorted_facts if f.as_of <= mid_cutoff)
    after_mid = frozenset(f.event_id for f in sorted_facts if f.as_of > mid_cutoff)
    all_ids = frozenset(f.event_id for f in sorted_facts)

    return (
        TemporalQuery(
            query="Rigpa meditation and teaching sessions",
            as_of=earliest.replace(year=earliest.year - 1),
            expected_event_ids=frozenset(),
            forbidden_event_ids=all_ids,
        ),
        TemporalQuery(
            query="Rigpa meditation and teaching sessions",
            as_of=mid_cutoff,
            expected_event_ids=at_or_before_mid,
            forbidden_event_ids=after_mid,
        ),
        TemporalQuery(
            query="Rigpa meditation and teaching sessions",
            as_of=latest.replace(year=latest.year + 1),
            expected_event_ids=frozenset(),
            forbidden_event_ids=frozenset(),
        ),
    )


def load_corpus(source: Path | None = None) -> Corpus:
    facts = load_facts(source)
    queries = _default_queries(facts)
    return Corpus(
        name="rigpa-export",
        facts=facts,
        queries=queries,
    )


# Eager convenience: load the fixture at import time so consumers can
# just `from .rigpa_export import CORPUS`. The env-path form is
# opt-in via `load_corpus()`; leaving `CORPUS` bound to the fixture keeps
# fast-tier tests hermetic.
def _default_corpus() -> Corpus:
    return load_corpus(_FIXTURE_PATH)


CORPUS = _default_corpus()

# Silence unused-import lints in some tooling.
_ = timezone
