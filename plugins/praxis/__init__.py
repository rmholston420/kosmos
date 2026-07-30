"""Praxis — governance plugin (Stage 2.1+, ADR-032).

Kosmos's first plugin. Stage 2.1 responsibility: boot-time constitution
verification (refuse boot on tamper). Later stages add APEX Change
Approval Tier engine (§2.2) and consume Phrouros anomaly signals (§2.3).

Public entry point: :class:`plugins.praxis.plugin.PraxisPlugin`.
"""

from __future__ import annotations

from plugins.praxis.plugin import (
    PRAXIS_GOVERNANCE_PANEL_ID,
    PRAXIS_KERNEL_COMPAT,
    PRAXIS_PLUGIN_NAME,
    PRAXIS_STATE_NAMESPACE,
    PRAXIS_VERSION,
    PraxisPlugin,
    build_praxis_descriptor,
)

__all__ = [
    "PRAXIS_GOVERNANCE_PANEL_ID",
    "PRAXIS_KERNEL_COMPAT",
    "PRAXIS_PLUGIN_NAME",
    "PRAXIS_STATE_NAMESPACE",
    "PRAXIS_VERSION",
    "PraxisPlugin",
    "build_praxis_descriptor",
]
