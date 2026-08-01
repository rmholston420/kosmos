"""Kosmos kernel FastAPI app (Stage 6.5.9 — GUI enablement kernel additions).

Boot sequence (Stage 6.5.1+6.5.2 baseline preserved; 6.5.3 adds route only):

1. Seven kernel subsystems boot behind per-subsystem try/except:
   ``notification``, ``frontend_contract``, ``resource``, ``event_bus``,
   ``approval``, ``phrouros`` (now real — ADR-059), ``zetesis`` (ADR-058).
2. Resource subsystem is seeded at boot with baseline balances so
   ``/api/resources/balances`` returns real numbers instead of ``null``
   (ADR-059 §D2). Failure is degraded, not fatal.
3. Phrouros mounts once ``event_bus``, ``notification``, ``resource``
   have booted. It composes ``PhrourosEngine`` over the shipped
   ``InMemoryTraceFeedAdapter`` (ports/trace_feed.py) + the four
   ``ports/observability`` detectors + the shared kernel adapters
   (ADR-059 §D1). Failure surfaces under ``registry.errors["phrouros"]``.

Kernel HTTP endpoints (6.5.5):

- ``/api/phrouros/anomalies`` — 200 with real (usually empty) records.
- ``POST /api/zetesis/research`` — SSE endpoint (ADR-060) emitting
  ``started`` + ``completed`` on the happy path; ``started`` + ``error``
  on failure.
- ``GET /api/events/ws`` — WebSocket event-bus bridge (ADR-061); on
  connect sends a ``ready`` frame with the subscribed event-type list,
  then forwards published ``EventEnvelope``s as JSON ``event`` frames.
- ``POST /api/approvals/{approval_id}/approve`` and
  ``POST /api/approvals/{approval_id}/reject`` — approval resolve
  endpoints (ADR-062) over the existing ``ApprovalResolverPort``.
- ``POST /api/tektos/turn`` — drives one ``TektosAgent`` iteration
  (ADR-063) over the kernel-owned ``LLMPort`` + ``MemoryPort``
  adapters; returns the resulting ``TektosStep``.
- ``GET /api/gnosis/query`` — Gnosis retrieval surrogate over
  ``MemoryPort.query_temporal`` (ADR-064). Optional ``as_of`` ISO-8601
  filter, ``limit`` bounded to ``[1, 100]`` (default 20), optional
  ``corpus`` name filter that restricts hits to a manifest provenance.
- ``GET /api/gnosis/corpora`` — manifest of the five landed corpora
  (ADR-064) — ``synthetic-lifeline``, ``humanities-cidoc-sample``,
  ``rigpa-export``, ``superpowers``, ``humanities-bilara`` — augmented
  with live ``fact_count`` and ``last_ingested_at`` from the boot seeder.
- ``GET /api/gnosis/stats`` — top-line dashboard numbers computed from
  the static ``ALL_CORPORA`` tuple (ADR-064).
- ``GET /api/gnosis/event/{event_id}`` — single hit lookup by
  ``event_id`` via ``MemoryPort.query_temporal`` (ADR-064).

Boot env vars (ADR-064):

- ``KOSMOS_GNOSIS_SEED=1`` — ingest ``ALL_CORPORA`` into ``MemoryPort``
  at startup (default off; safe no-op on populated DBs via class-name
  idempotency matching).
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import uuid
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation
from typing import Any, AsyncIterator

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse

# ---------------------------------------------------------------------------
# Boot helpers
# ---------------------------------------------------------------------------


class _BootRegistry:
    """Holds live adapters + per-subsystem boot errors."""

    def __init__(self) -> None:
        self.errors: dict[str, str] = {}
        self.frontend_contract: Any = None
        self.resource: Any = None
        self.approval: Any = None
        self.notification: Any = None
        self.phrouros: Any = None
        self.event_bus: Any = None
        self.zetesis: Any = None
        self.trace_feed: Any = None
        # Stage 6.5.6 additions (ADR-063).
        self.llm: Any = None
        self.memory: Any = None
        self.tektos: Any = None
        self.tektos_agent: Any = None
        self.tektos_agent_lock: Any = None
        # Stage 6.5.8 (ADR-065): Tektos UI sub-app + its executor. Mounted at
        # ``/tektos-ui`` independently of ``registry.tektos`` (Option B):
        # the UI only needs ``registry.approval`` + ``registry.memory``, so it
        # stays reachable when the agent is down for triage of stuck plans.
        self.tektos_ui: Any = None
        self.tektos_ui_executor: Any = None
        # Stage 6.5.7 (ADR-064): Gnosis seeder state. ``gnosis_corpus_counts``
        # maps corpus name -> number of facts successfully written this boot
        # (``0`` when the seeder didn't run or write-blocked every fact).
        # ``gnosis_last_seeded_at`` is the UTC ISO timestamp of the last
        # successful seeder run, or ``None`` when the seeder didn't run.
        self.gnosis_corpus_counts: dict[str, int] = {}
        self.gnosis_last_seeded_at: str | None = None


registry = _BootRegistry()


def _try(subsystem: str):
    """Decorator: catch bootstrap errors per subsystem."""

    def wrap(fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — deliberate broad catch
            registry.errors[subsystem] = f"{type(exc).__name__}: {exc}"
            return None

    return wrap


# ---------------------------------------------------------------------------
# Resource seed defaults (ADR-059 §D2)
# ---------------------------------------------------------------------------


# Kept in one place so tests and docs can reference them.
# ResourceKind values are enumerated in ports/resource.py: time, money,
# attention, compute, knowledge, energy (six canonical kinds per spec §16).
# Seed values are baselines the operator can adjust with subsequent
# ``replenish()`` calls; they are NOT commitments about real physical
# resources, only presentation defaults so the GUI's resource-meter
# widgets render immediately at boot.
KERNEL_RESOURCE_SEED: dict[str, Decimal] = {
    "time": Decimal("1440"),        # one day of minutes
    "money": Decimal("100.00"),     # $100 discretionary budget
    "attention": Decimal("100"),    # normalized 0-100 pool
    "compute": Decimal("100"),      # normalized capacity pool
    "knowledge": Decimal("1"),      # nominal starting unit; accrues via Zetesis / research (replenish() rejects 0)
    "energy": Decimal("100"),       # normalized human-energy pool
}


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Notification (no args) ------------------------------------------------
    @_try("notification")
    def _boot_notification():
        from adapters.notification.kernel.adapter import KernelNotificationAdapter

        return KernelNotificationAdapter()

    registry.notification = _boot_notification

    # --- FrontendContract (no required args) ----------------------------------
    @_try("frontend_contract")
    def _boot_frontend():
        from adapters.frontend_contract.kernel.adapter import (
            KernelFrontendContractAdapter,
        )

        return KernelFrontendContractAdapter()

    registry.frontend_contract = _boot_frontend

    # --- Resource (SqliteResourceAdapter needs Storage; use InMemoryStorage) --
    @_try("resource")
    def _boot_resource():
        from adapters.resource.sqlite.adapter import (
            InMemoryStorage,
            SqliteResourceAdapter,
        )

        storage = InMemoryStorage()
        adapter = SqliteResourceAdapter(storage=storage)
        # Stash storage on the adapter so /api/resources/balances can
        # read ResourceBalance rows directly (ResourcePort exposes no
        # get_balance surface — that lives on the Storage protocol).
        adapter._kernel_storage = storage  # type: ignore[attr-defined]
        return adapter

    registry.resource = _boot_resource

    # --- Resource seed (ADR-059 §D2) — best-effort ---------------------------
    if registry.resource is not None:
        try:
            from ports.resource import ResourceKind

            for kind_name, amount in KERNEL_RESOURCE_SEED.items():
                try:
                    kind = ResourceKind(kind_name)
                except ValueError:
                    # Kind not in current ResourceKind enum; skip silently.
                    # Seed table intentionally lists forward-compatible names.
                    continue
                await registry.resource.replenish(kind, amount)
        except Exception as exc:  # noqa: BLE001
            # Resource stays up; seeding is best-effort.
            registry.errors["resource_seed"] = f"{type(exc).__name__}: {exc}"

    # --- EventBus (Valkey; env-driven URL, best-effort) -----------------------
    @_try("event_bus")
    def _boot_event_bus():
        from adapters.event_bus.valkey.adapter import ValkeyEventBusAdapter

        return ValkeyEventBusAdapter()

    registry.event_bus = _boot_event_bus

    # --- Approval (KernelChangeApprovalAdapter, 4 seams) ----------------------
    @_try("approval")
    def _boot_approval():
        from adapters.approval_resolver.praxis.adapter import (
            PraxisApprovalResolverAdapter,
        )
        from plugins.praxis.apex.engine import KernelChangeApprovalAdapter
        from plugins.praxis.apex.scheduler import InProcessScheduler
        from plugins.praxis.apex.storage import InMemoryStorage as PraxisStorage

        if registry.event_bus is None or registry.notification is None:
            raise RuntimeError(
                "approval depends on event_bus + notification; "
                "one of them failed to boot"
            )

        engine = KernelChangeApprovalAdapter(
            storage=PraxisStorage(),
            scheduler=InProcessScheduler(),
            event_bus=registry.event_bus,
            notification=registry.notification,
        )
        return PraxisApprovalResolverAdapter(engine=engine)

    registry.approval = _boot_approval

    # --- Phrouros (ADR-059 §D1 — wire the real engine over InMemoryTraceFeedAdapter) ---
    # Requires event_bus + notification + resource to have booted. If any is
    # missing we surface the reason and continue degraded.
    if (
        registry.event_bus is None
        or registry.notification is None
        or registry.resource is None
    ):
        registry.errors["phrouros"] = (
            "phrouros depends on event_bus + notification + resource; "
            "one of them failed to boot"
        )
    else:
        try:
            # Only LoopDetector ships a real implementation at Stage 6.5.1
            # (per plugins/phrouros/detector.py module docstring). The
            # three skeletons (bus_factor_1, model_swap_slo, stub_degradation)
            # raise DetectorNotImplementedError on detect() and are wired in
            # by their own future stages. UnauthorizedToolDetector requires
            # a curated tool allowlist not yet defined at kernel level and
            # is deferred to the stage that produces one.
            from plugins.phrouros.detectors.loop import LoopDetector
            from plugins.phrouros.engine import PhrourosEngine
            from ports.trace_feed import InMemoryTraceFeedAdapter

            trace_feed = InMemoryTraceFeedAdapter()
            registry.trace_feed = trace_feed

            engine = PhrourosEngine(
                trace_feed=trace_feed,
                detectors=(LoopDetector(),),
                notification_port=registry.notification,
                resource_port=registry.resource,
                event_bus=registry.event_bus,
            )
            await engine.start()
            registry.phrouros = engine
        except Exception as exc:  # noqa: BLE001
            registry.errors["phrouros"] = f"{type(exc).__name__}: {exc}"

    # --- LLM (OllamaAdapter) --------------------------------------------------
    # Stage 6.5.6 addition (ADR-063): kernel-owned LLMPort shared by Tektos
    # and future plugins. Ollama endpoint + model overridable via env vars
    # ``KOSMOS_OLLAMA_BASE_URL`` (native Ollama HTTP API root, *not* the
    # ``/v1`` OpenAI-compat prefix — adapter posts to ``/api/generate``,
    # ``/api/chat``, ``/api/embed``, etc.) and ``KOSMOS_OLLAMA_DEFAULT_MODEL``.
    # Failure surfaces under ``registry.errors['llm']`` and cascades to
    # Tektos boot below.
    @_try("llm")
    def _boot_llm():
        from adapters.llm.ollama.adapter import OllamaAdapter

        # OllamaAdapter reads ``KOSMOS_OLLAMA_BASE_URL`` and
        # ``KOSMOS_OLLAMA_DEFAULT_MODEL`` itself when constructor args
        # are omitted, so pass through with no kwargs.
        return OllamaAdapter()

    registry.llm = _boot_llm

    # --- Memory (DozerDbMemoryAdapter, env-gated backends) --------------------
    # Stage 6.5.6 addition (ADR-063): kernel-owned MemoryPort shared by
    # Tektos and future plugins.
    #
    # ``KOSMOS_MEMORY_BACKEND`` selects the graph + temporal backends:
    #   ``in_memory`` (default)  — InMemoryGraphBackend + InMemoryTemporalIndex
    #                              + NoOpAmgPolicy. CI/test-safe, no external
    #                              services required.
    #   ``dozerdb``              — DozerDbGraphBackend + GraphitiTemporalIndex
    #                              + AmgGuardPolicy(tiered). Requires
    #                              ``KOSMOS_DOZERDB_URI``, ``_USER``,
    #                              ``_PASSWORD`` (and optional ``_DATABASE``).
    #                              Graphiti additionally uses
    #                              ``KOSMOS_OLLAMA_BASE_URL``,
    #                              ``KOSMOS_TEKTOS_MODEL`` (LLM) and
    #                              ``KOSMOS_EMBED_MODEL`` (default
    #                              ``nomic-embed-text``).
    @_try("memory")
    def _boot_memory():
        import os

        from adapters.memory.dozerdb.adapter import (
            DozerDbMemoryAdapter,
            InMemoryGraphBackend,
            InMemoryTemporalIndex,
            NoOpAmgPolicy,
        )

        backend = os.environ.get("KOSMOS_MEMORY_BACKEND", "in_memory").lower()

        if backend == "dozerdb":
            uri = os.environ["KOSMOS_DOZERDB_URI"]
            user = os.environ["KOSMOS_DOZERDB_USER"]
            password = os.environ["KOSMOS_DOZERDB_PASSWORD"]
            database = os.environ.get("KOSMOS_DOZERDB_DATABASE", "neo4j")
            # Graphiti calls Ollama via the OpenAI-compat ``/v1`` prefix,
            # not the native Ollama HTTP API root that ``OllamaAdapter``
            # uses. Separate env var so the two callers stay independent.
            llm_url = os.environ.get(
                "KOSMOS_GRAPHITI_LLM_URL", "http://127.0.0.1:11434/v1"
            )
            llm_model = os.environ.get(
                "KOSMOS_OLLAMA_DEFAULT_MODEL", "qwen2.5:32b-instruct-q4_K_M"
            )
            embed_model = os.environ.get(
                "KOSMOS_EMBED_MODEL", "nomic-embed-text"
            )

            from adapters.memory.dozerdb.amg_policy import AmgGuardPolicy
            from adapters.memory.dozerdb.dozerdb_graph_backend import (
                DozerDbGraphBackend,
            )
            from adapters.memory.dozerdb.graphiti_temporal_index import (
                GraphitiTemporalIndex,
            )

            graph = DozerDbGraphBackend(
                uri=uri,
                user=user,
                password=password,
                database=database,
            )
            temporal = GraphitiTemporalIndex(
                uri=uri,
                user=user,
                password=password,
                llm_url=llm_url,
                llm_model=llm_model,
                embed_model=embed_model,
            )
            amg = AmgGuardPolicy(policy_preset="tiered")
            return DozerDbMemoryAdapter(graph=graph, amg=amg, temporal=temporal)

        # Default: in-memory (CI / test / cold-start safe).
        return DozerDbMemoryAdapter(
            graph=InMemoryGraphBackend(),
            amg=NoOpAmgPolicy(),
            temporal=InMemoryTemporalIndex(),
        )

    registry.memory = _boot_memory

    # --- Gnosis boot seeder (ADR-064) ----------------------------------------
    # Env-gated by ``KOSMOS_GNOSIS_SEED=1``. Iterates ``ALL_CORPORA`` and
    # writes every fact through ``MemoryPort.write_event``. Idempotent
    # (re-runs on a populated DB are no-ops via class-name matching).
    # Best-effort: seeder failures do not block boot; Gnosis routes
    # remain functional against whatever facts the graph already contains.
    if os.environ.get("KOSMOS_GNOSIS_SEED", "0") == "1":
        if registry.memory is None:
            registry.errors["gnosis_seed"] = (
                "skipped: memory subsystem is None"
            )
        else:
            try:
                from adapters.memory.dozerdb.corpora import ALL_CORPORA
                from datetime import datetime as _dt, timezone as _tz

                counts: dict[str, int] = {}
                for corpus in ALL_CORPORA:
                    seeded = 0
                    for fact in corpus.facts:
                        try:
                            await registry.memory.write_event(
                                fact.subject,
                                fact.predicate,
                                fact.object_,
                                provenance=fact.provenance,
                                confidence=fact.confidence,
                                attributes={
                                    **fact.attributes,
                                    "corpus_name": corpus.name,
                                    "corpus_event_id": fact.event_id,
                                    "as_of": fact.as_of.isoformat(),
                                },
                            )
                            seeded += 1
                        except Exception as exc:  # noqa: BLE001
                            # Idempotent by class-name matching
                            # (ADR-007). Anything else is a real error.
                            if type(exc).__name__ in _GNOSIS_SEED_IGNORABLE:
                                continue
                            raise
                    counts[corpus.name] = seeded
                registry.gnosis_corpus_counts = counts
                registry.gnosis_last_seeded_at = _dt.now(_tz.utc).isoformat()
            except Exception as exc:  # noqa: BLE001
                registry.errors["gnosis_seed"] = (
                    f"{type(exc).__name__}: {exc}"
                )

    # --- Zetesis plugin mount (ADR-058) ---------------------------------------
    # Depends on frontend_contract having booted; reuses the same
    # KernelFrontendContractAdapter, event_bus, resource, and notification
    # instances so descriptor registration is visible on /api/kernel/plugins
    # and /api/kernel/routes without duplicate state.
    if registry.frontend_contract is None:
        registry.errors["zetesis"] = (
            "zetesis depends on frontend_contract; it failed to boot"
        )
    else:
        try:
            from plugins.zetesis.adapters.real.factory import (
                build_stage_6_5_zetesis_plugin,
            )

            plugin = build_stage_6_5_zetesis_plugin(
                frontend_contract=registry.frontend_contract,
                event_bus=registry.event_bus,
                resource=registry.resource,
                notification=registry.notification,
            )
            await plugin.start()
            registry.zetesis = plugin
        except Exception as exc:  # noqa: BLE001
            registry.errors["zetesis"] = f"{type(exc).__name__}: {exc}"

    # --- Tektos plugin mount + agent singleton (ADR-063) ----------------------
    # Depends on frontend_contract (descriptor registration), llm, memory.
    # Failure of any dependency surfaces under ``registry.errors['tektos']``
    # and returns ``tektos: false`` on ``/health.subsystems`` while keeping
    # the kernel 200 on every other endpoint.
    if (
        registry.frontend_contract is None
        or registry.llm is None
        or registry.memory is None
    ):
        missing = [
            name
            for name, val in (
                ("frontend_contract", registry.frontend_contract),
                ("llm", registry.llm),
                ("memory", registry.memory),
            )
            if val is None
        ]
        registry.errors["tektos"] = (
            f"tektos depends on {missing}; one or more failed to boot"
        )
    else:
        try:
            import asyncio as _asyncio

            from plugins.tektos.agent import TektosAgent
            from plugins.tektos.plugin import TektosPlugin

            tektos_plugin = TektosPlugin(
                frontend_contract_port=registry.frontend_contract,
            )
            await tektos_plugin.start()
            registry.tektos = tektos_plugin
            registry.tektos_agent = TektosAgent(
                llm=registry.llm,
                memory=registry.memory,
            )
            registry.tektos_agent_lock = _asyncio.Lock()
        except Exception as exc:  # noqa: BLE001
            registry.errors["tektos"] = f"{type(exc).__name__}: {exc}"

    # --- Tektos UI sub-app mount (ADR-065, Stage 6.5.8) -----------------------
    # Depends on ``registry.approval`` (ADR-062) + ``registry.memory``
    # (ADR-063) only. Deliberately does NOT depend on ``registry.tektos``
    # (the agent plugin) so the change-approval UI stays reachable during
    # LLM/agent outages — a triage requirement per ADR-065 Option B.
    if registry.approval is None or registry.memory is None:
        missing = [
            name
            for name, val in (
                ("approval", registry.approval),
                ("memory", registry.memory),
            )
            if val is None
        ]
        registry.errors["tektos_ui"] = (
            f"tektos_ui depends on {missing}; one or more failed to boot"
        )
    else:
        try:
            from plugins.tektos.ui.executor import NopExecutor
            from plugins.tektos.ui.server import build_tektos_ui_app

            _tektos_ui_executor = NopExecutor()
            _tektos_ui_app = build_tektos_ui_app(
                approval_resolver=registry.approval,
                memory=registry.memory,
                executor=_tektos_ui_executor,
            )
            registry.tektos_ui = _tektos_ui_app
            registry.tektos_ui_executor = _tektos_ui_executor
            # Guard against duplicate mounts when lifespan is re-entered
            # (TestClient reuses the module-level `app` across many tests).
            if not any(getattr(r, "path", "") == "/tektos-ui" for r in app.routes):
                app.mount("/tektos-ui", _tektos_ui_app)
        except Exception as exc:  # noqa: BLE001
            registry.errors["tektos_ui"] = f"{type(exc).__name__}: {exc}"

    yield

    # Shutdown — stop plugins/engines then close the event bus.
    if registry.tektos is not None:
        try:
            await registry.tektos.stop()
        except Exception:  # noqa: BLE001
            pass

    if registry.llm is not None:
        try:
            await registry.llm.close()
        except Exception:  # noqa: BLE001
            pass

    if registry.zetesis is not None:
        try:
            await registry.zetesis.stop()
        except Exception:  # noqa: BLE001
            pass

    if registry.phrouros is not None:
        try:
            await registry.phrouros.stop()
        except Exception:  # noqa: BLE001
            pass

    if registry.trace_feed is not None:
        try:
            await registry.trace_feed.close()
        except Exception:  # noqa: BLE001
            pass

    if registry.event_bus is not None:
        try:
            await registry.event_bus.close()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Kosmos Kernel", version="6.5.8", lifespan=lifespan)


# ---------------------------------------------------------------------------
# WebSocket event-bus bridge — ADR-061
# ---------------------------------------------------------------------------


WS_DEFAULT_EVENT_TYPES: tuple[str, ...] = (
    "phrouros.anomaly.detected",     # ADR-034
    "zetesis.research.started",      # ADR-056
    "zetesis.research.completed",    # ADR-056
)

_WS_QUEUE_MAXSIZE: int = 256


# ---------------------------------------------------------------------------
# Health + kernel introspection
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok" if not registry.errors else "degraded",
        "boot_errors": registry.errors,
        "subsystems": {
            "notification": registry.notification is not None,
            "frontend_contract": registry.frontend_contract is not None,
            "resource": registry.resource is not None,
            "event_bus": registry.event_bus is not None,
            "approval": registry.approval is not None,
            "phrouros": registry.phrouros is not None,
            "zetesis": registry.zetesis is not None,
            "llm": registry.llm is not None,
            "memory": registry.memory is not None,
            "tektos": registry.tektos is not None,
            "tektos_ui": registry.tektos_ui is not None,
        },
    }

@app.get("/api/kernel/schema")
async def kernel_schema() -> dict[str, Any]:
    fc = registry.frontend_contract
    if fc is None:
        raise HTTPException(503, detail=registry.errors.get("frontend_contract"))
    schema = await fc.render_kernel_schema()
    return _dataclass_to_dict(schema)


@app.get("/api/kernel/routes")
async def kernel_routes() -> list[dict[str, Any]]:
    fc = registry.frontend_contract
    if fc is None:
        raise HTTPException(503, detail=registry.errors.get("frontend_contract"))
    manifest = await fc.get_route_manifest()
    return [_dataclass_to_dict(r) for r in manifest]


@app.get("/api/kernel/panels")
async def kernel_panels() -> list[dict[str, Any]]:
    fc = registry.frontend_contract
    if fc is None:
        raise HTTPException(503, detail=registry.errors.get("frontend_contract"))
    panels = await fc.get_panel_manifest()
    return [_dataclass_to_dict(p) for p in panels]


@app.get("/api/kernel/plugins")
async def kernel_plugins() -> list[dict[str, Any]]:
    fc = registry.frontend_contract
    if fc is None:
        raise HTTPException(503, detail=registry.errors.get("frontend_contract"))
    plugins = await fc.list_plugins()
    return [_dataclass_to_dict(p) for p in plugins]


@app.get("/api/kernel/design-tokens")
async def kernel_design_tokens() -> dict[str, Any]:
    fc = registry.frontend_contract
    if fc is None:
        raise HTTPException(503, detail=registry.errors.get("frontend_contract"))
    return dict(await fc.get_design_tokens())


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


@app.get("/api/resources/balances")
async def resource_balances() -> dict[str, Any]:
    rp = registry.resource
    if rp is None:
        raise HTTPException(503, detail=registry.errors.get("resource"))
    from ports.resource import ResourceKind

    storage = getattr(rp, "_kernel_storage", None)
    out: dict[str, Any] = {}
    for kind in ResourceKind:
        bal = None
        if storage is not None and hasattr(storage, "get_balance"):
            try:
                bal = await storage.get_balance(kind)
            except Exception:
                bal = None
        out[kind.value] = (
            _dataclass_to_dict(bal) if bal is not None else None
        )
    return out


# ADR-066 D2 — resource queue passthrough


@app.get("/api/resources/queue")
async def resource_queue(
    kind: str, n: int = 5
) -> list[dict[str, Any]]:
    rp = registry.resource
    if rp is None:
        raise HTTPException(503, detail=registry.errors.get("resource"))
    from ports.resource import ResourceKind as _RK

    try:
        rk = _RK(kind)
    except ValueError as exc:
        valid = [m.value for m in _RK]
        raise HTTPException(
            400, detail=f"unknown kind {kind!r}; valid: {valid}"
        ) from exc
    if not isinstance(n, int) or n < 1 or n > 100:
        raise HTTPException(400, detail="'n' must be an int in [1, 100]")
    try:
        queued = await rp.peek(rk, n)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            502, detail=f"{type(exc).__name__}: {exc}"
        ) from exc
    return [_dataclass_to_dict(q) for q in queued]


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


@app.get("/api/approvals")
async def approvals_list() -> list[dict[str, Any]]:
    ap = registry.approval
    if ap is None:
        raise HTTPException(503, detail=registry.errors.get("approval"))
    pending = await ap.list_pending()
    return [_dataclass_to_dict(r) for r in pending]


@app.get("/api/approvals/{approval_id}")
async def approval_get(approval_id: str) -> dict[str, Any]:
    ap = registry.approval
    if ap is None:
        raise HTTPException(503, detail=registry.errors.get("approval"))
    try:
        record = await ap.get_by_id(approval_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(404, detail=str(exc)) from exc
    return _dataclass_to_dict(record)


# ADR-062 — approval resolve endpoints


def _resolve_error_status(exc: BaseException) -> int:
    """Map an ``ApprovalResolverPort.resolve`` exception to an HTTP status.

    Class names are matched against Praxis APEX's error hierarchy
    without importing plugin modules from the kernel:

    - ``ApprovalNotFoundError`` → 404
    - ``InvalidTransitionError`` → 409 (already resolved)
    - ``ValueError`` → 400 (reject-without-reason etc.)
    - anything else → 500
    """
    name = type(exc).__name__
    if name == "ApprovalNotFoundError":
        return 404
    if name == "InvalidTransitionError":
        return 409
    if isinstance(exc, ValueError):
        return 400
    return 500


async def _read_optional_json(request: Request) -> dict[str, Any]:
    """Parse an optional JSON body. Empty body → ``{}``. Bad JSON → 400."""
    raw = await request.body()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, detail=f"invalid JSON body: {exc}") from exc
    if not isinstance(payload, dict):
        raise HTTPException(400, detail="body must be a JSON object")
    return payload


@app.post("/api/approvals/{approval_id}/approve")
async def approval_approve(
    approval_id: str, request: Request
) -> dict[str, Any]:
    ap = registry.approval
    if ap is None:
        raise HTTPException(503, detail=registry.errors.get("approval"))
    body = await _read_optional_json(request)

    reason = body.get("reason")
    modifications = body.get("modifications")
    resolved_by = body.get("resolved_by", "user")

    if reason is not None and not isinstance(reason, str):
        raise HTTPException(400, detail="reason must be a string")
    if modifications is not None and not isinstance(modifications, dict):
        raise HTTPException(400, detail="modifications must be a JSON object")
    if not isinstance(resolved_by, str) or not resolved_by.strip():
        raise HTTPException(
            400, detail="resolved_by must be a non-empty string"
        )

    try:
        record = await ap.resolve(
            approval_id,
            True,
            reason=reason,
            modifications=modifications,
            resolved_by=resolved_by,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            _resolve_error_status(exc), detail=str(exc)
        ) from exc
    return _dataclass_to_dict(record)


@app.post("/api/approvals/{approval_id}/reject")
async def approval_reject(
    approval_id: str, request: Request
) -> dict[str, Any]:
    ap = registry.approval
    if ap is None:
        raise HTTPException(503, detail=registry.errors.get("approval"))
    body = await _read_optional_json(request)

    reason = body.get("reason")
    resolved_by = body.get("resolved_by", "user")

    if not isinstance(reason, str) or not reason.strip():
        raise HTTPException(
            400,
            detail="reject requires a non-empty 'reason' field",
        )
    if not isinstance(resolved_by, str) or not resolved_by.strip():
        raise HTTPException(
            400, detail="resolved_by must be a non-empty string"
        )

    try:
        record = await ap.resolve(
            approval_id,
            False,
            reason=reason,
            resolved_by=resolved_by,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            _resolve_error_status(exc), detail=str(exc)
        ) from exc
    return _dataclass_to_dict(record)


# ---------------------------------------------------------------------------
# Tektos — ADR-063
# ---------------------------------------------------------------------------


@app.post("/api/tektos/turn")
async def tektos_turn(request: Request) -> dict[str, Any]:
    """Drive one ``TektosAgent`` iteration.

    Body: ``{"content": <non-empty str>}``. Returns the resulting
    ``TektosStep`` as JSON. Serialized across concurrent requests via
    ``registry.tektos_agent_lock`` so a caller never sees
    ``TektosAgentAlreadyRunError`` from an overlapping request.
    """
    agent = registry.tektos_agent
    lock = registry.tektos_agent_lock
    if agent is None or lock is None:
        raise HTTPException(503, detail=registry.errors.get("tektos"))

    body = await _read_optional_json(request)
    content = body.get("content")
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(
            400, detail="'content' must be a non-empty string"
        )

    async with lock:
        try:
            agent.send_message(content)
            step = await agent.run()
        except ValueError as exc:
            raise HTTPException(400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            # Bubble upstream adapter errors (Ollama unreachable, memory
            # write failure) as 502; the kernel is up but a dependency
            # failed. Class-name check keeps kernel-plugin decoupled.
            name = type(exc).__name__
            if name in {
                "TektosAgentNotStartedError",
                "TektosAgentAlreadyRunError",
                "TektosInvalidConfidenceError",
            }:
                raise HTTPException(400, detail=str(exc)) from exc
            raise HTTPException(502, detail=f"{name}: {exc}") from exc

    return _dataclass_to_dict(step)


# ---------------------------------------------------------------------------
# Gnosis retrieval surrogate — ADR-064
#
# Three read-only routes projecting the kernel-owned ``MemoryPort``
# retrieval surface as ``/api/gnosis/*``. The Gnosis plugin does not
# exist yet (Phase 3 territory); ADR-051 blessed the surrogate pattern
# at the adapter layer and ADR-064 extends it to an HTTP surface so the
# GUI Gnosis tab can render corpus facts + provenance + timestamps
# against real data ahead of ``plugins/gnosis/`` landing.
# ---------------------------------------------------------------------------

import re as _gnosis_re

_GNOSIS_EVENT_ID_RE = _gnosis_re.compile(r"^[A-Za-z0-9._:\-]+$")

# Static manifest of landed corpora. ADR-051 locates corpus loading at
# the adapter fixtures layer, not at a live registry, so the router
# enumerates them here. Updates require the same-day edit to this
# constant when a new corpus lands under ``adapters/memory/dozerdb/corpora/``.
GNOSIS_CORPORA_MANIFEST: list[dict[str, Any]] = [
    {
        "name": "synthetic-lifeline",
        "provenance_predicate": "synthetic-lifeline-v1",
        "summary": "10 hand-authored R.M. Holston lifeline facts (Stage 4.2 DoD anchor).",
        "stage": "4.2",
    },
    {
        "name": "humanities-cidoc-sample",
        "provenance_predicate": "humanities-cidoc-sample-v1",
        "summary": "5 CIDOC-CRM Buddhist text facts; illustrative not scholarly.",
        "stage": "4.2",
    },
    {
        "name": "rigpa-export",
        "provenance_predicate": "rigpa-export-fixture-v1",
        "summary": "Rigpa-LMS JSONL export (fixtures fallback: 20 events 2024-05→2024-12); env-gated by KOSMOS_RIGPA_EXPORT_PATH.",
        "stage": "4.2",
    },
    {
        "name": "superpowers",
        "provenance_predicate": "superpowers-kb",
        "summary": "github.com/obra/superpowers skills at pinned SHA; MIT.",
        "stage": "4.4",
    },
    {
        "name": "humanities-bilara",
        "provenance_predicate": "humanities-bilara",
        "summary": "github.com/suttacentral/bilara-data translations + Pali roots + actors at pinned SHA; CC0-1.0 + public-domain.",
        "stage": "4.5",
    },
]

# Fast lookup: corpus name -> provenance predicate. Used by the query
# route to translate the ``corpus`` filter into a payload-side match.
_GNOSIS_CORPUS_BY_NAME: dict[str, dict[str, Any]] = {
    c["name"]: c for c in GNOSIS_CORPORA_MANIFEST
}

# Idempotent-write error class names (ADR-007 class-name matching).
# ``MemoryWriteBlocked`` is the AMG guard rejection; the neo4j driver
# raises ``ClientError`` for constraint violations. Anything else
# indicates a real seeder failure and gets recorded.
_GNOSIS_SEED_IGNORABLE = frozenset(
    {
        "MemoryWriteBlocked",
        "ClientError",
        "ConstraintValidationFailed",
    }
)


def _gnosis_hit_to_dict(hit: Any) -> dict[str, Any]:
    """Serialize a ``MemoryHit`` for the wire.

    ``as_of`` becomes ISO-8601 or ``None``. Payload is passed through
    verbatim — the adapter layer already sanitizes nested maps via the
    Stage 6.5.6 backend fix.
    """
    as_of = getattr(hit, "as_of", None)
    return {
        "id": getattr(hit, "id", None),
        "payload": getattr(hit, "payload", None),
        "score": getattr(hit, "score", None),
        "as_of": as_of.isoformat() if as_of is not None else None,
    }


@app.get("/api/gnosis/query")
async def gnosis_query(
    q: str,
    as_of: str | None = None,
    limit: int = 20,
    corpus: str | None = None,
) -> dict[str, Any]:
    """Query the temporal graph via ``MemoryPort.query_temporal``.

    Query params:

    - ``q`` — required, non-empty query text.
    - ``as_of`` — optional ISO-8601 timestamp with timezone; when set,
      hits with ``as_of > cutoff`` are filtered by the temporal index.
    - ``limit`` — bounded to ``[1, 100]``; default 20.
    - ``corpus`` — optional corpus name from the manifest; restricts
      hits to facts whose payload ``provenance`` equals the manifest
      ``provenance_predicate`` for that corpus.
    """
    if registry.memory is None:
        raise HTTPException(503, detail=registry.errors.get("memory"))
    if not isinstance(q, str) or not q.strip():
        raise HTTPException(400, detail="'q' must be a non-empty string")
    if not (1 <= limit <= 100):
        raise HTTPException(400, detail="'limit' must be in [1, 100]")

    provenance_filter: str | None = None
    if corpus is not None:
        entry = _GNOSIS_CORPUS_BY_NAME.get(corpus)
        if entry is None:
            raise HTTPException(
                400,
                detail=(
                    f"unknown 'corpus' {corpus!r}; valid: "
                    f"{sorted(_GNOSIS_CORPUS_BY_NAME.keys())}"
                ),
            )
        provenance_filter = entry["provenance_predicate"]

    parsed_as_of = None
    if as_of is not None:
        try:
            from datetime import datetime as _dt

            parsed_as_of = _dt.fromisoformat(as_of)
        except ValueError as exc:
            raise HTTPException(
                400, detail=f"'as_of' must be ISO-8601: {exc}"
            ) from exc
        if parsed_as_of.tzinfo is None:
            raise HTTPException(
                400, detail="'as_of' must be timezone-aware"
            )

    try:
        # When ``corpus`` is set we widen the raw limit aggressively so
        # post-filtering still returns a full page even when the query
        # text ranks a different corpus higher, then clip.
        raw_limit = (
            min(100, max(limit * 10, 50)) if provenance_filter else limit
        )
        hits = await registry.memory.query_temporal(
            q, as_of=parsed_as_of, limit=raw_limit
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        # Upstream adapter failure (Graphiti unreachable, Cypher error).
        # Class-name matching preserves ADR-007.
        raise HTTPException(
            502, detail=f"{type(exc).__name__}: {exc}"
        ) from exc

    if provenance_filter is not None:
        filtered = []
        for h in hits:
            payload = getattr(h, "payload", None) or {}
            # Graphiti dedupes entity edges across episodes, so a hit
            # may span multiple source corpora. Match membership in the
            # plural ``provenances`` set surfaced by the adapter; fall
            # back to the singular ``provenance`` field for adapters
            # that only expose one source.
            provenances = payload.get("provenances") or []
            if not isinstance(provenances, (list, tuple, set)):
                provenances = []
            singular = payload.get("provenance")
            if provenance_filter in provenances or singular == provenance_filter:
                filtered.append(h)
                if len(filtered) >= limit:
                    break
        hits = filtered

    return {"hits": [_gnosis_hit_to_dict(h) for h in hits]}


@app.get("/api/gnosis/corpora")
async def gnosis_corpora() -> dict[str, Any]:
    """Return the manifest of landed corpora with live fact counts (ADR-064).

    ``fact_count`` prefers the seeder count for this boot; when the
    seeder didn't run it degrades to the static corpus size.
    ``last_ingested_at`` is the seeder's UTC ISO timestamp or ``None``.
    """
    # Static fallback counts — corpora sizes at build time.
    try:
        from adapters.memory.dozerdb.corpora import ALL_CORPORA

        static_counts = {c.name: len(c.facts) for c in ALL_CORPORA}
    except Exception:  # noqa: BLE001
        static_counts = {}

    seeded = registry.gnosis_corpus_counts
    out: list[dict[str, Any]] = []
    for entry in GNOSIS_CORPORA_MANIFEST:
        row = dict(entry)
        row["fact_count"] = seeded.get(
            entry["name"], static_counts.get(entry["name"], 0)
        )
        row["last_ingested_at"] = registry.gnosis_last_seeded_at
        out.append(row)
    return {"corpora": out}


@app.get("/api/gnosis/stats")
async def gnosis_stats() -> dict[str, Any]:
    """Return top-line Gnosis dashboard numbers (ADR-064).

    Computed from the static ``ALL_CORPORA`` tuple — not a graph query.
    Safe to call even when memory is down.
    """
    try:
        from adapters.memory.dozerdb.corpora import ALL_CORPORA
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            500, detail=f"corpora import failed: {type(exc).__name__}: {exc}"
        ) from exc

    subjects: set[str] = set()
    predicates: set[str] = set()
    earliest = None
    latest = None
    total = 0
    for corpus in ALL_CORPORA:
        for fact in corpus.facts:
            total += 1
            subjects.add(fact.subject)
            predicates.add(fact.predicate)
            if earliest is None or fact.as_of < earliest:
                earliest = fact.as_of
            if latest is None or fact.as_of > latest:
                latest = fact.as_of

    return {
        "total_facts": total,
        "corpora_count": len(ALL_CORPORA),
        "distinct_subjects": len(subjects),
        "distinct_predicates": len(predicates),
        "earliest_as_of": earliest.isoformat() if earliest else None,
        "latest_as_of": latest.isoformat() if latest else None,
        "seeded_this_boot": dict(registry.gnosis_corpus_counts),
        "last_seeded_at": registry.gnosis_last_seeded_at,
    }


@app.get("/api/gnosis/event/{event_id}")
async def gnosis_event(event_id: str) -> dict[str, Any]:
    """Fetch a single memory event by id.

    ``event_id`` must match ``^[A-Za-z0-9._:-]+$``. Returns the hit's
    ``id`` / ``payload`` / ``score`` / ``as_of`` on success, 404 on
    miss, 400 on malformed id.
    """
    if registry.memory is None:
        raise HTTPException(503, detail=registry.errors.get("memory"))
    if not _GNOSIS_EVENT_ID_RE.match(event_id):
        raise HTTPException(400, detail="malformed 'event_id'")

    try:
        hits = await registry.memory.query_temporal(
            f"event_id:{event_id}", limit=1
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            502, detail=f"{type(exc).__name__}: {exc}"
        ) from exc

    for hit in hits:
        if getattr(hit, "id", None) == event_id:
            return _gnosis_hit_to_dict(hit)
    raise HTTPException(404, detail=f"event {event_id!r} not found")


# ---------------------------------------------------------------------------
# Phrouros anomalies
# ---------------------------------------------------------------------------


@app.get("/api/phrouros/anomalies")
def phrouros_anomalies() -> list[dict[str, Any]]:
    if registry.phrouros is None:
        raise HTTPException(503, detail=registry.errors.get("phrouros"))
    return [_dataclass_to_dict(r) for r in registry.phrouros.list_records()]


# ---------------------------------------------------------------------------
# Zetesis research (SSE) — ADR-060
# ---------------------------------------------------------------------------


_SSE_HEADERS: dict[str, str] = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def _sse_event(event: str, data: Any) -> bytes:
    """Format one SSE frame.

    SSE spec: `event: <name>\n` optional; `data: <payload>\n` required;
    frame terminated by a blank line.
    """
    payload = json.dumps(_dataclass_to_dict(data), ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def _build_research_config(raw: Any) -> Any:
    """Coerce a client-supplied dict into a ``ZetesisResearchConfig``.

    Applied over the plugin's defaults via ``dataclasses.replace``.
    Unknown keys ignored (forward-compat). Invalid coercion raises
    ``ValueError`` — caller maps to 400.
    """
    from plugins.zetesis.plugin import ZetesisResearchConfig
    from ports.resource import PriorityClass

    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("'config' must be a JSON object or omitted")

    valid_fields = {f.name for f in dataclasses.fields(ZetesisResearchConfig)}
    overrides: dict[str, Any] = {}
    for k, v in raw.items():
        if k not in valid_fields:
            continue
        if k == "priority_class" and isinstance(v, str):
            try:
                overrides[k] = PriorityClass[v.upper()]
            except KeyError as exc:
                raise ValueError(
                    f"unknown priority_class {v!r}; "
                    f"valid: {[m.name for m in PriorityClass]}"
                ) from exc
            continue
        if k == "compute_budget":
            try:
                overrides[k] = Decimal(str(v))
            except (InvalidOperation, TypeError) as exc:
                raise ValueError(
                    f"compute_budget must be a number, got {v!r}"
                ) from exc
            continue
        if k in ("fact_anchor_urls", "rubric_lines") and v is not None:
            if not isinstance(v, (list, tuple)):
                raise ValueError(f"{k} must be a list of strings")
            overrides[k] = tuple(str(x) for x in v)
            continue
        overrides[k] = v

    return dataclasses.replace(ZetesisResearchConfig(), **overrides)


@app.post("/api/zetesis/research")
async def zetesis_research(request: Request) -> StreamingResponse:
    if registry.zetesis is None:
        raise HTTPException(503, detail=registry.errors.get("zetesis"))

    # Parse + validate synchronously so validation errors are 400, not
    # mid-stream error events.
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, detail=f"invalid JSON body: {exc}") from exc
    if not isinstance(body, dict):
        raise HTTPException(400, detail="request body must be a JSON object")
    query = body.get("query")
    if not isinstance(query, str) or not query.strip():
        raise HTTPException(400, detail="'query' must be a non-empty string")
    try:
        config = _build_research_config(body.get("config"))
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc

    trial_id = (
        getattr(config, "trial_id", "") or ""
    ).strip() or uuid.uuid4().hex
    # Always ensure the config carries the server-issued trial_id so the
    # plugin echoes it back on `ResearchReport.trial_id`.
    if config is None:
        from plugins.zetesis.plugin import ZetesisResearchConfig
        config = ZetesisResearchConfig(trial_id=trial_id)
    elif getattr(config, "trial_id", "") != trial_id:
        config = dataclasses.replace(config, trial_id=trial_id)

    plugin = registry.zetesis

    async def _stream() -> AsyncIterator[bytes]:
        yield _sse_event(
            "started",
            {
                "query": query,
                "trial_id": trial_id,
            },
        )
        try:
            report = await plugin.research(query, config=config)
        except Exception as exc:  # noqa: BLE001
            yield _sse_event(
                "error",
                {
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "trial_id": trial_id,
                },
            )
            return
        yield _sse_event("completed", report)

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


# ---------------------------------------------------------------------------
# Notification SLO health
# ---------------------------------------------------------------------------


@app.get("/api/notifications/health")
@app.get("/api/notifications/slo")  # ADR-066 D4 alias
async def notification_health() -> dict[str, Any]:
    n = registry.notification
    if n is None:
        raise HTTPException(503, detail=registry.errors.get("notification"))
    try:
        slo = await n.check_delivery_slo()
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    payload = _dataclass_to_dict(slo)
    if not isinstance(payload, dict):
        return {"report": payload}
    return payload


# ADR-066 D1 — notification ack passthrough


@app.post("/api/notifications/{notification_id}/ack")
async def notification_ack(
    notification_id: str, request: Request
) -> dict[str, Any]:
    n = registry.notification
    if n is None:
        raise HTTPException(503, detail=registry.errors.get("notification"))
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, detail=f"invalid JSON body: {exc}") from exc
    if not isinstance(body, dict):
        raise HTTPException(400, detail="body must be a JSON object")
    sub = body.get("subscriber_id")
    if not isinstance(sub, str) or not sub.strip():
        raise HTTPException(
            400, detail="'subscriber_id' must be a non-empty string"
        )
    try:
        acked = await n.ack_receipt(notification_id, sub)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            502, detail=f"{type(exc).__name__}: {exc}"
        ) from exc
    return {"acked": bool(acked)}


# ---------------------------------------------------------------------------
# WebSocket route
# ---------------------------------------------------------------------------


def _parse_ws_types(raw: str | None) -> tuple[str, ...]:
    """Parse the ``?types=a,b,c`` query string.

    Whitespace-tolerant. Empty tokens dropped. Duplicates deduplicated
    while preserving first-seen order.
    """
    if raw is None or not raw.strip():
        return WS_DEFAULT_EVENT_TYPES
    seen: dict[str, None] = {}
    for token in raw.split(","):
        t = token.strip()
        if t:
            seen.setdefault(t, None)
    return tuple(seen.keys()) or WS_DEFAULT_EVENT_TYPES


def _envelope_to_wire(envelope: Any) -> dict[str, Any]:
    """Serialize an :class:`EventEnvelope` for a wire frame."""
    return {
        "frame": "event",
        "envelope": _dataclass_to_dict(envelope),
    }


@app.websocket("/api/events/ws")
async def events_ws(ws: WebSocket) -> None:
    if registry.event_bus is None:
        # Close before accepting; matches WS handshake semantics.
        await ws.close(code=1011, reason="event_bus subsystem down")
        return

    types = _parse_ws_types(ws.query_params.get("types"))
    bus = registry.event_bus

    await ws.accept()
    await ws.send_json({"frame": "ready", "subscribed": list(types)})

    # One queue per event type; one forwarder task per queue.
    queues: list[tuple[str, asyncio.Queue[Any]]] = []
    for t in types:
        q = bus.subscribe(t, maxsize=_WS_QUEUE_MAXSIZE)
        queues.append((t, q))

    async def _forward(q: asyncio.Queue[Any]) -> None:
        while True:
            envelope = await q.get()
            await ws.send_json(_envelope_to_wire(envelope))

    forwarders = [asyncio.create_task(_forward(q)) for _, q in queues]

    async def _drain_client() -> None:
        # Consume (and ignore) client-sent frames so a client `close()`
        # surfaces promptly as `WebSocketDisconnect`.
        while True:
            await ws.receive_text()

    drain = asyncio.create_task(_drain_client())

    try:
        # Wait for any task to finish (usually _drain_client on
        # disconnect); an exception in a forwarder also unblocks here.
        done, pending = await asyncio.wait(
            [*forwarders, drain],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        for task in forwarders + [drain]:
            task.cancel()
    except Exception:  # noqa: BLE001
        for task in forwarders + [drain]:
            task.cancel()
    finally:
        for t, q in queues:
            try:
                bus.unsubscribe(t, q)
            except Exception:  # noqa: BLE001
                pass


# ADR-066 D3 — algedonic WebSocket push channel


class _WebSocketAlgedonicSink:
    """Kernel-scoped :class:`ports.notification.Sink` that forwards
    only algedonic-tier records to a single WebSocket client.

    Non-algedonic tiers are soft-dropped (``return True``) so the port
    doesn't record them as SLO breaches. Transport errors from the
    WebSocket surface as ``return False`` per the ``Sink`` contract.
    """

    def __init__(self, ws: WebSocket) -> None:
        self._ws = ws

    async def deliver(self, record: Any) -> bool:
        # Local import to avoid a top-of-file cycle with the notification
        # port's enum module (kept identical to other route handlers).
        from ports.notification import AlgedonicTier

        tier = getattr(record, "tier", None)
        if tier != AlgedonicTier.ALGEDONIC:
            return True  # soft-drop non-algedonic tiers
        try:
            await self._ws.send_json(
                {
                    "frame": "algedonic",
                    "record": _dataclass_to_dict(record),
                }
            )
        except Exception:  # noqa: BLE001
            return False
        return True

    async def close(self) -> None:
        # WebSocket lifetime is owned by the route handler; nothing to do.
        return None


@app.websocket("/api/algedonic/ws")
async def algedonic_ws(ws: WebSocket) -> None:
    n = registry.notification
    if n is None:
        await ws.close(code=1011, reason="notification subsystem down")
        return

    await ws.accept()
    await ws.send_json({"frame": "ready"})

    sink = _WebSocketAlgedonicSink(ws)
    try:
        n.register_sink(sink)
    except Exception as exc:  # noqa: BLE001
        await ws.close(code=1011, reason=f"sink register failed: {exc}")
        return

    async def _drain_client() -> None:
        # Consume (and ignore) client frames so a client close surfaces
        # promptly as WebSocketDisconnect.
        while True:
            await ws.receive_text()

    drain = asyncio.create_task(_drain_client())
    try:
        await drain
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        pass
    finally:
        drain.cancel()
        try:
            n.unregister_sink(sink)
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dataclass_to_dict(obj: Any) -> Any:
    """Best-effort coerce dataclass / mapping / iterable to JSON-safe dict.

    Handles frozen-slotted dataclasses (no `__dict__`), Decimal, datetime,
    enum, and nested containers. Kosmos value objects are almost all
    `@dataclass(frozen=True, slots=True)` so `dataclasses.fields()` is
    the reliable extraction path.
    """
    import dataclasses
    from decimal import Decimal

    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Decimal):
        return str(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _dataclass_to_dict(getattr(obj, f.name))
            for f in dataclasses.fields(obj)
        }
    if hasattr(obj, "isoformat"):  # datetime / date
        return obj.isoformat()
    if hasattr(obj, "value") and hasattr(obj, "name"):  # enum
        return obj.value
    if isinstance(obj, dict):
        return {str(k): _dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_dataclass_to_dict(v) for v in obj]
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return {
            k: _dataclass_to_dict(v)
            for k, v in vars(obj).items()
            if not k.startswith("_")
        }
    return obj

# --- KOSMOS_STAGE_1_GNOSIS_GATE_MOUNT (ADR-067) ---
# Stage 1 GUI mount: Gnosis Stage 4.6 gate is a distinct ASGI sub-app; every
# other GUI-required endpoint already lives at /api/* on this kernel app.
# See ADR-067 (Stage 1 GUI · kernel_ui_glue superseded).
try:
    from adapters.memory.dozerdb.gate.server import (
        build_stage_46_gate_app as _kosmos_build_stage_46_gate_app,
    )
    from adapters.memory.dozerdb.corpora import ALL_CORPORA as _KOSMOS_ALL_CORPORA

    if not any(getattr(r, "path", "") == "/gnosis-gate" for r in app.routes):
        app.mount("/gnosis-gate", _kosmos_build_stage_46_gate_app(corpora=_KOSMOS_ALL_CORPORA))
except Exception as _kosmos_gate_exc:  # noqa: BLE001
    import logging as _kosmos_logging

    _kosmos_logging.getLogger(__name__).warning(
        "Kosmos Gnosis gate not mounted at /gnosis-gate: %s", _kosmos_gate_exc
    )
# --- END KOSMOS_STAGE_1_GNOSIS_GATE_MOUNT ---
