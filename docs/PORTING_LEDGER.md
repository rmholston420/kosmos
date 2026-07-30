# Kosmos Porting Ledger

**Rule:** Every OSS component vendored into Kosmos MUST be logged here **before** first commit that uses it. No exceptions.

**Fields per entry:**
- **Name** — canonical component name
- **Source** — upstream URL
- **Commit / Version** — exact SHA or release tag pinned
- **License** — SPDX identifier (only permissive: MIT, BSD-2/3, Apache-2.0, ISC, MPL-2.0)
- **Kosmos location** — where it lives in the repo
- **Port(s) used** — which formal port(s) it plugs into
- **Modifications** — bullet list of local changes; "none" if unmodified
- **ADR** — referencing ADR if any
- **Logged** — timestamp

**Status codes:** `PLANNED` (approved, not yet vendored) · `VENDORED` (in tree) · `EVALUATING` (spike/bench) · `REJECTED` (design reference only, do not vendor) · `SUPERSEDED` (replaced by another entry)

---

## Kernel-Layer Ports

### LLM stack

#### Ollama (consolidated adapter) — `VENDORED (Stage 1.1)`
- **Source (upstream runtime):** https://github.com/ollama/ollama (service; not vendored — runs as system service)
- **Adapter donor sources consolidated:**
  - [Rigpa-LMS/backend/src/rigpa/core/llm/ollama.py](https://github.com/rmholston420/Rigpa-LMS/blob/main/backend/src/rigpa/core/llm/ollama.py) — most complete: chat + generate + embed + model mgmt + lifecycle + singleton
  - [Rigpa-LMS/backend/src/rigpa/domains/integrations/ollama.py](https://github.com/rmholston420/Rigpa-LMS/blob/main/backend/src/rigpa/domains/integrations/ollama.py) — model list/pull/delete (folded into core)
  - [axiom/packages/axiom_providers/ollama.py](https://github.com/rmholston420/axiom/blob/main/packages/axiom_providers/ollama.py) — adds streaming (`generate_stream` via `httpx.stream`)
- **License:** MIT (Ollama upstream); donor code is user-authored under `rmholston420/*` (relicensable)
- **Kosmos location:** `adapters/llm/ollama/`
- **Port(s):** `LLMPort`
- **Modifications from consolidation:**
  - Base = Rigpa `core/llm/ollama.py` (async client + singleton + full API coverage)
  - Add streaming from axiom (`generate_stream`, `chat_stream`)
  - Drop Rigpa `domains/integrations/ollama.py` typed model schemas (fold into core; single `list_models` returning list[dict])
  - Keyword-only kwargs throughout (align with Kosmos convention seen in axiom)
  - Wrap all methods behind `LLMPort` Protocol
- **ADR:** ADR-012 (donor adapter consolidation) + ADR-022 (LLMPort surface expansion — defines the 10-method Protocol this adapter satisfies)
- **Logged:** 2026-07-29 21:05 EDT

#### llama-swap — `VENDORED` (Stage 1.3)
- **Source:** https://github.com/mostlygeek/llama-swap
- **Commit / Version:** `0c4233363ec589c439b7f7d12eaae2346811098d` (2026-07-28)
- **License:** MIT
- **Kosmos location:** `adapters/llm/llama_swap/` (HTTP-client adapter only; llama-swap runs as external Go daemon, not vendored source)
- **Port(s):** `LLMPort` (second adapter satisfying the Protocol — proves swappability against ADR-022 surface)
- **Modifications:**
  - HTTP-client adapter targets the OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, `/v1/models`)
  - `generate` / `generate_text` implemented via `/v1/completions`
  - `chat` implemented via `/v1/chat/completions`
  - `generate_stream` implemented via SSE on `/v1/completions?stream=true`
  - `list_models` implemented via `/v1/models`
  - `pull_model` / `delete_model` raise `NotImplementedError` — llama-swap does not manage weights (models are pre-declared in its `config.yaml`). Documented capability subset per ADR-022 Consequences §Downstream stages
  - `is_healthy` uses `/health` (llama-swap-native), non-throwing per ADR-022 rule 3
- **ADR:** ADR-009 (llama-swap primary sidecar) + ADR-022 (LLMPort surface)
- **Logged:** 2026-07-29 21:35 EDT

#### router-mode fallback — `PLANNED (fallback only)`
- **Source:** internal build using llama.cpp server routes
- **License:** MIT (llama.cpp)
- **Port(s):** LLMPort
- **ADR:** ADR-009
- **Logged:** —

### Event Bus

#### redis-py (async) — `VENDORED` (Stage 1.4)
- **Source:** https://github.com/redis/redis-py
- **Commit / Version:** dependency — pinned via pyproject `redis>=5.0` (installed on Colossus at run time)
- **License:** MIT
- **Kosmos location:** `adapters/event_bus/valkey/` (HTTP-client adapter; Valkey/Redis runs as external service)
- **Port(s):** `EventBusPort` (ADR-023)
- **Modifications:**
  - `redis.asyncio` imported lazily so unit tests using the in-memory fake do not require `redis` to be installed
  - Adapter uses only `xadd` / `xrange` / `ping` / `aclose` — consumer-group calls (`xgroup_create`/`xreadgroup`/`xack`/`xpending`/`xclaim`) deferred to ADR-024
  - Envelope-first: adapter refuses raw-dict publish (`TypeError`); every published payload is a validated `EventEnvelope`
  - In-process fan-out via `asyncio.Queue.put_nowait()` runs alongside stream append (matches Rigpa `KernelEventBus` two-layer pattern)
- **ADR:** ADR-007 (events-only cross-plugin coupling) + ADR-023 (EventBusPort envelope-first MVP)
- **Logged:** 2026-07-29 21:32 EDT

#### Rigpa event envelope + stream-client pattern — `VENDORED` (Stage 1.4)
- **Source:** https://github.com/rmholston420/Rigpa-LMS (user's own repo; permissively-licensed donor)
  - `backend/src/rigpa/core/events/envelope.py`
  - `backend/src/rigpa/core/events/valkey.py` (StreamClient Protocol + InMemoryStreamClient fake)
  - `backend/src/rigpa/core/events/kernel_bus.py` (two-layer publish + in-process fan-out)
- **Commit / Version:** inspected at donor `main` on 2026-07-29
- **License:** user's own code; treated as permissive donor
- **Kosmos location:** `ports/event_envelope.py`, `adapters/event_bus/valkey/adapter.py`
- **Modifications:**
  - Envelope reimplemented as stdlib `@dataclass(frozen=True, slots=True)` (kernel has no Pydantic dependency at Stage 1.4)
  - Envelope adds explicit `__post_init__` validation for empty `event_type` / `producer_plugin` / `schema_version`
  - `StreamClient` Protocol extended to include `ping()` and `aclose()` (health + lifecycle per ADR-023)
  - `InMemoryStreamClient` adds `ping_should_fail` toggle so tests can exercise non-throwing `is_healthy` path
  - Two-layer publish pattern simplified: no transactional outbox (deferred until MemoryPort is online in Stage 5+); Stage 1.4 does stream-append + in-process fan-out only
- **ADR:** ADR-023 (envelope-first MVP)
- **Logged:** 2026-07-29 21:32 EDT

### Memory / Graph

#### DozerDB — `PLANNED`
- **Source:** https://github.com/graphstack/DozerDB (community fork of Neo4j w/ enterprise features)
- **Commit / Version:** TBD (Stage 1.8)
- **License:** GPL-3 (Neo4j core) + fork additions — **VERIFY** at vendoring; if not permissive, escalate ADR-008
- **Kosmos location:** `adapters/memory/dozerdb/` (deployed via Docker Compose)
- **Port(s):** MemoryPort
- **Modifications:** none (deploy as service)
- **ADR:** ADR-008
- **Logged:** —

#### Agent Memory Guard — `PLANNED`
- **Source:** https://github.com/... (log full URL when vendoring)
- **Commit / Version:** v0.2.2 baseline; **CHECK release page immediately before Stage 4** for newer
- **License:** Apache-2.0 (verify)
- **Kosmos location:** `adapters/memory/guard/`
- **Port(s):** MemoryPort (write-time filter)
- **ADR:** ADR-008 (referenced), ADR-013 (bridge selection)
- **Logged:** —

#### Graphiti — `PLANNED`
- **Source:** https://github.com/getzep/graphiti
- **License:** Apache-2.0
- **Kosmos location:** `adapters/memory/graphiti/`
- **Port(s):** MemoryPort, VectorPort
- **ADR:** —
- **Logged:** —

### Vector store

#### Qdrant — `PLANNED`
- **Source:** https://github.com/qdrant/qdrant
- **License:** Apache-2.0
- **Kosmos location:** deployed via Docker Compose; adapter at `adapters/vector/qdrant/`
- **Port(s):** VectorPort
- **Logged:** —

### Search

#### SearXNG (consolidated adapter) — `VENDORED (Stage 1.1)`
- **Source (upstream runtime):** https://github.com/searxng/searxng (service; not vendored — runs via Docker Compose)
- **Adapter donor sources consolidated:**
  - [Rigpa-LMS/backend/src/rigpa/domains/integrations/searxng.py](https://github.com/rmholston420/Rigpa-LMS/blob/main/backend/src/rigpa/domains/integrations/searxng.py) — JSON-only, typed `SearchResponse`, engine list, language param
  - [axiom/packages/axiom_providers/searxng.py](https://github.com/rmholston420/axiom/blob/main/packages/axiom_providers/searxng.py) — JSON-first + HTML-fallback parser for 403 responses, User-Agent header
- **License:** AGPL-3.0 (SearXNG upstream — service only, not linked into Kosmos code); donor adapters user-authored (relicensable)
- **Kosmos location:** `adapters/search/searxng/`
- **Port(s):** `SearchPort` (new, per ADR-021)
- **Modifications from consolidation:**
  - Base = Rigpa adapter (typed response, engine list, language)
  - Add axiom's HTML fallback for `format=json` 403 responses (adapter-internal)
  - Add axiom's User-Agent header (`KosmosSearchAdapter/0.1 (+local; rmholston420/kosmos)`)
  - Add `provenance` field to `SearchResponse` (mandatory per ADR-021 for zero-trust memory writes)
  - Add `latency_ms` timing
  - Return typed dataclasses from `ports/search.py` (not adapter-local classes)
  - Wrap behind `SearchPort` Protocol
- **Runtime note:** SearXNG service runs in its own container; AGPL applies only to the service binary, not to Kosmos's HTTP-client adapter. Verify at deploy.
- **ADR:** ADR-012 (consolidation) + ADR-021 (SearchPort introduction)
- **Logged:** 2026-07-29 21:05 EDT

### Event bus

#### Valkey (Redis fork) — `PLANNED`
- **Source:** https://github.com/valkey-io/valkey
- **License:** BSD-3-Clause
- **Kosmos location:** Docker Compose; `adapters/eventbus/valkey/`
- **Port(s):** EventBusPort
- **Logged:** —

### Secrets

#### Vault (HashiCorp) + `hvac` client — `PLANNED`
- **Source:** https://github.com/hashicorp/vault (server); https://github.com/hvac/hvac (Python)
- **License:** BUSL-1.1 (Vault server) — **REVIEW** for local single-user compliance; MPL-2.0 (hvac)
- **Kosmos location:** Compose (dev); systemd (prod); `adapters/secrets/vault/`
- **Port(s):** SecretsPort
- **Notes:** BUSL-1.1 permits local single-user use; document justification in ADR if concern
- **Logged:** —

### Observability

#### Langfuse — `PLANNED`
- **Source:** https://github.com/langfuse/langfuse
- **License:** MIT (core)
- **Kosmos location:** Compose; `adapters/observability/langfuse/`
- **Port(s):** ObservabilityPort
- **Logged:** —

---

## Governance (Praxis / Phrouros)

#### agent-governance-toolkit — `PLANNED`
- **Source:** TBD (log at vendoring)
- **License:** verify permissive
- **Port(s):** governance internals
- **Logged:** —

---

## Tektos (Coding Plugin)

#### OpenHands SDK — `PLANNED`
- **Source:** https://github.com/All-Hands-AI/OpenHands (SDK subpackage)
- **License:** MIT
- **Kosmos location:** `plugins/tektos/vendor/openhands/`
- **Port(s):** LLMPort, MemoryPort, EventBusPort
- **Modifications:** wrap all I/O through Kosmos ports only; no direct filesystem or LLM calls
- **Logged:** —

#### MCP python-sdk — `PLANNED`
- **Source:** https://github.com/modelcontextprotocol/python-sdk
- **License:** MIT
- **Port(s):** EventBusPort (bridged)
- **Logged:** —

#### Playwright-MCP — `PLANNED`
- **Source:** https://github.com/microsoft/playwright-mcp
- **License:** Apache-2.0
- **Port(s):** via MCP → EventBus
- **Logged:** —

#### aider repomap — `PLANNED`
- **Source:** https://github.com/Aider-AI/aider (extract `repomap.py` module)
- **License:** Apache-2.0
- **Port(s):** DataPort, MemoryPort
- **Modifications:** memory writes get provenance="aider-repomap" and confidence=index freshness
- **Logged:** —

#### Bernstein Janitor — `EVALUATING` (spike per ADR-004)
- **Source:** log full URL at spike setup
- **License:** verify permissive before spike
- **Port(s):** internal Tektos loop
- **Adoption rule:** adopt iff fixture beats `local-agentic-loop-sample`
- **ADR:** ADR-004 (adr-bernstein-vendor)
- **Logged:** —

#### local-agentic-loop-sample — `PLANNED (baseline)`
- **Source:** TBD
- **License:** verify permissive
- **Port(s):** internal Tektos loop
- **Status note:** kept as baseline; may be superseded by Bernstein Janitor if spike passes
- **Logged:** —

#### Reflexion — `PLANNED`
- **Source:** https://github.com/noahshinn/reflexion (or canonical)
- **License:** MIT
- **Port(s):** MemoryPort (self-improvement traces)
- **Logged:** —

#### Voyager — `PLANNED`
- **Source:** https://github.com/MineDojo/Voyager
- **License:** MIT
- **Port(s):** MemoryPort
- **Logged:** —

#### OpenSpec — `PLANNED`
- **Source:** TBD
- **License:** verify
- **Port(s):** DataPort
- **ADR:** adr-openspec-primary
- **Logged:** —

#### spec-kit — `PLANNED`
- **Source:** TBD
- **License:** verify
- **Port(s):** FrontendContractPort
- **Logged:** —

#### Pier eval harness — `PLANNED`
- **Source:** TBD
- **License:** verify
- **Port(s):** internal
- **ADR:** adr-pier-eval-harness
- **Logged:** —

#### DeepSWE corpus subset — `PLANNED`
- **Source:** TBD
- **License:** verify (dataset license)
- **Port(s):** DataPort (read-only corpus)
- **ADR:** adr-deepswe-corpus
- **Logged:** —

#### docling — `PLANNED`
- **Source:** https://github.com/DS4SD/docling
- **License:** MIT
- **Port(s):** DataPort
- **Logged:** —

#### ruff — `VENDORED (dev dep)`
- **Source:** https://github.com/astral-sh/ruff
- **License:** MIT
- **Kosmos location:** `pyproject.toml` dev dep + pre-commit hook
- **Port(s):** none (build-time only)
- **Logged:** —

#### bandit — `VENDORED (dev dep)`
- **Source:** https://github.com/PyCQA/bandit
- **License:** Apache-2.0
- **Port(s):** none (build-time only)
- **Logged:** —

---

## Gnosis (Knowledge)

#### Superpowers KB — `PLANNED`
- **Source:** TBD
- **License:** verify
- **Port(s):** MemoryPort
- **ADR:** adr-superpowers-kb
- **Logged:** —

#### Humanities corpus — `PLANNED`
- **Source:** TBD
- **License:** dataset-specific
- **Port(s):** DataPort
- **ADR:** gnosis-humanities-adr
- **Logged:** —

---

## Zetesis (Research) — ADR-010 candidates

#### AREX (Autonomous Research Executor) — `EVALUATING`
- **Source:** log at eval
- **License:** verify
- **Port(s):** LLMPort, MemoryPort, VectorPort
- **ADR:** ADR-010 (open — pre-Phase-6.2 head-to-head)
- **Logged:** —

#### LangChain Open Deep Research — `EVALUATING`
- **Source:** https://github.com/langchain-ai/open_deep_research
- **License:** MIT
- **Port(s):** LLMPort, MemoryPort, VectorPort
- **ADR:** ADR-010
- **Logged:** —

---

## Koinonia / Synedrion (Agent-to-Agent)

#### a2a-sdk — `PLANNED (standalone transport)`
- **Source:** https://github.com/google/a2a (or canonical)
- **License:** Apache-2.0
- **Kosmos location:** `plugins/koinonia/vendor/a2a/`
- **Port(s):** EventBusPort (bridged), custom transport
- **ADR:** ADR-011 (a2a-sdk chosen over Moltbook transport)
- **Logged:** —

---

## Ops / Deploy

#### Coolify — `PLANNED`
- **Source:** https://github.com/coollabsio/coolify
- **License:** Apache-2.0
- **Kosmos location:** self-hosted single-node
- **Notes:** deploy convenience only; not required for kernel
- **Logged:** —

#### Kamal — `PLANNED`
- **Source:** https://github.com/basecamp/kamal
- **License:** MIT
- **Notes:** alternative deploy tool; hold as backup
- **Logged:** —

---

## Design References — Do Not Vendor

These informed design but are **not** in the tree. Recorded here so future maintainers know they were considered.

#### Superpowers (repo) — `DESIGN REFERENCE`
- **Source:** upstream Superpowers repo
- **Use:** shape of personal-KB UX
- **Note:** we vendor the KB substrate above; the reference-repo patterns inform the UI

#### Beads (task-state library) — `DESIGN REFERENCE`
- **Source:** TBD
- **Use:** informs TaskState modeling in Tektos and Oikos
- **ADR:** adr-beads-taskstate

#### karpathy/llm-council — `DESIGN REFERENCE`
- **Source:** https://github.com/karpathy/llm-council (or similar)
- **Use:** informs Synedrion multi-agent voting patterns

#### CMSgov BenefitAssist — `DESIGN REFERENCE`
- **Source:** CMS.gov open-source patterns
- **Use:** Oikos benefit-flow UX

#### 18F SNAP — `DESIGN REFERENCE`
- **Source:** 18F GitHub
- **Use:** Oikos benefit-flow UX

#### we-promise/sure — `REJECTED`
- **Reason:** does not fit Oikos zero-trust memory model / single-user constraints
- **Decision date:** TBD
- **Do not vendor without re-review + new ADR.**

---

## Ledger Maintenance

- Append entries in chronological order; do **not** re-order for prettiness.
- When a `PLANNED` entry is vendored: change status to `VENDORED`, add commit SHA, set `Logged` timestamp, and record the initial import commit hash of Kosmos in the entry.
- When a spike concludes: change `EVALUATING` → `VENDORED` or `REJECTED` with the benchmark reference.
- When one entry supersedes another: mark the older `SUPERSEDED` with a link to the new entry; do not delete.
- License must be re-verified at every version bump. Any change to a non-permissive license triggers immediate ADR.
