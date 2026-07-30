"""Aggregate corpus-run recorder for DeepSWE (Stage 3.9, ADR-007-DeepSWE).

The per-trial write path continues to live in
:mod:`plugins.tektos.eval.harness` (Stage 3.8's
``tektos.eval.trial_completed`` event). Stage 3.9 adds one *aggregate*
event per subset run: ``tektos.eval.corpus_run_completed``.

Design invariants:

* Q3=A envelope-first — no new port surface; verdicts flow through the
  existing :class:`ports.memory.MemoryPort`.
* ADR-007: no ``import plugins.<other>``.
* ADR-008: :func:`record_corpus_run` is the sole write path and always
  supplies ``provenance`` + a bounded ``confidence``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from ports.memory import MemoryEventId, MemoryPort

from .models import CorpusRunSummary
from .policy import (
    DEEPSWE_CORPUS_NAME,
    DEEPSWE_CORPUS_RUN_PREDICATE,
    DEEPSWE_EVAL_PROVENANCE,
    DEEPSWE_UPSTREAM_COMMIT,
    corpus_run_confidence,
)

__all__ = [
    "build_corpus_run_summary",
    "record_corpus_run",
    "utc_now_iso",
]


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp string (seconds precision)."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_corpus_run_summary(
    *,
    subset_task_ids: tuple[str, ...],
    outcomes: tuple[str, ...],
    trial_event_ids: tuple[str, ...] = (),
    pier_version: str,
    pier_env: str,
    started_at: str,
    finished_at: str,
    run_id: str | None = None,
) -> CorpusRunSummary:
    """Build a :class:`CorpusRunSummary` from per-trial outcome strings.

    ``outcomes`` MUST be aligned index-for-index with ``subset_task_ids``
    and contain only the three Stage 3.8 verdict strings ``"PASS"``,
    ``"FAIL"``, ``"ERROR"``.
    """
    if len(outcomes) != len(subset_task_ids):
        raise ValueError(
            f"outcomes length {len(outcomes)} does not match "
            f"subset_task_ids length {len(subset_task_ids)}"
        )
    n_pass = sum(1 for o in outcomes if o == "PASS")
    n_fail = sum(1 for o in outcomes if o == "FAIL")
    n_error = sum(1 for o in outcomes if o == "ERROR")
    unknown = [o for o in outcomes if o not in {"PASS", "FAIL", "ERROR"}]
    if unknown:
        raise ValueError(
            f"outcomes contains unknown verdict strings: {unknown!r} "
            "(only PASS, FAIL, ERROR are legal)"
        )
    n_total = len(outcomes)
    return CorpusRunSummary(
        run_id=run_id or f"run-{uuid.uuid4().hex[:12]}",
        corpus=DEEPSWE_CORPUS_NAME,
        upstream_commit=DEEPSWE_UPSTREAM_COMMIT,
        sample_seed=0,
        subset_task_ids=tuple(subset_task_ids),
        n_total=n_total,
        n_pass=n_pass,
        n_fail=n_fail,
        n_error=n_error,
        pier_version=pier_version,
        pier_env=pier_env,
        started_at=started_at,
        finished_at=finished_at,
        trial_event_ids=tuple(trial_event_ids),
    )


async def record_corpus_run(
    summary: CorpusRunSummary,
    *,
    memory_port: MemoryPort,
) -> MemoryEventId:
    """Write one ``tektos.eval.corpus_run_completed`` MemoryPort event.

    Locked write shape (ADR-007-DeepSWE STATUS AMENDMENT 2026-07-30):

    - ``provenance`` = :data:`.policy.DEEPSWE_EVAL_PROVENANCE`
    - ``predicate`` = :data:`.policy.DEEPSWE_CORPUS_RUN_PREDICATE`
    - ``subject`` = ``"<corpus>::<upstream_commit>::<sample_seed>::<run_id>"``
    - ``object`` = ``"<n_pass>/<n_total>"``
    - ``confidence`` = :func:`.policy.corpus_run_confidence`
    - ``attributes`` = :meth:`.models.CorpusRunSummary.to_attributes`
    """
    subject = (
        f"{summary.corpus}::{summary.upstream_commit}::"
        f"{summary.sample_seed}::{summary.run_id}"
    )
    obj = f"{summary.n_pass}/{summary.n_total}"
    attributes: dict[str, Any] = dict(summary.to_attributes())
    return await memory_port.write_event(
        subject=subject,
        predicate=DEEPSWE_CORPUS_RUN_PREDICATE,
        object=obj,
        provenance=DEEPSWE_EVAL_PROVENANCE,
        confidence=corpus_run_confidence(summary.n_pass, summary.n_total),
        attributes=attributes,
    )
