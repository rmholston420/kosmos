"""Value objects for the Stage 4.6 gate app (ADR-051).

Pure data classes — no I/O, no plugin imports. Mirror the frozen-slots
convention used by ``ports.memory`` and
``adapters.memory.dozerdb.corpora.models``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ClaimEnvelope:
    """One corpus fact projected onto the Stage 4.6 UI surface.

    Every field surfaced in the UI (source, timestamp, confidence) has
    a first-class attribute here so the templates never touch raw
    ``payload["attributes"]`` dicts. Immutable.
    """

    event_id: str
    corpus_name: str
    subject: str
    predicate: str
    object_: str
    as_of: datetime
    provenance: str
    confidence: float
    upstream_url: str | None = None
    license: str | None = None
    source_commit: str | None = None
    crm_class: str | None = None


@dataclass(frozen=True, slots=True)
class EdgeEnvelope:
    """One typed CIDOC-CRM edge projected onto the Stage 4.6 UI.

    ``kind`` is a CIDOC-CRM property URI when the corpus is
    ``humanities-bilara`` (``P73_is_translation_of`` /
    ``P94_was_created_by``); Superpowers KB uses the untyped
    ``references`` kind (Stage 4.4 vocabulary). The UI does not
    interpret ``kind`` — it renders whatever the corpus emitted.
    """

    src_event_id: str
    kind: str
    dst_event_id: str
    dst_subject: str
    dst_confidence: float
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProvenanceChain:
    """Full provenance chain for one corpus record.

    - ``claim`` — the record itself (source + timestamp + confidence).
    - ``outbound`` — typed edges where ``src_event_id == claim.event_id``.
    - ``inbound`` — typed edges where ``dst_event_id == claim.event_id``.

    Stage 4.6 DoD asserts that every claim can be rendered as a
    :class:`ProvenanceChain` with all three fields populated (empty
    tuples are valid; ``None`` is not).
    """

    claim: ClaimEnvelope
    outbound: tuple[EdgeEnvelope, ...]
    inbound: tuple[EdgeEnvelope, ...]

    @property
    def edge_count(self) -> int:
        return len(self.outbound) + len(self.inbound)


@dataclass(frozen=True, slots=True)
class CorpusSummary:
    """Aggregate view of one landed corpus for the dashboard.

    - ``name`` — corpus name (matches ``Corpus.name``).
    - ``n_facts`` / ``n_edges`` — cardinalities.
    - ``edge_kind_census`` — mapping of edge ``kind`` to count.
    - ``licenses`` — sorted tuple of every distinct ``license`` string
      seen in ``attributes.license`` across the corpus facts.
    """

    name: str
    n_facts: int
    n_edges: int
    edge_kind_census: tuple[tuple[str, int], ...]
    licenses: tuple[str, ...]
