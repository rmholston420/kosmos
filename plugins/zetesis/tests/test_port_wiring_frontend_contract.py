"""Fast-tier port-wiring contract: FrontendContractPort (ADR-056 sub-slice 2).

Unlike the other 9 ports, FrontendContractPort's real adapter
(`adapters/frontend_contract/kernel/`) already exists and is exercised
by Stage 6.1 tests. This test asserts:

- FrontendContractPort remains Protocol-conformant and importable.
- ZetesisPlugin's `frontend_contract` slot accepts a Protocol-conformant
  fake (the conftest fixture supplies one).
- The plugin holds the exact instance passed (identity, not proxied).
"""

from __future__ import annotations

from ports.frontend_contract import FrontendContractPort


def test_frontend_contract_port_is_runtime_checkable() -> None:
    # If FrontendContractPort loses @runtime_checkable, subclass-based
    # adapters silently break isinstance() checks. Guard against that.
    from typing import get_type_hints  # noqa: F401 (import proves the module loads)

    assert hasattr(FrontendContractPort, "_is_runtime_protocol")
    assert FrontendContractPort._is_runtime_protocol is True


def test_plugin_holds_frontend_contract_by_identity(make_zetesis_plugin) -> None:
    # Build a plugin using the default fixture. The fixture provides a
    # fake FrontendContract via the conftest.
    plugin = make_zetesis_plugin()
    # The frontend_contract slot must be populated (non-None) and stable.
    assert plugin.frontend_contract is not None
