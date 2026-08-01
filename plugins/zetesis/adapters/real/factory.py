"""ZetesisPlugin factory suite.

Two factories:

- :func:`build_stage_6_3_9_zetesis_plugin` — Stage-6.3.9-envelope wiring
  used by the ADR-054 DoD trial. Preserved verbatim so re-running the
  5.33/6 rater baseline stays apples-to-apples.
- :func:`build_stage_6_5_zetesis_plugin` — Stage 6.5 mount wiring. All
  ten required ports are real adapters. Backends that require a running
  daemon (DozerDB, real Qdrant) select in-memory or lazy-import backends
  by default so the plugin can be mounted in the kernel lifespan without
  a full compose stack up; each seam is injectable so the kernel can
  pass real backends when they are provisioned.

Zero network I/O at construction time. Every real adapter defers
backend I/O until first port call.
"""

from __future__ import annotations

from pathlib import Path

from adapters.data.filesystem.adapter import FilesystemDataAdapter
from adapters.event_bus.valkey.adapter import (
    InMemoryStreamClient,
    ValkeyEventBusAdapter,
)
from adapters.frontend_contract.kernel.adapter import KernelFrontendContractAdapter
from adapters.llm.ollama.adapter import OllamaAdapter
from adapters.memory.dozerdb.adapter import (
    DozerDbMemoryAdapter,
    InMemoryGraphBackend,
    InMemoryTemporalIndex,
    NoOpAmgPolicy,
)
from adapters.notification.kernel.adapter import KernelNotificationAdapter
from adapters.observability.otel_stack.adapter import (
    OtelStackObservabilityAdapter,
    StubOtelBackend,
)
from adapters.resource.sqlite.adapter import (
    InMemoryStorage as ResourceInMemoryStorage,
)
from adapters.resource.sqlite.adapter import SqliteResourceAdapter
from adapters.search.searxng.adapter import SearxngAdapter
from adapters.vector.qdrant.adapter import (
    InMemoryQdrantBackend,
    QdrantVectorAdapter,
)
from plugins.zetesis.adapters import (
    ZetesisDataStub,
    ZetesisMemoryStub,
    ZetesisNotificationStub,
    ZetesisResourceStub,
    ZetesisVectorStub,
)
from plugins.zetesis.plugin import ZetesisPlugin


# ---------------------------------------------------------------------------
# Stage 6.3.9 factory (preserved verbatim for ADR-054 trial parity)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Stage 6.5 factory — full-real-adapter mount
# ---------------------------------------------------------------------------


DEFAULT_DATA_ROOT = Path.home() / ".local" / "state" / "kosmos" / "data"


def build_stage_6_5_zetesis_plugin(
    *,
    frontend_contract: KernelFrontendContractAdapter | None = None,
    event_bus: ValkeyEventBusAdapter | None = None,
    resource: SqliteResourceAdapter | None = None,
    notification: KernelNotificationAdapter | None = None,
    ollama_base_url: str = "http://127.0.0.1:11434/v1",
    ollama_model: str = "qwen2.5:32b-instruct-q4_K_M",
    searxng_url: str = "http://127.0.0.1:8888",
    data_root: Path = DEFAULT_DATA_ROOT,
    service_name: str = "zetesis",
) -> ZetesisPlugin:
    """Construct a ZetesisPlugin with real adapters for all 10 required ports.

    Reuses kernel-shared adapters when the caller passes them (so the
    plugin and kernel share the same FrontendContractPort store, event
    bus, resource ledger, and notification sink). Constructs its own
    real adapters for MemoryPort, VectorPort, DataPort, LLMPort,
    SearchPort, and ObservabilityPort.

    Backends chosen for Stage 6.5:
      - MemoryPort: DozerDbMemoryAdapter with InMemoryGraphBackend +
        InMemoryTemporalIndex + NoOpAmgPolicy. Real DozerDB/Graphiti/AMG
        backends land at Stage 6.5.1 once neo4j-compose is up on
        Colossus. Zero-trust guard (validate_zero_trust_write) is
        already enforced at the port layer.
      - VectorPort: QdrantVectorAdapter(backend=InMemoryQdrantBackend()).
        Spec-endorsed — no RealQdrantBackend ships until Compose lands.
      - DataPort: FilesystemDataAdapter rooted under
        ``~/.local/state/kosmos/data``.
      - LLMPort: OllamaAdapter (real, lazy httpx connection).
      - SearchPort: SearxngAdapter (real, lazy httpx connection).
      - ObservabilityPort: OtelStackObservabilityAdapter(StubOtelBackend)
        until the OTEL collector lands.
      - EventBusPort / ResourcePort / NotificationPort /
        FrontendContractPort: reuse kernel instances when passed.

    Returns
    -------
    ZetesisPlugin
        Not yet started; caller must ``await plugin.start()``.
    """
    fc = frontend_contract or KernelFrontendContractAdapter()

    if event_bus is None:
        event_bus = ValkeyEventBusAdapter(
            client=InMemoryStreamClient(),
            stream_prefix="zetesis",
        )

    if resource is None:
        storage = ResourceInMemoryStorage()
        resource = SqliteResourceAdapter(storage=storage)

    if notification is None:
        notification = KernelNotificationAdapter()

    memory = DozerDbMemoryAdapter(
        graph=InMemoryGraphBackend(),
        amg=NoOpAmgPolicy(),
        temporal=InMemoryTemporalIndex(),
    )

    vector = QdrantVectorAdapter(backend=InMemoryQdrantBackend())

    data = FilesystemDataAdapter(storage_root=data_root)

    llm = OllamaAdapter(
        base_url=ollama_base_url,
        default_model=ollama_model,
    )

    search = SearxngAdapter(base_url=searxng_url)

    observability = OtelStackObservabilityAdapter(
        backend=StubOtelBackend(),
        service_name=service_name,
    )

    return ZetesisPlugin(
        frontend_contract=fc,
        llm=llm,
        memory=memory,
        vector=vector,
        data=data,
        search=search,
        event_bus=event_bus,
        resource=resource,
        notification=notification,
        observability=observability,
        secrets=None,
    )
