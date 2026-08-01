"""Contract tests for :class:`ZetesisPlugin` (Stage 6.1, ADR-052).

Stage 6.1 DoD is literally "Plugin loads." These tests verify:

- Locked module constants match plugin identity + MemoryPort contract.
- :func:`build_zetesis_descriptor` produces the ADR-052 §Q2=A shape
  amended by ADR-057: one route (`/zetesis`), zero panels, empty
  design tokens.
- :class:`ZetesisPlugin` constructs cheaply and side-effect-free.
- :meth:`ZetesisPlugin.start` is idempotent and registers exactly once.
- :meth:`ZetesisPlugin.stop` is idempotent and unregisters cleanly.
- The plugin holds every required port slot per ADR-052 §Q7=B-plus
  and one optional slot (``secrets``).
- **Only** ``FrontendContractPort`` is called at 6.1; the ten required
  business ports remain untouched (ADR-052 §Q3=A).
- ADR-007: no submodule under ``plugins/zetesis/`` imports any other
  plugin package (statically verified by AST scan).
"""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

import pytest

from plugins.zetesis import (
    ZETESIS_KERNEL_COMPAT,
    ZETESIS_MEMORY_DEFAULT_CONFIDENCE,
    ZETESIS_MEMORY_PREDICATE,
    ZETESIS_MEMORY_PROVENANCE,
    ZETESIS_PLUGIN_NAME,
    ZETESIS_STATE_NAMESPACE,
    ZETESIS_VERSION,
    ZetesisPlugin,
    build_zetesis_descriptor,
)
from ports.frontend_contract import (
    PluginDescriptor,
    PluginRegistration,
    UiParityStatus,
)

# ---------------------------------------------------------------------------
# Locked module constants
# ---------------------------------------------------------------------------


def test_plugin_name_is_locked_to_zetesis() -> None:
    assert ZETESIS_PLUGIN_NAME == "zetesis"


def test_state_namespace_matches_plugin_name() -> None:
    assert ZETESIS_STATE_NAMESPACE == ZETESIS_PLUGIN_NAME == "zetesis"


def test_version_is_0_1_0() -> None:
    assert ZETESIS_VERSION == "0.1.0"


def test_kernel_compat_matches_phase_1_shape() -> None:
    assert ZETESIS_KERNEL_COMPAT == "0.1.x"


def test_memory_provenance_is_locked() -> None:
    assert ZETESIS_MEMORY_PROVENANCE == "zetesis_research"


def test_memory_predicate_is_locked() -> None:
    assert ZETESIS_MEMORY_PREDICATE == "zetesis.research.completed"


def test_memory_default_confidence_is_locked() -> None:
    assert ZETESIS_MEMORY_DEFAULT_CONFIDENCE == 0.75


def test_memory_default_confidence_is_in_zero_trust_range() -> None:
    """MemoryPort validate_zero_trust_write rejects confidence <= 0 or > 1."""
    assert 0.0 < ZETESIS_MEMORY_DEFAULT_CONFIDENCE <= 1.0


# ---------------------------------------------------------------------------
# Descriptor factory — ADR-052 §Q2=A shape
# ---------------------------------------------------------------------------


def test_descriptor_metadata_matches_module_constants() -> None:
    d = build_zetesis_descriptor()
    assert isinstance(d, PluginDescriptor)
    assert d.name == ZETESIS_PLUGIN_NAME == "zetesis"
    assert d.state_namespace == ZETESIS_STATE_NAMESPACE == "zetesis"
    assert d.version == ZETESIS_VERSION
    assert d.kernel_compat == ZETESIS_KERNEL_COMPAT


def test_descriptor_has_zero_panels_at_stage_6_3() -> None:
    """ADR-052 §Q2=A amended by ADR-057: panels remain empty at 6.3;
    they land at Stage 6.4 when the kernel FastAPI shell mounts."""
    d = build_zetesis_descriptor()
    assert d.panels == ()


def test_descriptor_has_one_route_at_stage_6_3() -> None:
    """ADR-057 promotes the descriptor from zero routes to one route.
    Locked constants live in `plugins.zetesis.plugin`."""
    from plugins.zetesis.plugin import (
        ZETESIS_ROUTE_ICON,
        ZETESIS_ROUTE_LABEL,
        ZETESIS_ROUTE_LAZY_MODULE,
        ZETESIS_ROUTE_PATH,
    )

    d = build_zetesis_descriptor()
    assert len(d.routes) == 1
    (route,) = d.routes
    assert route.path == ZETESIS_ROUTE_PATH == "/zetesis"
    assert route.label == ZETESIS_ROUTE_LABEL == "Zetesis"
    assert route.icon == ZETESIS_ROUTE_ICON == "🔬"
    assert (
        route.lazy_module
        == ZETESIS_ROUTE_LAZY_MODULE
        == "zetesis/pages/ResearchPage"
    )


def test_descriptor_has_empty_design_tokens_at_stage_6_1() -> None:
    """ADR-052 §Q2=A: Zetesis inherits kernel design tokens at 6.1."""
    d = build_zetesis_descriptor()
    assert dict(d.design_tokens) == {}


def test_descriptor_factory_is_pure() -> None:
    """Two calls return equal descriptors — no shared mutable state."""
    d1 = build_zetesis_descriptor()
    d2 = build_zetesis_descriptor()
    assert d1 == d2
    assert d1 is not d2


# ---------------------------------------------------------------------------
# Fakes for lifecycle — every non-frontend port is a bare sentinel object
# ---------------------------------------------------------------------------


class _FakeFrontendContract:
    """Records every register_plugin / unregister_plugin call."""

    def __init__(self) -> None:
        self.registrations: list[PluginDescriptor] = []
        self.unregistered: list[str] = []

    async def register_plugin(
        self, descriptor: PluginDescriptor
    ) -> PluginRegistration:
        self.registrations.append(descriptor)
        return PluginRegistration(
            descriptor=descriptor,
            registered_at=datetime.now(UTC),
            ui_parity_status=UiParityStatus.IN_PROGRESS,
        )

    async def unregister_plugin(self, name: str) -> bool:
        self.unregistered.append(name)
        return True


class _UntouchablePort:
    """Sentinel port that raises on **any** attribute access.

    Used to prove that Stage 6.1 ``start()`` calls **zero** methods on
    the ten required business ports. ADR-052 §Q3=A: no business-port
    call at 6.1 because ADR-010 is still open.
    """

    __slots__ = ("_label",)

    def __init__(self, label: str) -> None:
        self._label = label

    def __getattr__(self, name: str) -> object:
        raise AssertionError(
            f"Stage 6.1 must not touch {self._label} — "
            f"business ports are held but not called (ADR-052 §Q3=A). "
            f"Attempted attribute: {name!r}"
        )


def _make_plugin(
    frontend_contract: _FakeFrontendContract | None = None,
    *,
    with_secrets: bool = False,
) -> tuple[ZetesisPlugin, _FakeFrontendContract]:
    """Build a plugin with an untouchable stub for every business port."""
    fc = frontend_contract or _FakeFrontendContract()
    plugin = ZetesisPlugin(
        frontend_contract=fc,  # type: ignore[arg-type]
        llm=_UntouchablePort("LLMPort"),  # type: ignore[arg-type]
        memory=_UntouchablePort("MemoryPort"),  # type: ignore[arg-type]
        vector=_UntouchablePort("VectorPort"),  # type: ignore[arg-type]
        data=_UntouchablePort("DataPort"),  # type: ignore[arg-type]
        search=_UntouchablePort("SearchPort"),  # type: ignore[arg-type]
        event_bus=_UntouchablePort("EventBusPort"),  # type: ignore[arg-type]
        resource=_UntouchablePort("ResourcePort"),  # type: ignore[arg-type]
        notification=_UntouchablePort("NotificationPort"),  # type: ignore[arg-type]
        observability=_UntouchablePort("ObservabilityPort"),  # type: ignore[arg-type]
        secrets=(
            _UntouchablePort("SecretsPort")  # type: ignore[arg-type]
            if with_secrets
            else None
        ),
    )
    return plugin, fc


# ---------------------------------------------------------------------------
# Constructor + port surface — ADR-052 §Q7=B-plus lock
# ---------------------------------------------------------------------------


def test_construction_is_side_effect_free() -> None:
    """Constructing the plugin must not register, touch memory, or
    reach any port. Only :meth:`start` performs I/O."""
    plugin, fc = _make_plugin()
    assert plugin.is_started is False
    assert fc.registrations == []


def test_plugin_holds_all_ten_required_ports() -> None:
    """ADR-052 §Q7=B-plus: 10 required business ports (non-None) +
    FrontendContractPort for registration."""
    plugin, _ = _make_plugin()
    required = (
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
    )
    for slot in required:
        held = getattr(plugin, slot)
        assert held is not None, f"required port slot {slot!r} was None"


def test_secrets_port_slot_is_optional_and_defaults_to_none() -> None:
    """ADR-052 §Q7=B-plus: ``SecretsPort`` is the sole optional slot."""
    plugin, _ = _make_plugin(with_secrets=False)
    assert plugin.secrets is None


def test_secrets_port_slot_accepts_a_port_when_wired() -> None:
    plugin, _ = _make_plugin(with_secrets=True)
    assert plugin.secrets is not None


def test_registration_property_raises_before_start() -> None:
    plugin, _ = _make_plugin()
    with pytest.raises(RuntimeError, match="has not started"):
        _ = plugin.registration


# ---------------------------------------------------------------------------
# Lifecycle — start / stop
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_registers_exactly_once() -> None:
    plugin, fc = _make_plugin()
    await plugin.start()
    assert plugin.is_started is True
    assert len(fc.registrations) == 1
    assert fc.registrations[0].name == ZETESIS_PLUGIN_NAME


@pytest.mark.asyncio
async def test_start_registers_the_canonical_descriptor() -> None:
    plugin, fc = _make_plugin()
    await plugin.start()
    assert fc.registrations[0] == build_zetesis_descriptor()


@pytest.mark.asyncio
async def test_start_is_idempotent() -> None:
    plugin, fc = _make_plugin()
    await plugin.start()
    await plugin.start()
    await plugin.start()
    assert len(fc.registrations) == 1


@pytest.mark.asyncio
async def test_start_touches_no_business_port() -> None:
    """ADR-052 §Q3=A: at Stage 6.1 :meth:`start` must not call any of
    the ten required business ports. The ``_UntouchablePort`` sentinel
    raises :class:`AssertionError` on any attribute access — if
    ``start()`` completes without raising, no business port was touched.
    """
    plugin, _ = _make_plugin()
    await plugin.start()  # Would raise AssertionError on any port touch.
    assert plugin.is_started is True


@pytest.mark.asyncio
async def test_registration_is_readable_after_start() -> None:
    plugin, _ = _make_plugin()
    await plugin.start()
    reg = plugin.registration
    assert isinstance(reg, PluginRegistration)
    assert reg.descriptor.name == ZETESIS_PLUGIN_NAME
    assert reg.ui_parity_status is UiParityStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_stop_after_start_unregisters() -> None:
    plugin, fc = _make_plugin()
    await plugin.start()
    await plugin.stop()
    assert plugin.is_started is False
    assert fc.unregistered == [ZETESIS_PLUGIN_NAME]


@pytest.mark.asyncio
async def test_stop_before_start_is_a_noop() -> None:
    plugin, fc = _make_plugin()
    await plugin.stop()
    assert fc.unregistered == []
    assert plugin.is_started is False


@pytest.mark.asyncio
async def test_stop_is_idempotent() -> None:
    plugin, fc = _make_plugin()
    await plugin.start()
    await plugin.stop()
    await plugin.stop()
    await plugin.stop()
    assert fc.unregistered == [ZETESIS_PLUGIN_NAME]


@pytest.mark.asyncio
async def test_registration_property_raises_after_stop() -> None:
    plugin, _ = _make_plugin()
    await plugin.start()
    await plugin.stop()
    with pytest.raises(RuntimeError, match="has not started"):
        _ = plugin.registration


@pytest.mark.asyncio
async def test_start_after_stop_re_registers() -> None:
    plugin, fc = _make_plugin()
    await plugin.start()
    await plugin.stop()
    await plugin.start()
    assert plugin.is_started is True
    assert len(fc.registrations) == 2


# ---------------------------------------------------------------------------
# ADR-007: no cross-plugin imports anywhere under plugins/zetesis/
# ---------------------------------------------------------------------------


def test_zetesis_package_imports_no_other_plugin_adr_007() -> None:
    """ADR-007: cross-plugin coupling flows through the event bus or a
    formal port. Statically scan every ``*.py`` under
    ``plugins/zetesis/`` (excluding this test file) and assert no
    ``import`` or ``from ... import`` touches another plugin package.
    """
    root = Path(__file__).resolve().parent.parent
    forbidden_prefixes = (
        "plugins.praxis",
        "plugins.phrouros",
        "plugins.tektos",
    )
    offenders: list[tuple[str, str]] = []
    for py in root.rglob("*.py"):
        if py.name == "test_zetesis_plugin.py":
            continue  # tests may reference anything
        rel = py.relative_to(root)
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.startswith(forbidden_prefixes):
                    offenders.append((str(rel), mod))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden_prefixes):
                        offenders.append((str(rel), alias.name))
    assert not offenders, (
        f"ADR-007 violation: plugins/zetesis/ imports other plugin packages: "
        f"{offenders}"
    )
