"""adapters.memory.dozerdb.amg_v02_policy — Backwards-compat shim (ADR-048).

The AMG adapter was renamed at Stage 4.3 when we bumped
`agent-memory-guard` from 0.2.2 → 0.3.0. New code should import from
`adapters.memory.dozerdb.amg_policy`.

This module is retained for one release cycle so downstream imports
`from adapters.memory.dozerdb.amg_v02_policy import AmgV02Policy` keep
working. Remove at Stage 5.
"""

from __future__ import annotations

from adapters.memory.dozerdb.amg_policy import AmgGuardPolicy, AmgV02Policy

__all__ = ["AmgGuardPolicy", "AmgV02Policy"]
