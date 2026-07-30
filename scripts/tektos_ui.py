"""Kernel runner for the Tektos UI (Stage 3.11, ADR-045).

Boots the real uvicorn server against ``127.0.0.1:8765`` with an
in-memory Praxis :class:`ApexEngine` + fake MemoryPort. Interactive
tier only \u2014 the fast unit tier uses FastAPI ``TestClient``
in-process (no port binding). Run via ``make ui-serve``.

Not part of the Stage 3.11 DoD literal test. The
``KOSMOS_STAGE_311_INTERACTIVE=1`` test path in
``plugins/tektos/tests/test_tektos_ui.py`` spawns this script as a
subprocess to verify the port binds.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from typing import Any

import uvicorn

from adapters.approval_resolver.praxis import PraxisApprovalResolverAdapter
from plugins.praxis.apex.engine import KernelChangeApprovalAdapter
from plugins.praxis.apex.scheduler import FakeScheduler
from plugins.praxis.apex.storage import InMemoryStorage
from plugins.tektos.ui import (
    NopExecutor,
    TEKTOS_UI_HOST,
    TEKTOS_UI_PORT,
    build_tektos_ui_app,
)
from ports.approval import ChangeApprovalTier
from ports.memory import MemoryEventId


class _StdoutMemory:
    """Print-only :class:`ports.memory.MemoryPort` fake for interactive tier."""

    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> MemoryEventId:
        print(
            f"[memory] {subject} :: {predicate} :: {object} "
            f"provenance={provenance} confidence={confidence} "
            f"attributes={attributes}",
            file=sys.stderr,
            flush=True,
        )
        return "mem-interactive"

    async def query_temporal(self, *args: Any, **kwargs: Any) -> Any:
        return ()


class _NullEventBus:
    async def publish(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None


class _NullNotification:
    async def notify(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None


async def _seed_apex(engine: KernelChangeApprovalAdapter) -> None:
    """Seed one Tektos-proposed pending approval so the UI shows a row."""
    from plugins.praxis.apex.models import Intention

    now = datetime.now(timezone.utc)
    intention = Intention(
        id="tektos.plan.add-dark-mode",
        subject="tektos:add-dark-mode",
        target_trajectory={"summary": "add dark mode"},
        current_state={},
        owning_domain="tektos",
        change_approval_tier=ChangeApprovalTier.HUMAN_REVIEW,
        created_at=now,
        updated_at=now,
    )
    await engine.register_intention(intention)
    await engine.propose(
        intention.id,
        {"summary": "swap default palette"},
        ChangeApprovalTier.HUMAN_REVIEW,
        proposing_domain="tektos",
        diff_preview={"human": "swap default palette to dark"},
    )


def main() -> None:
    storage = InMemoryStorage()
    scheduler = FakeScheduler()
    engine = KernelChangeApprovalAdapter(
        storage=storage,
        scheduler=scheduler,
        event_bus=_NullEventBus(),
        notification=_NullNotification(),
    )
    asyncio.run(_seed_apex(engine))
    resolver = PraxisApprovalResolverAdapter(engine)
    memory = _StdoutMemory()
    app = build_tektos_ui_app(
        approval_resolver=resolver,
        memory=memory,
        executor=NopExecutor(),
    )
    uvicorn.run(app, host=TEKTOS_UI_HOST, port=TEKTOS_UI_PORT, log_level="info")


if __name__ == "__main__":
    main()
