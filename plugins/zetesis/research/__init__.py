"""Zetesis research subpackage.

Re-exports the inner-loop entry points so callers use the stable
package-level names without depending on the physical module layout.

- ``run_zetesis_research`` — canonical async entry point, alias of
  :func:`plugins.zetesis.research.odr.run_odr_trial`.
- ``build_zetesis_research_config`` — canonical config builder, alias of
  :func:`plugins.zetesis.research.odr.build_odr_config`.
"""

from __future__ import annotations

from plugins.zetesis.research.odr import (
    build_zetesis_research_config,
    run_zetesis_research,
)

__all__ = [
    "build_zetesis_research_config",
    "run_zetesis_research",
]
