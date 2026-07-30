"""Auto-installed test fixtures for the ADR-010 harness.

Stage 6.3.4f introduced shim 10 (enterprise-license grounding), which by
default fetches ``https://neo4j.com/open-core-and-neo4j/``. Every ODR
integration test in this package invokes ``run_odr_trial`` and would
otherwise touch the live network. This conftest stubs the fetch
autouse so tests remain hermetic.

Tests that specifically exercise shim 10 opt out by depending on the
module directly and re-patching in their own test bodies.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _stub_enterprise_license_grounding(monkeypatch, request):
    """Replace shim 10's live fetch with a no-op returning empty facts.

    Tests that want to exercise shim 10 with a real or custom stub can
    add the marker ``@pytest.mark.no_stub_enterprise_license`` on the
    test function to opt out.
    """
    if request.node.get_closest_marker("no_stub_enterprise_license"):
        return
    from ops.benchmarks.adr_010.harness import enterprise_license_grounding

    async def _noop(**_kwargs):
        return []

    monkeypatch.setattr(
        enterprise_license_grounding, "ground_enterprise_license", _noop
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_stub_enterprise_license: opt out of the shim-10 network stub",
    )
