"""Stage 4.6 exit-gate FastAPI app (adapter surface, ADR-051).

Adapter-side surrogate for the Phase-3 Gnosis retrieval surface. Boots
a six-route FastAPI dashboard over the five landed Stage 4.2-shaped
MemoryPort adapter corpora and renders every claim with its full
provenance chain (source + timestamp + confidence + typed CIDOC-CRM
edges when the corpus has them).

Public surface:

* :func:`build_stage_46_gate_app` — FastAPI app factory (mirror of
  :func:`plugins.tektos.ui.server.build_tektos_ui_app`; ADR-051 Q4).
* :data:`STAGE_46_ROUTES` — locked route paths (policy constants).
* :func:`build_provenance_chain` — pure function that materializes a
  :class:`ProvenanceChain` for one corpus + subject; DoD anchor.
* :func:`traverse_typed_edges` — CIDOC-CRM edge traversal over a
  corpus (Stage 4.6 Q5 canned query surface).

No plugin imports (ADR-007). No I/O beyond MemoryPort read path and
in-memory corpus loaders.
"""

from __future__ import annotations

from .models import (
    ClaimEnvelope,
    CorpusSummary,
    EdgeEnvelope,
    ProvenanceChain,
)
from .policy import (
    STAGE_46_CORPUS_DETAIL_PATH,
    STAGE_46_DEFAULT_CONFIDENCE,
    STAGE_46_GATE_HOST,
    STAGE_46_GATE_PORT,
    STAGE_46_HEALTHZ_PATH,
    STAGE_46_INDEX_PATH,
    STAGE_46_PROVENANCE,
    STAGE_46_PROVENANCE_PATH,
    STAGE_46_QUERY_PATH,
    STAGE_46_ROUTES,
    STAGE_46_TRAVERSE_PATH,
)
from .server import build_stage_46_gate_app
from .traversal import build_provenance_chain, traverse_typed_edges

__all__ = [
    "ClaimEnvelope",
    "CorpusSummary",
    "EdgeEnvelope",
    "ProvenanceChain",
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
    "build_provenance_chain",
    "build_stage_46_gate_app",
    "traverse_typed_edges",
]
