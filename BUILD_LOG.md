# Kosmos Build Log

Append-only. Never edit or delete a prior entry. One entry per completed step.
Timestamps in America/Detroit (EDT/EST). Format: `YYYY-MM-DD HH:MM EDT`.

Use the `kosmos-log-maintenance` Perplexity Computer skill.

---

<!-- Example (delete when adding real entries)

## 2026-07-30 09:15 EDT — Stage 0.1 monorepo skeleton created

- **Stage / plugin / port:** Stage 0.1 · repo bootstrap
- **What changed:** Created top-level directories and pyproject.toml pinned to Python 3.12
- **Files touched:** `kosmos/pyproject.toml`, `kosmos/{kernel,plugins,ports,adapters,governance,ops,docs,adrs,templates,.perplexity/skills}/`
- **Ports / adapters affected:** none
- **PORTING_LEDGER / ADR updated:** ADR index initialized; PORTING_LEDGER seeded from v25 bundle
- **Stop-condition status:** met — proceeding to 0.2

-->

## 2026-07-29 21:00 EDT — ADR-021 authored: introduce SearchPort

- **Stage / plugin / port:** Stage 1.1 · SearchPort (new)
- **What changed:** Authored ADR-021 introducing SearchPort as the 11th formal Kosmos port. Unblocks Stage 1.1 SearXNG donor consolidation (previously blocked by port-workflow skill Step 5 stop condition — no existing port fit for web search).
- **Files touched:**
  - `docs/adrs/ADR-021-searchport-introduction.md` (new)
  - `docs/adrs/README.md` (ADR-021 row added)
  - `docs/Kosmos-Build-Spec-v25.md` §4.1 (Ten → Eleven, SearchPort row added) + §17 (ADR-021 row added)
- **Ports / adapters affected:** SearchPort declared (Protocol implemented in next entry)
- **PORTING_LEDGER / ADR updated:** ADR-021 Ratified v25
- **Stop-condition status:** met — proceeding to SearXNG consolidation

---

## 2026-07-29 21:05 EDT — Stage 1.1 Ollama adapter consolidated

- **Stage / plugin / port:** Stage 1.1 · LLMPort · Ollama adapter
- **What changed:** Consolidated three donor Ollama adapters (Rigpa-LMS `core/llm/ollama.py` + `domains/integrations/ollama.py` + `axiom/packages/axiom_providers/ollama.py`) into a single adapter at `adapters/llm/ollama/`. Base = Rigpa core (async client + singleton + full API coverage); added axiom streaming (`generate_stream`); folded away Rigpa integrations typed-schema variant; keyword-only kwargs; non-throwing `is_healthy`.
- **Files touched:**
  - `adapters/__init__.py`, `adapters/llm/__init__.py`, `adapters/llm/ollama/__init__.py`, `adapters/llm/ollama/adapter.py`, `adapters/llm/ollama/test_contract.py`
- **Ports / adapters affected:** LLMPort (adapter side; `ports/llm.py` Protocol formalization deferred to Stage 1.2)
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §LLM stack — Ollama entry added as VENDORED (Stage 1.1); ADR-012 remains Ratified v25
- **Stop-condition status:** met — 4 smoke tests pass; awaiting LLMPort Protocol at Stage 1.2 for full contract test

---

## 2026-07-29 21:05 EDT — Stage 1.1 SearXNG adapter consolidated + SearchPort implemented

- **Stage / plugin / port:** Stage 1.1 · SearchPort · SearXNG adapter
- **What changed:** Implemented `ports/search.py` (SearchPort Protocol + SearchResult/SearchResponse dataclasses per ADR-021). Consolidated two donor SearXNG adapters (Rigpa-LMS + axiom) into `adapters/search/searxng/`. Base = Rigpa (JSON + typed response + engines/language); added axiom's HTML-fallback parser for 403 responses; added `provenance` field (mandatory per ADR-021 for zero-trust memory writes); added `latency_ms` timing; non-throwing `search()` returns empty response on backend failure.
- **Files touched:**
  - `ports/__init__.py`, `ports/search.py` (new)
  - `adapters/search/__init__.py`, `adapters/search/searxng/__init__.py`, `adapters/search/searxng/adapter.py`, `adapters/search/searxng/test_contract.py`
  - `pyproject.toml` (new)
- **Ports / adapters affected:** SearchPort declared and satisfied by SearxngAdapter
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §Search — SearXNG entry added as VENDORED (Stage 1.1); references ADR-012 + ADR-021
- **Stop-condition status:** met — 8 contract tests pass including `isinstance(adapter, SearchPort)` runtime-protocol check, empty-response-on-failure guarantee, provenance-populated invariant, keyword-only kwargs signature

---

## 2026-07-29 21:20 EDT — ADR-022 authored: LLMPort surface expansion

- **Stage / plugin / port:** Stage 1.2 · LLMPort
- **What changed:** Authored ADR-022 to amend Kosmos-Build-Spec-v25.md §4.1's LLMPort row from the aspirational 3-method surface (`complete/stream/embed`) to the donor-derived 10-method surface (`generate/generate_text/chat/generate_stream/embed/list_models/pull_model/delete_model/is_healthy/close`). Option B chosen over A (verbatim spec) and C (split into LLMPort + ModelRegistryPort) — rationale: single-user local-first Colossus target means model management is a first-class user op, not admin-only; C's second port adds fault-injection/contract-test surface for what is functionally one Ollama process.
- **Files touched:**
  - `docs/adrs/ADR-022-llmport-surface-expansion.md` (new)
  - `docs/adrs/README.md` (ADR-022 row)
  - `docs/Kosmos-Build-Spec-v25.md` §4.1 LLMPort Contract column expanded; §17 ADR-022 row
  - `docs/PORTING_LEDGER.md` §Ollama entry references ADR-022
- **Ports / adapters affected:** LLMPort surface defined
- **PORTING_LEDGER / ADR updated:** ADR-022 Ratified v25
- **Stop-condition status:** met

---

## 2026-07-29 21:22 EDT — Stage 1.2 LLMPort Protocol formalized; OllamaAdapter binding confirmed

- **Stage / plugin / port:** Stage 1.2 · LLMPort
- **What changed:** Implemented `ports/llm.py` (LLMPort Protocol matching ADR-022 surface). Updated OllamaAdapter docstring to reference the port. Extended contract test to assert `isinstance(OllamaAdapter(), LLMPort)` at runtime; added coverage for method presence, `generate_stream` returning `AsyncIterator`, keyword-only-kwargs discipline on `generate/chat/embed/pull_model/delete_model`, non-throwing `is_healthy`, and singleton behavior.
- **Files touched:**
  - `ports/llm.py` (new)
  - `adapters/llm/ollama/adapter.py` (docstring only)
  - `adapters/llm/ollama/test_contract.py` (rewritten; 12 tests now vs. 4 smoke tests before)
- **Ports / adapters affected:** LLMPort declared and satisfied by OllamaAdapter
- **PORTING_LEDGER / ADR updated:** — (ADR-022 already logged above)
- **Stop-condition status:** met — 20/20 tests pass across `adapters/` (Ollama 12 + SearXNG 8)

---

## 2026-07-29 21:38 EDT — Stage 1.3 llama-swap adapter vendored; LLMPort swappability proven

- **Stage / plugin / port:** Stage 1.3 · LLMPort (second adapter)
- **What changed:** Vendored `mostlygeek/llama-swap@0c42333` (MIT, external Go daemon) as `adapters/llm/llama_swap/`. HTTP-client adapter speaks llama-swap's OpenAI-compatible endpoints (`/v1/completions`, `/v1/chat/completions`, `/v1/embeddings`, `/v1/models`) and llama-swap-native `/health`. Satisfies LLMPort (ADR-022) with a documented capability subset: `pull_model` / `delete_model` raise `NotImplementedError` because llama-swap does not manage weights (models are declared in its `config.yaml`). All other LLMPort methods fully implemented. Cold-load/warm-swap benchmarks deferred to Phase 1.7 window per ADR-009.
- **Files touched:**
  - `adapters/llm/llama_swap/__init__.py` (new)
  - `adapters/llm/llama_swap/adapter.py` (new)
  - `adapters/llm/llama_swap/test_contract.py` (new)
  - `docs/PORTING_LEDGER.md` — llama-swap flipped from PLANNED to VENDORED (Stage 1.3) with commit SHA, license, modifications, ADR refs; removed redundant SUPERSEDED provenance stub (git history preserves it)
- **Ports / adapters affected:** LLMPort — now satisfied by **two** adapters (Ollama + llama-swap); Protocol swappability proven at runtime
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §LLM stack — llama-swap VENDORED entry added; references ADR-009 + ADR-022
- **Stop-condition status:** met — 35/35 tests pass; `test_two_adapters_satisfy_same_llm_port` verifies both adapters isinstance-check against LLMPort simultaneously

---

## 2026-07-29 21:32 EDT — ADR-023 authored: EventBusPort envelope-first MVP

- **Stage / plugin / port:** Stage 1.4 · EventBusPort
- **What changed:** Authored ADR-023 to amend Kosmos-Build-Spec-v25.md §4.1's EventBusPort row from the aspirational 3-method surface (`publish/subscribe/ack`) to the donor-derived envelope-first surface (`publish(envelope)/subscribe/unsubscribe/read_recent/is_healthy/close`). Option B chosen over A (verbatim spec — `ack` cannot be responsibly designed at Stage 1.4 because no cross-process consumer exists to validate it) and C (full consumer-group surface — high API-drift risk without a real workload). Envelope discipline (`event_type/producer_plugin/payload/event_id/occurred_at/schema_version`) locked in at Protocol layer so downstream `MemoryPort.write_event()` gets provenance from `envelope.producer_plugin` by construction, satisfying ADR-008 zero-trust write contract. Consumer-group semantics deferred to future ADR-024, which MUST land before Stage 2 (Tektos) begins consuming events out-of-process.
- **Files touched:**
  - `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (new)
  - `docs/adrs/README.md` (ADR-023 row)
  - `docs/Kosmos-Build-Spec-v25.md` §4.1 EventBusPort Contract column expanded; §17 ADR-023 row
- **Ports / adapters affected:** EventBusPort surface + EventEnvelope shape defined
- **PORTING_LEDGER / ADR updated:** ADR-023 Ratified v25
- **Stop-condition status:** met

---

## 2026-07-29 21:34 EDT — Stage 1.4 EventBusPort formalized; Valkey adapter vendored

- **Stage / plugin / port:** Stage 1.4 · EventBusPort
- **What changed:** Implemented `ports/event_envelope.py` (frozen dataclass with `__post_init__` validation) and `ports/event_bus.py` (`EventBusPort` runtime-checkable Protocol per ADR-023). Wrote `adapters/event_bus/valkey/adapter.py` — stream-append + in-process fan-out; injectable `StreamClient` Protocol with `InMemoryStreamClient` fake so tests need no live Valkey. Publish accepts only `EventEnvelope` (raw-dict publish raises `TypeError`). `is_healthy` non-throwing (ADR-023 rule 5). `redis` imported lazily so unit tests don't require it installed. Extended contract test to 19 tests covering envelope invariants, Protocol conformance for both `EventBusPort` and `StreamClient`, publish round-trip via `read_recent`, in-process fan-out delivery + `unsubscribe`, keyword-only kwargs on `read_recent`, non-throwing `is_healthy`, idempotent `close`, and singleton behavior.
- **Files touched:**
  - `ports/event_envelope.py` (new)
  - `ports/event_bus.py` (new)
  - `adapters/event_bus/__init__.py` (new)
  - `adapters/event_bus/valkey/__init__.py` (new)
  - `adapters/event_bus/valkey/adapter.py` (new)
  - `adapters/event_bus/valkey/test_contract.py` (new)
  - `docs/PORTING_LEDGER.md` — new §Event Bus with redis-py VENDORED + Rigpa envelope/stream-client pattern VENDORED
  - `pyproject.toml` — adapter subpackages enumerated for editable install
- **Ports / adapters affected:** EventBusPort declared and satisfied by ValkeyEventBusAdapter; ADR-007 (events-only cross-plugin coupling) is now executable for the first time
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §Event Bus — 2 VENDORED entries (redis-py + Rigpa envelope pattern)
- **Stop-condition status:** met — 54/54 tests pass across `adapters/` (Ollama 12 + llama-swap 15 + SearXNG 8 + EventBus 19); Protocol conformance verified via `isinstance(adapter, EventBusPort)`

---

## 2026-07-29 21:36 EDT — ADR-024 authored: SecretsPort age-file primary (Vault deferred)

- **Stage / plugin / port:** Stage 1.5 · SecretsPort
- **What changed:** Authored ADR-024 to reconcile spec §4.1 (`SecretsPort` → hvac/Vault, `get_secret/rotate/lease`) with the project's local-first custom instruction and with donor Rigpa-LMS's age-encrypted file pattern. Vault is a network daemon with a control plane; Kosmos custom instructions forbid cloud control planes without explicit opt-in. Option B chosen (age-file primary + Vault-adapter deferred behind a future ADR) over Option A (verbatim Vault now, violates local-first) and Option C (defer SecretsPort entirely, underexercises ADR-007 events-only rule). `lease()` deferred until Tektos per-task secret scoping (§18.6) creates a real requirement for TTL semantics — same shape as ADR-023's deferred consumer-group `ack()`. Adopted `SecretValue` (stdlib frozen dataclass) with strict redaction: `__repr__` returns `"SecretValue(***)"`, `__eq__` compares redacted repr so distinct secrets never appear equal in logs, `__reduce__` refuses pickling, `.reveal()` is the sole raw-value accessor and is grep-able as an audit anchor. `SecretsPort` Protocol shape: `get_secret / put_secret / rotate / is_healthy / close` — rotate is intentionally distinct from put (rotate rejects unknown keys) so the audit signal for intentional key-material replacement is preserved.
- **Files touched:**
  - `docs/adrs/ADR-024-secretsport-age-file-backend.md` (new)
  - `docs/adrs/README.md` (ADR-024 row)
  - `docs/Kosmos-Build-Spec-v25.md` §4.1 SecretsPort row rewritten; §7 key-management bullet updated; §17 ADR-024 row
- **Ports / adapters affected:** SecretsPort surface + `SecretValue` shape defined
- **PORTING_LEDGER / ADR updated:** ADR-024 Ratified v25
- **Stop-condition status:** met

---

## 2026-07-29 21:37 EDT — Stage 1.5 SecretsPort formalized; age-file adapter vendored

- **Stage / plugin / port:** Stage 1.5 · SecretsPort
- **What changed:** Implemented `ports/secrets.py` (`SecretValue` frozen dataclass + `SecretsPort` runtime-checkable Protocol) and `adapters/secrets/age_file/adapter.py` (`AgeFileSecretsAdapter` with injectable `AgeBackend` Protocol + `PyrageBackend` real crypto + `InMemoryAgeBackend` deterministic fake for tests). `pyrage` and `yaml` imported lazily so unit tests do not require either dependency installed. Rotation writes to a sibling `.tmp` file then `os.replace` — POSIX-atomic so a crash mid-rotate cannot corrupt `secrets.age`. An `asyncio.Lock` serializes reads and writes so a rotate cannot land mid-decrypt. Missing secrets file treated as empty mapping so `put_secret` can bootstrap a fresh store. Non-string values rejected at both `put_secret` and `rotate`. Contract test has 23 tests covering `SecretValue` invariants (repr redaction, reveal, redacted-repr equality, hashability, pickle refusal), Protocol conformance for both `SecretsPort` and `AgeBackend`, get/put/rotate round-trip semantics, atomic file write (ciphertext prefix + no leftover `.tmp`), missing-file bootstrap, non-throwing `is_healthy` on bad ciphertext, idempotent `close`, and singleton behavior.
- **Files touched:**
  - `ports/secrets.py` (new — `SecretValue` + `SecretsPort` Protocol)
  - `adapters/secrets/__init__.py` (new)
  - `adapters/secrets/age_file/__init__.py` (new)
  - `adapters/secrets/age_file/adapter.py` (new — `AgeFileSecretsAdapter` + `PyrageBackend` + `InMemoryAgeBackend`)
  - `adapters/secrets/age_file/test_contract.py` (new — 23 tests)
  - `docs/PORTING_LEDGER.md` — new §Secrets with pyrage VENDORED + PyYAML VENDORED + Rigpa age-secrets loader pattern VENDORED
  - `pyproject.toml` — adapter subpackages enumerated for editable install
- **Ports / adapters affected:** SecretsPort declared and satisfied by AgeFileSecretsAdapter; §7 key-management path is now executable end-to-end for long-lived secrets
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §Secrets — 3 VENDORED entries (pyrage + PyYAML + Rigpa loader pattern)
- **Stop-condition status:** met — 77/77 tests pass across `adapters/` (Ollama 12 + llama-swap 15 + SearXNG 8 + EventBus 19 + Secrets 23); Protocol conformance verified via `isinstance(adapter, SecretsPort)` and `isinstance(backend, AgeBackend)`

---

## 2026-07-29 21:43 EDT — Declare pyrage/PyYAML/redis as runtime deps; seed DEBUG_LOG

- **Stage / plugin / port:** Cross-cutting · `pyproject.toml` runtime deps
- **What changed:** Live Colossus smoke test of `AgeFileSecretsAdapter + PyrageBackend` failed with `ModuleNotFoundError: No module named 'pyrage'` because Stages 1.4 and 1.5 lazy-imported vendor libraries (`pyrage`, `yaml`, `redis.asyncio`) but did not declare them in `[project].dependencies`. Contract tests (77/77) passed because they used the in-memory fakes (`InMemoryAgeBackend`, `InMemoryStreamClient`) which never trigger the lazy imports. Added `pyrage>=1.1`, `PyYAML>=6.0`, `redis>=5.0` to runtime deps. Also seeded `DEBUG_LOG.md` (mandated by custom instructions but never created) with the diagnosis entry. Established guardrail: every lazy-imported vendor library must be declared in runtime deps at commit time.
- **Files touched:**
  - `pyproject.toml` — 3 runtime deps declared (pyrage, PyYAML, redis)
  - `DEBUG_LOG.md` — new file, seeded with 2026-07-29 21:42 EDT diagnosis
- **Ports / adapters affected:** SecretsPort live path (`PyrageBackend`), EventBusPort live path (`redis.asyncio`)
- **PORTING_LEDGER / ADR updated:** —
- **Stop-condition status:** met — fix applied; DEBUG_LOG discipline now active for the project

---

## 2026-07-29 21:45 EDT — ADR-025 authored: ObservabilityPort OTel+Prometheus+structlog (Langfuse deferred)

- **Stage / plugin / port:** Stage 1.6 · ObservabilityPort
- **What changed:** Authored ADR-025 to reconcile spec §4.1 (`ObservabilityPort` → "Langfuse + OpenTelemetry", `trace/score/log_cost`) with donor reality: Rigpa-LMS ships OTel + Prometheus + structlog with LGTM (per Rigpa ADR-044); Langfuse appears in zero donor files. Local-first custom instruction and Langfuse's Postgres+ClickHouse+Redis footprint make Vault-style deferral appropriate. Option B chosen (OTel+Prometheus+structlog primary; Langfuse deferred to a future second adapter for LLM-specific prompt/response/eval-score UX). Locked in nine design decisions: `trace()` as sync context manager wrapping async and sync uniformly; `log_cost()` writes to OTel counters + active-span attributes; `score()` records a histogram (p50/p95/p99 later); `bind_context()` uses contextvars so bindings survive `await`; all exporters degrade gracefully to no-op when OTLP endpoint unreachable; `opentelemetry-*` and `structlog` imported lazily behind `OtelBackend` seam; non-throwing `is_healthy` (ADR-023 rule 5 reused); idempotent `close()` flushes both providers.
- **Files touched:**
  - `docs/adrs/ADR-025-observabilityport-otel-prometheus-structlog.md` (new)
- **Ports / adapters affected:** ObservabilityPort surface + `Span` Protocol defined; downstream LLMPort cost-accountability wiring path defined
- **PORTING_LEDGER / ADR updated:** ADR-025 Ratified v25 (spec §4.1 + §17 amendments + PORTING_LEDGER entries pending Stage 1.6 code)
- **Stop-condition status:** met (ADR authored); Stage 1.6 code + fan-out pending

---

## 2026-07-29 21:47 EDT — Stage 1.5 hotfix: PyrageBackend parses age-keygen identity file

- **Stage / plugin / port:** Stage 1.5 · SecretsPort · `PyrageBackend`
- **What changed:** Live smoke test surfaced `pyrage.IdentityError: invalid Bech32 encoding` when loading a standard `age-keygen -o` identity file. Root cause: `age-keygen` writes three lines (two `#` comments + the `AGE-SECRET-KEY-` secret line); donor Rigpa `.strip()` worked only because Rigpa's operator hand-stored a bare secret-key string. Added `PyrageBackend._extract_secret_key()` static helper that skips blank lines and comment lines, returns the first `AGE-SECRET-KEY-` line, and raises `ValueError` with remediation guidance when absent. `_ensure_identity` now routes through the helper. Four regression tests locked the fix into the contract suite.
- **Files touched:**
  - `adapters/secrets/age_file/adapter.py` (added `_extract_secret_key` static helper; `_ensure_identity` uses it)
  - `adapters/secrets/age_file/test_contract.py` (4 new regression tests)
- **Ports / adapters affected:** SecretsPort live path (`PyrageBackend`) now correctly loads `age-keygen`-formatted identity files
- **PORTING_LEDGER / ADR updated:** —
- **Stop-condition status:** met — 81/81 tests pass (77 + 4 new regression tests)

---

## 2026-07-29 21:52 EDT — Stage 1.6: ObservabilityPort formalized with OTel+Prometheus+structlog stack adapter

- **Stage / plugin / port:** Stage 1.6 · ObservabilityPort
- **What changed:** Codified ADR-025 by shipping `ports/observability.py` (`ObservabilityPort` Protocol + `Span` Protocol) and `adapters/observability/otel_stack/` (`OtelStackObservabilityAdapter` + `OtelBackend` Protocol seam + `StubOtelBackend` in-memory backend + `NoOpSpan` safe fallback). Port surface: `trace(name, *, attributes) -> Span` (sync context manager, records exceptions and re-raises), `score(name, value, *, attributes)` (histogram), `log_cost(*, model, prompt_tokens, completion_tokens, usd, attributes)` (three counters + active-span attribution), `bind_context(**keys)` / `clear_context()` (contextvars-backed), `get_tracer(name)` / `get_meter(name)` (direct-access escape hatches for plugins needing full OTel surface), `is_healthy() -> bool` (non-throwing per ADR-023 rule 5), `async close()` (idempotent flush of both providers). Third-party libs (`opentelemetry-*`, `prometheus_client`, `structlog`) imported lazily behind `OtelBackend` so contract tests do not need any real observability wheel installed — mirrors Stage 1.5 `PyrageBackend` / `InMemoryAgeBackend` split. All eight design invariants from ADR-025 enforced in code. 20 new contract tests covering Protocol conformance, `trace` open/exception path, `score` histogram reuse, `log_cost` three-counter + span-attribution behavior, `bind_context` / `clear_context`, non-throwing `is_healthy`, idempotent `close`, `NoOpSpan` fallback, and get_tracer / get_meter escape hatches. Fan-out to spec §4.1 ObservabilityPort row (rewritten to match locked-in surface), spec §17 (ADR-025 row appended), `docs/adrs/README.md` (ADR-024 backfilled + ADR-025 row added — index was one entry behind), `docs/PORTING_LEDGER.md §Observability` (Langfuse `PLANNED` stub replaced with 5 VENDORED entries: opentelemetry-sdk, opentelemetry-exporter-otlp-proto-grpc, prometheus-client, structlog, Rigpa-LMS observability seam pattern), `pyproject.toml` (`opentelemetry-sdk>=1.27`, `opentelemetry-exporter-otlp-proto-grpc>=1.27`, `prometheus-client>=0.20` declared as runtime deps; `structlog` already present is now formalized against this port; new packages registered).
- **Files touched:**
  - `ports/observability.py` (new, 172 lines)
  - `adapters/observability/__init__.py` (new)
  - `adapters/observability/otel_stack/__init__.py` (new)
  - `adapters/observability/otel_stack/adapter.py` (new, 396 lines: `OtelStackObservabilityAdapter` + `OtelBackend` + `StubOtelBackend` + `NoOpSpan`)
  - `adapters/observability/otel_stack/test_contract.py` (new, 20 tests)
  - `docs/Kosmos-Build-Spec-v25.md` (§4.1 ObservabilityPort row + §17 ADR-025 row)
  - `docs/adrs/README.md` (backfill ADR-024 row + add ADR-025 row)
  - `docs/PORTING_LEDGER.md` (§Observability, 5 VENDORED entries replacing Langfuse PLANNED)
  - `pyproject.toml` (3 new runtime deps + 2 new packages)
- **Ports / adapters affected:** `ObservabilityPort` declared and satisfied by `OtelStackObservabilityAdapter`; downstream LLMPort cost-accountability wiring path now available for Tektos in Stage 3
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §Observability — 5 VENDORED entries (opentelemetry-sdk + opentelemetry-exporter-otlp-proto-grpc + prometheus-client + structlog + Rigpa observability seam pattern)
- **Stop-condition status:** met — 101/101 tests pass across `adapters/` (Ollama 12 + llama-swap 15 + SearXNG 8 + EventBus 19 + Secrets 27 + Observability 20); Protocol conformance verified via `isinstance(adapter, ObservabilityPort)`, `isinstance(backend, OtelBackend)`, and `isinstance(NoOpSpan(), Span)`

---

## 2026-07-29 21:57 EDT — ADR-026 authored: VectorPort adopts Qdrant backend; port-level zero-trust

- **Stage / plugin / port:** Stage 1.7 · VectorPort
- **What changed:** Authored ADR-026 to reconcile spec §4.1 (`VectorPort` → `upsert / search / delete / snapshot`) with donor Rigpa `VectorStore` Protocol (four async verbs + `is_healthy`, no `snapshot`, no `close`, no zero-trust guard) and Rigpa's dual-adapter Qdrant/pgvector story (Rigpa ADR-036). Two design questions locked in per user: **Q1=A** — `upsert()` enforces §7 zero-trust at the port layer (`payload` must include truthy `provenance` and a `confidence` float in `[0.0, 1.0]`; `ValueError` otherwise). **Q2=A** — all backend-touching methods are async; `is_healthy` is the sync-non-throwing exception (ADR-023 rule 5). pgvector adapter deferred; Kosmos targets Colossus with one operator, well below the 5M-vector threshold. Deferred capabilities enumerated: pgvector fallback, multi-tenant filter grammar, batch `upsert_many`, named vectors, snapshot `restore`.
- **Files touched:**
  - `docs/adrs/ADR-026-vectorport-qdrant-backend.md` (new)
- **Ports / adapters affected:** `VectorPort` surface + `VectorHit` + `SnapshotHandle` typed value objects declared; port-level `validate_zero_trust_payload` helper declared
- **PORTING_LEDGER / ADR updated:** ADR-026 Ratified v25 (spec §4.1 + §17 amendments + PORTING_LEDGER §Vector store rewrite pending Stage 1.7 code)
- **Stop-condition status:** met (ADR authored); Stage 1.7 code + fan-out pending

---

## 2026-07-29 21:58 EDT — Stage 1.7: VectorPort formalized with Qdrant adapter (ADR-026)

- **Stage / plugin / port:** Stage 1.7 · VectorPort
- **What changed:** Codified ADR-026 by shipping `ports/vector.py` (`VectorPort` Protocol + `VectorHit` + `SnapshotHandle` frozen dataclasses + `validate_zero_trust_payload` helper + `REQUIRED_PAYLOAD_KEYS` constant) and `adapters/vector/qdrant/` (`QdrantVectorAdapter` primary + `QdrantBackend` Protocol seam + `InMemoryQdrantBackend` in-process test backend). Port surface: async `upsert / search / delete / snapshot` + sync non-throwing `is_healthy` + async idempotent `close`. Port-level §7 zero-trust enforcement is non-bypassable — `upsert()` calls `validate_zero_trust_payload(payload)` before any backend I/O, rejecting missing `provenance`, missing/invalid `confidence`, or out-of-range `confidence`. Free-form point ids (e.g. `claim-01`) hashed to stable UUIDv5 under `POINT_ID_NAMESPACE` before hitting the backend (donor Rigpa `QdrantClaimUpserter.claim_point_id` pattern) — Qdrant only accepts numeric or UUID ids. Collection creation lazy: `ensure_collection` inferrs dim from first vector; dim mismatch on same collection raises. `qdrant-client` is a lazy import inside the future `RealQdrantBackend` (not shipped in Stage 1.7 — added when the Docker Compose Qdrant service lands); `qdrant-client>=1.11` declared in `pyproject.toml` runtime deps AT COMMIT TIME per DEBUG_LOG 2026-07-29 21:42 EDT guardrail. `InMemoryQdrantBackend` implements cosine similarity in pure Python + supports snapshot / filter for contract tests; zero third-party imports. 33 new contract tests covering Protocol conformance for `VectorPort` + `QdrantBackend`, zero-trust guard (5 negative cases + 1 positive), `upsert` validation (empty vector, non-numeric elements), `upsert / search` round-trip, `search` ordering + `limit` + `filter` + unknown-collection + zero-limit + empty-query-vector, point-id UUIDv5 stability + upsert/delete id-mapping symmetry, `delete` unknown-collection / unknown-id no-op semantics, `snapshot` typed-handle return, non-throwing `is_healthy` + `close` idempotence + close-error swallowing, first-write dim inference + dim-mismatch rejection.
- **Files touched:**
  - `ports/vector.py` (new, 195 lines)
  - `adapters/vector/__init__.py` (new)
  - `adapters/vector/qdrant/__init__.py` (new)
  - `adapters/vector/qdrant/adapter.py` (new, 343 lines: `QdrantVectorAdapter` + `QdrantBackend` + `InMemoryQdrantBackend` + `_to_point_id` + `_cosine` + `_matches_filter`)
  - `adapters/vector/qdrant/test_contract.py` (new, 33 tests)
  - `docs/Kosmos-Build-Spec-v25.md` (§4.1 VectorPort row + §17 ADR-026 row)
  - `docs/adrs/README.md` (ADR-026 row)
  - `docs/PORTING_LEDGER.md` (§Vector store, 3 entries: Qdrant server PLANNED + qdrant-client VENDORED + Rigpa vector-Protocol donor pattern VENDORED)
  - `pyproject.toml` (`qdrant-client>=1.11` runtime dep + 2 new packages registered)
- **Ports / adapters affected:** `VectorPort` declared and satisfied by `QdrantVectorAdapter`; downstream `MemoryPort` (Stage 1.8, DozerDB + Graphiti) will consume this for entity-vector storage; Gnosis (Stage 6, deep-research claim upserts) will consume it directly
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §Vector store rewritten — Qdrant `PLANNED` stub expanded to 3 entries (Qdrant server PLANNED as Compose service + qdrant-client VENDORED + Rigpa donor VENDORED)
- **Stop-condition status:** met — 134/134 tests pass across `adapters/` (Ollama 12 + llama-swap 15 + SearXNG 8 + EventBus 19 + Secrets 27 + Observability 20 + Vector 33); Protocol conformance verified via `isinstance(adapter, VectorPort)` and `isinstance(backend, QdrantBackend)`
