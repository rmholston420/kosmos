"""Tektos plugin namespace (ADR-035, Stage 2.4 stub).

At Stage 2.4 this package hosts **only** the test-only
:class:`~plugins.tektos.stub.TektosSimulator` harness that publishes
``TraceEvent(plugin="tektos", ...)`` on a :class:`~ports.trace_feed.TraceFeedPort`.
The real Tektos coding plugin (with :class:`PluginDescriptor`,
``AGENT_TRACE`` panel, and full lifecycle) lands at Stage 3 and will
grow into this package alongside — or in place of — the ``stub``
subpackage.

**Do not** import Tektos from any other plugin at Stage 2.4. The
simulator has no lifecycle, no state, and no cross-plugin coupling by
design.
"""

from __future__ import annotations

__all__: list[str] = []
