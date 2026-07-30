"""Contract tests for EscalationPolicy (ADR-033 · spec §14).

Every spec §14 trigger must have a matching classify() branch, and
unknown deltas must return None (conservative default).
"""

from __future__ import annotations

import pytest

from plugins.praxis.apex import EscalationPolicy, Trigger


@pytest.fixture
def policy() -> EscalationPolicy:
    return EscalationPolicy()


class TestEscalationPolicyClassifyReturnsTrigger:
    def test_production_deploy_action(self, policy):
        assert (
            policy.classify({"action": "production_deploy"})
            == Trigger.PRODUCTION_DEPLOY
        )

    def test_deploy_action_alias(self, policy):
        assert policy.classify({"action": "deploy"}) == Trigger.PRODUCTION_DEPLOY

    def test_publish_action_alias(self, policy):
        assert policy.classify({"action": "publish"}) == Trigger.PRODUCTION_DEPLOY

    def test_destructive_delete(self, policy):
        assert (
            policy.classify({"action": "delete"}) == Trigger.DESTRUCTIVE_ACTION
        )

    def test_destructive_purge(self, policy):
        assert (
            policy.classify({"action": "purge"}) == Trigger.DESTRUCTIVE_ACTION
        )

    def test_unsigned_high_impact_memory_write(self, policy):
        assert (
            policy.classify({"memory_tier": "high", "memory_signed": False})
            == Trigger.UNSIGNED_HIGH_IMPACT_MEMORY_WRITE
        )

    def test_signed_high_impact_memory_write_is_not_trigger(self, policy):
        assert (
            policy.classify({"memory_tier": "high", "memory_signed": True})
            is None
        )

    def test_low_impact_memory_write_is_not_trigger(self, policy):
        assert policy.classify({"memory_tier": "low"}) is None

    def test_sustained_model_swap_slo_breach(self, policy):
        assert (
            policy.classify({"model_swap_slo_breach_sustained": True})
            == Trigger.SUSTAINED_MODEL_SWAP_SLO_BREACH
        )

    def test_bus_factor_1_no_fallback(self, policy):
        assert (
            policy.classify({"adapter_bus_factor": 1, "adapter_has_fallback": False})
            == Trigger.BUS_FACTOR_1_ADAPTER_WITHOUT_FALLBACK
        )

    def test_bus_factor_1_with_fallback_is_not_trigger(self, policy):
        assert (
            policy.classify({"adapter_bus_factor": 1, "adapter_has_fallback": True})
            is None
        )

    def test_bus_factor_2_no_fallback_is_not_trigger(self, policy):
        assert (
            policy.classify({"adapter_bus_factor": 2, "adapter_has_fallback": False})
            is None
        )

    def test_retry_bound_exhaustion(self, policy):
        assert (
            policy.classify({"retry_exhausted": True})
            == Trigger.RETRY_BOUND_EXHAUSTION
        )

    def test_conflicting_kb_publish(self, policy):
        assert (
            policy.classify({"kb_conflict": True})
            == Trigger.CONFLICTING_KB_PUBLISH
        )

    def test_port_version_deprecation(self, policy):
        assert (
            policy.classify({"port_version_deprecation": True})
            == Trigger.PORT_VERSION_DEPRECATION
        )

    def test_kernel_self_modification(self, policy):
        assert (
            policy.classify({"kernel_self_modification": True})
            == Trigger.KERNEL_SELF_MODIFICATION
        )


class TestEscalationPolicyReturnsNoneConservatively:
    def test_empty_delta_returns_none(self, policy):
        assert policy.classify({}) is None

    def test_unknown_action_returns_none(self, policy):
        assert policy.classify({"action": "read"}) is None
        assert policy.classify({"action": "update_metadata"}) is None

    def test_unknown_signal_returns_none(self, policy):
        assert policy.classify({"random_key": "random_value"}) is None

    def test_non_mapping_input_returns_none(self, policy):
        assert policy.classify(None) is None  # type: ignore[arg-type]
        assert policy.classify("not a mapping") is None  # type: ignore[arg-type]

    def test_non_boolean_signals_do_not_fire(self, policy):
        """Explicit-boolean-True signals must not fire on truthy non-bools."""
        # Only exact True triggers — this preserves conservative-by-default.
        assert policy.classify({"retry_exhausted": 1}) is None
        assert policy.classify({"retry_exhausted": "yes"}) is None
        assert policy.classify({"kb_conflict": "yes"}) is None


class TestEscalationPolicyPriorityOrder:
    def test_action_trigger_shadows_boolean_signal(self, policy):
        """Action-based triggers evaluate first."""
        # Both are Tier-2, but action fires first.
        got = policy.classify(
            {"action": "delete", "retry_exhausted": True}
        )
        assert got == Trigger.DESTRUCTIVE_ACTION


class TestEscalationPolicyCoversAllSpec14Triggers:
    def test_all_nine_triggers_reachable_via_classify(self, policy):
        """Sanity check: every spec §14 trigger enum has a classify() branch."""
        fixtures = {
            Trigger.PRODUCTION_DEPLOY: {"action": "production_deploy"},
            Trigger.DESTRUCTIVE_ACTION: {"action": "delete"},
            Trigger.UNSIGNED_HIGH_IMPACT_MEMORY_WRITE: {
                "memory_tier": "high",
                "memory_signed": False,
            },
            Trigger.SUSTAINED_MODEL_SWAP_SLO_BREACH: {
                "model_swap_slo_breach_sustained": True,
            },
            Trigger.BUS_FACTOR_1_ADAPTER_WITHOUT_FALLBACK: {
                "adapter_bus_factor": 1,
                "adapter_has_fallback": False,
            },
            Trigger.RETRY_BOUND_EXHAUSTION: {"retry_exhausted": True},
            Trigger.CONFLICTING_KB_PUBLISH: {"kb_conflict": True},
            Trigger.PORT_VERSION_DEPRECATION: {
                "port_version_deprecation": True
            },
            Trigger.KERNEL_SELF_MODIFICATION: {
                "kernel_self_modification": True
            },
        }
        assert set(fixtures.keys()) == set(Trigger)
        for trigger, delta in fixtures.items():
            assert policy.classify(delta) == trigger, trigger
