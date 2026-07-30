"""plugins.tektos.eval.corpora.deepswe — DeepSWE corpus (Stage 3.9, ADR-007-DeepSWE).

Filtered subset of the DeepSWE benchmark (upstream ``datacurve-ai/deep-swe``,
Apache-2.0). Every task in the subset is drawn from a permissively-licensed
upstream repository; the SPDX allowlist is enforced by
:mod:`.loader` at manifest-load time.

Design invariants (ADR-007-DeepSWE STATUS AMENDMENT 2026-07-30):

* Q1=A manifest-only vendoring — no task source is copied into the
  repo. ``manifest.toml`` pins ``upstream_repo`` + ``upstream_commit``
  + the ordered subset. Tasks are fetched on-demand by
  ``scripts/deepswe_fetch.py`` into ``.eval-cache/deepswe/`` (git-ignored).
* Q2=A subset size — 5 tasks (3 Python + 2 TypeScript), pinned in
  :data:`.policy.DEEPSWE_SUBSET_SIZE`.
* Q3=A two-tier record — aggregate ``tektos.eval.corpus_run_completed``
  event per run plus the existing Stage 3.8 per-trial event stream.
* Q4=A one-row ledger — one PORTING_LEDGER row for the corpus plus an
  inline subset table with per-task SPDX notes.
* Q5=A two-tier tests — fast unit tier under ``make stage1-gate`` plus
  an env-gated real tier under ``KOSMOS_STAGE_39_REAL_DEEPSWE=1``.
* Q6=A clause 3 defer — context-rot cross-check deferred pending the
  regression suite; documented in the ADR STATUS AMENDMENT.
* Q7=A amend-not-supersede — ADR-007-DeepSWE stays Ratified; a STATUS
  AMENDMENT block captures the Stage 3.9 scope pin.
* Q8=A binary outcome mapping — Pier ``reward == 1.0`` → PASS,
  everything else → FAIL, no-verifier-reached → ERROR. Reuses the
  Stage 3.8 :class:`plugins.tektos.eval.VerifierOutcome` unchanged.
"""

from __future__ import annotations

from .harness import (
    build_corpus_run_summary,
    record_corpus_run,
    utc_now_iso,
)
from .loader import DeepSweCorpus, DeepSweManifestError, load_deepswe_manifest
from .models import CorpusRunSummary, DeepSweSubsetEntry
from .policy import (
    DEEPSWE_CORPUS_NAME,
    DEEPSWE_CORPUS_RUN_PREDICATE,
    DEEPSWE_EVAL_PROVENANCE,
    DEEPSWE_MAX_CONFIDENCE,
    DEEPSWE_MIN_CONFIDENCE,
    DEEPSWE_PERMISSIVE_LICENSES,
    DEEPSWE_SAMPLE_SEED,
    DEEPSWE_SUBSET_SIZE,
    DEEPSWE_UPSTREAM_COMMIT,
    DEEPSWE_UPSTREAM_LICENSE,
    DEEPSWE_UPSTREAM_REPO,
    corpus_run_confidence,
)

__all__ = [
    "CorpusRunSummary",
    "DEEPSWE_CORPUS_NAME",
    "DEEPSWE_CORPUS_RUN_PREDICATE",
    "DEEPSWE_EVAL_PROVENANCE",
    "DEEPSWE_MAX_CONFIDENCE",
    "DEEPSWE_MIN_CONFIDENCE",
    "DEEPSWE_PERMISSIVE_LICENSES",
    "DEEPSWE_SAMPLE_SEED",
    "DEEPSWE_SUBSET_SIZE",
    "DEEPSWE_UPSTREAM_COMMIT",
    "DEEPSWE_UPSTREAM_LICENSE",
    "DEEPSWE_UPSTREAM_REPO",
    "DeepSweCorpus",
    "DeepSweManifestError",
    "DeepSweSubsetEntry",
    "build_corpus_run_summary",
    "corpus_run_confidence",
    "load_deepswe_manifest",
    "record_corpus_run",
    "utc_now_iso",
]
