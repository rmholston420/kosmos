"""Praxis plugin bootstrap — governance kernel-plugin (Stage 2.1, ADR-032).

Praxis is Kosmos's first plugin. Its Stage 2.1 responsibilities:

1. Load and cryptographically verify the ratified constitution at boot
   (see :class:`plugins.praxis.constitution.ConstitutionLoader`). A tamper
   failure raises before the plugin becomes ready — this is the
   Build-Sequence §2.1 DoD "boot refused" signal.

2. Register a :class:`~ports.frontend_contract.PluginDescriptor` with the
   :class:`~ports.frontend_contract.FrontendContractPort` so the Stage 3.5
   Next.js shell (when it lands) discovers Praxis's governance panel.
   Kernel-side registration + ``UiParityStatus.IN_PROGRESS`` satisfies
   spec §17.1 (ADR-014) without amending the UI Parity Rule.

Praxis does **not** import any other plugin (ADR-007 events-only
cross-plugin coupling). Future amendment workflow (Synedrion, Phase 6.3)
will publish ``praxis.constitution.amended`` events via
:class:`~ports.event_bus.EventBusPort`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from plugins.praxis.constitution import (
    ConstitutionArtifact,
    ConstitutionLoader,
)
from ports.frontend_contract import (
    FrontendContractPort,
    Panel,
    PanelSlot,
    PluginDescriptor,
    PluginRegistration,
    UiParityStatus,
)


PRAXIS_PLUGIN_NAME = "praxis"
PRAXIS_STATE_NAMESPACE = "praxis"
PRAXIS_VERSION = "0.1.0"
PRAXIS_KERNEL_COMPAT = "0.1.x"
"""Kosmos kernel semver Praxis 0.1.0 supports (matches Stage 1 port surface)."""


PRAXIS_GOVERNANCE_PANEL_ID = "praxis.governance"
PRAXIS_GOVERNANCE_LAZY_MODULE = "praxis/panels/GovernancePanel"
"""Frontend module identifier the Stage 3.5 Next.js shell will resolve."""


PRAXIS_GOVERNANCE_PANEL_PRIORITY = 100
"""Priority within :attr:`PanelSlot.GOVERNANCE`. Praxis is the only owner
of this slot at Stage 2.1 so any positive integer suffices; 100 leaves
headroom above (higher-priority overrides) and below (lower-priority
additions) for future kernel-scope governance widgets."""


def build_praxis_descriptor() -> PluginDescriptor:
    """Construct the Praxis :class:`PluginDescriptor`.

    Pure function — no I/O, no side effects. Split out for testability
    (contract tests inspect the descriptor without instantiating the
    plugin).

    Returns:
        The canonical Praxis descriptor. Registers exactly one panel
        (governance) in :attr:`PanelSlot.GOVERNANCE`; no routes at
        Stage 2.1; no plugin-scoped design tokens (Praxis uses
        kernel-inherited tokens).
    """
    panel = Panel(
        id=PRAXIS_GOVERNANCE_PANEL_ID,
        slot=PanelSlot.GOVERNANCE,
        priority=PRAXIS_GOVERNANCE_PANEL_PRIORITY,
        lazy_module=PRAXIS_GOVERNANCE_LAZY_MODULE,
        plugin_name=PRAXIS_PLUGIN_NAME,
    )
    return PluginDescriptor(
        name=PRAXIS_PLUGIN_NAME,
        state_namespace=PRAXIS_STATE_NAMESPACE,
        version=PRAXIS_VERSION,
        kernel_compat=PRAXIS_KERNEL_COMPAT,
        design_tokens={},
        routes=(),
        panels=(panel,),
    )


@dataclass(slots=True)
class PraxisPlugin:
    """The Praxis governance plugin.

    Construction is **cheap and side-effect-free**. Actual work happens in
    :meth:`start`, which:

    1. Loads and verifies the constitution (raises on tamper).
    2. Registers the plugin descriptor with the FrontendContractPort.

    Splitting init from start keeps testability high: contract tests can
    construct a :class:`PraxisPlugin` without a live constitution or
    FrontendContractPort adapter, then drive :meth:`start` with test
    doubles.

    Attributes:
        constitution_dir: Path to ``governance/constitution/``. Defaults
            to the monorepo-root location.
        frontend_contract: The :class:`FrontendContractPort` adapter that
            Praxis registers with at startup.
        constitution_version: Which constitution version to load. Stage
            2.1 supports ``1`` only (genesis).
    """

    frontend_contract: FrontendContractPort
    constitution_dir: Path | None = None
    constitution_version: int = 1
    _constitution: ConstitutionArtifact | None = field(default=None, init=False)
    _registration: PluginRegistration | None = field(default=None, init=False)
    _started: bool = field(default=False, init=False)

    @property
    def constitution(self) -> ConstitutionArtifact:
        """Return the verified constitution.

        Raises:
            RuntimeError: If :meth:`start` has not been called.
        """
        if self._constitution is None:
            raise RuntimeError(
                "PraxisPlugin has not started — call start() first"
            )
        return self._constitution

    @property
    def registration(self) -> PluginRegistration:
        """Return the FrontendContractPort registration record.

        Raises:
            RuntimeError: If :meth:`start` has not been called.
        """
        if self._registration is None:
            raise RuntimeError(
                "PraxisPlugin has not started — call start() first"
            )
        return self._registration

    @property
    def is_started(self) -> bool:
        """Whether :meth:`start` has completed successfully."""
        return self._started

    async def start(self) -> None:
        """Load-and-verify constitution, then register with frontend.

        Order matters: constitution verification happens **before** any
        external port call. A tamper failure must abort startup without
        having contacted the FrontendContractPort — the plugin never
        exists from the kernel's perspective on tamper.

        Raises:
            ConstitutionError: On any constitution failure (see
                :mod:`plugins.praxis.constitution.errors`).
        """
        if self._started:
            return

        loader = ConstitutionLoader(
            constitution_dir=self.constitution_dir,
            version_number=self.constitution_version,
            verify_on_init=True,
        )
        self._constitution = loader.artifact

        descriptor = build_praxis_descriptor()
        self._registration = await self.frontend_contract.register_plugin(
            descriptor
        )
        self._started = True

    async def stop(self) -> None:
        """Idempotent shutdown — unregister from FrontendContractPort.

        Safe to call multiple times or before :meth:`start`.
        """
        if not self._started:
            return
        await self.frontend_contract.unregister_plugin(PRAXIS_PLUGIN_NAME)
        self._registration = None
        self._constitution = None
        self._started = False
