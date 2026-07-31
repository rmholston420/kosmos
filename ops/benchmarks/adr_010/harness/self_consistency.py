"""Backward-compat shim per ADR-056 §D1 (Stage 6.3 (proper) sub-slice 1).

Module lifted to `plugins.zetesis.research.self_consistency`. This shim aliases the
old import path to the new module via `sys.modules` so every existing
`from ops.benchmarks.adr_010.harness.self_consistency import X` and
`from ops.benchmarks.adr_010.harness import self_consistency` call site continues to
work without change. Public API + private symbols + module attributes
are all identical because the two paths resolve to the same module object.

See `docs/adrs/ADR-056-stage-6-3-proper-zetesis-kernel-wiring.md`.
"""
from __future__ import annotations

import sys as _sys

from plugins.zetesis.research import self_consistency as _mod

_sys.modules[__name__] = _mod
