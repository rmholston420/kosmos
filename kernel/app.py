"""Kosmos kernel FastAPI app (Stage 6.5.5 — approval resolve endpoints).

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
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
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

    yield

    # Shutdown — stop plugins/engines then close the event bus.
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

app = FastAPI(title="Kosmos Kernel", version="6.5.5", lifespan=lifespan)


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
