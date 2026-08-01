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


## Stage 1.5 · Kosmos UI Persistent Shell (ADR-068)

The Next.js UI at `ui/` composes these permissively-licensed OSS
components behind the `FrontendContractPort` React client
(`ui/lib/kernel-client.ts`). All are node_modules dependencies, not
vendored source trees; SPDX license verified on every version listed.

#### next 16 + react 19 + react-dom 19 — DEPENDED-ON
- **Source:** https://github.com/vercel/next.js · https://github.com/facebook/react
- **Commit / Version:** next `16.0.0`, react/react-dom `19.0.0`
- **License:** MIT
- **Kosmos location:** `ui/` (Next.js `app/` router, static export `output: "export"`)
- **Port(s):** none directly; consumes `FrontendContractPort` schema
- **Modifications:** none
- **ADR:** ADR-067 (Stage 1 shell) · ADR-068 (Stage 1.5 realization)
- **Logged:** 2026-08-01 06:12 EDT

#### tailwindcss v4 (with Five-Wisdom OKLCH `@theme`) — DEPENDED-ON
- **Source:** https://github.com/tailwindlabs/tailwindcss
- **Commit / Version:** `^4.0.0`
- **License:** MIT
- **Kosmos location:** `ui/app/globals.css` (`@theme` block)
- **Port(s):** none
- **Modifications:** none — pure config; Tibetan Five Buddha Family palette
  authored in-tree as OKLCH tokens, hydratable at runtime from
  `/api/kernel/design-tokens` via `DesignTokenHydrator`.
- **ADR:** ADR-068
- **Logged:** 2026-08-01 06:12 EDT

#### @radix-ui/react-dialog — DEPENDED-ON
- **Source:** https://github.com/radix-ui/primitives
- **Commit / Version:** `^1.1.0`
- **License:** MIT
- **Kosmos location:** `ui/components/PersistentShell.tsx`,
  `ui/components/CommandPalette.tsx`, `ui/components/KillSwitch.tsx`
- **Port(s):** none — provides Radix `Sheet`-equivalent (contextual
  drawer), Cmd+K modal, and kill-switch confirmation dialog
- **Modifications:** none
- **ADR:** ADR-068
- **Logged:** 2026-08-01 06:12 EDT

#### cmdk — DEPENDED-ON
- **Source:** https://github.com/pacocoursey/cmdk
- **Commit / Version:** `^1.0.0`
- **License:** MIT
- **Kosmos location:** `ui/components/CommandPalette.tsx`
- **Port(s):** none — a11y-correct combobox for the Cmd+K palette per
  UX Design Spec §"Persistent Shell"
- **Modifications:** none — wraps a static navigation list in Wave A;
  Wave B swaps in kernel-schema-driven commands
- **ADR:** ADR-068
- **Logged:** 2026-08-01 06:12 EDT

#### @tanstack/react-query — DEPENDED-ON (Wave B onward)
- **Source:** https://github.com/TanStack/query
- **Commit / Version:** `^5.60.0`
- **License:** MIT
- **Kosmos location:** `ui/` (installed; not yet consumed — Wave A uses
  plain `useEffect` + `fetch` via `kernelClient`; Wave B introduces the
  QueryClient provider and per-port hooks)
- **Port(s):** none
- **Modifications:** none
- **ADR:** ADR-068
- **Logged:** 2026-08-01 06:12 EDT

#### zustand — DEPENDED-ON (Wave B onward)
- **Source:** https://github.com/pmndrs/zustand
- **Commit / Version:** `^5.0.0`
- **License:** MIT
- **Kosmos location:** `ui/` (installed; not yet consumed — Wave B
  introduces per-`state_namespace` store per UX Design Spec §"Stack
  Validation")
- **Port(s):** none
- **Modifications:** none
- **ADR:** ADR-068
- **Logged:** 2026-08-01 06:12 EDT


### Stage 1.5 Wave D · UI dependencies (MEMORY_INTEGRITY graph)

#### cytoscape — VENDORED
- **Source:** https://github.com/cytoscape/cytoscape.js
- **Commit / Version:** `^3.30.0`
- **License:** MIT
- **Kosmos location:** `ui/` (npm dep; consumed inside
  `ui/components/panels/MemoryIntegrityPanel.tsx` only — never
  imported by other components)
- **Port(s):** none — client-side graph rendering surface for the
  MEMORY_INTEGRITY panel per UX Design Spec §"Data-Type Taxonomy" #1
- **Modifications:** none
- **ADR:** ADR-070
- **Logged:** 2026-08-01 07:19 EDT

#### react-cytoscapejs — VENDORED
- **Source:** https://github.com/plotly/react-cytoscapejs
- **Commit / Version:** `^2.0.0`
- **License:** MIT
- **Kosmos location:** `ui/` (npm dep; thin React binding for cytoscape,
  consumed inside `ui/components/panels/MemoryIntegrityPanel.tsx` only)
- **Port(s):** none
- **Modifications:** none
- **ADR:** ADR-070
- **Logged:** 2026-08-01 07:19 EDT

#### DDC Uchen font (Christopher John Fynn, 2010) — VENDORED (font asset)
- **Source:** upstream distribution
  `https://deb.debian.org/debian/pool/main/f/fonts-ddc-uchen/fonts-ddc-uchen_1.0.orig.tar.gz`
  (identical binary to Chris Fynn's original release for the Dzongkha
  Development Commission of Bhutan)
- **Commit / Version:** `1.0` (Debian `orig.tar.gz`, single-file tarball
  containing `DDC_Uchen.ttf`; sha256 verifiable at build time)
- **License:** SIL Open Font License 1.1 (embedded name records IDs
  13 + 14; `OFL.txt` bundled beside the font per OFL clause 2 as an
  accompanying text file)
- **Kosmos location:** `ui/public/fonts/ddc-uchen/DDC_Uchen.woff2` plus
  `ui/public/fonts/ddc-uchen/OFL.txt` (converted TTF→woff2 via fonttools
  4.x; only compression format changed, not the underlying font tables)
- **Port(s):** none (static asset consumed by `@font-face` in
  `ui/app/globals.css` — the Kosmos wordmark and job-page display
  headings; wired via `--font-display: "DDC Uchen", ...`)
- **Modifications:** container format only (TTF→woff2, brotli-compressed
  Font Table Directory per WOFF2 spec). No glyph, kerning, name-record,
  or license-metadata modification. Reserved Font Name "DDC Uchen"
  preserved unmodified per OFL clause 3.
- **ADR:** ADR-072
- **Logged:** 2026-08-01 09:04 EDT

## Stage 1.6 Phase 0 · EmbeddingsPort (ADR-073)

#### httpx — EmbeddingsPort transport (continued satisfaction)
- **Source:** https://github.com/encode/httpx
- **Commit / Version:** already vendored per Stage 6.5.6 (ADR-063); no new version bump.
- **License:** BSD-3-Clause (SPDX)
- **Kosmos location:** `adapters/embeddings/ollama/adapter.py` (imports only)
- **Port(s):** `EmbeddingsPort` (transport layer; not a vendored implementation of the port itself)
- **Modifications:** none
- **ADR:** ADR-073
- **Logged:** 2026-08-01 10:35 EDT

No other new vendored components: ``OllamaEmbeddingsAdapter`` calls
Ollama's native ``/api/embed`` endpoint directly via ``httpx``. The
``EmbeddingsPort`` protocol itself is Kosmos-original code (no OSS port
vendored). Graphiti's ``EmbedderClient`` shape is duck-typed via
``KosmosGraphitiEmbedder`` — no `graphiti_core` API surface is vendored
into Kosmos beyond the existing memory adapter usage.


## Stage 1.6 Phase 1 · Semantic memory + graph visualization (ADR-074)

#### qdrant-client — VectorPort real backend (continued satisfaction)
- **Source:** https://github.com/qdrant/qdrant-client
- **Commit / Version:** already declared as `qdrant-client>=1.11` in
  `pyproject.toml`; no new version bump. Live-tier binding lands in
  Phase 1 with `adapters/vector/qdrant/real_backend.py`.
- **License:** Apache-2.0 (SPDX)
- **Kosmos location:** `adapters/vector/qdrant/real_backend.py`
  (lazy `AsyncQdrantClient` import inside `__init__`)
- **Port(s):** `VectorPort` via `QdrantBackend` seam (ADR-026)
- **Modifications:** none — Kosmos adds a wrapper backend around
  `AsyncQdrantClient` implementing the `QdrantBackend` Protocol.
- **ADR:** ADR-074
- **Logged:** 2026-08-01 11:05 EDT

#### qdrant image — Kosmos-owned Qdrant service (VENDORED)
- **Source:** https://hub.docker.com/r/qdrant/qdrant
- **Commit / Version:** `qdrant/qdrant:v1.12.1` (pinned image tag)
- **License:** Apache-2.0 (SPDX)
- **Kosmos location:** `ops/compose/memory.yml` service `qdrant`
  (container_name `kosmos-qdrant`); host ports **6339** REST /
  **6340** gRPC. Kernel env `KOSMOS_QDRANT_URL=http://127.0.0.1:6339`
  in `ops/systemd/kosmos-kernel.env`.
- **Port(s):** backs `VectorPort` via `RealQdrantBackend`
  (`adapters/vector/qdrant/real_backend.py`); no new port introduced.
- **Modifications:** none — stock upstream image. Kosmos-owned host
  ports 6339/6340 chosen to avoid the UIA project's Qdrant on
  6371/6372 on the same workstation.
- **ADR:** ADR-076 (Stage 1.6 Phase 3 live-tier target)
- **Logged:** 2026-08-01 14:05 EDT

#### react-force-graph-2d — DimensionalForceGraph 2D renderer
- **Source:** https://github.com/vasturiano/react-force-graph
- **Commit / Version:** ^1.29.1 (npm)
- **License:** MIT (SPDX)
- **Kosmos location:** `ui/components/graph/DimensionalForceGraph.tsx`
  (SSR-off dynamic import from `ui/app/gnosis/graph/page.tsx`)
- **Port(s):** none — DOM-only rendering component; consumed via
  `next/dynamic({ ssr: false })`
- **Modifications:** none (unmodified npm dep)
- **ADR:** ADR-074
- **Logged:** 2026-08-01 11:05 EDT

#### react-force-graph-3d — DimensionalForceGraph 3D renderer
- **Source:** https://github.com/vasturiano/react-force-graph
- **Commit / Version:** ^1.29.1 (npm)
- **License:** MIT (SPDX)
- **Kosmos location:** `ui/components/graph/DimensionalForceGraph.tsx`
- **Port(s):** none — DOM-only
- **Modifications:** none
- **ADR:** ADR-074
- **Logged:** 2026-08-01 11:05 EDT

#### three — WebGL runtime for react-force-graph-3d
- **Source:** https://github.com/mrdoob/three.js
- **Commit / Version:** ^0.185.1 (runtime), ^0.185.0 (types)
- **License:** MIT (SPDX)
- **Kosmos location:** transitive dep of `react-force-graph-3d`
- **Port(s):** none — pure WebGL runtime
- **Modifications:** none
- **ADR:** ADR-074
- **Logged:** 2026-08-01 11:05 EDT

#### DimensionalForceGraph.tsx — Rigpa-LMS donor
- **Source:** https://github.com/rmholston420/Rigpa-LMS
- **Commit / Version:** 2026-08-01 clone (Apache-2.0)
- **License:** Apache-2.0 (SPDX)
- **Kosmos location:** `ui/components/graph/DimensionalForceGraph.tsx`
- **Port(s):** none — presentational React component
- **Modifications:** dropped Vite-specific `import.meta.env.DEV` demo
  affordance (Next.js does not expose that global); tightened prop
  types to the shared 2D/3D intersection surface; renamed export to
  match Kosmos file naming.
- **ADR:** ADR-074
- **Logged:** 2026-08-01 11:05 EDT

#### graphDimensionStore.ts — Rigpa-LMS donor
- **Source:** https://github.com/rmholston420/Rigpa-LMS
- **Commit / Version:** 2026-08-01 clone (Apache-2.0)
- **License:** Apache-2.0 (SPDX)
- **Kosmos location:** `ui/lib/graph/graphDimensionStore.ts`
- **Port(s):** none — Zustand store
- **Modifications:** renamed persistence key
  `rigpa-graph-dimension` → `kosmos-graph-dimension`; removed
  demo-data flag branch (single-user local-first).
- **ADR:** ADR-074
- **Logged:** 2026-08-01 11:05 EDT

#### GraphDimensionToggle.tsx — Rigpa-LMS donor
- **Source:** https://github.com/rmholston420/Rigpa-LMS
- **Commit / Version:** 2026-08-01 clone (Apache-2.0)
- **License:** Apache-2.0 (SPDX)
- **Kosmos location:** `ui/components/graph/GraphDimensionToggle.tsx`
- **Port(s):** none
- **Modifications:** dropped the Vite dev-only “Demo data” checkbox;
  restyled with Kosmos design-token CSS variables
  (`--space-1/2`, `--color-*`).
- **ADR:** ADR-074
- **Logged:** 2026-08-01 11:05 EDT

#### bubblewrap (`bwrap`) — SYSTEM-BINARY
- **Source:** [containers/bubblewrap](https://github.com/containers/bubblewrap)
- **Commit / Version:** system-packaged `0.11.1` on Kubuntu 26.04
- **License:** LGPL-2.0-or-later (system binary invoked as subprocess; no source copied or linked)
- **Kosmos location:** `adapters/sandbox/gitworktree/adapter.py` (subprocess invocation only)
- **Port(s):** `SandboxProvider`
- **Modifications:** none — invoked as `bwrap --die-with-parent --unshare-{net,pid,uts,ipc} --ro-bind ... --bind <worktree> ... --chdir ... -- <argv>`
- **ADR:** ADR-079 (chose bubblewrap over `python-landlock`: bwrap gives mount-namespace read-only overlays, seccomp, network unshare, and pid-namespace in one binary; §156 subprocess-boundary inheritance satisfied by namespace construction; zero new pip deps)
- **Logged:** 2026-08-01 17:22 EDT

## Stage 3.14b · Tektos Executor (ADR-080)

#### loop_guard — VENDORED (Forge-OH donor)
- **Source:** [rmholston420/Forge-OH `bff/services/loop_guard.py`](https://github.com/rmholston420/Forge-OH/blob/9e7209d/bff/services/loop_guard.py)
- **Commit / Version:** `9e7209d` (Forge-OH `main`, LICENSE added 2026-08-01)
- **License:** MIT (SPDX: MIT)
- **Kosmos location:** `plugins/tektos/executor/loop_guard.py`
- **Port(s):** none (executor-internal helper)
- **Modifications:** module-level docstring rewrite documenting Kosmos usage + provenance block; `Deque[str]` typing modernized to `deque[str]`; `ActionFingerprint` hardened with `frozen=True, slots=True` (upstream was a plain mutable `@dataclass` — upstream never mutates instances so this is a strengthening, not a semantic change, but callers that mutated fields would now raise `FrozenInstanceError`). `LoopGuard` public API (`fingerprint`, `is_looping`, `suggest_escalation`, `reset`) and window+threshold semantics unchanged. Consumed by `TektosExecutorLoop.run_plan` between attempts to detect the LLM emitting the same failing diff shape twice; when `is_looping` fires, the loop escalates via `suggest_escalation` and skips attempt 2. Under ADR-080's `TEKTOS_EXECUTOR_MAX_ATTEMPTS = 2` retry budget the default `threshold=3` never fires within a single plan — the vendored code is kept intact so 3.15+ can widen retries without a re-port.
- **ADR:** ADR-080
- **Logged:** 2026-08-01 17:43 EDT (PLANNED); 2026-08-01 17:54 EDT (VENDORED, kosmos commit forthcoming this session)

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
