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

### Secrets

#### pyrage — `VENDORED` (Stage 1.5)
- **Source:** https://github.com/woodruffw/pyrage
- **Commit / Version:** dependency — pinned via pyproject `pyrage>=1.1` (Rust-compiled wheel installed on Colossus)
- **License:** Apache-2.0 / MIT (dual)
- **Kosmos location:** `adapters/secrets/age_file/adapter.py` (used inside `PyrageBackend` only)
- **Port(s):** `SecretsPort` (ADR-024)
- **Modifications:**
  - `pyrage` and `yaml` imported lazily so unit tests using `InMemoryAgeBackend` do not require either dependency installed
  - Only two operations used: `pyrage.decrypt(ciphertext, [identity])` and `pyrage.encrypt(plaintext, [recipient])`
  - Recipients derived from the identity file's public key so rotation writes are decryptable by the same identity; multi-recipient (§7 succession key escrow) is a future extension
- **ADR:** ADR-024 (SecretsPort age-file primary)
- **Logged:** 2026-07-29 21:36 EDT

#### PyYAML — `VENDORED` (Stage 1.5)
- **Source:** https://github.com/yaml/pyyaml
- **Commit / Version:** dependency — pinned via pyproject `PyYAML>=6.0`
- **License:** MIT
- **Kosmos location:** `adapters/secrets/age_file/adapter.py` (safe_load/safe_dump of the decrypted secrets mapping)
- **Port(s):** `SecretsPort`
- **Modifications:** `yaml.safe_load` / `yaml.safe_dump` only (no arbitrary-object deserialization)
- **ADR:** ADR-024
- **Logged:** 2026-07-29 21:36 EDT

#### Rigpa age-secrets loader pattern — `VENDORED` (Stage 1.5)
- **Source:** https://github.com/rmholston420/Rigpa-LMS (user's own repo; permissively-licensed donor)
  - `backend/src/rigpa/core/secrets.py` (age-file loader, `SecretSettings` + `load_secrets`)
  - `backend/src/rigpa/core/secrets_meta_model.py` (`SecretsMeta` ORM)
  - `docs/adr/0002-single-user-knowsys-vaults.md` (single-user framing)
- **Commit / Version:** inspected at donor `main` on 2026-07-29
- **License:** user's own code; treated as permissive donor
- **Kosmos location:** `ports/secrets.py`, `adapters/secrets/age_file/adapter.py`
- **Modifications:**
  - Rigpa uses `SecretSettings` Pydantic model wrapping every field in `SecretStr`; Kosmos uses `SecretValue` (stdlib frozen dataclass) so `ports/` has zero Pydantic dependency — same redaction guarantee, stricter accessor (`.reveal()` verb is grep-able audit anchor)
  - `SecretValue.__eq__` compares redacted repr so distinct secrets never appear equal in logs; `SecretValue.__reduce__` refuses pickling (Rigpa's SecretStr permits both)
  - Rotate is a filesystem operation on the whole file (§7 semantics) rather than field-level updates; write-to-temp + `os.replace` for POSIX atomicity
  - `AgeBackend` Protocol isolates age crypto so tests can inject a fake without installing `pyrage` — mirrors the Stage 1.4 `StreamClient` pattern
  - No Alembic migration for `SecretsMeta` at Stage 1.5; that lands with MemoryPort in Stage 5+
- **ADR:** ADR-024
- **Logged:** 2026-07-29 21:36 EDT

### Memory / Graph

#### DozerDB server — `PLANNED` (Compose service; not vendored into Python code)
- **Source:** https://github.com/graphstack/DozerDB (community fork of Neo4j Community with enterprise-tier features backported permissively)
- **Commit / Version:** container image — pinned by Compose (added when Docker Compose lands post-Stage 1.8; last verified upstream at Docker tag 5.26.27 per spec §184)
- **License:** Apache-2.0 (fork additions; upstream Neo4j Community is GPL-3, but DozerDB fork additions are permissive per ADR-008 requirement) — re-verify at Compose landing
- **Kosmos location:** Docker Compose service `dozerdb`; Bolt on 7687; Colossus-local; DR-drill dump target per spec §184
- **Port(s):** `MemoryPort` (ADR-008 backend choice; ADR-027 surface + enforcement)
- **Modifications:** none — upstream container image; page cache + tx log sizing tuned for Colossus's 128 GB RAM envelope per `ops/dozerdb-tuning.md` when Compose lands
- **ADR:** ADR-008 + ADR-027
- **Logged:** 2026-07-29 22:02 EDT

#### neo4j (Python driver) — `VENDORED` (Stage 1.8)
- **Source:** https://github.com/neo4j/neo4j-python-driver
- **Commit / Version:** dependency — pinned via pyproject `neo4j>=5.26`
- **License:** Apache-2.0 AND Python-2.0 ([neo4j-python-driver LICENSE](https://github.com/neo4j/neo4j-python-driver/blob/6.x/LICENSE.txt))
- **Kosmos location:** `adapters/memory/dozerdb/adapter.py` (used inside the future `DozerDbGraphBackend` only)
- **Port(s):** `MemoryPort`
- **Modifications:**
  - Imported lazily behind `GraphBackend` Protocol so contract tests using `InMemoryGraphBackend` do not require the wheel installed — mirrors Stage 1.5 `PyrageBackend` / Stage 1.6 `OtelBackend` / Stage 1.7 `QdrantBackend` splits
  - `AsyncGraphDatabase` is the sole entry point (donor Rigpa `rigpa.core.neo4j` async singleton pattern); sync driver not used
  - DozerDB is Bolt-protocol compatible with Neo4j; no wire-protocol changes needed
- **ADR:** ADR-008 + ADR-027
- **Logged:** 2026-07-29 22:02 EDT

#### graphiti-core — `VENDORED` (Stage 1.8)
- **Source:** https://github.com/getzep/graphiti
- **Commit / Version:** dependency — pinned via pyproject `graphiti-core>=0.5`
- **License:** Apache-2.0 ([getzep/graphiti pyproject](https://github.com/getzep/graphiti/blob/main/pyproject.toml))
- **Kosmos location:** `adapters/memory/dozerdb/adapter.py` (used inside the future `GraphitiTemporalIndex` only)
- **Port(s):** `MemoryPort` (temporal index only — Graphiti shares DozerDB's Neo4j-driver Bolt connection)
- **Modifications:**
  - Imported lazily behind `TemporalIndex` Protocol; contract tests use `InMemoryTemporalIndex` (list of typed episodes)
  - Graphiti sits atop the same DozerDB instance via the same `neo4j` driver — no second connection pool
  - **Sequencing note:** pulled forward from Stage 4.2 to Stage 1.8 per ADR-027 Q1=A. Stage 4.2 reduced to temporal-index tuning + `PORT_CONTRACTS.md` metrics (schema drift, edge-type churn, temporal-episode latency).
- **ADR:** ADR-027
- **Logged:** 2026-07-29 22:02 EDT

#### agent-memory-guard v0.2.2 — `VENDORED` (Stage 1.8)
- **Source:** https://github.com/OWASP/www-project-agent-memory-guard
- **Commit / Version:** PyPI `agent-memory-guard==0.2.2` (pinned exactly; verified upstream May 3, 2026; v0.3.0 not yet shipped)
- **License:** OWASP Foundation (PyPI-shipped Python package; Python code under permissive OWASP terms; free redistribution)
- **Kosmos location:** `adapters/memory/dozerdb/adapter.py` (used inside the future `AmgV02Policy` only)
- **Port(s):** `MemoryPort` (write-time policy filter, second layer after non-bypassable port-level guard)
- **Modifications:**
  - Imported lazily behind `AmgPolicy` Protocol; contract tests use `NoOpAmgPolicy` / `AlwaysBlockAmgPolicy` / `AlwaysQuarantineAmgPolicy`
  - Policy loaded from `ops/agent-memory-guard/policy.yaml` at adapter construction (YAML file lands with Compose)
  - AMG v0.2.2 provides SHA-256 cryptographic baseline + declarative YAML policy engine (`allow` / `redact` / `quarantine` / `block`) per spec §112
  - **Standing action per spec §643 + custom-instructions:** re-check https://github.com/OWASP/www-project-agent-memory-guard/releases immediately before Gnosis Phase 3 for v0.3.0 (LlamaIndex/CrewAI adapters, Redis/PostgreSQL backends, Prometheus metrics)
- **ADR:** ADR-027
- **Logged:** 2026-07-29 22:02 EDT

#### Rigpa-LMS MemoryBridge + GraphClient donor pattern — `VENDORED` (Stage 1.8)
- **Source:** https://github.com/rmholston420/Rigpa-LMS (user's own repo; permissively-licensed donor)
  - `backend/src/rigpa/core/graph/protocol.py` (Rigpa `GraphClient` Protocol — Cypher-shaped: `query_cypher / add_node / add_edge / is_healthy / close`)
  - `backend/src/rigpa/core/neo4j.py` (async driver singleton)
  - `backend/src/rigpa/domains/memory/bridge.py` (`MemoryBridge` — async Cypher wrapper for store/query/link/graph)
  - `backend/src/rigpa/domains/memory/schemas.py` (Pydantic v2 request/response models)
  - `backend/src/rigpa/domains/memory/service.py` (thin service layer over the bridge)
- **Commit / Version:** inspected at donor `main` on 2026-07-29 (cached at `/tmp/donor-mem/`)
- **License:** user's own code; treated as permissive donor
- **Kosmos location:** `ports/memory.py`, `adapters/memory/dozerdb/adapter.py`
- **Modifications:**
  - Rigpa `MemoryCreate` schema carries no `provenance` / no `confidence`; `MemoryBridge.store_memory` writes `str(metadata or {})` — not typed, no schema enforcement. Kosmos adds a non-bypassable port-level guard (`ports.memory.validate_zero_trust_write`) that rejects missing/invalid `provenance` or `confidence` at the top of every write method before any backend I/O; mirrors ADR-026 `VectorPort` zero-trust pattern.
  - Rigpa exposes no `quarantine_write` and no `query_temporal`; Kosmos ships all four spec verbs (write_event / query_temporal / link_entities / quarantine_write) day-one per ADR-027 Q1=A.
  - Rigpa's `Neo4jGraphClient` is a Phase-1 stub (only Kuzu is wired); Kosmos ships a live DozerDB backend via `neo4j` driver (Bolt).
  - Rigpa returns raw `dict[str, Any]` from queries; Kosmos returns typed `MemoryHit` — matches SearchPort ADR-021 / SecretsPort ADR-024 / VectorPort ADR-026 typing discipline.
  - Rigpa's `is_healthy` is async; Kosmos version is sync + non-throwing (ADR-023 rule 5) so it can be called in kernel hot paths without spawning a coroutine — reuses `try/except -> False` guard from ObservabilityPort.
  - CIDOC-CRM triple decomposition: Kosmos writes three graph nodes (subject Entity + object Entity + MemoryEvent) + two directed edges (`SUBJECT_OF` + `OBJECT_OF`) per `write_event` — Rigpa has no CRM concept.
  - Quarantine lane (spec §115): Kosmos writes `:Quarantined` nodes that are NOT indexed in the temporal index — they are not semantic memory until reviewed and promoted. Rigpa has no quarantine concept.
- **ADR:** ADR-027
- **Logged:** 2026-07-29 22:02 EDT

### Vector store

#### Qdrant server — `PLANNED` (Compose service; not vendored into Python code)
- **Source:** https://github.com/qdrant/qdrant
- **Commit / Version:** container image — pinned by Compose (added when Docker Compose lands post-Stage 1.7)
- **License:** Apache-2.0
- **Kosmos location:** Docker Compose service `qdrant`; ports 6333 (HTTP) + 6334 (gRPC); Colossus-local
- **Port(s):** `VectorPort` (ADR-026)
- **Modifications:** none — upstream container image; snapshot artifacts written to a bind-mounted volume for the four-store DR-drill (§11)
- **ADR:** ADR-026
- **Logged:** 2026-07-29 21:58 EDT

#### qdrant-client — `VENDORED` (Stage 1.7)
- **Source:** https://github.com/qdrant/qdrant-client
- **Commit / Version:** dependency — pinned via pyproject `qdrant-client>=1.11`
- **License:** Apache-2.0
- **Kosmos location:** `adapters/vector/qdrant/adapter.py` (used inside the future `RealQdrantBackend` only)
- **Port(s):** `VectorPort`
- **Modifications:**
  - Imported lazily behind `QdrantBackend` Protocol so contract tests using `InMemoryQdrantBackend` do not require the wheel installed — mirrors Stage 1.5 `PyrageBackend` / Stage 1.6 `OtelBackend` splits
  - `AsyncQdrantClient` is the sole entry point (donor Rigpa `rigpa.core.qdrant` pattern); sync client not used
  - Free-form point ids hashed to stable UUIDv5 under `POINT_ID_NAMESPACE` before hitting the client (Rigpa `QdrantClaimUpserter.claim_point_id` pattern); Qdrant only accepts numeric or UUID ids
  - Collection creation is idempotent (get-then-create fallback), dimension inferred from the first vector inserted (Rigpa `_ensure_collection` pattern)
- **ADR:** ADR-026
- **Logged:** 2026-07-29 21:58 EDT

#### Rigpa-LMS vector-Protocol donor pattern — `VENDORED` (Stage 1.7)
- **Source:** https://github.com/rmholston420/Rigpa-LMS (user's own repo; permissively-licensed donor)
  - `backend/src/rigpa/core/vectors/protocol.py` (Rigpa `VectorStore` Protocol — four verbs + `is_healthy`)
  - `backend/src/rigpa/core/qdrant.py` (async singleton client pattern)
  - `plugins/gnosis/src/rigpa_gnosis/services/qdrant_upserter.py` (`QdrantClaimUpserter` — UUIDv5 point-id normalization; idempotent `_ensure_collection`; typed payload assembly)
  - Rigpa ADR-036 (pgvector→Qdrant threshold decision; referenced but not adopted in Kosmos day-one)
- **Commit / Version:** inspected at donor `main` on 2026-07-29 (cached at `/tmp/donor-vec/`)
- **License:** user's own code; treated as permissive donor
- **Kosmos location:** `ports/vector.py`, `adapters/vector/qdrant/adapter.py`
- **Modifications:**
  - Rigpa `VectorStore` Protocol added no `snapshot`, no `close`, and no port-level `provenance`/`confidence` guard — Kosmos adds all three (ADR-026 Q1). `snapshot()` returns a typed `SnapshotHandle` so the §11 DR-drill can verify the artifact directly.
  - Rigpa `search` returned raw `dict[str, Any]`; Kosmos returns typed `VectorHit` — matches `SearchPort`/`SecretValue` typing discipline (ADR-021/024)
  - Rigpa allowed unlabeled writes (payload had no schema); Kosmos raises `ValueError` at the port layer if `payload` lacks `provenance` or `confidence` outside `[0.0, 1.0]`. Enforced via `ports.vector.validate_zero_trust_payload`; non-bypassable
  - Rigpa's `is_healthy` is async; Kosmos version is sync + non-throwing (ADR-023 rule 5 reused) so it can be called in kernel hot paths without spawning a coroutine
  - pgvector adapter (Rigpa's phase-1 backend) is deferred; trigger for a future pgvector ADR is documented in ADR-026 §Deferred capabilities
- **ADR:** ADR-026
- **Logged:** 2026-07-29 21:58 EDT

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

#### opentelemetry-sdk — `VENDORED` (Stage 1.6)
- **Source:** https://github.com/open-telemetry/opentelemetry-python
- **Commit / Version:** dependency — pinned via pyproject `opentelemetry-sdk>=1.27`
- **License:** Apache-2.0
- **Kosmos location:** `adapters/observability/otel_stack/adapter.py` (used inside the future `RealOtelBackend` only)
- **Port(s):** `ObservabilityPort` (ADR-025)
- **Modifications:**
  - Imported lazily behind `OtelBackend` Protocol so contract tests using `StubOtelBackend` do not require the wheel installed
  - Only `TracerProvider`, `MeterProvider`, span/`start_as_current_span`, counter/histogram, and resource attributes are used
- **ADR:** ADR-025
- **Logged:** 2026-07-29 21:52 EDT

#### opentelemetry-exporter-otlp-proto-grpc — `VENDORED` (Stage 1.6)
- **Source:** https://github.com/open-telemetry/opentelemetry-python (contrib exporters)
- **Commit / Version:** dependency — pinned via pyproject `opentelemetry-exporter-otlp-proto-grpc>=1.27`
- **License:** Apache-2.0
- **Kosmos location:** `adapters/observability/otel_stack/adapter.py` (`RealOtelBackend` OTLP wiring, added when LGTM stack lands)
- **Port(s):** `ObservabilityPort`
- **Modifications:** Endpoint defaults to `http://127.0.0.1:4317` (Colossus-local LGTM collector); OTLP failures degrade to no-op so a downed collector never crashes plugins
- **ADR:** ADR-025
- **Logged:** 2026-07-29 21:52 EDT

#### prometheus-client — `VENDORED` (Stage 1.6)
- **Source:** https://github.com/prometheus/client_python
- **Commit / Version:** dependency — pinned via pyproject `prometheus-client>=0.20`
- **License:** Apache-2.0
- **Kosmos location:** `adapters/observability/otel_stack/adapter.py` (Prometheus scrape endpoint at `:9090/metrics` for Grafana)
- **Port(s):** `ObservabilityPort`
- **Modifications:** Used only for the scrape-endpoint HTTP server; OTel meter is the primary write path (Prometheus is the read path for Grafana Alloy)
- **ADR:** ADR-025
- **Logged:** 2026-07-29 21:52 EDT

#### structlog — `VENDORED` (Stage 1.6)
- **Source:** https://github.com/hynek/structlog
- **Commit / Version:** dependency — pinned via pyproject `structlog>=24.1` (already present since Stage 0.1; now formalized against `ObservabilityPort`)
- **License:** Apache-2.0 / MIT (dual)
- **Kosmos location:** `adapters/observability/otel_stack/adapter.py` (bind_context/clear_context routed through `structlog.contextvars`)
- **Port(s):** `ObservabilityPort`
- **Modifications:**
  - Only `structlog.contextvars.bind_contextvars` and `clear_contextvars` are used from structlog directly; log formatting is delegated to the caller's processor chain
  - Mandatory correlation keys per Kosmos custom instructions (`plugin, request_id, user_id, trace_id, event`) are the contract; not enforced at runtime yet
- **ADR:** ADR-025
- **Logged:** 2026-07-29 21:52 EDT

#### Rigpa-LMS observability seam pattern — `VENDORED` (Stage 1.6)
- **Source:** https://github.com/rmholston420/Rigpa-LMS (user's own repo; permissively-licensed donor)
  - `backend/src/rigpa/observability/__init__.py`, `config.py`, `tracing.py`, `metrics.py`, `logging.py`
  - Rigpa ADR-044 (LGTM stack), ADR-013a (OTel adoption)
- **Commit / Version:** inspected at donor `main` on 2026-07-29 (cached at `/tmp/donor-obs/`)
- **License:** user's own code; treated as permissive donor
- **Kosmos location:** `ports/observability.py`, `adapters/observability/otel_stack/adapter.py`
- **Modifications:**
  - Rigpa layered OTel/Prometheus/structlog behind an `ObservabilityConfig` init; Kosmos formalizes the four verbs (`trace / score / log_cost / bind_context`) as a `Protocol` so plugins depend on the port not the vendors
  - `trace()` returns a `NoOpSpan` if the backend fails to open a span, so calling code never has to guard `with obs.trace(...):` — Rigpa's version implicitly assumed the backend was up
  - `log_cost()` writes both counters *and* attaches attributes to the currently active span (Rigpa only wrote counters), so trace views show spend inline with the request
  - `AgeBackend`-style Protocol seam (`OtelBackend`) mirrors the Stage 1.5 `PyrageBackend` split so tests never need any OTel wheel installed
  - `is_healthy` is non-throwing (ADR-023 rule 5); `close()` is idempotent — both stronger than Rigpa's originals
  - Langfuse (spec §4.1 aspirational) is deferred to a future second adapter for LLM-specific prompt/response/eval-score UX; ADR-025 sizes the trigger
- **ADR:** ADR-025
- **Logged:** 2026-07-29 21:52 EDT

### DataPort

#### rfc8785 (JCS canonicalizer) — `VENDORED` (Stage 1.10)
- **Source:** https://github.com/trailofbits/rfc8785.py
- **Commit / Version:** `rfc8785>=0.1.4` (verified via `gh api repos/trailofbits/rfc8785.py` on 2026-07-29)
- **License:** Apache-2.0 (SPDX: `Apache-2.0`)
- **Kosmos location:** runtime dep in `pyproject.toml`; used by `adapters/data/filesystem/adapter.py::JcsCanonicalizer` (lazy import at construction time)
- **Port(s):** DataPort
- **Modifications:** none — the wheel is invoked verbatim via `rfc8785.dumps(payload) -> bytes`. Contract tests use a pure-stdlib `SortedJsonCanonicalizer` double so tests do not depend on the wheel being installed.
- **ADR:** ADR-028
- **Logged:** 2026-07-29 22:35 EDT

#### cryptography — `VENDORED (deferred use)` (Stage 1.10)
- **Source:** https://github.com/pyca/cryptography
- **Commit / Version:** `cryptography>=49` (verified via `gh api repos/pyca/cryptography` on 2026-07-29)
- **License:** Apache-2.0 OR BSD-3-Clause (SPDX)
- **Kosmos location:** runtime dep in `pyproject.toml`; **not imported anywhere in Kosmos code at Stage 1.10**. Reserved for `Ed25519FileSigner` which lands at Stage 5 governance-key wiring (age-key-file-backed per ADR-024 SecretsPort pattern). Declared now so the dep exists at the moment the seam is populated, avoiding a future `pyproject` bump entangled with a governance ADR.
- **Port(s):** DataPort (via `Signer` Protocol seam)
- **Modifications:** none.
- **ADR:** ADR-028
- **Logged:** 2026-07-29 22:35 EDT

#### Rigpa-LMS knowsys export subsystem donor pattern — `VENDORED (pattern only; domain schema rejected)` (Stage 1.10)
- **Source:** https://github.com/rmholston420/Rigpa-LMS (user's own repo; permissively-licensed donor)
  - `plugins/knowsys/src/rigpa_knowsys/models/export.py` (`ExportEnvelope` SQLAlchemy row with `envelope_json_hash CHAR(64)` + Ed25519 base64 signature)
  - `plugins/knowsys/src/rigpa_knowsys/schemas/export.py` (Pydantic `ExportEnvelope` + `NoteExportItem` + `AttachmentRef` + `EXPORT_SIGNED_FIELDS` tuple + `signed_payload()`)
  - `plugins/knowsys/src/rigpa_knowsys/services/export_service.py` (`build_export_envelope / sign_envelope / verify_envelope_signature / import_envelope`)
  - `plugins/knowsys/src/rigpa_knowsys/routers/export.py` (FastAPI endpoints)
  - `plugins/knowsys/tests/test_export.py` (tampering, dedup, signature-failure test patterns)
  - `backend/src/rigpa/domains/knowledge/schema_registry.py` (`SchemaRegistry` + `SchemaValidationError`)
- **Commit / Version:** inspected at donor `main` on 2026-07-29 (cached at `/tmp/donor-dataport/`)
- **License:** user's own code; treated as permissive donor
- **Kosmos location:** `ports/data.py`, `adapters/data/filesystem/adapter.py`
- **Modifications:**
  - Rigpa's schema is **Knowsys-domain-locked** (PostgreSQL `Note`/`NoteAttachment` upsert, PARA folders, Ed25519 constitution key). Kosmos DataPort is **domain-neutral** — every plugin (Gnosis, Tektos, Oikos, Nomisma, Zetesis) will call `export_canonical` with its own `record_type`.
  - Rigpa uses `rigpa.domains.governance.constitution.signing.{canonicalize, sign, verify}` (Ed25519 with a live constitution key). Kosmos has no governance key at Stage 1.10 — signing is behind a pluggable `Signer` Protocol seam with `NoOpSigner` as Stage 1.10 primary. Envelopes remain hash-anchored (SHA-256 over JCS bytes) so DR-drill cross-verify per spec §187 still works. `Ed25519FileSigner` slots in at Stage 5 with zero port changes (mirrors ADR-027 seam pattern).
  - Rigpa persists envelopes as PostgreSQL rows in `notes_export_envelopes` with an `envelope_json_hash CHAR(64)` UNIQUE constraint providing dedup. Kosmos writes to `{root}/{record_type}/{sha256}.jsonld` — the filesystem path itself is the dedup key; matches project custom-instructions "single-user, local-first".
  - Rigpa has no `check_format_health` or `migrate_schema` verbs. Kosmos ships all three spec §4.1-line-93 verbs day-one per ADR-028 Q1=A (same discipline as ADR-027 Q1=A for MemoryPort).
  - Rigpa has no PII tier concept on the envelope. Kosmos requires a `pii_tier: PIITier` field per spec §150 four-tier classification; Restricted-tier records route under `{root}/restricted/{record_type}/` prefix to enable a future AES-256-at-rest wrapper (spec §147) at ops-deploy.
  - Rigpa has no never-overwrite migration guard. Kosmos ships one live at Stage 1.10 per spec §230/§232 (`MigrationTargetExists` raised on collision; idempotent same-hash re-runs allowed).
  - Rigpa signs a specific `EXPORT_SIGNED_FIELDS` subset. Kosmos signs the full envelope-minus-hash-minus-signature bytes; simpler contract, no field-inclusion registry to maintain.
- **ADR:** ADR-028
- **Logged:** 2026-07-29 22:35 EDT

#### FilesystemDataAdapter + three Protocol seams (`Canonicalizer` / `Signer` / `Storage`) — `KOSMOS-NATIVE` (Stage 1.10)
- **Source:** authored in this repo
- **Kosmos location:** `adapters/data/filesystem/adapter.py`
- **Port(s):** DataPort
- **Notes:** three injectable Protocol seams so contract tests run without any third-party imports; mirrors ADR-027 memory-adapter seam pattern (`GraphBackend` / `AmgPolicy` / `TemporalIndex`). Stage 1.10 primary composition: `SortedJsonCanonicalizer` (or `JcsCanonicalizer` in prod) + `NoOpSigner` + `FilesystemStorage`. Stage 5 governance-key wiring swaps in `Ed25519FileSigner` with zero port changes.
- **ADR:** ADR-028
- **Logged:** 2026-07-29 22:35 EDT

### ResourcePort

#### aiosqlite (`omnilib/aiosqlite`) — `VENDORED`
- **Source:** https://github.com/omnilib/aiosqlite
- **Commit / Version:** `>=0.20` (declared in `pyproject.toml` at Stage 1.11)
- **License:** MIT (verified via `gh api repos/omnilib/aiosqlite` on 2026-07-29; last push 2026-03-01, active)
- **Kosmos location:** runtime dep; lazy-imported inside `adapters/resource/sqlite/adapter.py::AioSqliteStorage.open`
- **Port(s):** `ResourcePort` (Storage seam)
- **Modifications:** none — upstream driver used unmodified.
- **Notes:** primary durable Storage backend at Stage 1.11. Opens one shared connection at adapter startup, enables `PRAGMA journal_mode=WAL`, reuses it for the whole adapter lifecycle (per spec §16 SQLite lifecycle rule). Contract tests use the pure-stdlib `InMemoryStorage` double so `aiosqlite` is not required to run the port's Protocol-conformance suite.
- **ADR:** ADR-029
- **Logged:** 2026-07-29 22:40 EDT

#### APEX `ResourceProtocol` pattern (`rmholston420/Rigpa-LMS`) — `PATTERN-VENDORED`
- **Source:** https://github.com/rmholston420/Rigpa-LMS (files: `backend/src/rigpa/domains/apex/protocols.py`, `.../models.py`, `.../service.py`)
- **Commit / Version:** inspected at HEAD 2026-07-29 (cached at `/tmp/donor-resource/`)
- **License:** internal donor (rmholston420); Kosmos vendors pattern only, not source.
- **Kosmos location:** `ports/resource.py` (Protocol surface, six canonical kinds enum, Decimal balance semantics)
- **Port(s):** `ResourcePort`
- **Modifications:** dropped SQLAlchemy substrate (Rigpa's `Resource` ORM depends on `rigpa.db.base` + multi-tenant Users FK — domain-locked, incompatible with Kosmos single-user local-first per project custom instructions); reused pattern (six canonical kinds enum: time/money/attention/compute/knowledge/energy; `can_allocate/allocate/replenish` signatures; `NUMERIC(20,4)` Decimal precision preserved on the Port surface); made verbs async; added Q1=B priority-queue verbs (`enqueue`/`peek`/`dequeue`/`cancel`) per spec §172 fixed-order arbitration; added zero-trust port-level guard on all writes.
- **Notes:** matches ADR-028's rejection of Rigpa's Knowsys-domain-locked schema for the same domain-locking reason. Kosmos ports the pattern, not the ORM.
- **ADR:** ADR-029
- **Logged:** 2026-07-29 22:40 EDT

#### Rigpa-v2 priority-queue router pattern — `PATTERN-VENDORED`
- **Source:** https://github.com/rmholston420/Rigpa-v2 (file: `backend/src/rigpa/routers/priority_queue.py`)
- **Commit / Version:** inspected at HEAD 2026-07-29 (cached at `/tmp/donor-resource/priority_queue.py`)
- **License:** internal donor (rmholston420); Kosmos vendors pattern only, not source.
- **Kosmos location:** `adapters/resource/sqlite/adapter.py` (priority-queue arbitration inside `SqliteResourceAdapter`)
- **Port(s):** `ResourcePort` (priority-queue verbs)
- **Modifications:** dropped FastAPI/Pydantic REST substrate (donor is HTTP-router-shaped, Kosmos ResourcePort is called in-process by plugins); reused pattern (UUID-keyed queue rows, `enqueue`/`peek`/`dequeue`/`cancel` verb naming, `(priority DESC, enqueued_at ASC)` ordering); replaced threaded in-memory dict with async SQLite (via `Storage` seam) so restarts don't wipe reservations (Build-Sequence §1.13 DoD + DR-drill §187 restart-durability); constrained donor's `priority: int 1-100` open scale to the fixed three-class `PriorityClass` IntEnum per spec §172 (`PHROUROS_ANOMALY=100 > TEKTOS_ACTIVE=50 > BACKGROUND=10`).
- **ADR:** ADR-029
- **Logged:** 2026-07-29 22:40 EDT

### NotificationPort

#### httpx (already vendored at ADR-021) — `VENDORED (reused)`
- **Source:** https://github.com/encode/httpx
- **Commit / Version:** existing project dep declared in `pyproject.toml` since Stage 1.1 (SearchPort)
- **License:** BSD-3-Clause (verified at ADR-021)
- **Kosmos location:** lazy-imported inside `adapters/notification/kernel/adapter.py::NtfySink._ensure_client`
- **Port(s):** `NotificationPort` (Sink seam via `NtfySink` stub)
- **Modifications:** none — upstream client used unmodified with `timeout=0.4` to protect Build-Sequence §1.12 <500ms DoD.
- **Notes:** no new runtime dep added at Stage 1.12; NtfySink reuses the existing httpx vendoring.
- **ADR:** ADR-030
- **Logged:** 2026-07-29 22:52 EDT

#### Rigpa-v2 `NotificationCenterService` pattern — `PATTERN-VENDORED`
- **Source:** https://github.com/rmholston420/Rigpa-v2 (files: `backend/src/rigpa/notifications/service.py`, `backend/src/rigpa/routers/notifications.py`, `backend/src/rigpa/routers/alerts.py`, `backend/src/rigpa/tektos/alert_service.py`)
- **Commit / Version:** inspected at HEAD 2026-07-29 (cached at `/tmp/donor-notif/`)
- **License:** internal donor (rmholston420); Kosmos vendors pattern only, not source.
- **Kosmos location:** `adapters/notification/kernel/adapter.py::InProcessSink` (ring-buffer FIFO semantics + read/dismiss bookkeeping)
- **Port(s):** `NotificationPort` (primary Sink)
- **Modifications:** dropped FastAPI dependency-graph glue (Rigpa donor uses `Depends()` and `str` severity, domain-locked to Rigpa REST handlers); reused pattern (200-cap FIFO ring buffer, newest-first, per-notification UUID, thread-safe `RLock`, `read`/`dismissed` set bookkeeping, four-severity taxonomy); replaced open-set `str` severity with `AlgedonicTier` enum (INFO/WARN/ACTION/ALGEDONIC per spec §30/§280/§344); made verbs async; wrapped behind `Sink` Protocol seam so external sinks slot in without port-surface change.
- **Notes:** matches ADR-028/029 domain-locking rejection pattern. Kosmos ports the ring-buffer + read/dismiss pattern, not the FastAPI class.
- **ADR:** ADR-030
- **Logged:** 2026-07-29 22:52 EDT

#### Forge-OH `bff/routers/notifications.py` pattern — `PATTERN-VENDORED (reference only)`
- **Source:** https://github.com/rmholston420/Forge-OH (file: `bff/routers/notifications.py`)
- **Commit / Version:** inspected at HEAD 2026-07-29 (cached at `/tmp/donor-notif/forge-notifications.py`)
- **License:** internal donor (rmholston420); Kosmos vendors pattern only, not source.
- **Kosmos location:** reference for future kernel-dashboard-native `WebSocketSink` (deferred to Stage 1.14 FrontendContractPort landing)
- **Port(s):** `NotificationPort` (future dashboard-native Sink)
- **Modifications:** none at Stage 1.12; used as design reference for how the kernel dashboard will poll `InProcessSink.snapshot(limit)` at Stage 1.14.
- **ADR:** ADR-030
- **Logged:** 2026-07-29 22:52 EDT

### FrontendContractPort

#### Rigpa-LMS `RigpaFrontendPlugin` shape — `PATTERN-VENDORED`
- **Source:** https://github.com/rmholston420/Rigpa-LMS (file: `frontend/src/plugins/dashboard/index.ts`)
- **Commit / Version:** inspected at HEAD 2026-07-29 (cached at `/tmp/donor-frontend/rigpa-dashboard-index.ts`)
- **License:** internal donor (rmholston420); Kosmos vendors pattern only, not source.
- **Kosmos location:** `ports/frontend_contract.py::PluginDescriptor` (Python dataclass mirror of donor TypeScript shape)
- **Port(s):** `FrontendContractPort` (primary descriptor shape)
- **Modifications:** ported donor `RigpaFrontendPlugin` shape (`name`, `stateNamespace`, `designTokens`, `routes` — each route with `path`/`label`/`icon` + lazy loader) to Python `PluginDescriptor` frozen dataclass; renamed camelCase to snake_case; typed `routes` as `tuple[Route, ...]` with `lazy_module: str` (frontend resolves via `import(lazy_module)`); extended with Kosmos-specific fields (`version`, `kernel_compat`, `panels: tuple[Panel, ...]`) driven by spec §280 nine-panel kernel dashboard; rejected donor `PluginRoutes.tsx` React-Suspense mount code as too domain-locked to Rigpa file-relative lazy semantics.
- **Notes:** kernel-side authority is Python (this port); frontend-side Next.js/React 19/Radix/shadcn/ui/Tailwind/Zustand/TanStack Query shell lands separately per spec §21.3.5 and consumes `KernelSchema` via HTTP.
- **ADR:** ADR-031
- **Logged:** 2026-07-29 23:05 EDT

#### Rigpa-LMS backend `RigpaPlugin` lifecycle protocol — `PATTERN-VENDORED (reference only)`
- **Source:** https://github.com/rmholston420/Rigpa-LMS (file: `backend/src/rigpa_core/plugins/scaffold_plugin.py`)
- **Commit / Version:** inspected at HEAD 2026-07-29 (cached at `/tmp/donor-frontend/rigpa-scaffold-plugin.py`)
- **License:** internal donor (rmholston420); Kosmos vendors pattern only, not source.
- **Kosmos location:** reference for backend lifecycle contract (`startup`/`shutdown`/`health_check`) — not vendored at Stage 1.14; Kosmos exposes `is_healthy()` / `close()` on the port itself.
- **Port(s):** `FrontendContractPort` (informs future `PluginLifecyclePort` if needed)
- **Modifications:** none at Stage 1.14; Kosmos treats backend plugin lifecycle as orthogonal to frontend UI-schema publication.
- **ADR:** ADR-031
- **Logged:** 2026-07-29 23:05 EDT

#### `pathlib` + `json` (stdlib) — `VENDORED (reused stdlib)`
- **Source:** Python 3.12 standard library
- **Commit / Version:** stdlib
- **License:** PSF-2.0
- **Kosmos location:** `adapters/frontend_contract/kernel/adapter.py::FileManifestStore`
- **Port(s):** `FrontendContractPort` (ManifestStore stub for Stage 5 auditor wiring)
- **Modifications:** used unmodified with atomic tmp-rename write via `tempfile.mkstemp` + `Path.replace`; no new runtime dependency added at Stage 1.14.
- **Notes:** primary storage is `InMemoryManifestStore` (dict-backed) which is sufficient for §1.14 DoD; `FileManifestStore` is present as a proven-swappable stub only.
- **ADR:** ADR-031
- **Logged:** 2026-07-29 23:05 EDT

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
