"""Locked constants for the Tektos UI HTMX dashboard (Stage 3.11, ADR-045).

Every value here is load-bearing on ADR-045 and the Stage 3.11 DoD
literal test. Do not tweak without an ADR-045 amendment.
"""

from __future__ import annotations

__all__ = [
    "TEKTOS_UI_HEALTHZ_PATH",
    "TEKTOS_UI_HOST",
    "TEKTOS_UI_HTMX_JS_PATH",
    "TEKTOS_UI_HTMX_SHA256",
    "TEKTOS_UI_HTMX_UPSTREAM_COMMIT",
    "TEKTOS_UI_HTMX_UPSTREAM_LICENSE",
    "TEKTOS_UI_HTMX_UPSTREAM_REPO",
    "TEKTOS_UI_HTMX_VERSION",
    "TEKTOS_UI_INDEX_PATH",
    "TEKTOS_UI_MAX_CONFIDENCE",
    "TEKTOS_UI_MIN_CONFIDENCE",
    "TEKTOS_UI_PLAN_APPROVED_PREDICATE",
    "TEKTOS_UI_PLAN_APPROVE_PATH",
    "TEKTOS_UI_PLAN_DETAIL_PATH",
    "TEKTOS_UI_PLAN_DIFF_PATH",
    "TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE",
    "TEKTOS_UI_PLAN_EXECUTED_PREDICATE",
    "TEKTOS_UI_PLAN_EXECUTE_PATH",
    "TEKTOS_UI_PORT",
    "TEKTOS_UI_PROVENANCE",
    "TEKTOS_UI_RESOLVED_BY",
    "TEKTOS_UI_ROUTE_ICON",
    "TEKTOS_UI_ROUTE_LABEL",
    "TEKTOS_UI_ROUTE_LAZY_MODULE",
    "TEKTOS_UI_ROUTE_PATH",
    "TEKTOS_UI_SUCCESS_CONFIDENCE",
    "confidence_for_ui_event",
]


# ── Provenance + audit ─────────────────────────────────────────────────────

TEKTOS_UI_PROVENANCE: str = "tektos_ui"
"""MemoryPort ``provenance`` field for every UI-driven event (ADR-008)."""

TEKTOS_UI_RESOLVED_BY: str = "tektos_ui"
"""``resolved_by`` value passed on every UI-driven
:meth:`ports.approval.ApprovalResolverPort.resolve` call (Q_res_2=B).

Matches :data:`TEKTOS_UI_PROVENANCE` so audit tooling can correlate
``resolved_by="tektos_ui"`` on the APEX record with
``provenance="tektos_ui"`` on the MemoryPort event."""


# ── MemoryPort predicates ──────────────────────────────────────────────────

TEKTOS_UI_PLAN_APPROVED_PREDICATE: str = "tektos.plan.approved"
"""Predicate for the ``POST /plan/{id}/approve`` MemoryPort write (Q5=A)."""

TEKTOS_UI_PLAN_EXECUTED_PREDICATE: str = "tektos.plan.executed"
"""Predicate for the ``POST /plan/{id}/execute`` MemoryPort write (Q5=A)."""

TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE: str = "tektos.plan.diff_rendered"
"""Predicate for the ``GET /plan/{id}/diff`` MemoryPort write (Q5=A)."""


# ── Confidence bounds ──────────────────────────────────────────────────────

TEKTOS_UI_SUCCESS_CONFIDENCE: float = 1.0
"""Confidence on every successful UI-driven event write.

The UI never emits a fractional-confidence event — every write is
one deterministic transition the user just performed. Failures raise
before any write, so no ``0.0`` path exists on this surface."""

TEKTOS_UI_MIN_CONFIDENCE: float = 0.0
"""Lower bound (inclusive) for :func:`confidence_for_ui_event`."""

TEKTOS_UI_MAX_CONFIDENCE: float = 1.0
"""Upper bound (inclusive) for :func:`confidence_for_ui_event`."""


def confidence_for_ui_event(*, success: bool) -> float:
    """Return the confidence value for a UI-driven MemoryPort write.

    Args:
        success: ``True`` \u2192 :data:`TEKTOS_UI_SUCCESS_CONFIDENCE`;
            ``False`` \u2192 :data:`TEKTOS_UI_MIN_CONFIDENCE`.

    Raises:
        TypeError: ``success`` is not a bool.
    """
    if not isinstance(success, bool):
        raise TypeError(
            f"confidence_for_ui_event: success must be bool, "
            f"got {type(success).__name__}"
        )
    return TEKTOS_UI_SUCCESS_CONFIDENCE if success else TEKTOS_UI_MIN_CONFIDENCE


# ── Server bind ────────────────────────────────────────────────────────────

TEKTOS_UI_HOST: str = "127.0.0.1"
"""Bind host for :func:`plugins.tektos.ui.server.build_tektos_ui_app`.

Loopback only (Q1c=A + Q1g=A). Single-user local-first invariant
makes this the security boundary; no auth on any route."""

TEKTOS_UI_PORT: int = 8765
"""Bind port for the Tektos UI (Q1c=A)."""


# ── Route paths ────────────────────────────────────────────────────────────

TEKTOS_UI_INDEX_PATH: str = "/"
TEKTOS_UI_PLAN_DETAIL_PATH: str = "/plan/{approval_id}"
TEKTOS_UI_PLAN_APPROVE_PATH: str = "/plan/{approval_id}/approve"
TEKTOS_UI_PLAN_EXECUTE_PATH: str = "/plan/{approval_id}/execute"
TEKTOS_UI_PLAN_DIFF_PATH: str = "/plan/{approval_id}/diff"
TEKTOS_UI_HEALTHZ_PATH: str = "/healthz"
TEKTOS_UI_HTMX_JS_PATH: str = "/htmx.min.js"


# ── FrontendContractPort Route ────────────────────────────────────────────

TEKTOS_UI_ROUTE_PATH: str = "/tektos"
"""The kernel-frontend route path Tektos claims (Q1e=A).

Distinct from :data:`TEKTOS_UI_INDEX_PATH` above: the former is the
declarative :class:`ports.frontend_contract.Route.path` the Rigpa-donor
frontend uses to `import(lazy_module)`; the latter is the HTTP-server
mount point for the HTMX dashboard's index route."""

TEKTOS_UI_ROUTE_LABEL: str = "Tektos"
TEKTOS_UI_ROUTE_ICON: str = "\U0001f4d0"  # 📐
TEKTOS_UI_ROUTE_LAZY_MODULE: str = "tektos/pages/DashboardPage"


# ── Vendored HTMX identity ────────────────────────────────────────────────

TEKTOS_UI_HTMX_VERSION: str = "2.0.4"
TEKTOS_UI_HTMX_UPSTREAM_COMMIT: str = (
    "b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f"
)
TEKTOS_UI_HTMX_UPSTREAM_LICENSE: str = "0BSD"
TEKTOS_UI_HTMX_UPSTREAM_REPO: str = "https://github.com/bigskysoftware/htmx"
TEKTOS_UI_HTMX_SHA256: str = (
    "e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447"
)
"""SHA-256 of the vendored ``plugins/tektos/ui/htmx.min.js`` bytes.

Contract tests recompute the hash on the vendored file and assert
equality so any accidental swap (curl re-download, tampering) fails
fast at ``make stage1-gate``."""
