"""Zetesis plugin bootstrap — research kernel-plugin (Stage 6.1, ADR-052).

Zetesis is Kosmos's Phase-6 System-4 (Intelligence) research plugin.

Stage 6.1 responsibility is exactly one thing: **the plugin loads**. The
kernel can construct it with the ten required ports named in ADR-052
§Q7=B-plus (extending Build-Sequence §6.1's original 4-port list), plus
one optional port slot, then call :meth:`ZetesisPlugin.start` and reach
the started state without raising.

Port surface — ADR-052 §Q7=B-plus lock:

Required (non-None) — 10 ports:

- :class:`~ports.frontend_contract.FrontendContractPort` — descriptor
  registration at :meth:`start`.
- :class:`~ports.llm.LLMPort` — inner-loop query decomposition,
  summarization, citation grounding. First call at Stage 6.3 after
  ADR-010 resolves the AREX-vs-Open-Deep-Research choice.
- :class:`~ports.memory.MemoryPort` — records
  ``zetesis.research.completed`` events; retrieves prior research
  context. First write at Stage 6.3.
- :class:`~ports.vector.VectorPort` — semantic retrieval over prior
  research + external corpora.
- :class:`~ports.data.DataPort` — canonical JSON-LD import/export for
  research questions + reports.
- :class:`~ports.search.SearchPort` — web-search substrate. Primary
  means of gathering fresh evidence. Added at 6.1 to correct the
  Build-Sequence §6.1 vs. spec §95 / ADR-021 omission (ADR-052 §Q7).
- :class:`~ports.event_bus.EventBusPort` — publishes
  ``zetesis.research.completed`` for downstream Synedrion strategic-
  signal consumption (spec §35 System-4).
- :class:`~ports.resource.ResourcePort` — required for spec §172's
  fixed-priority queue (``Phrouros anomaly > Tektos active >
  Synedrion/Zetesis background``). Also fulfills the spec §191
  fixture-stub contract: at Q5=C the real plugin *is* the
  ``zetesis-stub`` that requests a background model load on a fixed
  schedule to exercise priority-queue arbitration.
- :class:`~ports.notification.NotificationPort` — algedonic signals
  for grounding-failure / source-diversity-gate violations (spec §46
  two-layer anti-hallucination). Required so no research path silently
  swallows a signal.
- :class:`~ports.observability.ObservabilityPort` — trace + metrics
  for every LLM call and research pipeline stage. Required so no
  inner-loop call escapes observation.

Optional (may be None at 6.1) — 1 port:

- :class:`~ports.secrets.SecretsPort` — external-service credentials
  (academic APIs, alternate SearchPort backends). ``None`` at 6.1;
  wired when Zetesis first consumes a non-local SearXNG backend or
  paywalled data source.

At Stage 6.1 the plugin:

- Holds all 11 port slots but **calls none of the business ports**.
  ADR-010's AREX-vs-Open-Deep-Research head-to-head is still open;
  premature use of ``LLMPort`` would pre-empt that decision
  (ADR-052 §Q3=A).
- Registers a :class:`~ports.frontend_contract.PluginDescriptor` with
  **zero panels and zero routes** — matching the DoD literal "Plugin
  loads." UI surface lands at Stage 6.3/6.4 (ADR-052 §Q2=A).
- Serves as the ``zetesis-stub`` fixture stub that spec §191 +
  Build-Sequence §1.6 require for Tektos Phase-10 model-swap-under-
  load. There is no separate stub package; the real plugin *is* the
  stub (ADR-052 §Q5=C).

Locked MemoryPort write constants (first exercised at Stage 6.3):

- ``ZETESIS_MEMORY_PROVENANCE = "zetesis_research"``
- ``ZETESIS_MEMORY_PREDICATE = "zetesis.research.completed"``
- ``ZETESIS_MEMORY_DEFAULT_CONFIDENCE = 0.75``

The default confidence mirrors Tektos's pre-Reflexion default from
ADR-036; Zetesis's inner loop (Phase 6.3) will replace it with a
task-tuned score once ADR-010 resolves.

ADR-007: this module imports only from ``ports.*``. It MUST NOT import
any other plugin. The AST guard in ``tests/test_zetesis_plugin.py``
enforces this at test time.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from ports.data import DataPort, PIITier
from ports.event_bus import EventBusPort
from ports.event_envelope import EventEnvelope
from ports.frontend_contract import (
    FrontendContractPort,
    PluginDescriptor,
    PluginRegistration,
)
from ports.llm import LLMPort
from ports.memory import MemoryPort
from ports.notification import NotificationPort
from ports.observability import ObservabilityPort
from ports.resource import PriorityClass, ResourceKind, ResourcePort
from ports.search import SearchPort
from ports.secrets import SecretsPort
from ports.vector import VectorPort

__all__ = [
    "ZETESIS_KERNEL_COMPAT",
    "ZETESIS_MEMORY_DEFAULT_CONFIDENCE",
    "ZETESIS_MEMORY_PREDICATE",
    "ZETESIS_MEMORY_PROVENANCE",
    "ZETESIS_PLUGIN_NAME",
    "ZETESIS_RESEARCH_EVENT_COMPLETED",
    "ZETESIS_RESEARCH_EVENT_STARTED",
    "ZETESIS_STATE_NAMESPACE",
    "ZETESIS_VERSION",
    "ResearchReport",
    "ZetesisPlugin",
    "ZetesisResearchConfig",
    "build_zetesis_descriptor",
]


# ---------------------------------------------------------------------------
# Plugin identity — locked at Stage 6.1
# ---------------------------------------------------------------------------

ZETESIS_PLUGIN_NAME: str = "zetesis"
"""Locked plugin name. Matches ``ZETESIS_STATE_NAMESPACE`` (ADR-031 shape)
and spec §35/§38 System-4/System-1 references."""

ZETESIS_STATE_NAMESPACE: str = "zetesis"
"""Locked state namespace. Mirrors the plugin name (ADR-031 pattern)."""

ZETESIS_VERSION: str = "0.1.0"
"""Semantic version. Bumps require an ADR."""

ZETESIS_KERNEL_COMPAT: str = "0.1.x"
"""Kernel-compat range. Matches every Phase-1/2/3/4 plugin."""


# ---------------------------------------------------------------------------
# MemoryPort write contract — locked at Stage 6.1, first exercised Stage 6.3
# ---------------------------------------------------------------------------

ZETESIS_MEMORY_PROVENANCE: str = "zetesis_research"
"""Locked provenance string for every Zetesis MemoryPort write.

Fixed at Stage 6.1 so downstream Stage-6 tests + Phrouros grounding
checks can pin the exact value. First real write lands at Stage 6.3
after ADR-010 resolves the inner-loop vendor choice.
"""

ZETESIS_MEMORY_PREDICATE: str = "zetesis.research.completed"
"""Locked predicate for the Stage-6.3+ research-completion event."""

ZETESIS_MEMORY_DEFAULT_CONFIDENCE: float = 0.75
"""Default confidence for Zetesis MemoryPort writes prior to the
Phase-6 inner-loop scorer. Mirrors Tektos's pre-Reflexion default from
ADR-036. Must sit in ``(0, 1]`` — enforced by
:func:`ports.memory.validate_zero_trust_write`."""


# ---------------------------------------------------------------------------
# EventBus event-type constants — locked at Stage 6.3 (proper) sub-slice 3
# ---------------------------------------------------------------------------

ZETESIS_RESEARCH_EVENT_STARTED: str = "zetesis.research.started"
"""EventBusPort event-type for the start of a `research()` call.
Emitted after ResourcePort.allocate returns and before the inner-loop
invocation. Payload includes `query_id` + `trial_id` + `question_id`."""

ZETESIS_RESEARCH_EVENT_COMPLETED: str = "zetesis.research.completed"
"""EventBusPort event-type for successful completion of a `research()`
call. Emitted after MemoryPort.write_event returns. Payload includes
`query_id`, `trial_id`, `question_id`, `latency_seconds`, and
`source_diversity`. Matches ZETESIS_MEMORY_PREDICATE by design —
ADR-052 §Q4 predicate is written to memory; this event-type is the
pub/sub companion."""


# ---------------------------------------------------------------------------
# Public research API dataclasses — locked at Stage 6.3 (proper) sub-slice 3
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ZetesisResearchConfig:
    """Immutable per-call configuration for :meth:`ZetesisPlugin.research`.

    Bundles the ~18 kwargs of the underlying ``run_zetesis_research``
    inner loop into a single explicit value. Optional — pass ``None``
    to :meth:`research` and the plugin applies Stage 6.3.9-locked
    defaults (all feature gates on; Colossus-local Ollama/SearXNG
    URLs).

    Kept a plain dataclass (not TypedDict / not Pydantic) per ADR-023
    kernel-avoids-Pydantic rule.
    """

    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    ollama_model: str = "qwen2.5:32b-instruct-q4_K_M"
    mcp_server_url: str = "http://127.0.0.1:8000"
    question_id: str = "adhoc"
    trial_id: str = ""  # empty — :meth:`research` assigns a uuid4
    fact_anchor_urls: tuple[str, ...] | None = None
    rubric_lines: tuple[str, ...] | None = None
    # Stage 6.3.9-locked feature gates (all on).
    enable_fact_check: bool = True
    enable_license_grounding: bool = True
    enable_feature_grounding: bool = True
    enable_enterprise_license_grounding: bool = True
    enable_rubric_critique: bool = True
    enable_cove: bool = True
    enable_claim_support_gate: bool = True
    enable_structural_finalize: bool = True
    # Resource-budget parameters.
    compute_budget: Decimal | float = Decimal("1")
    priority_class: PriorityClass = PriorityClass.BACKGROUND


@dataclass(frozen=True, slots=True)
class ResearchReport:
    """Plugin-facing output of :meth:`ZetesisPlugin.research`.

    Higher-level than the internal ``TrialMetrics`` used by the
    ADR-010 harness. ``TrialMetrics`` carries head-to-head benchmark
    fields (GPU peak, VRAM peak, integration effort) that are not part
    of the general research API surface. Consumers of the plugin's
    public API get :class:`ResearchReport`; the harness continues to
    consume ``TrialMetrics`` directly via
    ``plugins.zetesis.research.run_zetesis_research``.
    """

    query: str
    answer: str
    citations: tuple[str, ...]
    evidences: tuple[Mapping[str, str], ...]
    source_diversity: int
    latency_seconds: float
    trial_id: str
    question_id: str
    trajectory_events: int
    memory_event_id: str | None
    error: str | None = None


# ---------------------------------------------------------------------------
# Descriptor factory — pure, testable, ADR-052 §Q2=A shape
# ---------------------------------------------------------------------------

def build_zetesis_descriptor() -> PluginDescriptor:
    """Construct the Zetesis :class:`PluginDescriptor`.

    Pure function — no I/O, no side effects. Split out for testability
    (contract tests inspect the descriptor without instantiating the
    plugin or any port adapter).

    ADR-052 §Q2=A shape: **zero panels, zero routes, empty design
    tokens**. Stage 6.1 DoD is literally "Plugin loads." Panels + routes
    land at Stage 6.3/6.4 when real research output exists to render.

    Returns:
        The canonical Zetesis descriptor.
    """
    return PluginDescriptor(
        name=ZETESIS_PLUGIN_NAME,
        state_namespace=ZETESIS_STATE_NAMESPACE,
        version=ZETESIS_VERSION,
        kernel_compat=ZETESIS_KERNEL_COMPAT,
        design_tokens={},
        routes=(),
        panels=(),
    )


# ---------------------------------------------------------------------------
# Plugin class — dataclass with cheap side-effect-free construction
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ZetesisPlugin:
    """The Zetesis research plugin — Stage 6.1 skeleton.

    Construction is **cheap and side-effect-free**. All work happens in
    :meth:`start`, which registers the descriptor with the
    :class:`FrontendContractPort`. **No other port is touched at 6.1.**

    The ten required business ports are held as constructor
    dependencies — this proves the ADR-052 §Q7=B-plus wiring shape and
    lets the kernel discover the port surface Zetesis will consume from
    Stage 6.3 onward. They are **not** called at 6.1 (ADR-052 §Q3=A;
    ADR-010 still open).

    :attr:`secrets` is the single optional slot; it defaults to ``None``
    and is wired when Zetesis first needs external-service credentials.

    Splitting init from start keeps testability high: contract tests
    can construct a :class:`ZetesisPlugin` without live port adapters,
    then drive :meth:`start` with test doubles.

    Attributes:
        frontend_contract: :class:`FrontendContractPort` — descriptor
            registration at startup.
        llm: :class:`LLMPort` (held, not called at 6.1).
        memory: :class:`MemoryPort` (held, not called at 6.1).
        vector: :class:`VectorPort` (held, not called at 6.1).
        data: :class:`DataPort` (held, not called at 6.1).
        search: :class:`SearchPort` (held, not called at 6.1).
        event_bus: :class:`EventBusPort` (held, not called at 6.1).
        resource: :class:`ResourcePort` (held, not called at 6.1;
            first exercised by the §191 fixture-stub contract from
            Phase 1's Tektos Phase-10 test rig).
        notification: :class:`NotificationPort` (held, not called at
            6.1; algedonic path for grounding-failure escalation).
        observability: :class:`ObservabilityPort` (held, not called at
            6.1; trace + metrics for every 6.3+ inner-loop call).
        secrets: :class:`SecretsPort` | ``None`` — optional at 6.1.
    """

    frontend_contract: FrontendContractPort
    llm: LLMPort
    memory: MemoryPort
    vector: VectorPort
    data: DataPort
    search: SearchPort
    event_bus: EventBusPort
    resource: ResourcePort
    notification: NotificationPort
    observability: ObservabilityPort
    secrets: SecretsPort | None = None
    _registration: PluginRegistration | None = field(default=None, init=False)
    _started: bool = field(default=False, init=False)

    @property
    def registration(self) -> PluginRegistration:
        """Return the FrontendContractPort registration record.

        Raises:
            RuntimeError: If :meth:`start` has not been called.
        """
        if self._registration is None:
            raise RuntimeError(
                "ZetesisPlugin has not started — call start() first"
            )
        return self._registration

    @property
    def is_started(self) -> bool:
        """Whether :meth:`start` has completed successfully."""
        return self._started

    async def start(self) -> None:
        """Register the Zetesis descriptor with the FrontendContractPort.

        Idempotent — safe to call multiple times.

        At Stage 6.1 this is the entire startup surface. No LLM call,
        no vector search, no memory write, no data-source poll, no
        SearchPort query, no event published, no resource allocated,
        no algedonic signal, no trace span. The ten required business
        ports are held but untouched (ADR-052 §Q3=A).
        """
        if self._started:
            return

        descriptor = build_zetesis_descriptor()
        self._registration = await self.frontend_contract.register_plugin(
            descriptor
        )
        self._started = True

    async def stop(self) -> None:
        """Idempotent shutdown — unregister from FrontendContractPort.

        Safe to call multiple times or before :meth:`start`.
        """
        if not self._started:
            return
        await self.frontend_contract.unregister_plugin(ZETESIS_PLUGIN_NAME)
        self._registration = None
        self._started = False

    # ---- Stage 6.3 (proper) sub-slice 3 — public research API ----------

    async def research(
        self,
        query: str,
        *,
        config: ZetesisResearchConfig | None = None,
    ) -> ResearchReport:
        """Run a Zetesis research query end-to-end.

        Signature locked at ADR-056 sub-slice 3 kickoff (2026-07-30):
        positional ``query`` + keyword-only ``config``. Config is
        optional; when ``None``, Stage 6.3.9-locked defaults apply.

        Wiring order (satisfies ADR-056 §D3 as amended sub-slice 3):

        1. :class:`ObservabilityPort` — wrap the entire call in a
           ``zetesis.research`` span (attributes: query, question_id,
           trial_id).
        2. :class:`ResourcePort` — ``can_allocate(COMPUTE, ...)`` then
           ``allocate(...)`` at :attr:`config.priority_class` with
           requester="zetesis". No explicit release verb exists on
           :class:`ResourcePort` (spec surface is fire-and-forget);
           replenish is the operator-facing counter-verb.
        3. :class:`EventBusPort` — publish
           :data:`ZETESIS_RESEARCH_EVENT_STARTED` envelope.
        4. Inner loop — delegate to
           ``plugins.zetesis.research.run_zetesis_research`` (aliased
           to ``run_odr_trial``). Returns
           :class:`ops.benchmarks.adr_010.metrics.TrialMetrics`.
        5. :class:`VectorPort` — no-op ``search(...)`` per ADR-056
           §D3 (retrieval wiring proof; results ignored at 6.3).
        6. :class:`DataPort` — ``export_canonical(...)`` the report as
           ``zetesis_research_report`` with ADR-052 §Q4 provenance +
           :data:`ZETESIS_MEMORY_DEFAULT_CONFIDENCE` + PIITier.PUBLIC.
        7. :class:`MemoryPort` — ``write_event(...)`` with subject=query,
           predicate=:data:`ZETESIS_MEMORY_PREDICATE`, object=answer
           (elided to first 256 chars for temporal-index compactness),
           provenance=:data:`ZETESIS_MEMORY_PROVENANCE`, confidence=
           :data:`ZETESIS_MEMORY_DEFAULT_CONFIDENCE`. Zero-trust
           invariants enforced by :func:`ports.memory.validate_zero_trust_write`.
        8. :class:`EventBusPort` — publish
           :data:`ZETESIS_RESEARCH_EVENT_COMPLETED` envelope with
           latency + source_diversity.

        LLMPort and SearchPort are exercised **inside** the inner loop
        (via LangGraph + MCP), not by this wrapper directly.
        NotificationPort is not exercised at sub-slice 3 — the
        algedonic path is reserved for grounding-failure escalation
        (spec §46) which requires a scorer that lands post-Phase-6.
        SecretsPort is optional and untouched by the default flow.

        Args:
            query: Verbatim user query.
            config: Optional per-call configuration bundle. When
                ``None``, Stage 6.3.9-locked defaults apply.

        Returns:
            :class:`ResearchReport` — plugin-facing view of the trial's
            output (higher-level than the internal ``TrialMetrics``).

        Raises:
            RuntimeError: If :meth:`start` has not been called.
            Any exception raised by the inner loop propagates verbatim
            after being recorded on the observability span and after
            the started event has been published (the completed event
            is not published on failure).
        """
        if not self._started:
            raise RuntimeError(
                "ZetesisPlugin has not started — call start() before research()"
            )

        # Import inside method to keep module import cost low. The
        # inner-loop import triggers a LangGraph dependency chain that
        # test suites monkeypatch out at the module attribute level.
        from plugins.zetesis.research import run_zetesis_research
        from ops.benchmarks.adr_010.metrics import TrialMetrics

        cfg = config if config is not None else ZetesisResearchConfig()
        trial_id = cfg.trial_id or str(uuid.uuid4())

        span_attrs: dict[str, Any] = {
            "query": query,
            "question_id": cfg.question_id,
            "trial_id": trial_id,
            "ollama_model": cfg.ollama_model,
        }

        with self.observability.trace(
            "zetesis.research", attributes=span_attrs
        ) as span:
            # 2. Resource allocation.
            _ok = await self.resource.can_allocate(
                ResourceKind.COMPUTE, cfg.compute_budget
            )
            _handle = await self.resource.allocate(
                ResourceKind.COMPUTE,
                cfg.compute_budget,
                intent="zetesis.research",
                priority_class=cfg.priority_class,
                requester=ZETESIS_PLUGIN_NAME,
            )

            # 3. Started event.
            started_env = EventEnvelope(
                producer_plugin=ZETESIS_PLUGIN_NAME,
                event_type=ZETESIS_RESEARCH_EVENT_STARTED,
                payload={
                    "query": query,
                    "question_id": cfg.question_id,
                    "trial_id": trial_id,
                },
            )
            await self.event_bus.publish(started_env)

            # 4. Inner-loop delegation.
            metrics: TrialMetrics = await run_zetesis_research(
                question=query,
                question_id=cfg.question_id,
                trial_id=trial_id,
                ollama_base_url=cfg.ollama_base_url,
                ollama_model=cfg.ollama_model,
                mcp_server_url=cfg.mcp_server_url,
                fact_anchor_urls=(
                    list(cfg.fact_anchor_urls)
                    if cfg.fact_anchor_urls is not None
                    else None
                ),
                enable_fact_check=cfg.enable_fact_check,
                enable_license_grounding=cfg.enable_license_grounding,
                enable_feature_grounding=cfg.enable_feature_grounding,
                enable_enterprise_license_grounding=cfg.enable_enterprise_license_grounding,
                enable_rubric_critique=cfg.enable_rubric_critique,
                rubric_lines=(
                    list(cfg.rubric_lines)
                    if cfg.rubric_lines is not None
                    else None
                ),
                enable_cove=cfg.enable_cove,
                enable_claim_support_gate=cfg.enable_claim_support_gate,
                enable_structural_finalize=cfg.enable_structural_finalize,
            )

            citations = tuple(
                str(ev.get("url", "")) for ev in metrics.final_evidences
            )
            evidences = tuple(
                dict(ev) for ev in metrics.final_evidences
            )

            # 5. Vector no-op retrieval (ADR-056 §D3).
            _hits = await self.vector.search(
                collection=ZETESIS_STATE_NAMESPACE,
                query_vector=[],
                limit=1,
            )

            # 6. Canonical data export.
            _data_handle = await self.data.export_canonical(
                record_type="zetesis_research_report",
                payload={
                    "query": query,
                    "answer": metrics.final_answer,
                    "citations": list(citations),
                    "trial_id": trial_id,
                    "question_id": cfg.question_id,
                    "source_diversity": metrics.source_diversity,
                    "latency_seconds": metrics.latency_seconds,
                },
                provenance=ZETESIS_MEMORY_PROVENANCE,
                confidence=ZETESIS_MEMORY_DEFAULT_CONFIDENCE,
                pii_tier=PIITier.PUBLIC,
            )

            # 7. Memory event (zero-trust ADR-008).
            answer_head = (metrics.final_answer or "")[:256]
            event_id_obj = await self.memory.write_event(
                subject=query,
                predicate=ZETESIS_MEMORY_PREDICATE,
                object=answer_head,
                provenance=ZETESIS_MEMORY_PROVENANCE,
                confidence=ZETESIS_MEMORY_DEFAULT_CONFIDENCE,
                pii_tier=PIITier.PUBLIC.value,
                attributes={
                    "trial_id": trial_id,
                    "question_id": cfg.question_id,
                    "source_diversity": metrics.source_diversity,
                    "latency_seconds": metrics.latency_seconds,
                    "citations_count": len(citations),
                },
            )
            memory_event_id_str = (
                str(getattr(event_id_obj, "id", event_id_obj))
                if event_id_obj is not None
                else None
            )

            # 8. Completed event.
            completed_env = EventEnvelope(
                producer_plugin=ZETESIS_PLUGIN_NAME,
                event_type=ZETESIS_RESEARCH_EVENT_COMPLETED,
                payload={
                    "query": query,
                    "question_id": cfg.question_id,
                    "trial_id": trial_id,
                    "latency_seconds": metrics.latency_seconds,
                    "source_diversity": metrics.source_diversity,
                    "memory_event_id": memory_event_id_str,
                },
            )
            await self.event_bus.publish(completed_env)

            span.set_attribute("source_diversity", metrics.source_diversity)
            span.set_attribute("latency_seconds", metrics.latency_seconds)

            return ResearchReport(
                query=query,
                answer=metrics.final_answer,
                citations=citations,
                evidences=evidences,
                source_diversity=metrics.source_diversity,
                latency_seconds=metrics.latency_seconds,
                trial_id=trial_id,
                question_id=cfg.question_id,
                trajectory_events=len(metrics.trajectory),
                memory_event_id=memory_event_id_str,
                error=metrics.error,
            )
