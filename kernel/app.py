"""Kosmos kernel FastAPI application — Stage 6.4 landing.

Boots against REAL adapter constructors discovered by audit of
rmholston420/kosmos @ main. Every subsystem bootstraps behind a
try/except so a single failure does not brick the kernel — failing
subsystems return 503 with the exception text under their route.

Endpoints wired at 6.4:
  GET /health
  GET /api/kernel/schema
  GET /api/kernel/routes
  GET /api/kernel/panels
  GET /api/kernel/plugins
  GET /api/kernel/design-tokens
  GET /api/resources/balances
  GET /api/approvals
  GET /api/approvals/{approval_id}
  GET /api/phrouros/anomalies
  GET /api/notifications/health

Zetesis plugin remains NOT registered at boot — it requires 10 live
ports and its own start(). It lands via a follow-up mount PR when
memory/vector/observability backends are provisioned on Colossus.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

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

    # --- Phrouros (best-effort — needs TraceFeedPort we don't wire yet) ------
    # We intentionally skip PhrourosEngine at 6.4 boot: it requires a real
    # TraceFeedPort adapter which is not yet in adapters/. Anomalies endpoint
    # returns 503 until Stage 6.5.
    registry.errors["phrouros"] = (
        "PhrourosEngine not wired at 6.4 — TraceFeedPort adapter not yet "
        "provisioned. See ADR-046."
    )

    yield

    # Shutdown — event bus is the only adapter needing explicit close
    if registry.event_bus is not None:
        try:
            await registry.event_bus.close()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Kosmos Kernel", version="6.4.0", lifespan=lifespan)


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


# ---------------------------------------------------------------------------
# Phrouros anomalies
# ---------------------------------------------------------------------------


@app.get("/api/phrouros/anomalies")
def phrouros_anomalies() -> list[dict[str, Any]]:
    if registry.phrouros is None:
        raise HTTPException(503, detail=registry.errors.get("phrouros"))
    return [_dataclass_to_dict(r) for r in registry.phrouros.list_records()]


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
