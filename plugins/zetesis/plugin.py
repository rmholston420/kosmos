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

from dataclasses import dataclass, field

from ports.data import DataPort
from ports.event_bus import EventBusPort
from ports.frontend_contract import (
    FrontendContractPort,
    PluginDescriptor,
    PluginRegistration,
)
from ports.llm import LLMPort
from ports.memory import MemoryPort
from ports.notification import NotificationPort
from ports.observability import ObservabilityPort
from ports.resource import ResourcePort
from ports.search import SearchPort
from ports.secrets import SecretsPort
from ports.vector import VectorPort

__all__ = [
    "ZETESIS_KERNEL_COMPAT",
    "ZETESIS_MEMORY_DEFAULT_CONFIDENCE",
    "ZETESIS_MEMORY_PREDICATE",
    "ZETESIS_MEMORY_PROVENANCE",
    "ZETESIS_PLUGIN_NAME",
    "ZETESIS_STATE_NAMESPACE",
    "ZETESIS_VERSION",
    "ZetesisPlugin",
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
