"""Tektos intention → OpenSpec change scaffolder (Stage 3.13).

Public surface:

* :data:`INTENTION_ROOT_ENV` — env var naming the scaffold destination
  root (defaults to ``$XDG_STATE_HOME/kosmos/tektos/intentions`` or
  ``~/.local/state/kosmos/tektos/intentions``).
* :data:`INTENTION_PROVENANCE` — the fixed provenance string every
  MemoryPort write from this module carries. Distinct from
  :data:`plugins.tektos.models.TEKTOS_AGENT_PROVENANCE` (chat) and
  :data:`plugins.tektos.ui.policy.TEKTOS_UI_PROVENANCE` (HTMX surface).
* :func:`scaffold_intention` — deterministic string → change directory
  writer (writes ``proposal.md`` + optional ``tasks.md``). No LLM at
  this tier; interactive Ollama tier is Stage 3.14 territory.
* :func:`intention_to_change_id` — pure slug function; safe to call in
  either sync or async contexts.

ADR-077 (Ratified v25): allocates Stages 3.13/3.14/3.15 under v25's
Phase 3 extension after v25 §3.12 exit gate landed. Locks Stage 3.13
scope as *intention → deterministic scaffold → plan produced →
plan-card gated*, with no code execution (that is Stage 3.14+).
"""

from __future__ import annotations

from .policy import (
    INTENTION_PROVENANCE,
    INTENTION_ROOT_ENV,
    INTENTION_SCAFFOLD_PREDICATE,
    INTENTION_WRITE_CONFIDENCE,
    MAX_INTENTION_LENGTH,
    MIN_INTENTION_LENGTH,
)
from .scaffolder import (
    IntentionScaffoldError,
    ScaffoldResult,
    intention_to_change_id,
    resolve_intention_root,
    scaffold_intention,
)

__all__ = [
    "INTENTION_PROVENANCE",
    "INTENTION_ROOT_ENV",
    "INTENTION_SCAFFOLD_PREDICATE",
    "INTENTION_WRITE_CONFIDENCE",
    "IntentionScaffoldError",
    "MAX_INTENTION_LENGTH",
    "MIN_INTENTION_LENGTH",
    "ScaffoldResult",
    "intention_to_change_id",
    "resolve_intention_root",
    "scaffold_intention",
]
