"""Zetesis — Kosmos research plugin (Stage 6.1, ADR-052).

Stage 6.1 is a pure skeleton: DoD is literally "Plugin loads." The plugin
takes exactly four ports — :class:`~ports.llm.LLMPort`,
:class:`~ports.memory.MemoryPort`, :class:`~ports.vector.VectorPort`,
:class:`~ports.data.DataPort` — matching Build-Sequence §6.1.

Zetesis 6.1 is inner-loop-agnostic. The AREX-vs-Open-Deep-Research
head-to-head that resolves ADR-010 happens pre-Phase-6.2. No `LLMPort`
call, no vector search, no research-pipeline scaffolding at 6.1.

Per spec §191 + Build-Sequence §1.6 + ADR-052 §Q5=C, the real
:class:`ZetesisPlugin` also serves as the `zetesis-stub` fixture stub
that Tektos's Phase-10 model-swap-under-load scenario binds to. There
is no separate stub package.

ADR-007: this package imports only from ``ports.*`` and its own
submodules. It MUST NOT import any other plugin.
"""

from __future__ import annotations

from plugins.zetesis.plugin import (
    ZETESIS_KERNEL_COMPAT,
    ZETESIS_MEMORY_DEFAULT_CONFIDENCE,
    ZETESIS_MEMORY_PREDICATE,
    ZETESIS_MEMORY_PROVENANCE,
    ZETESIS_PLUGIN_NAME,
    ZETESIS_STATE_NAMESPACE,
    ZETESIS_VERSION,
    ZetesisPlugin,
    build_zetesis_descriptor,
)

__all__ = [
    "ZETESIS_KERNEL_COMPAT",
    "ZETESIS_MEMORY_PREDICATE",
    "ZETESIS_MEMORY_PROVENANCE",
    "ZETESIS_MEMORY_DEFAULT_CONFIDENCE",
    "ZETESIS_PLUGIN_NAME",
    "ZETESIS_STATE_NAMESPACE",
    "ZETESIS_VERSION",
    "ZetesisPlugin",
    "build_zetesis_descriptor",
]
