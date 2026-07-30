"""plugins.tektos.eval — Pier eval harness (Stage 3.8, ADR-042).

Tektos-internal subsystem that runs Harbor-format eval tasks through the
Pier CLI (upstream ``datacurve-ai/pier`` @ Apache-2.0), then records each
trial verdict as a ``tektos.eval.trial_completed`` MemoryPort event.

Design invariants (ADR-042):

* Q1=A vendored — ``datacurve-pier`` PyPI package as a dev dep only;
  no source is copied into the tree.
* Q2=A Docker env only — Colossus-local Docker daemon; no cloud plane.
* Q3=A envelope-first, no new port surface — Pier is CLI-invoked from
  ``scripts/pier_eval.py`` and the trial verdict is written back through
  the existing ``MemoryPort``.
* Q4=A subsystem layout — this package plus ``scripts/pier_eval.py``.
* Q5=A executed-trajectory eval — Pier trials execute Tektos-relevant
  Harbor tasks; verifier verdict is what enters MemoryPort.
* Q6=A one ``tektos.eval.trial_completed`` MemoryPort event per trial
  with ``provenance="pier-eval-harness"`` and confidence ``1.0`` on PASS,
  ``0.0`` on FAIL.
* Q7=B advisory only — Pier verdict does NOT mutate APEX state; user
  reviews the plan card and consults the verdict alongside it.
* Q8=A two-tier tests — fast unit tier in ``make stage1-gate``; real
  Pier tier env-gated by ``KOSMOS_STAGE_38_REAL_PIER=1``.
* Q10=A one committed Harbor fixture at
  ``plugins/tektos/eval/tasks/tektos-plan-execution-smoke/``.

ADR-007 (events-only cross-plugin coupling): this subsystem imports
zero other plugins. AST-verified by
``test_eval_subsystem_imports_no_other_plugins_adr_007``.

ADR-008 (zero-trust MemoryPort writes): every write carries locked
provenance and a bounded confidence value.

ADR-023 (envelope-first): no new port surface introduced. Pier is
invoked as a subprocess; the trajectory JSON is parsed back into a
:class:`TrialVerdict` value object.
"""

from __future__ import annotations

from .harness import (
    PierNotAvailableError,
    PierTrialFailure,
    record_pier_verdict,
    run_and_record_trial,
    run_pier_trial,
)
from .models import PierEnv, TrialVerdict, VerifierOutcome
from .policy import (
    PIER_DEFAULT_ENV,
    PIER_EVAL_PROVENANCE,
    PIER_MAX_CONFIDENCE,
    PIER_MIN_CONFIDENCE,
    PIER_TIMEOUT_SEC,
    PIER_TRIAL_PREDICATE,
    PIER_UPSTREAM_COMMIT,
    PIER_UPSTREAM_LICENSE,
    PIER_UPSTREAM_PACKAGE,
    PIER_UPSTREAM_PYPI_VERSION,
    confidence_for_outcome,
)

__all__ = [
    "PIER_DEFAULT_ENV",
    "PIER_EVAL_PROVENANCE",
    "PIER_MAX_CONFIDENCE",
    "PIER_MIN_CONFIDENCE",
    "PIER_TIMEOUT_SEC",
    "PIER_TRIAL_PREDICATE",
    "PIER_UPSTREAM_COMMIT",
    "PIER_UPSTREAM_LICENSE",
    "PIER_UPSTREAM_PACKAGE",
    "PIER_UPSTREAM_PYPI_VERSION",
    "PierEnv",
    "PierNotAvailableError",
    "PierTrialFailure",
    "TrialVerdict",
    "VerifierOutcome",
    "confidence_for_outcome",
    "record_pier_verdict",
    "run_and_record_trial",
    "run_pier_trial",
]
