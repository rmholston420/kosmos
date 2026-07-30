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

---

## 2026-07-29 22:01 EDT — ADR-027 authored: MemoryPort full surface + DozerDB + Graphiti + AMG

- **Stage / plugin / port:** Stage 1.8 · MemoryPort
- **What changed:** Authored ADR-027 to codify the full `MemoryPort` surface + enforcement placement + Stage 1.8 scope. **Explicitly confirmed ADR-008 already ratifies DozerDB as the graph backend — no reopening.** ADR-010 (Zetesis inner loop AREX vs. LangChain Deep Research) is unrelated to MemoryPort and remains OPEN pending its own Phase-6.2 head-to-head benchmark. Two design questions locked in per user: **Q1=A** — full four-verb surface in Stage 1.8, Graphiti pulled forward from Stage 4.2. **Q2=C** — both port-level zero-trust guard AND Agent Memory Guard v0.2.2 landed at Stage 1.8; port-level guard is the non-bypassable floor, AMG runs as a defense-in-depth policy layer atop it. Deferred: AMG v0.3.0 upgrade (v0.3.0 unshipped, v0.2.2 latest verified May 3, 2026); CIDOC-CRM full type-hierarchy enforcement (Gnosis 3.1); sign/scope/TTL for high-impact writes; delete/soft-delete; streaming query_temporal.
- **Files touched:**
  - `docs/adrs/ADR-027-memoryport-dozerdb-graphiti-amg.md` (new)
- **Ports / adapters affected:** `MemoryPort` full surface + `MemoryEventId` + `MemoryHit` + `MemoryWriteBlocked` + `validate_zero_trust_write` + `MEMORY_REQUIRED_FIELDS` declared
- **PORTING_LEDGER / ADR updated:** ADR-027 Ratified v25 (spec §4.1 + §17 amendments + PORTING_LEDGER §Memory / Graph rewrite pending Stage 1.8 code)
- **Stop-condition status:** met (ADR authored); Stage 1.8 code + fan-out pending

---

## 2026-07-29 22:03 EDT — Stage 1.8: MemoryPort formalized with DozerDB + Graphiti + AMG (ADR-027)

- **Stage / plugin / port:** Stage 1.8 · MemoryPort
- **What changed:** Codified ADR-027 by shipping `ports/memory.py` (`MemoryPort` Protocol + `MemoryEventId` + `MemoryHit` frozen dataclasses + `MemoryWriteBlocked` exception + `MEMORY_REQUIRED_FIELDS` constant + `validate_zero_trust_write` non-bypassable pure-function guard) and `adapters/memory/dozerdb/` (`DozerDbMemoryAdapter` primary + `GraphBackend` Protocol seam + `AmgPolicy` Protocol seam + `TemporalIndex` Protocol seam + `InMemoryGraphBackend` + `NoOpAmgPolicy` + `AlwaysBlockAmgPolicy` + `AlwaysQuarantineAmgPolicy` + `InMemoryTemporalIndex` test doubles + `AmgVerdict` frozen dataclass). Port surface: async `write_event / query_temporal / link_entities / quarantine_write` + sync non-throwing `is_healthy` + async idempotent `close`. Write-time enforcement order: **(1)** `validate_zero_trust_write` runs at the top of every write method — rejects missing/empty `provenance` string, non-string `provenance`, missing `confidence`, non-numeric `confidence`, bool `confidence` (bool subclass check mirrors ADR-026), or `confidence` outside `[0.0, 1.0]`; **(2)** `AmgPolicy.evaluate` returns `AmgVerdict` with `allow / redact / quarantine / block` decision — `block` raises `MemoryWriteBlocked`, `quarantine` routes to `quarantine_write` lane (NOT indexed in Graphiti — not semantic memory per spec §115), `redact` uses `redacted_payload`, `allow` proceeds; **(3)** graph transaction writes CIDOC-CRM-shaped decomposition (subject `:Entity` node + object `:Entity` node + `:MemoryEvent` node with full provenance/confidence/pii_tier/source_citation properties + `SUBJECT_OF` + `OBJECT_OF` edges); **(4)** `TemporalIndex.record_event` registers the episode with the current UTC timestamp for `as_of` queries. Real backends (`DozerDbGraphBackend` via `neo4j` driver + `AmgV02Policy` via `agent_memory_guard` v0.2.2 + `GraphitiTemporalIndex` via `graphiti_core`) are lazy imports — not shipped in Stage 1.8 code; land with Docker Compose ops-deploy stage. `pyproject.toml` runtime deps declared AT COMMIT TIME per DEBUG_LOG 2026-07-29 21:42 EDT guardrail: `neo4j>=5.26` (Apache-2.0 AND Python-2.0) + `graphiti-core>=0.5` (Apache-2.0) + `agent-memory-guard==0.2.2` (pinned exactly). 42 new contract tests covering Protocol conformance for `MemoryPort` + `GraphBackend` + `AmgPolicy` + `TemporalIndex`, `MEMORY_REQUIRED_FIELDS` freeze, port-level guard 11-case matrix (5 negative + 3 boundary + 3 positive), `write_event` graph + temporal round-trip, guard-before-backend invariant, AMG `block / redact / quarantine` routing (with a custom test-only `RedactAmg` policy), `link_entities` edge creation + guard rejection + AMG block, `quarantine_write` graph write + no temporal index side-effect + guard rejection, `query_temporal` typed-hit return + `as_of` filter + `limit`, `is_healthy` true/false transitions + defensive `try/except -> False` when backend raises, `close` idempotence + `close` swallowing backend errors. Added `asyncio_mode = "auto"` to `[tool.pytest.ini_options]` so `pytest-asyncio` (dev dep) handles the async test functions.
- **Files touched:**
  - `ports/memory.py` (new, 201 lines)
  - `adapters/memory/__init__.py` (new)
  - `adapters/memory/dozerdb/__init__.py` (new)
  - `adapters/memory/dozerdb/adapter.py` (new, 496 lines: `DozerDbMemoryAdapter` + `GraphBackend` + `AmgPolicy` + `TemporalIndex` + `AmgVerdict` + 4 in-memory test doubles)
  - `adapters/memory/dozerdb/test_contract.py` (new, 42 tests, 443 lines)
  - `docs/Kosmos-Build-Spec-v25.md` (§4.1 MemoryPort row rewritten + §17 ADR-027 row)
  - `docs/Kosmos-Build-Sequence-v25.md` (§1.8 DoD expanded + §4.2 amended to note Graphiti now at 1.8)
  - `docs/adrs/README.md` (ADR-027 row)
  - `docs/PORTING_LEDGER.md` (§Memory / Graph rewrite: 3 PLANNED entries → 5 entries: DozerDB server PLANNED as Compose service + `neo4j` VENDORED + graphiti-core VENDORED + agent-memory-guard v0.2.2 VENDORED + Rigpa MemoryBridge donor pattern VENDORED)
  - `pyproject.toml` (3 new runtime deps + 2 new packages registered + `asyncio_mode = "auto"`)
- **Ports / adapters affected:** `MemoryPort` declared and satisfied by `DozerDbMemoryAdapter`; unblocks Stage 2 (Tektos — durable outputs through MemoryPort per spec §572), Stage 3.1 (Gnosis — typed claim-triple schema rule per spec §566), Stage 4.2 (Graphiti — reduced to tuning + benchmarks; core vendored at 1.8), Stage 5.1 (Oikos — jurisdiction rule-pack facts as provenance-tagged semantic memory per spec §482)
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §Memory / Graph fully rewritten — 3 PLANNED stubs replaced with 5 entries (1 PLANNED Compose service + 4 VENDORED)
- **Stop-condition status:** met — 176/176 tests pass across `adapters/` (Ollama 12 + llama-swap 15 + SearXNG 8 + EventBus 19 + Secrets 27 + Observability 20 + Vector 33 + Memory 42); Protocol conformance verified via `isinstance(adapter, MemoryPort)`, `isinstance(backend, GraphBackend)`, `isinstance(policy, AmgPolicy)`, `isinstance(index, TemporalIndex)`

---

## 2026-07-29 22:18 EDT — Stage 1.9: Memory-bridge redundancy resolved — Gnosis schema wins 6/6 (ADR-013 LOCKED)

- **Stage / plugin / port:** Stage 1.9 · MemoryPort (formal ADR-013 resolution, no code changes)
- **What changed:** Executed ADR-013's mandatory procedure now that Stage 1.8 has landed the winning shape. Enumerated schemas side-by-side, enumerated call sites, ran the 6-axis score matrix, applied ADR-013's selection rule (Gnosis wins unless Rigpa strictly higher on 4/6). Rigpa `MemoryBridge` scored strictly higher on **0/6** axes; threshold not met; **Gnosis provenance schema wins 6/6**. Winning implementation was already committed in `0e77199` as `ports/memory.py` + `adapters/memory/dozerdb/` — zero new code required. Rigpa donor **pattern** (async Neo4j driver singleton + Cypher-per-verb structure) remains VENDORED in `PORTING_LEDGER.md` for reuse in the future `DozerDbGraphBackend`; Rigpa **write schema** (`str(metadata or {})` + missing provenance/confidence/CIDOC-CRM triple + missing quarantine lane + missing temporal index) is formally rejected. Preserved lessons from the loser documented in §5 of the comparison doc (async driver singleton, Cypher-per-verb structure, `HAS_MEMORY` owner-edge pattern noted but not adopted — Kosmos is single-user, `get_memory_graph` visualization query, `delete_memory` verb pattern for whenever soft-delete is added per ADR-027 §Deferred).
- **Files touched:**
  - `docs/memory-bridge-comparison.md` (new, 243 lines) — side-by-side schemas + call-site enumeration + 6-axis score matrix + verdict + preserved lessons + references
  - `docs/adrs/ADR-013-memory-bridge-selection.md` (STATUS AMENDMENT block added at top; status line rewritten to **LOCKED** with verdict + date + Stage 1.9 lock-in phase; body preserved verbatim per `kosmos-adr-authoring` amend-not-overwrite rule)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-013 row rewritten: **Ratified v25** → **LOCKED** with Gnosis-6/6 verdict + comparison-doc reference + Stage 1.9)
  - `docs/adrs/README.md` (ADR-013 index row rewritten: **Ratified v25** → **LOCKED** + verdict + 2026-07-29 + Stage 1.9)
- **Ports / adapters affected:** none directly. `MemoryPort` unchanged from Stage 1.8. ADR-013 is now the sole formal reference explaining **why** the Kosmos MemoryPort shape looks the way it does relative to Rigpa donor code, closing a spec-flagged decision loop.
- **PORTING_LEDGER / ADR updated:** ADR-013 status `Ratified v25` → `LOCKED`; ADR-027 unchanged (its own procedure ratified the winning shape; ADR-013 just formally documents the loss for the loser)
- **Stop-condition status:** met — ADR-013 DoD ("ADR-013 status = `LOCKED`; one bridge implementation; other deleted") satisfied: (1) ADR-013 marked LOCKED, (2) one implementation (Gnosis schema) survives in Kosmos as `ports/memory.py`, (3) Rigpa `MemoryBridge` schema was never ported into Kosmos code — rejection is documented at the source of choice, not by deleting non-existent Kosmos code. 176/176 tests still green (no code changes).


## 2026-07-29 22:35 EDT — Stage 1.10: DataPort authored — ADR-028 Ratified v25 + JSON-LD + JCS + pluggable Signer seam

- **Stage / plugin / port:** Stage 1.10 · DataPort · ADR-028 authoring (spec-driven, pre-code)
- **What changed:** Authored `docs/adrs/ADR-028-dataport-jsonld-canonical-export.md` locking two questions: (Q1=A) full three-verb DataPort surface at Stage 1.10 — `export_canonical` + `check_format_health` + `migrate_schema`, with `migrate_schema` shipping under a live never-overwrite guard even though no schemas exist yet (prevents a future ADR when Stage 3 Gnosis lands its first schema; mirrors ADR-027 Q1=A discipline); (Q2=C) JCS canonicalization + SHA-256 hash anchor + **pluggable `Signer` Protocol seam** with `NoOpSigner` as Stage 1.10 primary and `Ed25519FileSigner` deferred to Stage 5 governance-key wiring (age-key-file-backed per ADR-024 SecretsPort pattern). Rationale: Kosmos has no governance/constitution key at Stage 1.10; attaching signing to a not-yet-existent key source would either force a premature governance ADR or hardcode a dev key (zero-trust violation). Envelopes remain hash-anchored so spec §187 quarterly DR-drill cross-verify still works.
- **Files touched:**
  - `docs/adrs/ADR-028-dataport-jsonld-canonical-export.md` (new; 367 lines)
- **Ports / adapters affected:** DataPort surface declared as three verbs + `is_healthy` (sync, non-throwing) + async idempotent `close`, plus three injectable Protocol seams (`Canonicalizer` / `Signer` / `Storage`); non-bypassable port-level guard `validate_canonical_record` mandates `provenance` + `confidence` + `pii_tier` on every write.
- **PORTING_LEDGER / ADR updated:** ADR-028 authored; PORTING_LEDGER fan-out follows in the Stage 1.10 build entry below.
- **Stop-condition status:** met — ADR-028 written per `kosmos-adr-authoring` workflow (context + decision + rationale + alternatives + consequences + lock-in phase + references); ready for code.

---

## 2026-07-29 22:36 EDT — Stage 1.10: DataPort built — full surface + JCS + pluggable Signer landed; 223/223 green

- **Stage / plugin / port:** Stage 1.10 · DataPort · `ports/data.py` + `adapters/data/filesystem/` (ADR-028)
- **What changed:** Landed the full DataPort surface with three injectable Protocol seams matching ADR-027's memory-adapter pattern. `FilesystemDataAdapter` composes a `Canonicalizer` (default `SortedJsonCanonicalizer` stdlib double; production drops in `JcsCanonicalizer` backed by lazy `rfc8785` import), a `Signer` (Stage 1.10 primary `NoOpSigner` returning `""`; Stage 5 will swap in `Ed25519FileSigner`), and a `Storage` (default `InMemoryStorage`; production drops in `FilesystemStorage(root)`). Canonical envelopes carry `@context: https://kosmos.local/context/v1.jsonld` + `@type: CanonicalExport` + `schema_version: 1.0` + `record_type` + `exported_at` + `producer: kosmos-dataport` + `provenance` + `confidence` + `pii_tier` + `source_citation` + `attributes` + `payload` + trailing `canonical_hash` (sha256 hex over JCS of envelope-minus-hash-minus-sig) + `signature`. Restricted-tier records route under `{root}/restricted/{record_type}/` prefix so the ops-deploy AES-256-at-rest wrapper (spec §147) has a distinct subtree. `migrate_schema` writes new envelopes to `{root}/{record_type}/migrations/{migration_id}/{sha256}.jsonld` under fresh hashes; the never-overwrite guard (spec §230, §232) raises `MigrationTargetExists` if the target already exists with a different canonical hash and allows idempotent same-hash re-runs. `exported_at` for migrated envelopes is deterministic (derived from `sha256(migration_id + original_hash)`) so re-runs produce bit-identical output → same target path → clean idempotent skip. `check_format_health` iterates every envelope, recomputes JCS + hash, and reports mismatches as `degraded_reasons` per spec §187 DR-drill cross-verify.
- **Files touched:**
  - `ports/data.py` (new; 312 lines — `DataPort` + `Canonicalizer` + `Signer` + `Storage` Protocols + `PIITier` enum + `CanonicalExportHandle` + `FormatHealthReport` + `MigrationResult` value objects + `CanonicalRecordRejected` + `MigrationTargetExists` exceptions + `DATA_REQUIRED_FIELDS` frozenset + `validate_canonical_record` guard)
  - `adapters/data/__init__.py` (new)
  - `adapters/data/filesystem/__init__.py` (new)
  - `adapters/data/filesystem/adapter.py` (new; 625 lines — `FilesystemDataAdapter` + `SortedJsonCanonicalizer` + `JcsCanonicalizer` + `NoOpSigner` + `InMemoryStorage` + `FilesystemStorage`)
  - `adapters/data/filesystem/test_contract.py` (new; 706 lines; 47 contract tests: Protocol conformance ×5, guard ×11, canonicalizer determinism ×3, envelope round-trip ×4, signer seam swap ×2, PII tier routing ×2, storage seam swap ×1, health ×5, migrate ×8, lifecycle ×4, misc ×2)
  - `docs/Kosmos-Build-Spec-v25.md` (§4.1 line 93 DataPort row expanded to full ADR-028 surface + §17 ADR-028 row added)
  - `docs/Kosmos-Build-Sequence-v25.md` (§1.10 rewritten as DataPort landing with ADR-028 DoD + `Locked` timestamp; §1.11 marked as historical VectorPort slot already satisfied at Stage 1.7)
  - `docs/adrs/README.md` (ADR-028 index row added)
  - `docs/PORTING_LEDGER.md` (new §DataPort section with 4 entries: `rfc8785` VENDORED + `cryptography` VENDORED-deferred-use + Rigpa knowsys export donor VENDORED-pattern-only + `FilesystemDataAdapter` KOSMOS-NATIVE)
  - `pyproject.toml` (`rfc8785>=0.1.4` + `cryptography>=49` runtime deps added; `adapters.data` + `adapters.data.filesystem` packages registered)
- **Ports / adapters affected:** DataPort declared and satisfied by `FilesystemDataAdapter`; unblocks Stage 2 (Tektos — durable outputs via `export_canonical` per spec §572), Stage 3.1 (Gnosis — every Gnosis write flows through canonical export per spec §230, typed claim-triple schema stored as JSON-LD), Stage 5.1 (Oikos — jurisdiction rule-packs stored as versioned/dated JSON-LD per spec §490), Ops-Deploy (spec §187 DR-drill quarterly cross-verify against restored DozerDB/Qdrant/Litestream stores measured through `check_format_health`).
- **PORTING_LEDGER / ADR updated:** ADR-028 Ratified v25; §DataPort section with 4 entries added to PORTING_LEDGER; §17 ADR summary table + adrs/README.md + Build-Sequence §1.10 all synced.
- **Stop-condition status:** met — 223/223 tests pass across `adapters/` (176 prior + 47 new DataPort); Protocol conformance verified via `isinstance(adapter, DataPort)`, `isinstance(SortedJsonCanonicalizer(), Canonicalizer)`, `isinstance(NoOpSigner(), Signer)`, `isinstance(InMemoryStorage(), Storage)`, `isinstance(FilesystemStorage(tmp_path), Storage)`; canonical envelopes round-trip losslessly (recomputed hash ≡ stored hash); `check_format_health` flags hash tampering + non-deterministic canonicalizer + raising canonicalizer as `degraded_reasons`; `migrate_schema` never-overwrite guard fires on collision + idempotent same-hash re-run treated as skip; `is_healthy` returns `False` when canonicalizer raises (never throws); `close` is idempotent.

---

## 2026-07-29 22:40 EDT — Stage 1.11: ResourcePort authored — ADR-029 Ratified v25 + APEX substrate + priority queue

- **Stage / plugin / port:** Stage 1.11 · ResourcePort · ADR-029 authoring (spec-driven, pre-code)
- **What changed:** Authored `docs/adrs/ADR-029-resourceport-apex-substrate-priority-queue.md` locking two questions: (Q1=B) **full ResourcePort surface** at Stage 1.11 — spec §4.1 line 92 verbs (`can_allocate` + `allocate` + `replenish` + `priority_queue_position`) **plus** explicit priority-queue verbs (`enqueue` + `peek` + `dequeue` + `cancel`) as first-class port methods per spec §172 fixed-order arbitration (Phrouros anomaly > Tektos active > Synedrion/Zetesis background). Prevents a future ADR when Tektos Phase 10 model-swap-under-load lands and lets Phase-1 fixture-stubs (`zetesis-stub`, `synedrion-stub`, spec §191) consume the final Port surface directly. Mirrors ADR-027 Q1=A + ADR-028 Q1=A discipline (ship full surface early). (Q2=C) **SQLite primary (WAL) via `aiosqlite>=0.20` (MIT) + pluggable `Storage` Protocol seam** — Build-Sequence §1.13 explicitly says "SQLite-backed"; DR-drill quarterly restore per spec §187 needs restart-durable ledger balances; the Storage seam keeps contract tests third-party-free (pure-stdlib `InMemoryStorage` double) and lets a future PostgreSQL adapter slot in when multi-plugin contention exceeds SQLite's WAL-mode throughput. Six canonical `ResourceKind` enum (time/money/attention/compute/knowledge/energy). Fixed three-class `PriorityClass` IntEnum (`PHROUROS_ANOMALY=100 > TEKTOS_ACTIVE=50 > BACKGROUND=10`) satisfies spec §172 fixed order. Non-bypassable port-level zero-trust guard `validate_resource_request` rejects missing/invalid `kind`/`amount`/`intent`/`priority_class`/`requester`. `Decimal` balance precision preserved on the Port surface (mirrors donor Rigpa APEX `NUMERIC(20,4)` — SQLite stores TEXT-serialized Decimal for lossless round-trip; avoids float drift in long-horizon accumulations).
- **Files touched:**
  - `docs/adrs/ADR-029-resourceport-apex-substrate-priority-queue.md` (new; 422 lines)
- **Ports / adapters affected:** ResourcePort surface declared as eight verbs + `is_healthy` (sync, non-throwing per ADR-023 rule 5) + async idempotent `close`, plus one injectable Protocol seam (`Storage`); non-bypassable port-level guard runs at the top of every write verb before any Storage I/O.
- **PORTING_LEDGER / ADR updated:** ADR-029 authored; PORTING_LEDGER fan-out follows in the Stage 1.11 build entry below.
- **Stop-condition status:** met — ADR-029 written per `kosmos-adr-authoring` workflow (context + decision + rationale + alternatives + consequences + lock-in phase + references); ready for code.

---

## 2026-07-29 22:41 EDT — Stage 1.11: ResourcePort built — full surface + priority queue + SQLite Storage seam landed; 277/277 green

- **Stage / plugin / port:** Stage 1.11 · ResourcePort · `ports/resource.py` + `adapters/resource/sqlite/` (ADR-029)
- **What changed:** Landed the full ResourcePort surface with one injectable Protocol seam (`Storage`). `SqliteResourceAdapter` composes a `Storage` (default `InMemoryStorage` — dict-backed, pure stdlib, used by contract tests; production drops in `AioSqliteStorage.open(db_path)` with `PRAGMA journal_mode=WAL` + one shared connection per adapter lifecycle per spec §16 SQLite lifecycle rule). Port surface: allocation verbs (`can_allocate`, `allocate`, `replenish`, `priority_queue_position`) + priority-queue verbs (`enqueue`, `peek`, `dequeue`, `cancel`) + lifecycle (`is_healthy`, `close`). Priority queue ordering: `(priority_class DESC, enqueued_at ASC)` — higher IntEnum = higher priority; FIFO within a class. `PHROUROS_ANOMALY` always peeks/dequeues before any `TEKTOS_ACTIVE`, which always peeks/dequeues before any `BACKGROUND`. `allocate` deducts balance atomically on success; raises `ResourceExhausted` on over-subscription (Build-Sequence §1.13 DoD: 40 GB VRAM on 32 GB card → clean rejection). `replenish` creates the balance row with the kind's default unit on first call (compute→GB-VRAM, time→minutes, money→USD, attention→focus-blocks, knowledge→items, energy→kWh) and adds to existing balance on subsequent calls. `dequeue` marks the popped row `ALLOCATED` in storage; concurrent-dequeue race handled by re-trying next row if `update_queue_row_status` returns False. `cancel` transitions `PENDING → CANCELLED`; returns `False` on already-terminal or unknown. `priority_queue_position` raises `KeyError` on unknown/terminal request. `is_healthy` is sync, non-throwing, returns `False` after close (ADR-023 rule 5). `close` is idempotent and cascades to `Storage.close()`.
- **Files touched:**
  - `ports/resource.py` (new; 378 lines — `ResourcePort` + `Storage` Protocols + `ResourceKind` + `PriorityClass` + `RequestStatus` enums + `ResourceBalance` + `AllocationHandle` + `QueuedRequest` + `QueuePosition` value objects + `ResourceRequestRejected` + `ResourceExhausted` exceptions + `RESOURCE_REQUIRED_FIELDS` frozenset + `validate_resource_request` guard)
  - `adapters/resource/__init__.py` (new; empty package marker)
  - `adapters/resource/sqlite/__init__.py` (new; re-exports)
  - `adapters/resource/sqlite/adapter.py` (new; 547 lines — `SqliteResourceAdapter` + `AioSqliteStorage` (lazy `aiosqlite` import, WAL, one shared conn) + `InMemoryStorage` + `_default_unit` mapping)
  - `adapters/resource/sqlite/test_contract.py` (new; 750 lines; 54 contract tests: Protocol conformance ×3, guard ×15, allocation + can_allocate + replenish + over-subscription ×10 (incl. Build-Sequence §1.13 DoD test literally named `test_over_subscription_rejected_build_sequence_1_13_dod`), Decimal precision ×2, priority queue ×15, lifecycle ×3, AioSqliteStorage seam-swap ×6 (skip if `aiosqlite` absent))
  - `docs/Kosmos-Build-Spec-v25.md` (§4.1 line 92 ResourcePort row expanded to full ADR-029 surface + §17 ADR-029 row added)
  - `docs/Kosmos-Build-Sequence-v25.md` (§1.11 rewritten as ResourcePort landing with ADR-029 DoD + `Locked` timestamp; §1.13 marked as historical GPU/RAM reservation slot already satisfied at Stage 1.11)
  - `docs/adrs/README.md` (ADR-029 index row added)
  - `docs/PORTING_LEDGER.md` (new §ResourcePort section with 3 entries: `aiosqlite` VENDORED + APEX ResourceProtocol pattern PATTERN-VENDORED + Rigpa-v2 priority-queue router pattern PATTERN-VENDORED)
  - `pyproject.toml` (`aiosqlite>=0.20` runtime dep added; `adapters.resource` + `adapters.resource.sqlite` packages registered)
- **Ports / adapters affected:** ResourcePort declared and satisfied by `SqliteResourceAdapter`; unblocks Stage 1 fixture-stub contracts (spec §191 — `zetesis-stub` + `synedrion-stub` can now consume final Port verbs directly), Stage 2 Tektos (model-swap contention arbitration via `enqueue(priority_class=TEKTOS_ACTIVE)` + over-subscription via `can_allocate` per spec §572), Stage 5.1 Oikos (money/time resource kinds consumed via `can_allocate()` before recommending purchase/filing per spec §483), Kernel model-swap sidecar (llama-swap consults ResourcePort before any model load per spec §16 model-routing-policy).
- **PORTING_LEDGER / ADR updated:** ADR-029 Ratified v25; §ResourcePort section with 3 entries added to PORTING_LEDGER; §17 ADR summary table + adrs/README.md + Build-Sequence §1.11 all synced.
- **Stop-condition status:** met — 277/277 tests pass across `adapters/` (223 prior + 54 new ResourcePort); Protocol conformance verified via `isinstance(adapter, ResourcePort)` + `isinstance(InMemoryStorage(), Storage)`; over-subscription rejection literally satisfies Build-Sequence §1.13 DoD (test `test_over_subscription_rejected_build_sequence_1_13_dod` replenishes 32 GB VRAM, `can_allocate(40)` returns False, `allocate(40)` raises `ResourceExhausted`); priority queue fixed order verified across all three classes (Phrouros>Tektos>Background) with cross-class + within-class FIFO tests; `AioSqliteStorage` seam-swap tests run when `aiosqlite` present and cover over-subscription + priority order + Decimal precision + dequeue-marks-ALLOCATED + cancel + idempotent close; `is_healthy` sync-non-throwing + False-after-close verified; `close` idempotent.

---

## 2026-07-29 22:52 EDT — Stage 1.12: ADR-030 NotificationPort Ratified v25 (algedonic channel, full surface + Sink seam)

- **Stage / plugin / port:** Stage 1.12 · NotificationPort · ADR authoring
- **What changed:** Authored ADR-030 locking Q1=B (full surface — spec §4.1 verbs `notify` / `subscribe_channel` / `ack_receipt` **plus** `deliver_algedonic` fast-path + `check_delivery_slo` self-probe + `AlgedonicTier` enum {INFO/WARN/ACTION/ALGEDONIC per spec §30/§280/§344}) and Q2=B (`InProcessSink` primary matching Rigpa `NotificationCenterService` donor 200-cap FIFO ring-buffer pattern + `NtfySink` stub with lazy `httpx` import, 0.4s timeout to protect Build-Sequence §1.12 <500ms DoD). One injectable Protocol seam: `Sink` (`async deliver(record) -> bool` + `async close()`). Non-bypassable port-level zero-trust `validate_notification` guard rejects missing/invalid `tier`/`source`/`title`/`body`. Algedonic fast-path fans out to all sinks concurrently via `asyncio.gather(*, return_exceptions=True)` so latency is bounded by slowest sink, not the sum. `is_healthy` sync non-throwing (ADR-023 rule 5); `close` idempotent async, cascades to sinks. Alternatives considered: A (spec-§4.1-verbatim slim), C (defer subscribe/algedonic), Q2-A (in-process only, defer ntfy), Q2-C (pluggable seam no adapters), verbatim Rigpa port (domain-locked FastAPI class), SMS at Stage 1.12 (deferred to §344.4 mobile-fallback ADR since it needs Stage 5 governance-key wiring for Ed25519-signed tokens).
- **Files touched:**
  - `docs/adrs/ADR-030-notificationport-algedonic-channel.md` (new; 405 lines)
- **Ports / adapters affected:** NotificationPort surface declared as five verbs (`notify` / `subscribe_channel` / `ack_receipt` / `deliver_algedonic` / `check_delivery_slo`) + `register_sink`/`unregister_sink` + `is_healthy` (sync, non-throwing per ADR-023 rule 5) + async idempotent `close`, plus one injectable Protocol seam (`Sink`); non-bypassable port-level guard runs at the top of every write verb before any Sink I/O.
- **PORTING_LEDGER / ADR updated:** ADR-030 authored; PORTING_LEDGER fan-out follows in the Stage 1.12 build entry below.
- **Stop-condition status:** met — ADR-030 written per `kosmos-adr-authoring` workflow (context + decision + rationale + alternatives + consequences + lock-in phase + references); ready for code.

---

## 2026-07-29 22:53 EDT — Stage 1.12: NotificationPort built — full surface + Sink seam + algedonic <500ms DoD landed; 336/336 green

- **Stage / plugin / port:** Stage 1.12 · NotificationPort · `ports/notification.py` + `adapters/notification/kernel/` (ADR-030)
- **What changed:** Landed the full NotificationPort surface with one injectable Protocol seam (`Sink`). `KernelNotificationAdapter` composes zero-or-more `Sink` instances; primary `InProcessSink` is a thread-safe 200-cap FIFO ring buffer, newest-first, per-notification UUID, with `snapshot(limit)` + `mark_read` + `mark_dismissed` bookkeeping the kernel dashboard polls (matches Rigpa `NotificationCenterService` donor pattern). Stub `NtfySink` lazy-imports `httpx` inside `_ensure_client`, POSTs each notification to a configurable self-hosted ntfy endpoint (`{endpoint}/{topic}`) with `AlgedonicTier`→ntfy-priority header mapping (INFO=2, WARN=3, ACTION=4, ALGEDONIC=5) and a tight 0.4s timeout so a stalled remote cannot violate the <500ms DoD. `notify` runs the guard first, fans out to all registered sinks concurrently via `asyncio.gather(*, return_exceptions=True)`, returns `NotificationReceipt` with status `DELIVERED` (≥1 accept) or `PENDING` (0 accepts) + wall-clock `latency_ms` + `sink_count`. `deliver_algedonic` is the priority-interrupt fast-path — tier is implicit `ALGEDONIC`, bypasses subscriber filters, same concurrent-fan-out semantics; returns `AlgedonicReceipt`. `check_delivery_slo(window=100)` reads a bounded deque (cap 1024) of observed latencies, returns p50/p95/p99/max + `breach_count_over_500ms` per spec §170. `subscribe_channel` stores per-channel-per-subscriber subscriptions; `ack_receipt` transitions `PENDING → ACKED` and returns `False` on unknown or double-ack. Guard rejects raw string tiers (not enum), empty/non-string source/title/body, and missing fields. `is_healthy` is sync, non-throwing, returns `False` after close (ADR-023 rule 5). `close` is idempotent and cascades to `Sink.close()`, swallowing sink close errors so shutdown always completes.
- **Files touched:**
  - `ports/notification.py` (new; 326 lines — `NotificationPort` + `Sink` Protocols + `AlgedonicTier` + `NotificationStatus` enums + `NotificationRecord` + `NotificationReceipt` + `AlgedonicReceipt` + `Subscription` + `DeliverySloReport` value objects + `NotificationRejected` exception + `NOTIFICATION_REQUIRED_FIELDS` frozenset + `ALGEDONIC_SLO_MS=500` + `validate_notification` guard)
  - `adapters/notification/__init__.py` (new; empty package marker)
  - `adapters/notification/kernel/__init__.py` (new; re-exports)
  - `adapters/notification/kernel/adapter.py` (new; 446 lines — `KernelNotificationAdapter` + `InProcessSink` (ring buffer + snapshot/mark_read/mark_dismissed) + `NtfySink` (lazy httpx, 0.4s timeout, tier→priority mapping) + `_percentile` helper)
  - `adapters/notification/kernel/test_contract.py` (new; 642 lines; 59 contract tests: Protocol conformance ×6, guard ×12 (parametrized over required fields + wrong tier type + empty/non-string source/title/body), notify ×7 (delivery+multi-sink+no-sinks+guard-before-io+channel+attributes+soft-fail+raising-sink-swallowed), subscribe_channel ×4, ack_receipt ×4, deliver_algedonic ×4 including concurrent-fan-out timing test AND `test_algedonic_delivery_under_500ms_dod` literally satisfying Build-Sequence §1.12 DoD, check_delivery_slo ×5 (empty+samples+window-slice+breach-count+invalid-window), Sink seam swap ×3, InProcessSink ring-buffer semantics ×7 (newest-first+FIFO-trim+snapshot-limit+mark_read+mark_dismissed-hides+capacity>0+close-stops), NtfySink lazy import ×2, lifecycle ×5 (is_healthy-nonthrowing+close-marks-unhealthy+close-idempotent+cascades-to-sinks+swallows-sink-errors))
  - `docs/Kosmos-Build-Spec-v25.md` (§4.1 line 94 NotificationPort row expanded to full ADR-030 surface + §17 ADR-030 row added)
  - `docs/Kosmos-Build-Sequence-v25.md` (§1.12 rewritten as NotificationPort landing with ADR-030 DoD + `landed 2026-07-29 22:52 EDT` timestamp)
  - `docs/adrs/README.md` (ADR-030 index row added)
  - `docs/PORTING_LEDGER.md` (new §NotificationPort section with 3 entries: `httpx` VENDORED-reused + Rigpa-v2 `NotificationCenterService` pattern PATTERN-VENDORED + Forge-OH `bff/routers/notifications.py` pattern PATTERN-VENDORED-reference-only)
  - `pyproject.toml` (no new runtime deps; `adapters.notification` + `adapters.notification.kernel` packages registered)
- **Ports / adapters affected:** NotificationPort declared and satisfied by `KernelNotificationAdapter`; unblocks Stage 1 fixture-stub contracts (spec §191), Stage 2 Phrouros anomaly-detection consumers of `deliver_algedonic` + `check_delivery_slo` (spec §170), Stage 2.4 Praxis Approvals-Queue via `notify(tier=ACTION)` (spec §17.13), Stage 5.1 Oikos deadline reminders + filing-approval prompts (spec §488), Stage 5-plugin routines wired to NotificationPort (spec §418), Oikos runway threshold-breached → algedonic channel wiring (spec §522).
- **PORTING_LEDGER / ADR updated:** ADR-030 Ratified v25; §NotificationPort section with 3 entries added to PORTING_LEDGER; §17 ADR summary table + adrs/README.md + Build-Sequence §1.12 all synced.
- **Stop-condition status:** met — 336/336 tests pass across `adapters/` (277 prior + 59 new NotificationPort); Protocol conformance verified via `isinstance(adapter, NotificationPort)` + `isinstance(InProcessSink(), Sink)` + `isinstance(NtfySink(...), Sink)`; Build-Sequence §1.12 DoD literally satisfied by `test_algedonic_delivery_under_500ms_dod` (asserts `receipt.latency_ms < ALGEDONIC_SLO_MS` with `sink_count >= 1`); concurrent fan-out verified by `test_fans_out_to_all_sinks_concurrently` (5 sinks × 100ms sleep completes in <300ms vs. sequential 500ms); zero-trust guard runs before I/O verified by `test_notify_runs_guard_before_io` (raising sink receives nothing on validation failure); raising sink swallowed verified by `test_notify_swallows_sink_exceptions`; InProcessSink FIFO+trim+read+dismiss semantics verified; NtfySink lazy httpx import verified (`_client is None` after construction); `is_healthy` sync-non-throwing + False-after-close verified; `close` idempotent + cascades to sinks + swallows sink close errors verified.

---

## 2026-07-29 23:04 EDT — Stage 1.14: ADR-031 FrontendContractPort Ratified v25 (declarative UI schema, full surface + ManifestStore seam)

- **Stage / plugin / port:** Stage 1.14 · FrontendContractPort · ADR authoring
- **What changed:** Authored ADR-031 locking Q1=B (full surface — spec §4.1 line 91 verbs `register_plugin` / `unregister_plugin` / `list_plugins` / `get_route_manifest` / `get_design_tokens` / `get_state_namespaces` / `get_panel_manifest` / `check_ui_parity` / `render_kernel_schema` plus `is_healthy`/`close` lifecycle) and Q2=B (`InMemoryManifestStore` primary, dict-backed pure stdlib + `FileManifestStore` stub — stdlib `pathlib`+`json`, atomic tmp-rename write, deferred to Stage 5 auditor wiring). One injectable Protocol seam: `ManifestStore` (`async save(schema)` / `async load() -> KernelSchema | None` / `async close()`). PluginDescriptor mirrors the Rigpa-LMS `RigpaFrontendPlugin` donor shape (`name`/`state_namespace`/`design_tokens`/`routes`) extended with typed `Panel` value objects across nine `PanelSlot`s (spec §280 + §17.9 + §17.13: ALGEDONIC/GOVERNANCE/MEMORY_INTEGRITY/MODEL_SWAP_SLO/STUB_DEGRADATION/CONTEXT_PRESSURE/HARDWARE_RESILIENCE/APPROVALS_QUEUE/AGENT_TRACE) + `version` + `kernel_compat`. `UiParityStatus` enum {NOT_STARTED, IN_PROGRESS, COMPLIANT, GRANDFATHERED} per spec §7/§17.1 UI Parity Rule. Non-bypassable port-level zero-trust `validate_plugin_descriptor` guard rejects missing/invalid required fields, invalid plugin-name regex (`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`), empty route/panel `lazy_module`, and duplicate registrations. Design-token merge is last-registered-wins; panel ordering is `priority DESC` with insertion-order tiebreaker (deterministic). `render_kernel_schema()` returns `KernelSchema(title="Kosmos", plugins=(), panels=())` on empty registry — literal Build-Sequence §1.14 DoD anchor. `is_healthy` sync non-throwing (ADR-023 rule 5); `close` idempotent async, cascades to `ManifestStore`. Alternatives considered: A (spec-§4.1-verbatim slim), C (defer panels), Q2-A (single storage, no seam), Q2-C (pluggable seam with no adapters), verbatim Rigpa `PluginRoutes.tsx` port (rejected — domain-locked React-Suspense mount code), backend `RigpaPlugin` lifecycle protocol port (deferred — orthogonal to frontend UI-schema publication).
- **Files touched:**
  - `docs/adrs/ADR-031-frontendcontractport-declarative-ui-schema.md` (new; 431 lines)
- **Ports / adapters affected:** FrontendContractPort surface declared as nine verbs (`register_plugin` / `unregister_plugin` / `list_plugins` / `get_route_manifest` / `get_design_tokens` / `get_state_namespaces` / `get_panel_manifest` / `check_ui_parity` / `render_kernel_schema`) + `is_healthy` (sync, non-throwing per ADR-023 rule 5) + async idempotent `close`, plus one injectable Protocol seam (`ManifestStore`); non-bypassable port-level guard runs at the top of `register_plugin` before any store I/O.
- **PORTING_LEDGER / ADR updated:** ADR-031 authored; PORTING_LEDGER fan-out follows in the Stage 1.14 build entry below.
- **Stop-condition status:** met — ADR-031 written per `kosmos-adr-authoring` workflow (context + decision + rationale + alternatives + consequences + lock-in phase + references); ready for code.

---

## 2026-07-29 23:05 EDT — Stage 1.14: FrontendContractPort built — full surface + ManifestStore seam + "Kosmos" DoD landed; 392/392 green

- **Stage / plugin / port:** Stage 1.14 · FrontendContractPort · `ports/frontend_contract.py` + `adapters/frontend_contract/kernel/` (ADR-031)
- **What changed:** Landed the full FrontendContractPort surface with one injectable Protocol seam (`ManifestStore`). `KernelFrontendContractAdapter` composes exactly one `ManifestStore`; primary `InMemoryManifestStore` is a dict-backed asyncio.Lock-guarded store, sufficient for §1.14 DoD; stub `FileManifestStore` uses stdlib `pathlib` + `json` + `tempfile.mkstemp` + `Path.replace` for atomic tmp-rename writes and returns `None` on load when path is missing or JSON is corrupt (deferred to Stage 5 auditor wiring). `register_plugin` runs `validate_plugin_descriptor` first, rejects duplicates via `PluginDescriptorRejected`, derives `UiParityStatus` (COMPLIANT if descriptor has routes AND panels; else IN_PROGRESS), records `registered_at`, and persists via `_persist()` which serializes `render_kernel_schema()` through the store — store `save()` errors are swallowed (soft-fail per ManifestStore contract; observability logs elsewhere). `unregister_plugin` returns `False` on unknown, `True` on success. `list_plugins` preserves registration order. `get_route_manifest` aggregates in insertion order. `get_design_tokens` merges last-registered-wins. `get_state_namespaces` returns per-plugin namespace strings. `get_panel_manifest(slot=None)` sorts by `(priority DESC, insertion_index ASC)` for deterministic ordering; optional `slot` filter. `check_ui_parity` raises `PluginNotFound` on unknown. `render_kernel_schema` returns `KernelSchema(title="Kosmos", plugins=(), panels=(), design_tokens={}, generated_at=<utc>)` on empty registry — literally satisfies Build-Sequence §1.14 DoD via `test_empty_dashboard_renders_kosmos_title_build_sequence_1_14_dod`. `is_healthy` sync, non-throwing, `False` after close (ADR-023 rule 5). `close` idempotent, cascades to `ManifestStore.close()`, swallowing store close errors so shutdown always completes.
- **Files touched:**
  - `ports/frontend_contract.py` (new; 330 lines — `FrontendContractPort` + `ManifestStore` Protocols + `UiParityStatus` + `PanelSlot` (9 slots) enums + `Route` + `Panel` + `PluginDescriptor` + `PluginRegistration` + `KernelSchema` frozen dataclasses + `PLUGIN_REQUIRED_FIELDS` frozenset + `KERNEL_SCHEMA_TITLE="Kosmos"` + `PluginDescriptorRejected` + `PluginNotFound` exceptions + `validate_plugin_descriptor` guard)
  - `adapters/frontend_contract/__init__.py` (new; empty package marker)
  - `adapters/frontend_contract/kernel/__init__.py` (new; re-exports)
  - `adapters/frontend_contract/kernel/adapter.py` (new; 329 lines — `KernelFrontendContractAdapter` + `InMemoryManifestStore` + `FileManifestStore` + `_schema_to_dict`/`_schema_from_dict` codecs + `_derive_parity` helper)
  - `adapters/frontend_contract/kernel/test_contract.py` (new; 594 lines; 56 contract tests: Protocol conformance ×7 (adapter=FrontendContractPort + InMemory/File/Recording stores=ManifestStore + required-fields frozen + KERNEL_SCHEMA_TITLE constant + PanelSlot spec §280 completeness), guard ×11 (non-descriptor + parametrized empty required field ×4 + parametrized invalid name ×7 + empty route lazy_module + empty panel lazy_module), Build-Sequence §1.14 DoD ×2 (`test_empty_dashboard_renders_kosmos_title_build_sequence_1_14_dod` + generated_at), register/unregister ×7 (returns-registration + rejects-duplicate + guard-before-store + unregister-unknown-returns-false + register-then-unregister + reregister-after-unregister + list-preserves-order), manifest queries ×4 (route aggregation + design-tokens last-wins + state-namespaces + empty), panel manifest ×4 (priority DESC + slot filter + insertion-order tiebreak + cross-plugin aggregation), UI parity ×4 (in-progress-no-routes-no-panels + compliant-routes-and-panels + in-progress-routes-only + PluginNotFound-on-unknown), ManifestStore seam ×8 (InMemory persists + Recording receives + unregister persists + save-failure swallowed + File round-trip + File atomic-write-no-leftovers + File load-none-when-missing + File load-none-on-corrupt), lifecycle ×5 (is_healthy non-throwing + close marks unhealthy + close idempotent + close cascades + close swallows store errors))
  - `docs/Kosmos-Build-Spec-v25.md` (§4.1 line 91 FrontendContractPort row expanded to full ADR-031 surface + §17 ADR-031 row added)
  - `docs/Kosmos-Build-Sequence-v25.md` (§1.14 rewritten as FrontendContractPort landing with ADR-031 DoD + `landed 2026-07-29 23:05 EDT` timestamp)
  - `docs/adrs/README.md` (ADR-031 index row added)
  - `docs/PORTING_LEDGER.md` (new §FrontendContractPort section with 3 entries: Rigpa-LMS `RigpaFrontendPlugin` shape PATTERN-VENDORED + Rigpa-LMS backend `RigpaPlugin` lifecycle PATTERN-VENDORED-reference-only + stdlib `pathlib`+`json` VENDORED-reused-stdlib)
  - `pyproject.toml` (no new runtime deps; `adapters.frontend_contract` + `adapters.frontend_contract.kernel` packages registered)
- **Ports / adapters affected:** FrontendContractPort declared and satisfied by `KernelFrontendContractAdapter`; unblocks Stage 3.5 Next.js kernel-dashboard shell (spec §21.3.5) consumption of `KernelSchema` via HTTP, Stage 2.4 Praxis Approvals-Queue panel wiring (spec §17.13), Stage 2 Phrouros algedonic panel wiring (spec §280), spec §522 Oikos runway threshold algedonic panel, spec §597 Oikos day-one FrontendContractPort no-exception rule. UI Parity Rule per plugin DoD is now programmatically checkable via `check_ui_parity(name)`.
- **PORTING_LEDGER / ADR updated:** ADR-031 Ratified v25; §FrontendContractPort section with 3 entries added to PORTING_LEDGER; §17 ADR summary table + adrs/README.md + Build-Sequence §1.14 all synced.
- **Stop-condition status:** met — 392/392 tests pass across `adapters/` (336 prior + 56 new FrontendContractPort); Protocol conformance verified via `isinstance(adapter, FrontendContractPort)` + `isinstance(InMemoryManifestStore(), ManifestStore)` + `isinstance(FileManifestStore(path), ManifestStore)` + `isinstance(RecordingStore(), ManifestStore)`; Build-Sequence §1.14 DoD literally satisfied by `test_empty_dashboard_renders_kosmos_title_build_sequence_1_14_dod` (asserts `schema.title == "Kosmos"`, `schema.plugins == ()`, `schema.panels == ()`, `schema.design_tokens == {}`); zero-trust guard runs before store I/O verified by `test_register_runs_guard_before_store`; last-registered-wins design-token merge verified; panel priority-DESC + insertion-order tiebreak ordering verified; File-store round-trip through fresh instance verified; File-store atomic-write leaves no `.tmp` leftovers verified; File-store load returns `None` on missing/corrupt path; `is_healthy` sync-non-throwing + False-after-close verified; `close` idempotent + cascades to store + swallows store close errors verified.
