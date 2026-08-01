# Kosmos Porting Ledger

Every vendored, evaluated, or rejected OSS component. Required by
`Kosmos-Build-Spec-v25.md` §§48 & 252.

**Backfilled 2026-08-01 01:12 EDT** — this file was previously missing
from the repo root despite spec references. Entries below cover the
kernel bootstrap (new) plus placeholders for historical vendor
decisions already ratified in ADRs (see `docs/adrs/README.md` for
authoritative history through ADR-056).

Format per entry:

```
#### <Component> — <STATUS>
- **Source:** <upstream URL>
- **Commit / Version:** <SHA or tag>
- **License:** <SPDX>
- **Kosmos location:** `<path>`
- **Port(s):** <formal port name(s)>
- **Modifications:** <bullet list; "none" if unmodified>
- **ADR:** <ADR-###>
- **Logged:** <YYYY-MM-DD HH:MM EDT>
```

Statuses: `VENDORED` · `PATTERN-VENDORED` · `PLANNED` ·
`EVALUATED-REJECTED` · `SUPERSEDED`

---

## Kernel

#### FastAPI kernel bootstrap — HAND-BUILT (no vendor)
- **Source:** none — purpose-written for Kosmos
- **Commit / Version:** —
- **License:** MIT (Kosmos)
- **Kosmos location:** `kernel/app.py`, `kernel_ui_glue/`
- **Port(s):** none directly; composes `FrontendContractPort`,
  `ApprovalResolverPort`, `ResourcePort`, `NotificationPort`,
  `EventBusPort`
- **Modifications:** N/A
- **ADR:** ADR-057 (Stage 6.3 route surface) · ADR-052 (Stage 6.1
  skeleton)
- **Logged:** 2026-08-01 01:12 EDT
- **Notes:** Vendor-before-build check ratified 2026-08-01:
  Rigpa-LMS `plugin_kernel/` is plugin-side only (does not expose a
  kernel bootstrap surface); no permissively-licensed OSS candidate
  matches Kosmos's composed-port bootstrap requirement — closest
  Python scaffolds (`fastapi-mvc`, NestJS-style DI frameworks) all
  inject their own DI which conflicts with our formal-port Protocol
  seams. Hand-build ratified.


## Stage 6.5 · Zetesis Kernel Mount (ADR-058)

The following adapters go from `PLANNED` / `VENDORED` to `WIRED` at
Stage 6.5 — the kernel lifespan constructs each one via
`build_stage_6_5_zetesis_plugin()` and holds the resulting plugin
under `registry.zetesis`. Real backends (DozerDB compose, real Qdrant
client, OTEL collector) attach at Stage 6.5.1+.

#### DozerDbMemoryAdapter — WIRED
- **Source:** `adapters/memory/dozerdb/adapter.py`
- **Backend at 6.5:** `InMemoryGraphBackend` + `InMemoryTemporalIndex`
  + `NoOpAmgPolicy` (real DozerDB/Graphiti/AMG backends attach at
  6.5.1 once neo4j-compose is up on Colossus)
- **License:** MIT (Kosmos code) + GPLv3 (embedded DozerDB backend)
- **Kosmos location:** `plugins/zetesis/adapters/real/factory.py`
- **Port(s):** `MemoryPort`
- **Modifications:** none — factory wires seams via DI
- **ADR:** ADR-058 · ADR-027 (adapter shape) · ADR-047 (backend)
- **Logged:** 2026-08-01 01:36 EDT

#### QdrantVectorAdapter — WIRED
- **Source:** `adapters/vector/qdrant/adapter.py`
- **Backend at 6.5:** `InMemoryQdrantBackend` (spec-endorsed until
  Compose lands per adapter docstring §7)
- **License:** MIT
- **Kosmos location:** `plugins/zetesis/adapters/real/factory.py`
- **Port(s):** `VectorPort`
- **Modifications:** none
- **ADR:** ADR-058 · ADR-026 (adapter shape)
- **Logged:** 2026-08-01 01:36 EDT

#### FilesystemDataAdapter — WIRED
- **Source:** `adapters/data/filesystem/adapter.py`
- **Backend at 6.5:** on-disk storage rooted at
  `~/.local/state/kosmos/data` (created lazily on first write)
- **License:** MIT
- **Kosmos location:** `plugins/zetesis/adapters/real/factory.py`
- **Port(s):** `DataPort`
- **Modifications:** none
- **ADR:** ADR-058 · ADR-028 (adapter shape)
- **Logged:** 2026-08-01 01:36 EDT

#### OllamaAdapter — WIRED (via Zetesis plugin)
- **Source:** `adapters/llm/ollama/adapter.py`
- **Backend at 6.5:** local Ollama at `http://127.0.0.1:11434/v1`,
  default model `qwen2.5:32b-instruct-q4_K_M`
- **License:** MIT
- **Kosmos location:** `plugins/zetesis/adapters/real/factory.py`
- **Port(s):** `LLMPort`
- **Modifications:** none
- **ADR:** ADR-058 · ADR-022 (LLMPort surface)
- **Logged:** 2026-08-01 01:36 EDT

#### SearxngAdapter — WIRED (via Zetesis plugin)
- **Source:** `adapters/search/searxng/adapter.py`
- **Backend at 6.5:** local SearXNG at `http://127.0.0.1:8888`
- **License:** MIT
- **Kosmos location:** `plugins/zetesis/adapters/real/factory.py`
- **Port(s):** `SearchPort`
- **Modifications:** none
- **ADR:** ADR-058 · ADR-021 (SearchPort surface)
- **Logged:** 2026-08-01 01:36 EDT

#### OtelStackObservabilityAdapter — WIRED (via Zetesis plugin)
- **Source:** `adapters/observability/otel_stack/adapter.py`
- **Backend at 6.5:** `StubOtelBackend` (real OTEL collector attaches
  at 6.5.1+ once the observability compose service lands)
- **License:** MIT
- **Kosmos location:** `plugins/zetesis/adapters/real/factory.py`
- **Port(s):** `ObservabilityPort`
- **Modifications:** none
- **ADR:** ADR-058
- **Logged:** 2026-08-01 01:36 EDT

## Historical entries

Full history through ADR-056 lives in `docs/adrs/README.md`. Notable
vendored components (see linked ADRs for details):

- **docling 2.116.0** — MIT · PATTERN-VENDORED · ADR-044 · Stage 3.10
- **datacurve-pier 0.3.0** — Apache-2.0 · VENDORED (dev-only) ·
  ADR-042 · Stage 3.8
- **HTMX 2.0.4** — 0BSD · VENDORED · ADR-045 · Stage 3.11
- **OpenHands SDK** — MIT · PATTERN-VENDORED · ADR-036 · Stage 3.1
- **Open Deep Research** (`langchain-ai/open_deep_research@d337ae3`)
  — MIT · VENDORED · ADR-010 · Stage 6.2 (WINNER)
- **AREX-Turbo** (`BAAI/AREX-Turbo`) — Apache-2.0 ·
  EVALUATED-REJECTED (Stage 6.2) · ADR-010 · retained on-shelf with
  four-clause revisit gate
- **agent-memory-guard 0.3.0** — Apache-2.0 · VENDORED · ADR-048 ·
  Stage 4.3
- **DozerDB 5.26.27** — GPLv3 (embedded backend only) · VENDORED ·
  ADR-047 · Stage 4.2
- **Graphiti** — Apache-2.0 · VENDORED · ADR-027 · Stage 4.2
- **SuttaCentral Bilara** — CC0 · VENDORED (data corpus) · ADR-050 ·
  Stage 4.5
- **Superpowers KB** — MIT · VENDORED (data corpus) · ADR-049 ·
  Stage 4.4

New adopts, evaluations, and rejections must be appended to
this file **at the same time** as the ADR that ratifies them, per
`kosmos-spec-diff` skill fan-out rules.
