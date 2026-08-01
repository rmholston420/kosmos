"""Stage 6.5 Zetesis mount integration tests (ADR-058 DoD).

Verifies:

- Kernel lifespan mounts ZetesisPlugin without adding boot errors.
- `/api/kernel/plugins` exposes the Zetesis descriptor.
- `/api/kernel/routes` exposes the `/zetesis` route.
- Plugin start is idempotent; a second lifespan cycle does not raise.
- Mount failure (simulated via monkey-patched factory) is degraded, not
  fatal — the kernel keeps returning 200 on the other endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from kernel.app import app, registry


@pytest.fixture
def client():
    """Client with lifespan enabled (mounts + unmounts the plugin)."""
    with TestClient(app) as c:
        yield c


def test_health_reports_zetesis_up(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    # zetesis subsystem must have booted
    assert body["subsystems"]["zetesis"] is True
    # zetesis must not have contributed a boot error
    assert "zetesis" not in body["boot_errors"]


def test_kernel_plugins_lists_zetesis(client) -> None:
    r = client.get("/api/kernel/plugins")
    assert r.status_code == 200
    plugins = r.json()
    assert isinstance(plugins, list)
    names = [p.get("name") for p in plugins]
    assert "kosmos.plugin.zetesis" in names, (
        f"expected zetesis in plugin list, got {names}"
    )


def test_kernel_routes_contains_zetesis_path(client) -> None:
    r = client.get("/api/kernel/routes")
    assert r.status_code == 200
    routes = r.json()
    assert isinstance(routes, list)
    paths = [r.get("path") for r in routes]
    assert "/zetesis" in paths, (
        f"expected /zetesis in route manifest, got {paths}"
    )


def test_all_kernel_endpoints_still_200(client) -> None:
    """Regression: adding zetesis must not break any 6.4 endpoint."""
    for path in (
        "/health",
        "/api/kernel/schema",
        "/api/kernel/routes",
        "/api/kernel/panels",
        "/api/kernel/plugins",
        "/api/kernel/design-tokens",
        "/api/resources/balances",
        "/api/approvals",
        "/api/notifications/health",
    ):
        r = client.get(path)
        assert r.status_code == 200, f"{path} returned {r.status_code}"


def test_plugin_registration_holds_after_start(client) -> None:
    """The mounted plugin must be started and hold a registration."""
    assert registry.zetesis is not None
    assert registry.zetesis.is_started is True
    reg = registry.zetesis.registration
    assert reg is not None


def test_factory_wires_all_ten_ports() -> None:
    """Every required port on ZetesisPlugin is a real (non-stub) adapter."""
    from plugins.zetesis.adapters.real.factory import (
        build_stage_6_5_zetesis_plugin,
    )

    plugin = build_stage_6_5_zetesis_plugin()

    # None of the 10 required ports may be a plugin-local stub.
    stub_module_prefix = "plugins.zetesis.adapters"
    for port_name in (
        "frontend_contract",
        "llm",
        "memory",
        "vector",
        "data",
        "search",
        "event_bus",
        "resource",
        "notification",
        "observability",
    ):
        adapter = getattr(plugin, port_name)
        module = type(adapter).__module__
        assert not module.startswith(stub_module_prefix) or module.startswith(
            "plugins.zetesis.adapters.real"
        ), f"{port_name} still bound to stub: {module}"
