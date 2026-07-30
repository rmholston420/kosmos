"""EscalationPolicy — superset kernel-wide Tier-2 triggers (ADR-033 · spec §14).

Spec §14 enumerates nine trigger classes that MUST escalate any proposal
to ``HUMAN_REQUIRED`` regardless of the proposing plugin's own tier
preference. This module provides the classification scaffold that
plugins call before ``propose(...)``:

    policy = EscalationPolicy()
    detected = policy.classify(delta)
    if detected is not None:
        tier = ChangeApprovalTier.HUMAN_REQUIRED
    else:
        tier = plugin_choice

Stage 2.2 lands the scaffold + a small set of pattern-based classifiers
that cover the trigger classes for which the delta shape is already
well-defined. Individual plugin-side triggers wire in as their plugins
land — Tektos production-deploy trigger wires at Stage 3, Praxis
constitution self-amendment wires at Synedrion Phase 6.3.

The scaffold is deliberately conservative: unknown deltas do NOT
auto-elevate. Elevation must be triggered by an explicit signal in the
delta (e.g. ``{"action": "production_deploy"}``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from plugins.praxis.apex.models import Trigger

__all__ = ["EscalationPolicy"]


class EscalationPolicy:
    """Classify a proposed delta against spec §14 Tier-2 triggers.

    ``classify(delta) -> Trigger | None`` returns the FIRST matching
    trigger, or ``None`` if the delta does not match any. Callers use
    the presence of a trigger to elevate the proposal tier.

    The classifier is pure-function: no state, no I/O. Tests can call
    it directly with fixture dicts.
    """

    # Signal keys the classifier inspects. Each is a top-level key in
    # the delta dict; missing keys are treated as "signal absent".
    _ACTION_KEY = "action"
    _MEMORY_TIER_KEY = "memory_tier"
    _MEMORY_SIGNED_KEY = "memory_signed"
    _MODEL_SWAP_BREACH_KEY = "model_swap_slo_breach_sustained"
    _ADAPTER_BUS_FACTOR_KEY = "adapter_bus_factor"
    _ADAPTER_HAS_FALLBACK_KEY = "adapter_has_fallback"
    _RETRY_EXHAUSTED_KEY = "retry_exhausted"
    _KB_CONFLICT_KEY = "kb_conflict"
    _PORT_DEPRECATION_KEY = "port_version_deprecation"
    _KERNEL_SELF_MOD_KEY = "kernel_self_modification"

    # Delta actions that indicate a Tier-2 trigger directly.
    _PRODUCTION_DEPLOY_ACTIONS = frozenset(
        {"production_deploy", "deploy", "publish"}
    )
    _DESTRUCTIVE_ACTIONS = frozenset(
        {"delete", "destroy", "purge", "drop_table", "wipe"}
    )

    def classify(self, delta: Mapping[str, Any]) -> Trigger | None:
        """Return the first matching Tier-2 trigger, or None."""
        if not isinstance(delta, Mapping):
            return None

        action = delta.get(self._ACTION_KEY)
        if isinstance(action, str):
            if action in self._PRODUCTION_DEPLOY_ACTIONS:
                return Trigger.PRODUCTION_DEPLOY
            if action in self._DESTRUCTIVE_ACTIONS:
                return Trigger.DESTRUCTIVE_ACTION

        # Unsigned high-impact memory write — memory_tier == "high" and
        # memory_signed is not True.
        if delta.get(self._MEMORY_TIER_KEY) == "high" and not delta.get(
            self._MEMORY_SIGNED_KEY, False
        ):
            return Trigger.UNSIGNED_HIGH_IMPACT_MEMORY_WRITE

        # Sustained model-swap SLO breach — explicit boolean signal.
        if delta.get(self._MODEL_SWAP_BREACH_KEY) is True:
            return Trigger.SUSTAINED_MODEL_SWAP_SLO_BREACH

        # Bus-factor-1 adapter adoption without fallback — explicit signal.
        if delta.get(self._ADAPTER_BUS_FACTOR_KEY) == 1 and not delta.get(
            self._ADAPTER_HAS_FALLBACK_KEY, False
        ):
            return Trigger.BUS_FACTOR_1_ADAPTER_WITHOUT_FALLBACK

        # Retry-bound exhaustion — explicit boolean signal.
        if delta.get(self._RETRY_EXHAUSTED_KEY) is True:
            return Trigger.RETRY_BOUND_EXHAUSTION

        # Conflicting KB publish — explicit boolean signal.
        if delta.get(self._KB_CONFLICT_KEY) is True:
            return Trigger.CONFLICTING_KB_PUBLISH

        # Port version deprecation — explicit boolean signal.
        if delta.get(self._PORT_DEPRECATION_KEY) is True:
            return Trigger.PORT_VERSION_DEPRECATION

        # Kernel self-modification — explicit boolean signal.
        if delta.get(self._KERNEL_SELF_MOD_KEY) is True:
            return Trigger.KERNEL_SELF_MODIFICATION

        return None
