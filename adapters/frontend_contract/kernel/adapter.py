"""KernelFrontendContractAdapter — ADR-031 Stage 1.14 primary FrontendContractPort.

Composes one injectable Protocol seam:

    - ``ManifestStore`` : primary ``InMemoryManifestStore`` (dict-backed,
                          pure stdlib, zero deps; satisfies §1.14 DoD)
                          and stub ``FileManifestStore`` (``pathlib`` +
                          ``json`` stdlib only; atomic tmp-rename write).

Non-bypassable :func:`ports.frontend_contract.validate_plugin_descriptor`
runs at the top of :meth:`register_plugin` before any store I/O.

Design-token collision policy: last-registered wins. Panel ordering per
slot: ``priority DESC`` (higher priority renders first), ties broken by
insertion order (deterministic).
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ports.frontend_contract import (
    KERNEL_SCHEMA_TITLE,
    FrontendContractPort,
    KernelSchema,
    ManifestStore,
    Panel,
    PanelSlot,
    PluginDescriptor,
    PluginNotFound,
    PluginRegistration,
    Route,
    UiParityStatus,
    validate_plugin_descriptor,
)

__all__ = [
    "FileManifestStore",
    "InMemoryManifestStore",
    "KernelFrontendContractAdapter",
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# InMemoryManifestStore — primary
# ---------------------------------------------------------------------------


class InMemoryManifestStore:
    """Dict-backed :class:`ManifestStore`; zero external deps."""

    def __init__(self) -> None:
        self._schema: KernelSchema | None = None
        self._lock = asyncio.Lock()
        self._closed = False

    async def save(self, schema: KernelSchema) -> None:
        if self._closed:
            return
        async with self._lock:
            self._schema = schema

    async def load(self) -> KernelSchema | None:
        if self._closed:
            return None
        async with self._lock:
            return self._schema

    async def close(self) -> None:
        self._closed = True


# ---------------------------------------------------------------------------
# FileManifestStore — stub (deferred wiring per ADR-031)
# ---------------------------------------------------------------------------


class FileManifestStore:
    """Atomic-write :class:`ManifestStore`; stdlib ``pathlib`` + ``json``.

    Ships as a stub at Stage 1.14 to prove the seam swap contract; kernel
    wires it in at Stage 5 auditor landing per ADR-031.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()
        self._closed = False

    async def save(self, schema: KernelSchema) -> None:
        if self._closed:
            return
        payload = _schema_to_dict(schema)
        async with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write: tmp file + rename.
            tmp_fd, tmp_name = tempfile.mkstemp(
                prefix=".manifest-",
                suffix=".tmp",
                dir=str(self._path.parent),
            )
            try:
                with open(tmp_fd, "w", encoding="utf-8") as fp:
                    json.dump(payload, fp, indent=2, sort_keys=True)
                Path(tmp_name).replace(self._path)
            except Exception:  # noqa: BLE001
                Path(tmp_name).unlink(missing_ok=True)
                raise

    async def load(self) -> KernelSchema | None:
        if self._closed:
            return None
        async with self._lock:
            if not self._path.exists():
                return None
            try:
                with self._path.open("r", encoding="utf-8") as fp:
                    return _schema_from_dict(json.load(fp))
            except Exception:  # noqa: BLE001
                return None

    async def close(self) -> None:
        self._closed = True


def _schema_to_dict(schema: KernelSchema) -> dict[str, Any]:
    return {
        "title": schema.title,
        "plugins": [_descriptor_to_dict(p) for p in schema.plugins],
        "panels": [_panel_to_dict(p) for p in schema.panels],
        "design_tokens": dict(schema.design_tokens),
        "generated_at": schema.generated_at.isoformat(),
    }


def _descriptor_to_dict(d: PluginDescriptor) -> dict[str, Any]:
    return {
        "name": d.name,
        "state_namespace": d.state_namespace,
        "version": d.version,
        "kernel_compat": d.kernel_compat,
        "design_tokens": dict(d.design_tokens),
        "routes": [asdict(r) for r in d.routes],
        "panels": [_panel_to_dict(p) for p in d.panels],
    }


def _panel_to_dict(p: Panel) -> dict[str, Any]:
    return {
        "id": p.id,
        "slot": p.slot.value,
        "priority": p.priority,
        "lazy_module": p.lazy_module,
        "plugin_name": p.plugin_name,
    }


def _schema_from_dict(payload: dict[str, Any]) -> KernelSchema:
    return KernelSchema(
        title=payload["title"],
        plugins=tuple(_descriptor_from_dict(p) for p in payload.get("plugins", [])),
        panels=tuple(_panel_from_dict(p) for p in payload.get("panels", [])),
        design_tokens=dict(payload.get("design_tokens", {})),
        generated_at=datetime.fromisoformat(payload["generated_at"]),
    )


def _descriptor_from_dict(payload: dict[str, Any]) -> PluginDescriptor:
    return PluginDescriptor(
        name=payload["name"],
        state_namespace=payload["state_namespace"],
        version=payload["version"],
        kernel_compat=payload["kernel_compat"],
        design_tokens=dict(payload.get("design_tokens", {})),
        routes=tuple(Route(**r) for r in payload.get("routes", [])),
        panels=tuple(_panel_from_dict(p) for p in payload.get("panels", [])),
    )


def _panel_from_dict(payload: dict[str, Any]) -> Panel:
    return Panel(
        id=payload["id"],
        slot=PanelSlot(payload["slot"]),
        priority=payload["priority"],
        lazy_module=payload["lazy_module"],
        plugin_name=payload["plugin_name"],
    )


# ---------------------------------------------------------------------------
# KernelFrontendContractAdapter
# ---------------------------------------------------------------------------


class KernelFrontendContractAdapter:
    """Primary Kosmos FrontendContractPort adapter (ADR-031)."""

    def __init__(self, store: ManifestStore | None = None) -> None:
        self._store: ManifestStore = store if store is not None else InMemoryManifestStore()
        self._plugins: dict[str, PluginRegistration] = {}
        self._insertion_order: list[str] = []  # insertion-order tiebreaker
        self._closed = False

    # ---- Registration ---------------------------------------------------

    async def register_plugin(
        self, descriptor: PluginDescriptor
    ) -> PluginRegistration:
        validate_plugin_descriptor(descriptor)
        if descriptor.name in self._plugins:
            from ports.frontend_contract import PluginDescriptorRejected

            raise PluginDescriptorRejected(
                f"descriptor rejected: plugin {descriptor.name!r} already "
                f"registered; call unregister_plugin first"
            )
        parity = _derive_parity(descriptor)
        reg = PluginRegistration(
            descriptor=descriptor,
            registered_at=_utcnow(),
            ui_parity_status=parity,
        )
        self._plugins[descriptor.name] = reg
        self._insertion_order.append(descriptor.name)
        await self._persist()
        return reg

    async def unregister_plugin(self, name: str) -> bool:
        if name not in self._plugins:
            return False
        del self._plugins[name]
        self._insertion_order.remove(name)
        await self._persist()
        return True

    async def list_plugins(self) -> list[PluginDescriptor]:
        return [self._plugins[n].descriptor for n in self._insertion_order]

    # ---- Manifest queries ------------------------------------------------

    async def get_route_manifest(self) -> list[Route]:
        routes: list[Route] = []
        for name in self._insertion_order:
            routes.extend(self._plugins[name].descriptor.routes)
        return routes

    async def get_design_tokens(self) -> dict[str, str]:
        # Last-registered-wins per ADR-031.
        merged: dict[str, str] = {}
        for name in self._insertion_order:
            merged.update(self._plugins[name].descriptor.design_tokens)
        return merged

    async def get_state_namespaces(self) -> list[str]:
        return [
            self._plugins[n].descriptor.state_namespace
            for n in self._insertion_order
        ]

    async def get_panel_manifest(
        self, slot: PanelSlot | None = None
    ) -> list[Panel]:
        panels: list[tuple[int, Panel]] = []
        for idx, name in enumerate(self._insertion_order):
            for panel in self._plugins[name].descriptor.panels:
                if slot is None or panel.slot is slot:
                    panels.append((idx, panel))
        # Sort by (priority DESC, insertion_index ASC) for determinism.
        panels.sort(key=lambda t: (-t[1].priority, t[0]))
        return [p for _, p in panels]

    async def check_ui_parity(self, name: str) -> UiParityStatus:
        if name not in self._plugins:
            raise PluginNotFound(name)
        return self._plugins[name].ui_parity_status

    async def render_kernel_schema(self) -> KernelSchema:
        return KernelSchema(
            title=KERNEL_SCHEMA_TITLE,
            plugins=tuple(await self.list_plugins()),
            panels=tuple(await self.get_panel_manifest()),
            design_tokens=await self.get_design_tokens(),
            generated_at=_utcnow(),
        )

    # ---- Lifecycle -------------------------------------------------------

    def is_healthy(self) -> bool:
        try:
            return not self._closed
        except Exception:  # noqa: BLE001
            return False

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self._store.close()
        except Exception:  # noqa: BLE001
            pass

    # ---- Internal --------------------------------------------------------

    async def _persist(self) -> None:
        try:
            await self._store.save(await self.render_kernel_schema())
        except Exception:  # noqa: BLE001
            # ManifestStore contract: soft-fail; observability logs elsewhere.
            pass


def _derive_parity(descriptor: PluginDescriptor) -> UiParityStatus:
    """Derive :class:`UiParityStatus` from descriptor content per ADR-031."""
    if not descriptor.routes and not descriptor.panels:
        return UiParityStatus.IN_PROGRESS
    if descriptor.routes and descriptor.panels:
        return UiParityStatus.COMPLIANT
    return UiParityStatus.IN_PROGRESS
