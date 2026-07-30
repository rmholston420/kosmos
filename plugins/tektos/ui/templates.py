"""HTML fragment rendering for the Tektos UI (Stage 3.11, ADR-045).

Pure-Python string templates \u2014 no jinja / mako / any template
engine. Kosmos owns every character emitted to the browser. Each
public function is one HTML fragment; the server routes concatenate
fragments into full responses.

All user-supplied strings (approval id, change id, diff body) are
escaped via :func:`html.escape` before interpolation. The vendored
HTMX runtime executes only server-emitted HTML, but escaping is a
non-negotiable defense-in-depth line.
"""

from __future__ import annotations

from collections.abc import Iterable
from html import escape

from ports.approval import ApprovalRecord

from .models import DiffRender
from .policy import (
    TEKTOS_UI_HTMX_JS_PATH,
    TEKTOS_UI_INDEX_PATH,
    TEKTOS_UI_PLAN_APPROVE_PATH,
    TEKTOS_UI_PLAN_DETAIL_PATH,
    TEKTOS_UI_PLAN_DIFF_PATH,
    TEKTOS_UI_PLAN_EXECUTE_PATH,
)

__all__ = [
    "render_dashboard_index",
    "render_diff_fragment",
    "render_execute_confirmation",
    "render_pending_row",
    "render_plan_detail",
]


_INDEX_SHELL = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Kosmos Tektos Dashboard</title>
    <script src="{htmx_src}"></script>
    <style>
      body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
      table {{ border-collapse: collapse; width: 100%; }}
      th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #ddd; }}
      pre {{ background: #f4f4f4; padding: 0.75rem; overflow-x: auto; }}
      .empty {{ color: #666; font-style: italic; }}
    </style>
  </head>
  <body>
    <h1>Tektos plan approvals</h1>
    <p>
      Stage 3.11 dashboard \u2014 Plan \u2192 Approve \u2192 Execute \u2192 Diff.
      Every action stamps a MemoryPort event with
      <code>provenance=&quot;tektos_ui&quot;</code>.
    </p>
    <table id="pending-plans">
      <thead>
        <tr>
          <th>Approval ID</th>
          <th>Change ID</th>
          <th>Tier</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </body>
</html>
"""


_EMPTY_ROW = (
    '<tr><td colspan="5" class="empty">'
    "No pending Tektos-proposed approvals."
    "</td></tr>"
)


def _detail_url(approval_id: str) -> str:
    return TEKTOS_UI_PLAN_DETAIL_PATH.format(approval_id=approval_id)


def _approve_url(approval_id: str) -> str:
    return TEKTOS_UI_PLAN_APPROVE_PATH.format(approval_id=approval_id)


def _execute_url(approval_id: str) -> str:
    return TEKTOS_UI_PLAN_EXECUTE_PATH.format(approval_id=approval_id)


def _diff_url(approval_id: str) -> str:
    return TEKTOS_UI_PLAN_DIFF_PATH.format(approval_id=approval_id)


_TEKTOS_INTENTION_PREFIX = "tektos.plan."


def _change_id_from_intention(intention_id: str) -> str:
    if intention_id.startswith(_TEKTOS_INTENTION_PREFIX):
        return intention_id[len(_TEKTOS_INTENTION_PREFIX):]
    return intention_id


def render_pending_row(record: ApprovalRecord) -> str:
    """Render one ``<tr>`` for the dashboard index table."""
    approval_id = escape(str(record.approval_id))
    change_id = escape(_change_id_from_intention(record.intention_id))
    tier = escape(record.tier.value)
    status = escape(record.status.value)
    detail_url = escape(_detail_url(approval_id))
    approve_url = escape(_approve_url(approval_id))
    return (
        f'<tr id="row-{approval_id}">'
        f"<td>{approval_id}</td>"
        f"<td>{change_id}</td>"
        f"<td>{tier}</td>"
        f"<td>{status}</td>"
        f"<td>"
        f'<a href="{detail_url}">detail</a> '
        f'<button hx-post="{approve_url}" '
        f'hx-target="#row-{approval_id}" hx-swap="outerHTML">'
        f"approve</button>"
        f"</td>"
        f"</tr>"
    )


def render_dashboard_index(records: Iterable[ApprovalRecord]) -> str:
    """Render the full HTML shell for ``GET /`` (Q1e=A)."""
    rendered_rows = [render_pending_row(r) for r in records]
    body = "".join(rendered_rows) if rendered_rows else _EMPTY_ROW
    return _INDEX_SHELL.format(
        htmx_src=escape(TEKTOS_UI_HTMX_JS_PATH),
        rows=body,
    )


def render_plan_detail(record: ApprovalRecord) -> str:
    """Render the ``GET /plan/{approval_id}`` fragment.

    Kept as an HTML fragment (no ``<html>`` shell) so HTMX can target
    the response into an existing dashboard slot. The interactive tier
    also loads it standalone; browsers render orphan fragments fine.
    """
    approval_id = escape(str(record.approval_id))
    change_id = escape(_change_id_from_intention(record.intention_id))
    tier = escape(record.tier.value)
    status = escape(record.status.value)
    approve_url = escape(_approve_url(approval_id))
    execute_url = escape(_execute_url(approval_id))
    diff_url = escape(_diff_url(approval_id))
    index_url = escape(TEKTOS_UI_INDEX_PATH)
    return (
        f'<section id="plan-detail-{approval_id}">'
        f"<h2>Plan approval <code>{approval_id}</code></h2>"
        f"<dl>"
        f"<dt>Change ID</dt><dd>{change_id}</dd>"
        f"<dt>Tier</dt><dd>{tier}</dd>"
        f"<dt>Status</dt><dd id=\"status-{approval_id}\">{status}</dd>"
        f"</dl>"
        f'<button hx-post="{approve_url}" '
        f'hx-target="#status-{approval_id}" hx-swap="innerHTML">'
        f"approve</button> "
        f'<button hx-post="{execute_url}" '
        f'hx-target="#exec-{approval_id}" hx-swap="innerHTML">'
        f"execute</button> "
        f'<button hx-get="{diff_url}" '
        f'hx-target="#diff-{approval_id}" hx-swap="innerHTML">'
        f"diff</button>"
        f'<div id="exec-{approval_id}"></div>'
        f'<div id="diff-{approval_id}"></div>'
        f'<p><a href="{index_url}">back to dashboard</a></p>'
        f"</section>"
    )


def render_execute_confirmation(*, approval_id: str, diff_sha256: str) -> str:
    """Render the ``POST /plan/{approval_id}/execute`` response fragment."""
    approval_id_e = escape(str(approval_id))
    diff_sha256_e = escape(str(diff_sha256))
    return (
        f'<p id="exec-body-{approval_id_e}">'
        f"Executed \u2014 diff sha256 <code>{diff_sha256_e}</code>."
        f"</p>"
    )


def render_diff_fragment(diff: DiffRender) -> str:
    """Render the ``GET /plan/{approval_id}/diff`` response fragment."""
    approval_id = escape(str(diff.approval_id))
    body = escape(diff.body) if diff.body else "(no changes)"
    diff_sha256 = escape(str(diff.diff_sha256))
    return (
        f'<div id="diff-body-{approval_id}">'
        f"<h3>Unified diff</h3>"
        f"<pre>{body}</pre>"
        f"<p>sha256 <code>{diff_sha256}</code></p>"
        f"</div>"
    )


def render_approve_row(record: ApprovalRecord) -> str:
    """Render the row-replacement fragment for HTMX after approve.

    Same shape as :func:`render_pending_row` but updated status.
    HTMX targets this fragment via ``hx-target="#row-{approval_id}"``
    and ``hx-swap="outerHTML"``.
    """
    return render_pending_row(record)


__all__.append("render_approve_row")
