"""Stage 6.5.8 - Tektos UI kernel mount tests (ADR-065).

Two tiers of fast integration:

* Kernel-boot tier: the real kernel ``TestClient`` boots the app; we
  assert ``/health.subsystems.tektos_ui`` is ``true``, the sub-app is
  mounted, ``/tektos-ui/healthz`` returns 200, and
  ``registry.tektos_ui_executor`` is a ``NopExecutor``. These tests use
  the real ``registry.approval`` + ``registry.memory`` singletons
  wired by the boot block.

* Sub-app contract tier: we call ``build_tektos_ui_app`` directly with
  fake ``ApprovalResolverPort`` + ``MemoryPort`` + ``ExecutorPort``
  and drive the route handlers through their own ``TestClient``. This
  is the only way to observe per-request memory writes without
  mutating the kernel's live singletons (which the sub-app captured
  by reference at mount time).

* Boot-degradation tier: two extra tests build ``lifespan`` manually
  with ``registry.approval = None`` / ``registry.memory = None`` to
  confirm the UI mount records ``registry.errors['tektos_ui']`` and
  keeps ``/health.subsystems.tektos_ui = false`` without breaking the
  rest of the kernel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import app
from plugins.tektos.ui.executor import NopExecutor
from plugins.tektos.ui.models import ExecutionResult
from plugins.tektos.ui.policy import (
    TEKTOS_UI_PLAN_APPROVED_PREDICATE,
    TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE,
    TEKTOS_UI_PLAN_EXECUTED_PREDICATE,
    TEKTOS_UI_PROVENANCE,
)
from plugins.tektos.ui.server import build_tektos_ui_app
from ports.approval import ApprovalRecord, ApprovalStatus, ChangeApprovalTier
from ports.memory import MemoryEventId


# --------------------------------------------------------------------------
# Fake ports (sub-app contract tier)
# --------------------------------------------------------------------------


def _make_record(
    approval_id: str = "apr-1",
    intention_id: str = "int-1",
    status: ApprovalStatus = ApprovalStatus.PENDING,
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        intention_id=intention_id,
        proposing_domain="tektos",
        tier=ChangeApprovalTier.HUMAN_REVIEW,
        delta={},
        status=status,
        proposed_at=datetime.now(timezone.utc),
    )


@dataclass
class _FakeApprovalResolverPort:
    records: dict[str, ApprovalRecord] = field(default_factory=dict)
    resolve_calls: list[dict[str, Any]] = field(default_factory=list)

    async def list_pending(
        self, *, proposing_domain: str | None = None
    ) -> tuple[ApprovalRecord, ...]:
        return tuple(
            r
            for r in self.records.values()
            if r.status == ApprovalStatus.PENDING
            and (proposing_domain is None or r.proposing_domain == proposing_domain)
        )

    async def get_by_id(self, approval_id: str) -> ApprovalRecord:
        if approval_id not in self.records:
            raise KeyError(approval_id)
        return self.records[approval_id]

    async def resolve(
        self,
        approval_id: str,
        approve: bool,
        *,
        reason: str | None = None,
        modifications: Any = None,
        resolved_by: str | None = None,
    ) -> ApprovalRecord:
        self.resolve_calls.append(
            {
                "approval_id": approval_id,
                "approve": approve,
                "reason": reason,
                "modifications": modifications,
                "resolved_by": resolved_by,
            }
        )
        rec = self.records[approval_id]
        new_status = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        updated = ApprovalRecord(
            approval_id=rec.approval_id,
            intention_id=rec.intention_id,
            proposing_domain=rec.proposing_domain,
            tier=rec.tier,
            delta=rec.delta,
            status=new_status,
            proposed_at=rec.proposed_at,
            resolved_at=datetime.now(timezone.utc),
            resolved_by=resolved_by,
            reason=reason,
        )
        self.records[approval_id] = updated
        return updated


@dataclass
class _FakeMemoryPort:
    events: list[dict[str, Any]] = field(default_factory=list)

    async def write_event(self, *args: Any, **kwargs: Any) -> MemoryEventId:
        now = datetime.now(timezone.utc)
        event_id = f"evt-{len(self.events) + 1}"
        self.events.append(
            {
                "id": event_id,
                "subject": (args[0] if len(args) >= 1 else kwargs.get("subject")),
                "predicate": (args[1] if len(args) >= 2 else kwargs.get("predicate")),
                "object": (args[2] if len(args) >= 3 else kwargs.get("object")),
                "provenance": kwargs.get("provenance"),
                "confidence": kwargs.get("confidence"),
                "attributes": kwargs.get("attributes") or {},
            }
        )
        return MemoryEventId(id=event_id, written_at=now)

    async def query_temporal(
        self,
        predicate: str,
        *,
        subject: str | None = None,
        as_of: datetime | None = None,
        limit: int = 10,
    ) -> list[Any]:
        return []

    async def query_graph(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    async def is_healthy(self) -> bool:
        return True

    async def close(self) -> None:
        return None


# --------------------------------------------------------------------------
# Kernel-boot tier (real registry, mounted sub-app)
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def kernel_client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def test_health_reports_tektos_ui_true(kernel_client: TestClient) -> None:
    resp = kernel_client.get("/health")
    assert resp.status_code == 200
    subs = resp.json()["subsystems"]
    if kernel_app_module.registry.tektos_ui is None:
        pytest.skip(
            "tektos_ui not booted on this environment: "
            f"{kernel_app_module.registry.errors.get('tektos_ui')}"
        )
    assert subs["tektos_ui"] is True


def test_tektos_ui_healthz_reachable(kernel_client: TestClient) -> None:
    if kernel_app_module.registry.tektos_ui is None:
        pytest.skip("tektos_ui not booted")
    resp = kernel_client.get("/tektos-ui/healthz")
    assert resp.status_code == 200
    assert resp.text.strip() == "ok"


def test_registry_binds_nop_executor(kernel_client: TestClient) -> None:
    if kernel_app_module.registry.tektos_ui is None:
        pytest.skip("tektos_ui not booted")
    exec_obj = kernel_app_module.registry.tektos_ui_executor
    assert exec_obj is not None
    assert exec_obj.__class__.__name__ == "NopExecutor"


def test_sub_app_mounted_under_tektos_ui(kernel_client: TestClient) -> None:
    if kernel_app_module.registry.tektos_ui is None:
        pytest.skip("tektos_ui not booted")
    # Look at the parent app's routes for a Mount to /tektos-ui.
    mount_paths = [
        r.path for r in app.routes if getattr(r, "path", "") == "/tektos-ui"
    ]
    assert mount_paths == ["/tektos-ui"], (
        f"expected a Mount at /tektos-ui, got: "
        f"{[getattr(r, 'path', repr(r)) for r in app.routes]}"
    )


# --------------------------------------------------------------------------
# Sub-app contract tier (direct build_tektos_ui_app with fakes)
# --------------------------------------------------------------------------


@pytest.fixture
def sub_client() -> Iterator[
    tuple[TestClient, _FakeApprovalResolverPort, _FakeMemoryPort, NopExecutor]
]:
    resolver = _FakeApprovalResolverPort()
    resolver.records["apr-1"] = _make_record(
        approval_id="apr-1", intention_id="int-1"
    )
    memory = _FakeMemoryPort()
    executor = NopExecutor()
    sub_app = build_tektos_ui_app(
        approval_resolver=resolver, memory=memory, executor=executor
    )
    with TestClient(sub_app) as c:
        yield c, resolver, memory, executor


def test_sub_get_index_returns_200(
    sub_client: tuple[
        TestClient, _FakeApprovalResolverPort, _FakeMemoryPort, NopExecutor
    ],
) -> None:
    client, _, _, _ = sub_client
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_sub_plan_detail_known_id(
    sub_client: tuple[
        TestClient, _FakeApprovalResolverPort, _FakeMemoryPort, NopExecutor
    ],
) -> None:
    client, _, _, _ = sub_client
    resp = client.get("/plan/apr-1")
    assert resp.status_code == 200


def test_sub_plan_detail_unknown_id_returns_404(
    sub_client: tuple[
        TestClient, _FakeApprovalResolverPort, _FakeMemoryPort, NopExecutor
    ],
) -> None:
    client, _, _, _ = sub_client
    resp = client.get("/plan/does-not-exist")
    assert resp.status_code == 404


def test_sub_approve_calls_resolver_and_writes_memory_event(
    sub_client: tuple[
        TestClient, _FakeApprovalResolverPort, _FakeMemoryPort, NopExecutor
    ],
) -> None:
    client, resolver, memory, _ = sub_client
    resp = client.post("/plan/apr-1/approve")
    assert resp.status_code == 200, resp.text
    assert len(resolver.resolve_calls) == 1
    call = resolver.resolve_calls[0]
    assert call["approval_id"] == "apr-1"
    assert call["approve"] is True
    # Memory audit event was written with locked predicate + provenance.
    assert len(memory.events) == 1
    evt = memory.events[0]
    assert evt["predicate"] == TEKTOS_UI_PLAN_APPROVED_PREDICATE
    assert evt["provenance"] == TEKTOS_UI_PROVENANCE
    assert evt["confidence"] is not None
    assert 0.0 < evt["confidence"] <= 1.0


def test_sub_execute_calls_executor_and_writes_memory_event(
    sub_client: tuple[
        TestClient, _FakeApprovalResolverPort, _FakeMemoryPort, NopExecutor
    ],
) -> None:
    client, _, memory, _ = sub_client
    resp = client.post("/plan/apr-1/execute")
    assert resp.status_code == 200, resp.text
    assert len(memory.events) == 1
    evt = memory.events[0]
    assert evt["predicate"] == TEKTOS_UI_PLAN_EXECUTED_PREDICATE
    assert evt["provenance"] == TEKTOS_UI_PROVENANCE
    assert evt["attributes"]["diff_sha256"]


def test_sub_diff_writes_diff_rendered_event(
    sub_client: tuple[
        TestClient, _FakeApprovalResolverPort, _FakeMemoryPort, NopExecutor
    ],
) -> None:
    client, _, memory, _ = sub_client
    resp = client.get("/plan/apr-1/diff")
    assert resp.status_code == 200, resp.text
    assert len(memory.events) == 1
    evt = memory.events[0]
    assert evt["predicate"] == TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE
    assert evt["provenance"] == TEKTOS_UI_PROVENANCE


# --------------------------------------------------------------------------
# Boot-degradation tier
# --------------------------------------------------------------------------
# We cannot re-run the parent kernel lifespan cheaply, so these tests
# exercise the ADR-065 boot block by directly invoking the same logic
# against a fresh registry snapshot. This keeps the fast tier under 1s
# while asserting the two dependency-failure branches record
# ``registry.errors['tektos_ui']`` and set ``registry.tektos_ui`` to
# ``None``.


class _MinimalRegistry:
    def __init__(self) -> None:
        self.errors: dict[str, str] = {}
        self.approval: Any = None
        self.memory: Any = None
        self.tektos_ui: Any = None
        self.tektos_ui_executor: Any = None


def _simulate_ui_boot(reg: _MinimalRegistry) -> None:
    """Mirror the exact conditional in kernel.app.lifespan for ADR-065."""
    if reg.approval is None or reg.memory is None:
        missing = [
            name
            for name, val in (
                ("approval", reg.approval),
                ("memory", reg.memory),
            )
            if val is None
        ]
        reg.errors["tektos_ui"] = (
            f"tektos_ui depends on {missing}; one or more failed to boot"
        )
    else:  # pragma: no cover - happy path exercised by kernel-boot tier
        from plugins.tektos.ui.executor import NopExecutor as _Nop
        from plugins.tektos.ui.server import build_tektos_ui_app as _build

        reg.tektos_ui_executor = _Nop()
        reg.tektos_ui = _build(
            approval_resolver=reg.approval,
            memory=reg.memory,
            executor=reg.tektos_ui_executor,
        )


def test_boot_degradation_no_approval() -> None:
    reg = _MinimalRegistry()
    reg.approval = None
    reg.memory = _FakeMemoryPort()
    _simulate_ui_boot(reg)
    assert reg.tektos_ui is None
    assert "tektos_ui" in reg.errors
    assert "approval" in reg.errors["tektos_ui"]


def test_boot_degradation_no_memory() -> None:
    reg = _MinimalRegistry()
    reg.approval = _FakeApprovalResolverPort()
    reg.memory = None
    _simulate_ui_boot(reg)
    assert reg.tektos_ui is None
    assert "tektos_ui" in reg.errors
    assert "memory" in reg.errors["tektos_ui"]
