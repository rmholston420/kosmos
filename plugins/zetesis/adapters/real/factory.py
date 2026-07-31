"""Stage 6.3.9-envelope ZetesisPlugin factory (ADR-056 §D4).

Builds a :class:`ZetesisPlugin` bound to the exact adapter matrix used
for the Stage 6.3 (proper) DoD trial. Four production adapters are wired
against real Colossus backends (Ollama + SearXNG) or against real
production adapter code paths with test-safe backends (Observability +
EventBus). The remaining five ports use the sub-slice-2 stubs because
their production backends (DozerDB, Qdrant, DataPort filesystem, real
ResourcePort MVP, NotificationPort algedonic dispatch) were not yet
booted at Stage 6.3.9 — matching that envelope keeps the DoD trial
apples-to-apples with the ADR-054 baseline that produced the 5.33 / 6
rater score.

Zero network I/O happens at construction time. Every real adapter
either defers backend I/O until first port call (httpx clients are
lazy at the connection level) or accepts an injected in-memory client.
"""

from __future__ import annotations

from adapters.event_bus.valkey.adapter import (
    InMemoryStreamClient,
    ValkeyEventBusAdapter,
)
from adapters.frontend_contract.kernel.adapter import KernelFrontendContractAdapter
from adapters.llm.ollama.adapter import OllamaAdapter
from adapters.observability.otel_stack.adapter import (
    OtelStackObservabilityAdapter,
    StubOtelBackend,
)
from adapters.search.searxng.adapter import SearxngAdapter
from plugins.zetesis.adapters import (
    ZetesisDataStub,
    ZetesisMemoryStub,
    ZetesisNotificationStub,
    ZetesisResourceStub,
    ZetesisVectorStub,
)
from plugins.zetesis.plugin import ZetesisPlugin


def build_stage_6_3_9_zetesis_plugin(
    *,
    ollama_base_url: str = "http://127.0.0.1:11434/v1",
    ollama_model: str = "qwen2.5:32b-instruct-q4_K_M",
    searxng_url: str = "http://127.0.0.1:8888",
    service_name: str = "zetesis-adr010",
) -> ZetesisPlugin:
    """Construct a ZetesisPlugin with the Stage 6.3.9-envelope adapters.

    Parameters
    ----------
    ollama_base_url:
        OpenAI-compatible Ollama endpoint. Default matches the Colossus
        ADR-010 harness.
    ollama_model:
        Ollama model tag to pass through the LLMPort. Held for parity
        with the inner loop; the inner loop constructs its own LLM
        client via env vars ``OPENAI_API_KEY`` / ``OPENAI_BASE_URL``
        because ODR internally hardcodes the OpenAI adapter surface.
    searxng_url:
        SearXNG JSON endpoint. Held for parity with the inner loop; the
        MCP search server uses this url directly.
    service_name:
        OpenTelemetry ``service.name`` written on every span.

    Returns
    -------
    ZetesisPlugin
        Not yet started; caller must ``await plugin.start()``.
    """
    return ZetesisPlugin(
        frontend_contract=KernelFrontendContractAdapter(),
        llm=OllamaAdapter(
            base_url=ollama_base_url,
            default_model=ollama_model,
        ),
        memory=ZetesisMemoryStub(),
        vector=ZetesisVectorStub(),
        data=ZetesisDataStub(),
        search=SearxngAdapter(base_url=searxng_url),
        event_bus=ValkeyEventBusAdapter(
            client=InMemoryStreamClient(),
            stream_prefix="zetesis-adr010",
        ),
        resource=ZetesisResourceStub(),
        notification=ZetesisNotificationStub(),
        observability=OtelStackObservabilityAdapter(
            backend=StubOtelBackend(),
            service_name=service_name,
        ),
        secrets=None,
    )
