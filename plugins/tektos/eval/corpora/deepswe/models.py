"""Frozen dataclasses for the DeepSWE corpus (Stage 3.9, ADR-007-DeepSWE).

All value objects are immutable and JSON-friendly so an aggregated
corpus-run summary can round-trip through
:meth:`ports.memory.MemoryPort.write_event` attributes without custom
encoders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["CorpusRunSummary", "DeepSweSubsetEntry"]


@dataclass(frozen=True, slots=True)
class DeepSweSubsetEntry:
    """One row from ``manifest.toml``'s ``[[subset]]`` table.

    Enforces the shape a Stage 3.9 contract test asserts against. Every
    field is a primitive so the row projects trivially into an event
    attributes dict.
    """

    task_id: str
    language: str
    upstream_repo: str
    upstream_owner: str
    upstream_repo_name: str
    base_commit: str
    spdx_license: str

    def to_attributes(self) -> dict[str, Any]:
        """Project this entry into a JSON-serializable dict."""
        return {
            "task_id": self.task_id,
            "language": self.language,
            "upstream_repo": self.upstream_repo,
            "upstream_owner": self.upstream_owner,
            "upstream_repo_name": self.upstream_repo_name,
            "base_commit": self.base_commit,
            "spdx_license": self.spdx_license,
        }


@dataclass(frozen=True, slots=True)
class CorpusRunSummary:
    """Aggregated result of running the DeepSWE subset through Pier.

    Recorded as one ``tektos.eval.corpus_run_completed`` MemoryPort
    event per run. Per-trial verdicts continue to write through the
    existing Stage 3.8 ``tektos.eval.trial_completed`` predicate.

    Field mapping:

    - :attr:`run_id` — uuid4 stamped when the run kicks off.
    - :attr:`corpus` — corpus name (``"deepswe"``).
    - :attr:`upstream_commit` — commit SHA the subset was pinned to.
    - :attr:`sample_seed` — deterministic sample seed used to freeze
      the pick order (recorded for reproducibility even when the
      subset is a manual pick).
    - :attr:`subset_task_ids` — tuple of task ids that ran; frozen so
      the summary is hashable and immutable.
    - :attr:`n_total` — total number of tasks that ran.
    - :attr:`n_pass`, :attr:`n_fail`, :attr:`n_error` — per-outcome
      counts. ``n_pass + n_fail + n_error == n_total`` is asserted at
      construction time.
    - :attr:`pier_version`, :attr:`pier_env` — Pier build info for the
      run (recorded on the aggregate for consumer convenience).
    - :attr:`started_at`, :attr:`finished_at` — ISO-8601 UTC strings.
    - :attr:`trial_event_ids` — MemoryPort event ids for the per-trial
      writes, so a downstream query can walk from the aggregate to
      each individual verdict.
    """

    run_id: str
    corpus: str
    upstream_commit: str
    sample_seed: int
    subset_task_ids: tuple[str, ...]
    n_total: int
    n_pass: int
    n_fail: int
    n_error: int
    pier_version: str
    pier_env: str
    started_at: str
    finished_at: str
    trial_event_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Frozen dataclass — assertions here are pure validators; no
        # mutation of self.
        if self.n_total < 0 or self.n_pass < 0 or self.n_fail < 0 or self.n_error < 0:
            raise ValueError(
                "CorpusRunSummary: negative count "
                f"(total={self.n_total}, pass={self.n_pass}, fail={self.n_fail}, error={self.n_error})"
            )
        if self.n_pass + self.n_fail + self.n_error != self.n_total:
            raise ValueError(
                "CorpusRunSummary: n_pass + n_fail + n_error must equal n_total "
                f"(got {self.n_pass} + {self.n_fail} + {self.n_error} != {self.n_total})"
            )
        if len(self.subset_task_ids) != self.n_total:
            raise ValueError(
                "CorpusRunSummary: len(subset_task_ids) must equal n_total "
                f"(got {len(self.subset_task_ids)} != {self.n_total})"
            )

    def to_attributes(self) -> dict[str, Any]:
        """Project this summary into a JSON-serializable attributes dict."""
        return {
            "run_id": self.run_id,
            "corpus": self.corpus,
            "upstream_commit": self.upstream_commit,
            "sample_seed": self.sample_seed,
            "subset_task_ids": list(self.subset_task_ids),
            "n_total": self.n_total,
            "n_pass": self.n_pass,
            "n_fail": self.n_fail,
            "n_error": self.n_error,
            "pier_version": self.pier_version,
            "pier_env": self.pier_env,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "trial_event_ids": list(self.trial_event_ids),
        }
