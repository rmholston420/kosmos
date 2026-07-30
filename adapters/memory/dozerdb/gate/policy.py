"""Locked constants for the Stage 4.6 exit-gate FastAPI app (ADR-051).

Every value here is load-bearing on ADR-051 and the Stage 4.6 DoD
literal test. Do not tweak without an ADR-051 amendment. Naming
convention mirrors ``plugins.tektos.ui.policy``.
"""

from __future__ import annotations

__all__ = [
    "STAGE_46_CORPUS_DETAIL_PATH",
    "STAGE_46_DEFAULT_CONFIDENCE",
    "STAGE_46_GATE_HOST",
    "STAGE_46_GATE_PORT",
    "STAGE_46_HEALTHZ_PATH",
    "STAGE_46_INDEX_PATH",
    "STAGE_46_PROVENANCE",
    "STAGE_46_PROVENANCE_PATH",
    "STAGE_46_QUERY_PATH",
    "STAGE_46_ROUTES",
    "STAGE_46_TRAVERSE_PATH",
]


# ── Provenance identity ────────────────────────────────────────────────────

STAGE_46_PROVENANCE: str = "stage_46_gate"
"""MemoryPort ``provenance`` field for every gate-emitted event.

The gate does not itself write to MemoryPort on read paths (it's a
retrieval surface, not a mutation surface). This constant is exposed
for symmetry with ``TEKTOS_UI_PROVENANCE`` and is used by the healthz
probe when it optionally stamps a heartbeat event (env-gated)."""


STAGE_46_DEFAULT_CONFIDENCE: float = 1.0
"""Default confidence surfaced for corpus-sourced facts at Stage 4.6.

Corpus facts already carry an explicit ``confidence`` field enforced
by :class:`adapters.memory.dozerdb.corpora.models.Corpus` invariants
(``0.0 < confidence <= 1.0``). This default is applied only when the
underlying record is missing a confidence value — never overrides one
that is present. Stage 5 revisit (Graphiti-derived confidences)
tracked in ADR-051 §Consequences."""


# ── Server bind ────────────────────────────────────────────────────────────

STAGE_46_GATE_HOST: str = "127.0.0.1"
"""Bind host for :func:`build_stage_46_gate_app`.

Loopback only. Single-user local-first invariant makes this the
security boundary; no auth on any route. Matches the Tektos UI
convention (ADR-045 Q1c=A)."""

STAGE_46_GATE_PORT: int = 8746
"""Bind port for the Stage 4.6 gate app.

Chosen as ``8746`` (4-6 encodes the stage) to avoid collision with
Tektos UI (``8765``, Stage 3.11)."""


# ── Route paths ────────────────────────────────────────────────────────────

STAGE_46_INDEX_PATH: str = "/"
"""Dashboard listing every landed corpus with fact/edge counts."""

STAGE_46_CORPUS_DETAIL_PATH: str = "/corpus/{corpus_name}"
"""Corpus detail page: fact count, edge kind census, sample facts."""

STAGE_46_PROVENANCE_PATH: str = "/corpus/{corpus_name}/provenance/{event_id}"
"""Full provenance chain for one corpus record.

Renders: source (provenance string + upstream_url when present),
timestamp (``as_of``), confidence, subject/predicate/object triple,
and every outbound/inbound typed edge in the same corpus."""

STAGE_46_QUERY_PATH: str = "/corpus/{corpus_name}/query"
"""Temporal query passthrough. Query params: ``q`` (query string),
``as_of`` (ISO-8601 cutoff, optional), ``limit`` (default 20)."""

STAGE_46_TRAVERSE_PATH: str = "/corpus/{corpus_name}/traverse/{event_id}"
"""CIDOC-CRM typed-edge traversal. Renders outbound edges grouped by
``kind`` with the destination record's subject + confidence."""

STAGE_46_HEALTHZ_PATH: str = "/healthz"
"""Health probe. Returns 200 ``ok`` when every registered corpus
loads without raising. Matches the Tektos UI convention."""


STAGE_46_ROUTES: tuple[str, ...] = (
    STAGE_46_INDEX_PATH,
    STAGE_46_CORPUS_DETAIL_PATH,
    STAGE_46_PROVENANCE_PATH,
    STAGE_46_QUERY_PATH,
    STAGE_46_TRAVERSE_PATH,
    STAGE_46_HEALTHZ_PATH,
)
"""Ordered tuple of every route path the app registers.

Contract tests iterate this tuple so a route added or removed
without an ADR-051 amendment fails ``pytest``."""
