"""Locked policy constants for the DeepSWE corpus (Stage 3.9, ADR-007-DeepSWE).

Every constant is load-bearing and referenced by contract tests. Do not
rename or repoint any of these outside a superseding ADR or a STATUS
AMENDMENT on ADR-007-DeepSWE.
"""

from __future__ import annotations

from typing import Final, FrozenSet

__all__ = [
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
    "corpus_run_confidence",
]

#: Corpus name stamped into the MemoryPort event subject.
DEEPSWE_CORPUS_NAME: Final[str] = "deepswe"

#: Provenance stamped on every corpus-run MemoryPort write.
DEEPSWE_EVAL_PROVENANCE: Final[str] = "deepswe-eval-corpus"

#: Predicate for the aggregate ``tektos.eval.corpus_run_completed`` event.
#: Per-trial writes continue to use ``tektos.eval.trial_completed``
#: (Stage 3.8's :data:`plugins.tektos.eval.policy.PIER_TRIAL_PREDICATE`).
DEEPSWE_CORPUS_RUN_PREDICATE: Final[str] = "tektos.eval.corpus_run_completed"

#: Upstream GitHub commit SHA locked at Stage 3.9 kickoff for audit.
DEEPSWE_UPSTREAM_COMMIT: Final[str] = "e016041a6ccf8da29906afc9a3f5a8df940a1f78"

#: Upstream repository URL (canonical, no ``.git`` suffix).
DEEPSWE_UPSTREAM_REPO: Final[str] = "https://github.com/datacurve-ai/deep-swe"

#: Upstream SPDX license for the corpus wrapper itself.
DEEPSWE_UPSTREAM_LICENSE: Final[str] = "Apache-2.0"

#: Subset size Q2=A: 5 tasks (3 Python + 2 TypeScript).
DEEPSWE_SUBSET_SIZE: Final[int] = 5

#: Deterministic sample seed used to document the pick order.
DEEPSWE_SAMPLE_SEED: Final[int] = 0

#: MemoryPort confidence recorded when zero tasks passed.
DEEPSWE_MIN_CONFIDENCE: Final[float] = 0.0

#: MemoryPort confidence recorded when every task passed.
DEEPSWE_MAX_CONFIDENCE: Final[float] = 1.0

#: Permissive-license allowlist. A corpus subset entry whose SPDX id is
#: NOT in this set is rejected at manifest-load time. Anything copyleft
#: (GPL/AGPL/LGPL) or source-available (BUSL/SSPL) requires a superseding
#: ADR before it enters this list.
DEEPSWE_PERMISSIVE_LICENSES: Final[FrozenSet[str]] = frozenset(
    {
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "MPL-2.0",
    }
)


def corpus_run_confidence(n_pass: int, n_total: int) -> float:
    """Aggregate a corpus run into a bounded ``[0.0, 1.0]`` confidence.

    Contract: ``n_pass / n_total`` clamped to ``[MIN, MAX]``. An empty
    run (``n_total == 0``) yields :data:`DEEPSWE_MIN_CONFIDENCE` so the
    MemoryPort zero-trust guard still accepts the write.

    Args:
        n_pass: Number of tasks whose Pier verifier returned PASS.
        n_total: Total number of tasks that ran (PASS + FAIL + ERROR).

    Returns:
        A float in ``[DEEPSWE_MIN_CONFIDENCE, DEEPSWE_MAX_CONFIDENCE]``.

    Raises:
        TypeError: ``n_pass`` or ``n_total`` is not an int.
        ValueError: ``n_pass`` or ``n_total`` is negative, or
            ``n_pass > n_total``.
    """
    if not isinstance(n_pass, int) or not isinstance(n_total, int):
        raise TypeError(
            "corpus_run_confidence requires int inputs, "
            f"got n_pass={type(n_pass).__name__}, n_total={type(n_total).__name__}"
        )
    if n_pass < 0 or n_total < 0:
        raise ValueError(
            f"corpus_run_confidence: negative counts (n_pass={n_pass}, n_total={n_total})"
        )
    if n_pass > n_total:
        raise ValueError(
            f"corpus_run_confidence: n_pass ({n_pass}) exceeds n_total ({n_total})"
        )
    if n_total == 0:
        return DEEPSWE_MIN_CONFIDENCE
    ratio = n_pass / n_total
    if ratio < DEEPSWE_MIN_CONFIDENCE:
        return DEEPSWE_MIN_CONFIDENCE
    if ratio > DEEPSWE_MAX_CONFIDENCE:
        return DEEPSWE_MAX_CONFIDENCE
    return ratio
