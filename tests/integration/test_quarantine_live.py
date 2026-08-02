"""Stage 1.6 Phase 3 · ADR-076 D4 — quarantine review live smoke.

Env-gated by ``KOSMOS_STAGE_16_LIVE=1``. Skipped by default so CI + local
fast tier stay green without external services.

Live-tier preconditions (all must be reachable on 127.0.0.1):

  * Kosmos kernel at 8000        (systemd unit ``kosmos-kernel``)
  * DozerDB at 7687              (docker: ``ops/compose/memory.yml``)

The kernel /api/memory/quarantined routes only need MemoryPort to be
booted; they do not require Qdrant or Ollama. Qdrant/Ollama enrichment
happens on approve (promotion write), but the semantic side-effect is
best-effort — an unreachable Qdrant does not block promotion.

Flow:

  1. GET /api/kernel/identity          → returns reviewer name.
  2. GET /api/memory/quarantined       → returns a list (may be empty).
  3. If the list is non-empty, POST /api/memory/quarantined/{id}/reject
     with a marker reason and confirm the row is gone on the next list.

The test deliberately does NOT try to synthesize a quarantine row
directly against the live DozerDB — that is the fast-tier contract's
job. This test verifies the HTTP surface, degradation contract, and
end-to-end plumbing to the adapter port method.
"""

from __future__ import annotations

import os
import socket
from contextlib import closing

import pytest
import httpx

LIVE_ENABLED = os.environ.get("KOSMOS_STAGE_16_LIVE") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason=(
        "Stage 1.6 Phase 3 live tier requires KOSMOS_STAGE_16_LIVE=1 plus "
        "kernel (127.0.0.1:8000) + DozerDB (127.0.0.1:7687) reachable. "
        "See ADR-076 D4."
    ),
)

KERNEL_URL = os.environ.get("KOSMOS_KERNEL_URL", "http://127.0.0.1:8000")
KERNEL_HOST = os.environ.get("KOSMOS_KERNEL_HOST", "127.0.0.1")
KERNEL_PORT = int(os.environ.get("KOSMOS_KERNEL_PORT", "8000"))
DOZERDB_HOST = os.environ.get("KOSMOS_DOZERDB_HOST", "127.0.0.1")
DOZERDB_PORT = int(os.environ.get("KOSMOS_DOZERDB_PORT", "7687"))


def _tcp_reachable(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except OSError:
        return False


def _require_services() -> None:
    unreachable = [
        (name, host, port)
        for name, host, port in (
            ("Kosmos kernel", KERNEL_HOST, KERNEL_PORT),
            ("DozerDB", DOZERDB_HOST, DOZERDB_PORT),
        )
        if not _tcp_reachable(host, port)
    ]
    if unreachable:
        parts = ", ".join(f"{n} at {h}:{p}" for n, h, p in unreachable)
        pytest.skip(f"live-tier services unreachable: {parts}")


def test_kernel_identity_route_live() -> None:
    """ADR-076 D4: /api/kernel/identity returns a non-empty reviewer."""
    _require_services()
    with httpx.Client(base_url=KERNEL_URL, timeout=5.0) as c:
        r = c.get("/api/kernel/identity")
        r.raise_for_status()
        body = r.json()
        assert isinstance(body, dict)
        assert isinstance(body.get("reviewer"), str)
        assert body["reviewer"]


def test_quarantined_list_live() -> None:
    """ADR-076 D4: /api/memory/quarantined returns a well-shaped page.

    Accepts either a booted-memory response (``degraded: False``) or the
    degradation envelope (``entries: [], degraded: True``). Both are
    contract-valid.
    """
    _require_services()
    with httpx.Client(base_url=KERNEL_URL, timeout=10.0) as c:
        r = c.get("/api/memory/quarantined", params={"limit": 10})
        r.raise_for_status()
        body = r.json()
        assert isinstance(body, dict)
        assert isinstance(body.get("entries"), list)
        assert body.get("degraded") in (True, False)
        if body["degraded"]:
            assert body["entries"] == []
            return
        # If entries are present, each must carry the D4 contract shape.
        for e in body["entries"]:
            assert isinstance(e.get("event_id"), str) and e["event_id"]
            assert isinstance(e.get("provenance"), str)
            assert isinstance(e.get("confidence"), (int, float))
            assert isinstance(e.get("payload"), dict)
            assert isinstance(e.get("quarantined_at"), str)


def test_quarantined_reject_404_on_missing_id_live() -> None:
    """ADR-076 D4: reject on an unknown id surfaces as 404."""
    _require_services()
    with httpx.Client(base_url=KERNEL_URL, timeout=10.0) as c:
        # First check the list route — if it's degraded, the write path
        # is unavailable and the semantics of reject change to 503.
        preflight = c.get("/api/memory/quarantined")
        preflight.raise_for_status()
        if preflight.json().get("degraded"):
            pytest.skip("memory port not booted; reject path returns 503")
        r = c.post(
            "/api/memory/quarantined/no-such-id-adr076-d4-live/reject",
            json={"reviewer": "adr076-live-test", "reason": "smoke-missing"},
        )
        assert r.status_code == 404, r.text
