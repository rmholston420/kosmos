"""Phrouros plugin bootstrap (Stage 2.3, ADR-034).

Mirrors :class:`~plugins.praxis.plugin.PraxisPlugin`'s shape:

- Dataclass with cheap side-effect-free construction.
- Async :meth:`start` — starts the engine (subscribes to trace feed) and
  registers the :class:`~ports.frontend_contract.PluginDescriptor` with
  :class:`~ports.frontend_contract.FrontendContractPort`. Idempotent.
- Async :meth:`stop` — stops the engine and is idempotent.

Phrouros does **not** import any other plugin (ADR-007). It is a
governance-domain sibling to Praxis, not a Praxis submodule.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from plugins.phrouros.engine import PhrourosEngine
from ports.frontend_contract import (
    FrontendContractPort,
    Panel,
    PanelSlot,
    PluginDescriptor,
    PluginRegistration,
)


PHROUROS_PLUGIN_NAME = "phrouros"
PHROUROS_STATE_NAMESPACE = "phrouros"
PHROUROS_VERSION = "0.1.0"
PHROUROS_KERNEL_COMPAT = "0.1.x"


PHROUROS_TRACE_PANEL_ID = "phrouros.trace"
PHROUROS_TRACE_LAZY_MODULE = "phrouros/panels/AgentTracePanel"
"""Frontend module identifier the Stage 3.5 Next.js shell will resolve."""

PHROUROS_TRACE_PANEL_PRIORITY = 100
"""Priority within :attr:`PanelSlot.AGENT_TRACE`. Phrouros is the only
producer of anomaly-observability content at Stage 2.3."""


def build_phrouros_descriptor() -> PluginDescriptor:
    """Construct the Phrouros :class:`PluginDescriptor`.

    Pure function — no I/O, no side effects. Split out for testability
    (contract tests inspect the descriptor without instantiating the
    plugin).
    """
    trace_panel = Panel(
        id=PHROUROS_TRACE_PANEL_ID,
        slot=PanelSlot.AGENT_TRACE,
        priority=PHROUROS_TRACE_PANEL_PRIORITY,
        lazy_module=PHROUROS_TRACE_LAZY_MODULE,
        plugin_name=PHROUROS_PLUGIN_NAME,
    )
    return PluginDescriptor(
        name=PHROUROS_PLUGIN_NAME,
        state_namespace=PHROUROS_STATE_NAMESPACE,
        version=PHROUROS_VERSION,
        kernel_compat=PHROUROS_KERNEL_COMPAT,
        design_tokens={},
        routes=(),
        panels=(trace_panel,),
    )


@dataclass
class PhrourosPlugin:
    """Kosmos anomaly-detection plugin.

    Args:
        engine: composed :class:`PhrourosEngine` (trace feed + detectors +
            notification + resource + event bus).
        frontend_contract_port: kernel-side registration surface.
    """

    engine: PhrourosEngine
    frontend_contract_port: FrontendContractPort

    _started: bool = field(default=False, init=False, repr=False)
    _registration: PluginRegistration | None = field(
        default=None, init=False, repr=False
    )

    async def start(self) -> None:
        """Start the engine + register the descriptor. Idempotent."""
        if self._started:
            return
        await self.engine.start()
        descriptor = build_phrouros_descriptor()
        self._registration = await self.frontend_contract_port.register_plugin(
            descriptor
        )
        self._started = True

    async def stop(self) -> None:
        """Stop the engine. Idempotent."""
        if not self._started:
            return
        await self.engine.stop()
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def registration(self) -> PluginRegistration | None:
        return self._registration
