"""Zetesis production-adapter factory (ADR-056 sub-slice 4).

Re-exports the Stage 6.3.9-envelope factory used by
``ops/benchmarks/adr_010/run_zetesis_dod.py`` and any future kernel
boot path that needs to construct a real ``ZetesisPlugin`` outside
the fast-tier tests.

The factory returns a fully-constructed :class:`ZetesisPlugin` whose
adapter matrix matches ADR-056 §D4:

- LLMPort              → OllamaAdapter                  (real, live Ollama)
- SearchPort           → SearxngAdapter                 (real, live SearXNG)
- ObservabilityPort    → OtelStackObservabilityAdapter  (real adapter, StubOtelBackend backend)
- EventBusPort         → ValkeyEventBusAdapter          (real adapter, InMemoryStreamClient client)
- FrontendContractPort → KernelFrontendContractAdapter  (real, production)
- MemoryPort           → ZetesisMemoryStub              (sub-slice-2 stub — DozerDB not up at 6.3.9)
- VectorPort           → ZetesisVectorStub              (sub-slice-2 stub — Qdrant not up at 6.3.9)
- DataPort             → ZetesisDataStub                (sub-slice-2 stub — DataPort adapter not up at 6.3.9)
- ResourcePort         → ZetesisResourceStub            (sub-slice-2 stub — ResourcePort MVP)
- NotificationPort     → ZetesisNotificationStub        (sub-slice-2 stub — algedonic path unused at 6.3.9)

See docs/adrs/ADR-056-stage-6-3-proper-zetesis-kernel-wiring.md §D4.
"""

from plugins.zetesis.adapters.real.factory import (
    build_stage_6_3_9_zetesis_plugin,
)

__all__ = ["build_stage_6_3_9_zetesis_plugin"]
