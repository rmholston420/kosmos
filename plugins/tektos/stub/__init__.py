"""Test-only Tektos stub (ADR-035 Q6=A).

This subpackage exists **only** so the Stage-2 exit-gate scenario can
publish ``TraceEvent(plugin="tektos", ...)`` events on a
:class:`~ports.trace_feed.TraceFeedPort` without pre-committing the
real Stage-3 Tektos plugin's shape (descriptor, panels, kernel_compat).

The :class:`TektosSimulator` here is a plain dataclass composed with a
:class:`TraceFeedPort`. It has:

- **no** :class:`PluginDescriptor`
- **no** ``FrontendContractPort`` registration
- **no** ``AGENT_TRACE`` panel
- **no** start/stop lifecycle
- **no** state persistence

It will be **deleted or superseded** at Stage 3 when the real Tektos
plugin lands.
"""

from __future__ import annotations

from plugins.tektos.stub.simulator import TektosSimulator

__all__ = ["TektosSimulator"]
