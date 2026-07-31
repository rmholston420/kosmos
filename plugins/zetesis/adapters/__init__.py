"""Zetesis plugin-local stub adapters (ADR-056 sub-slice 2).

Minimal Protocol-conformant stubs used to construct ZetesisPlugin during
tests and pre-DoD wiring. Production Zetesis binds to real root-level
adapters (adapters/*/) at kernel-boot time. These stubs exist so:

1. Sub-slice 2 port-wiring contract tests can construct ZetesisPlugin
   without dragging in real adapter runtime deps (Ollama, SearXNG, DozerDB, ...).
2. Sub-slice 3's `ZetesisPlugin.research()` can be exercised in fast-tier
   tests against controllable port behavior.
3. Sub-slice 4's Colossus DoD trial replaces the LLM and Search stubs
   (only) with real backends; the other 8 stay stubbed since they are
   incidental to the research rating.

Every stub is Protocol-conformant per @runtime_checkable so
`isinstance(stub, Port)` returns True. Unused methods raise
NotImplementedError with a stable message; used methods return
minimal safe defaults.
"""

from plugins.zetesis.adapters.data_stub import ZetesisDataStub
from plugins.zetesis.adapters.event_bus_stub import ZetesisEventBusStub
from plugins.zetesis.adapters.llm_stub import ZetesisLLMStub
from plugins.zetesis.adapters.memory_stub import ZetesisMemoryStub
from plugins.zetesis.adapters.notification_stub import ZetesisNotificationStub
from plugins.zetesis.adapters.observability_stub import ZetesisObservabilityStub
from plugins.zetesis.adapters.resource_stub import ZetesisResourceStub
from plugins.zetesis.adapters.search_stub import ZetesisSearchStub
from plugins.zetesis.adapters.vector_stub import ZetesisVectorStub

__all__ = [
    "ZetesisDataStub",
    "ZetesisEventBusStub",
    "ZetesisLLMStub",
    "ZetesisMemoryStub",
    "ZetesisNotificationStub",
    "ZetesisObservabilityStub",
    "ZetesisResourceStub",
    "ZetesisSearchStub",
    "ZetesisVectorStub",
]
