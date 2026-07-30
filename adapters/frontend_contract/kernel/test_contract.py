"""Contract tests for :mod:`ports.frontend_contract` + KernelFrontendContractAdapter.

Stdlib-only Protocol doubles verify seam swap without third-party imports.

Structure:

    - Protocol conformance
    - Zero-trust guard (:func:`validate_plugin_descriptor`)
    - Build-Sequence §1.14 DoD (empty dashboard renders "Kosmos" title)
    - register_plugin + unregister_plugin
    - Route / design-token / state-namespace manifests
    - Panel manifest priority ordering (spec §280 slots)
    - UI parity status transitions
    - ManifestStore seam swap (InMemory + File + custom double)
    - Lifecycle (``is_healthy`` non-throwing, idempotent ``close``)
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from adapters.frontend_contract.kernel import (
    FileManifestStore,
    InMemoryManifestStore,
    KernelFrontendContractAdapter,
)
from ports.frontend_contract import (
    KERNEL_SCHEMA_TITLE,
    PLUGIN_REQUIRED_FIELDS,
    FrontendContractPort,
    KernelSchema,
    ManifestStore,
    Panel,
    PanelSlot,
    PluginDescriptor,
    PluginDescriptorRejected,
    PluginNotFound,
    PluginRegistration,
    Route,
    UiParityStatus,
    validate_plugin_descriptor,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _desc(
    name: str = "dashboard",
    *,
    routes: tuple[Route, ...] = (),
    panels: tuple[Panel, ...] = (),
    design_tokens: dict[str, str] | None = None,
) -> PluginDescriptor:
    return PluginDescriptor(
        name=name,
        state_namespace=name,
        version="0.1.0",
        kernel_compat=">=0.1,<1.0",
        design_tokens=design_tokens or {},
        routes=routes,
        panels=panels,
    )


def _route(path: str = "/x", lazy: str = "./X") -> Route:
    return Route(path=path, label="X", icon="Layout", lazy_module=lazy)


def _panel(
    id_: str = "p1",
    slot: PanelSlot = PanelSlot.ALGEDONIC,
    priority: int = 10,
    plugin_name: str = "dashboard",
) -> Panel:
    return Panel(
        id=id_,
        slot=slot,
        priority=priority,
        lazy_module=f"./{id_}",
        plugin_name=plugin_name,
    )


class RecordingStore:
    """Stdlib ManifestStore double."""

    def __init__(self) -> None:
        self.schema: KernelSchema | None = None
        self.saves = 0
        self.closed = False

    async def save(self, schema: KernelSchema) -> None:
        self.schema = schema
        self.saves += 1

    async def load(self) -> KernelSchema | None:
        return self.schema

    async def close(self) -> None:
        self.closed = True


class ExplodingStore:
    """ManifestStore that raises on save; adapter must swallow."""

    async def save(self, schema: KernelSchema) -> None:  # noqa: ARG002
        raise RuntimeError("boom")

    async def load(self) -> KernelSchema | None:
        return None

    async def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter() -> KernelFrontendContractAdapter:
    return KernelFrontendContractAdapter()


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_adapter_is_frontendcontractport(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        assert isinstance(adapter, FrontendContractPort)

    def test_inmemory_store_is_manifeststore(self) -> None:
        assert isinstance(InMemoryManifestStore(), ManifestStore)

    def test_file_store_is_manifeststore(self, tmp_path: Path) -> None:
        assert isinstance(FileManifestStore(tmp_path / "m.json"), ManifestStore)

    def test_recording_store_is_manifeststore(self) -> None:
        assert isinstance(RecordingStore(), ManifestStore)

    def test_required_fields_frozen(self) -> None:
        assert PLUGIN_REQUIRED_FIELDS == frozenset(
            {"name", "state_namespace", "version", "kernel_compat"}
        )
        with pytest.raises(AttributeError):
            PLUGIN_REQUIRED_FIELDS.add("x")  # type: ignore[attr-defined]

    def test_kernel_schema_title_constant(self) -> None:
        assert KERNEL_SCHEMA_TITLE == "Kosmos"

    def test_panel_slot_has_all_spec_280_slots(self) -> None:
        expected = {
            "ALGEDONIC",
            "GOVERNANCE",
            "MEMORY_INTEGRITY",
            "MODEL_SWAP_SLO",
            "STUB_DEGRADATION",
            "CONTEXT_PRESSURE",
            "HARDWARE_RESILIENCE",
            "APPROVALS_QUEUE",
            "AGENT_TRACE",
        }
        assert {s.name for s in PanelSlot} == expected


# ---------------------------------------------------------------------------
# Zero-trust guard
# ---------------------------------------------------------------------------


class TestValidatePluginDescriptor:
    def test_valid_descriptor_passes(self) -> None:
        validate_plugin_descriptor(_desc())

    def test_rejects_non_descriptor(self) -> None:
        with pytest.raises(PluginDescriptorRejected, match="PluginDescriptor"):
            validate_plugin_descriptor({"name": "x"})  # type: ignore[arg-type]

    @pytest.mark.parametrize("field", sorted(PLUGIN_REQUIRED_FIELDS))
    def test_rejects_empty_required_field(self, field: str) -> None:
        kwargs = {
            "name": "d",
            "state_namespace": "d",
            "version": "0.1.0",
            "kernel_compat": ">=0.1,<1.0",
        }
        kwargs[field] = ""
        with pytest.raises(PluginDescriptorRejected, match=field):
            validate_plugin_descriptor(PluginDescriptor(**kwargs))

    @pytest.mark.parametrize(
        "bad_name",
        ["Dashboard", "dash_board", "-dashboard", "dashboard-", "dash--board", "1", ""],
    )
    def test_rejects_invalid_name(self, bad_name: str) -> None:
        try:
            desc = PluginDescriptor(
                name=bad_name,
                state_namespace="d",
                version="0.1.0",
                kernel_compat=">=0.1,<1.0",
            )
        except Exception:
            return  # dataclass may reject at construction; test still holds
        with pytest.raises(PluginDescriptorRejected):
            validate_plugin_descriptor(desc)

    def test_rejects_route_without_lazy_module(self) -> None:
        desc = _desc(
            routes=(Route(path="/x", label="X", icon="I", lazy_module=""),)
        )
        with pytest.raises(PluginDescriptorRejected, match="lazy_module"):
            validate_plugin_descriptor(desc)

    def test_rejects_panel_without_lazy_module(self) -> None:
        panel = Panel(
            id="p",
            slot=PanelSlot.ALGEDONIC,
            priority=10,
            lazy_module="",
            plugin_name="d",
        )
        desc = _desc(panels=(panel,))
        with pytest.raises(PluginDescriptorRejected, match="lazy_module"):
            validate_plugin_descriptor(desc)


# ---------------------------------------------------------------------------
# Build-Sequence §1.14 DoD (literal name)
# ---------------------------------------------------------------------------


class TestBuildSequence114DoD:
    async def test_empty_dashboard_renders_kosmos_title_build_sequence_1_14_dod(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        """Build-Sequence §1.14 DoD: empty kernel dashboard renders 'Kosmos'."""
        schema = await adapter.render_kernel_schema()
        assert schema.title == "Kosmos"
        assert schema.plugins == ()
        assert schema.panels == ()
        assert schema.design_tokens == {}

    async def test_schema_has_generated_at(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        schema = await adapter.render_kernel_schema()
        assert schema.generated_at is not None


# ---------------------------------------------------------------------------
# register_plugin / unregister_plugin
# ---------------------------------------------------------------------------


class TestRegister:
    async def test_register_returns_registration(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        reg = await adapter.register_plugin(_desc())
        assert isinstance(reg, PluginRegistration)
        assert reg.descriptor.name == "dashboard"
        assert reg.registered_at is not None

    async def test_register_rejects_duplicate(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(_desc())
        with pytest.raises(PluginDescriptorRejected, match="already registered"):
            await adapter.register_plugin(_desc())

    async def test_register_runs_guard_before_store(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        with pytest.raises(PluginDescriptorRejected):
            await adapter.register_plugin(_desc(name="Bad_Name"))

    async def test_unregister_returns_false_when_unknown(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        assert await adapter.unregister_plugin("nope") is False

    async def test_register_then_unregister(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(_desc())
        assert await adapter.unregister_plugin("dashboard") is True
        assert await adapter.list_plugins() == []

    async def test_reregister_after_unregister(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(_desc())
        await adapter.unregister_plugin("dashboard")
        await adapter.register_plugin(_desc())  # no error

    async def test_list_plugins_preserves_registration_order(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(_desc("a"))
        await adapter.register_plugin(_desc("b"))
        await adapter.register_plugin(_desc("c"))
        names = [p.name for p in await adapter.list_plugins()]
        assert names == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Route / design-token / state-namespace manifests
# ---------------------------------------------------------------------------


class TestManifestQueries:
    async def test_route_manifest_aggregates(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(
            _desc("a", routes=(_route("/a", "./a"),))
        )
        await adapter.register_plugin(
            _desc("b", routes=(_route("/b", "./b"), _route("/b2", "./b2")))
        )
        routes = await adapter.get_route_manifest()
        assert [r.path for r in routes] == ["/a", "/b", "/b2"]

    async def test_design_tokens_merge_last_wins(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(
            _desc("a", design_tokens={"--accent": "red", "--a-only": "1"})
        )
        await adapter.register_plugin(
            _desc("b", design_tokens={"--accent": "blue", "--b-only": "2"})
        )
        tokens = await adapter.get_design_tokens()
        assert tokens["--accent"] == "blue"  # last-wins
        assert tokens["--a-only"] == "1"
        assert tokens["--b-only"] == "2"

    async def test_state_namespaces_returned(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(_desc("a"))
        await adapter.register_plugin(_desc("b"))
        assert await adapter.get_state_namespaces() == ["a", "b"]

    async def test_empty_manifests(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        assert await adapter.get_route_manifest() == []
        assert await adapter.get_design_tokens() == {}
        assert await adapter.get_state_namespaces() == []


# ---------------------------------------------------------------------------
# Panel manifest priority ordering
# ---------------------------------------------------------------------------


class TestPanelManifest:
    async def test_panels_sorted_priority_desc(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(
            _desc(
                "a",
                panels=(
                    _panel("low", priority=1, plugin_name="a"),
                    _panel("mid", priority=50, plugin_name="a"),
                    _panel("hi", priority=100, plugin_name="a"),
                ),
            )
        )
        panels = await adapter.get_panel_manifest()
        assert [p.id for p in panels] == ["hi", "mid", "low"]

    async def test_panels_filtered_by_slot(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(
            _desc(
                "a",
                panels=(
                    _panel("al", slot=PanelSlot.ALGEDONIC, plugin_name="a"),
                    _panel("gv", slot=PanelSlot.GOVERNANCE, plugin_name="a"),
                    _panel("aq", slot=PanelSlot.APPROVALS_QUEUE, plugin_name="a"),
                ),
            )
        )
        alg = await adapter.get_panel_manifest(slot=PanelSlot.ALGEDONIC)
        assert [p.id for p in alg] == ["al"]

    async def test_panel_ties_broken_by_insertion_order(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(
            _desc("a", panels=(_panel("a1", priority=10, plugin_name="a"),))
        )
        await adapter.register_plugin(
            _desc("b", panels=(_panel("b1", priority=10, plugin_name="b"),))
        )
        panels = await adapter.get_panel_manifest()
        assert [p.id for p in panels] == ["a1", "b1"]

    async def test_panels_cross_plugin_aggregation(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(
            _desc(
                "phrouros",
                panels=(_panel("alg", slot=PanelSlot.ALGEDONIC, priority=100, plugin_name="phrouros"),),
            )
        )
        await adapter.register_plugin(
            _desc(
                "praxis",
                panels=(_panel("aq", slot=PanelSlot.APPROVALS_QUEUE, priority=90, plugin_name="praxis"),),
            )
        )
        panels = await adapter.get_panel_manifest()
        assert {p.id for p in panels} == {"alg", "aq"}


# ---------------------------------------------------------------------------
# UI parity status
# ---------------------------------------------------------------------------


class TestUiParity:
    async def test_in_progress_when_no_routes_no_panels(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(_desc("a"))
        assert await adapter.check_ui_parity("a") is UiParityStatus.IN_PROGRESS

    async def test_compliant_when_routes_and_panels(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(
            _desc(
                "a",
                routes=(_route(),),
                panels=(_panel(plugin_name="a"),),
            )
        )
        assert await adapter.check_ui_parity("a") is UiParityStatus.COMPLIANT

    async def test_in_progress_when_routes_only(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.register_plugin(_desc("a", routes=(_route(),)))
        assert await adapter.check_ui_parity("a") is UiParityStatus.IN_PROGRESS

    async def test_raises_pluginnotfound_on_unknown(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        with pytest.raises(PluginNotFound):
            await adapter.check_ui_parity("nope")


# ---------------------------------------------------------------------------
# ManifestStore seam swap
# ---------------------------------------------------------------------------


class TestManifestStoreSeam:
    async def test_inmemory_store_persists_across_reads(self) -> None:
        store = InMemoryManifestStore()
        adapter = KernelFrontendContractAdapter(store=store)
        await adapter.register_plugin(_desc("a"))
        loaded = await store.load()
        assert loaded is not None
        assert len(loaded.plugins) == 1

    async def test_recording_store_receives_saves(self) -> None:
        store = RecordingStore()
        adapter = KernelFrontendContractAdapter(store=store)
        await adapter.register_plugin(_desc("a"))
        await adapter.register_plugin(_desc("b"))
        assert store.saves == 2
        assert store.schema is not None
        assert len(store.schema.plugins) == 2

    async def test_unregister_persists(self) -> None:
        store = RecordingStore()
        adapter = KernelFrontendContractAdapter(store=store)
        await adapter.register_plugin(_desc("a"))
        await adapter.unregister_plugin("a")
        assert store.saves == 2
        assert store.schema is not None
        assert store.schema.plugins == ()

    async def test_store_save_failure_swallowed(self) -> None:
        adapter = KernelFrontendContractAdapter(store=ExplodingStore())
        # Must not raise even though save() explodes.
        await adapter.register_plugin(_desc("a"))
        assert (await adapter.list_plugins())[0].name == "a"

    async def test_file_store_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "manifest.json"
        store = FileManifestStore(path)
        adapter = KernelFrontendContractAdapter(store=store)
        await adapter.register_plugin(
            _desc(
                "a",
                routes=(_route("/a", "./a"),),
                panels=(_panel(plugin_name="a"),),
                design_tokens={"--a": "red"},
            )
        )
        assert path.exists()
        # Fresh store reads what was written.
        fresh = FileManifestStore(path)
        loaded = await fresh.load()
        assert loaded is not None
        assert loaded.title == "Kosmos"
        assert len(loaded.plugins) == 1
        assert loaded.plugins[0].name == "a"
        assert loaded.plugins[0].routes[0].path == "/a"
        assert loaded.panels[0].slot is PanelSlot.ALGEDONIC

    async def test_file_store_atomic_write(self, tmp_path: Path) -> None:
        # After a save, no leftover .tmp files.
        path = tmp_path / "manifest.json"
        store = FileManifestStore(path)
        adapter = KernelFrontendContractAdapter(store=store)
        await adapter.register_plugin(_desc("a"))
        leftovers = list(tmp_path.glob(".manifest-*.tmp"))
        assert leftovers == []

    async def test_file_store_load_returns_none_when_missing(
        self, tmp_path: Path
    ) -> None:
        store = FileManifestStore(tmp_path / "nope.json")
        assert await store.load() is None

    async def test_file_store_load_returns_none_on_corrupt(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not-json")
        store = FileManifestStore(path)
        assert await store.load() is None


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_is_healthy_non_throwing(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        assert adapter.is_healthy() is True

    async def test_close_marks_unhealthy(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.close()
        assert adapter.is_healthy() is False

    async def test_close_idempotent(
        self, adapter: KernelFrontendContractAdapter
    ) -> None:
        await adapter.close()
        await adapter.close()  # must not raise

    async def test_close_cascades_to_store(self) -> None:
        store = RecordingStore()
        adapter = KernelFrontendContractAdapter(store=store)
        await adapter.close()
        assert store.closed is True

    async def test_close_swallows_store_errors(self) -> None:
        class ExplodingCloseStore:
            async def save(self, schema: KernelSchema) -> None: ...
            async def load(self) -> KernelSchema | None:
                return None
            async def close(self) -> None:
                raise RuntimeError("boom")

        adapter = KernelFrontendContractAdapter(store=ExplodingCloseStore())
        await adapter.close()  # must not raise
