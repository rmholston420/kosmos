"""FastAPI application factory for the Tektos UI (Stage 3.11, ADR-045).

Six-route surface (Q1e=A) + vendored htmx serve (Q1f=A). The factory
:func:`build_tektos_ui_app` takes the three collaborators it needs:

* :class:`ports.approval.ApprovalResolverPort` \u2014 pending list,
  detail, and Approve leg.
* :class:`ports.memory.MemoryPort` \u2014 per-transition event writes
  (Q5=A).
* :class:`ExecutorPort` \u2014 Execute leg (Q3=A ``NopExecutor`` at
  Stage 3.11; swappable at Stage 3.12).

No dependency on any other plugin (ADR-007) \u2014 the UI only imports
from ``ports`` and its own subpackage.
"""

from __future__ import annotations

import datetime as _dt
from importlib.resources import as_file, files

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

from ports.approval import ApprovalResolverPort
from ports.memory import MemoryPort

from .executor import ExecutorPort, render_unified_diff, compute_diff_sha256
from .models import DiffRender, ExecutionResult
from .policy import (
    TEKTOS_UI_HEALTHZ_PATH,
    TEKTOS_UI_HTMX_JS_PATH,
    TEKTOS_UI_INDEX_PATH,
    TEKTOS_UI_PLAN_APPROVED_PREDICATE,
    TEKTOS_UI_PLAN_APPROVE_PATH,
    TEKTOS_UI_PLAN_DETAIL_PATH,
    TEKTOS_UI_PLAN_DIFF_PATH,
    TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE,
    TEKTOS_UI_PLAN_EXECUTED_PREDICATE,
    TEKTOS_UI_PLAN_EXECUTE_PATH,
    TEKTOS_UI_PROVENANCE,
    TEKTOS_UI_RESOLVED_BY,
    TEKTOS_UI_SUCCESS_CONFIDENCE,
)
from .templates import (
    render_approve_row,
    render_dashboard_index,
    render_diff_fragment,
    render_execute_confirmation,
    render_plan_detail,
)

__all__ = [
    "TEKTOS_UI_PROPOSING_DOMAIN",
    "build_tektos_ui_app",
]


TEKTOS_UI_PROPOSING_DOMAIN: str = "tektos"
"""Value passed to
:meth:`ports.approval.ApprovalResolverPort.list_pending` so the
dashboard shows only Tektos-proposed approvals (Q_res_1=B).

Matches the ``proposing_domain`` field APEX records for every
:meth:`plugins.tektos.plan.render_and_gate_plan_card` invocation
(Stage 3.7, ADR-041)."""


_TEKTOS_INTENTION_ID_PREFIX = "tektos.plan."


def _change_id_from_intention(intention_id: str) -> str:
    """Derive the Tektos ``change_id`` from an ``ApprovalRecord.intention_id``.

    Stage 3.7's :func:`plugins.tektos.renderer.project.render_and_gate_plan_card`
    persists intentions as ``"tektos.plan.<change_id>"`` (see
    ``plugins/tektos/renderer/project.py:163``). Strip the prefix
    when present; return the raw intention id otherwise so the audit
    trail still carries a stable correlation id.
    """
    if intention_id.startswith(_TEKTOS_INTENTION_ID_PREFIX):
        return intention_id[len(_TEKTOS_INTENTION_ID_PREFIX):]
    return intention_id


def _utcnow_iso() -> str:
    """Return the current UTC time as an ISO-8601 string with ``Z``."""
    now = _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")


def _memory_subject(*, change_id: str, approval_id: str) -> str:
    """Compose the MemoryPort ``subject`` string.

    Shape: ``<change_id>::<approval_id>``. Downstream queries locate
    any Execute / Diff leg by either field without a join.
    """
    return f"{change_id}::{approval_id}"


def build_tektos_ui_app(
    *,
    approval_resolver: ApprovalResolverPort,
    memory: MemoryPort,
    executor: ExecutorPort,
) -> FastAPI:
    """Return a fresh FastAPI application wired to the given ports.

    Args:
        approval_resolver: The
            :class:`ports.approval.ApprovalResolverPort` binding
            (typically
            :class:`adapters.approval_resolver.praxis.PraxisApprovalResolverAdapter`
            wrapping the kernel :class:`ApexEngine`).
        memory: The :class:`ports.memory.MemoryPort` binding.
        executor: The :class:`plugins.tektos.ui.executor.ExecutorPort`
            binding. Stage 3.11 uses
            :class:`plugins.tektos.ui.executor.NopExecutor`.

    The returned app has zero global state; passing the same
    collaborators to a second call returns a fresh independent
    application.
    """
    app = FastAPI(title="Kosmos Tektos UI", version="3.11")

    @app.get(TEKTOS_UI_INDEX_PATH, response_class=HTMLResponse)
    async def _index() -> HTMLResponse:
        records = await approval_resolver.list_pending(
            proposing_domain=TEKTOS_UI_PROPOSING_DOMAIN,
        )
        return HTMLResponse(render_dashboard_index(records))

    @app.get(TEKTOS_UI_PLAN_DETAIL_PATH, response_class=HTMLResponse)
    async def _plan_detail(approval_id: str) -> HTMLResponse:
        try:
            record = await approval_resolver.get_by_id(approval_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return HTMLResponse(render_plan_detail(record))

    @app.post(TEKTOS_UI_PLAN_APPROVE_PATH, response_class=HTMLResponse)
    async def _plan_approve(approval_id: str) -> HTMLResponse:
        try:
            record = await approval_resolver.resolve(
                approval_id,
                True,
                resolved_by=TEKTOS_UI_RESOLVED_BY,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        change_id = _change_id_from_intention(record.intention_id)
        await memory.write_event(
            _memory_subject(
                change_id=change_id,
                approval_id=record.approval_id,
            ),
            TEKTOS_UI_PLAN_APPROVED_PREDICATE,
            record.status.value,
            provenance=TEKTOS_UI_PROVENANCE,
            confidence=TEKTOS_UI_SUCCESS_CONFIDENCE,
            attributes={
                "approval_id": record.approval_id,
                "change_id": change_id,
                "resolved_by": TEKTOS_UI_RESOLVED_BY,
                "resolved_at": _utcnow_iso(),
            },
        )
        return HTMLResponse(render_approve_row(record))

    @app.post(TEKTOS_UI_PLAN_EXECUTE_PATH, response_class=HTMLResponse)
    async def _plan_execute(approval_id: str) -> HTMLResponse:
        try:
            record = await approval_resolver.get_by_id(approval_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        change_id = _change_id_from_intention(record.intention_id)
        result: ExecutionResult = await executor.execute(
            approval_id=record.approval_id,
            change_id=change_id,
        )
        await memory.write_event(
            _memory_subject(
                change_id=result.change_id,
                approval_id=result.approval_id,
            ),
            TEKTOS_UI_PLAN_EXECUTED_PREDICATE,
            result.diff_sha256,
            provenance=TEKTOS_UI_PROVENANCE,
            confidence=TEKTOS_UI_SUCCESS_CONFIDENCE,
            attributes={
                "approval_id": result.approval_id,
                "change_id": result.change_id,
                "diff_sha256": result.diff_sha256,
                "executed_at": _utcnow_iso(),
            },
        )
        return HTMLResponse(
            render_execute_confirmation(
                approval_id=result.approval_id,
                diff_sha256=result.diff_sha256,
            )
        )

    @app.get(TEKTOS_UI_PLAN_DIFF_PATH, response_class=HTMLResponse)
    async def _plan_diff(approval_id: str) -> HTMLResponse:
        try:
            record = await approval_resolver.get_by_id(approval_id)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        change_id = _change_id_from_intention(record.intention_id)
        # Stage 3.11: NopExecutor snapshot; identical to the Execute leg.
        result = await executor.execute(
            approval_id=record.approval_id,
            change_id=change_id,
        )
        body = render_unified_diff(before=result.before, after=result.after)
        diff = DiffRender(
            approval_id=result.approval_id,
            change_id=result.change_id,
            body=body,
            diff_sha256=compute_diff_sha256(body),
        )
        await memory.write_event(
            _memory_subject(
                change_id=diff.change_id,
                approval_id=diff.approval_id,
            ),
            TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE,
            diff.diff_sha256,
            provenance=TEKTOS_UI_PROVENANCE,
            confidence=TEKTOS_UI_SUCCESS_CONFIDENCE,
            attributes={
                "approval_id": diff.approval_id,
                "change_id": diff.change_id,
                "diff_sha256": diff.diff_sha256,
                "rendered_at": _utcnow_iso(),
            },
        )
        return HTMLResponse(render_diff_fragment(diff))

    @app.get(TEKTOS_UI_HEALTHZ_PATH, response_class=PlainTextResponse)
    async def _healthz() -> PlainTextResponse:
        return PlainTextResponse("ok")

    @app.get(TEKTOS_UI_HTMX_JS_PATH)
    async def _htmx_js() -> Response:
        resource = files("plugins.tektos.ui").joinpath("htmx.min.js")
        with as_file(resource) as path:
            data = path.read_bytes()
        return Response(
            content=data,
            media_type="application/javascript",
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    return app
