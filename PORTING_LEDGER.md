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

#### llama-swap — `PLANNED`
- **Source:** https://github.com/mostlygeek/llama-swap
- **Commit / Version:** TBD (pin latest at Stage 1.3)
- **License:** MIT
- **Kosmos location:** `adapters/llm/llama_swap/`
- **Port(s):** LLMPort
- **Modifications:** wrap behind LLMPort protocol; add priority-queue hook
- **ADR:** ADR-009 (llama-swap primary + router-mode fallback)
- **Logged:** —

#### router-mode fallback — `PLANNED (fallback only)`
- **Source:** internal build using llama.cpp server routes
- **License:** MIT (llama.cpp)
- **Port(s):** LLMPort
- **ADR:** ADR-009
- **Logged:** —

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
