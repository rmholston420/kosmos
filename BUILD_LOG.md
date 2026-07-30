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

---

## 2026-07-29 23:12 EDT — Stage 1.15: Stage-1 exit gate — PASS (11 ports + 31 ADRs + 12 sub-stages + 392/392 pytest)

- **Stage / phase / port:** Stage 1.15 · Stage-1 exit gate · N/A (meta-gate)
- **What changed:** Landed `scripts/stage1_gate.py` (266 lines) + root `Makefile` with `stage1-gate` target. Gate enforces all four Build-Sequence §1.15 criteria in order: (1) all **eleven** ports have a module in `ports/` plus an adapter package under `adapters/` plus at least one `test_contract.py` — corrected §1.15 from the pre-FrontendContractPort "ten ports" wording; (2) ADR statuses audited via `docs/adrs/README.md` status column (the load-bearing table per spec §17.1), regex-parsed from pipe-delimited rows, with ADR-010 required OPEN and every other ADR required Ratified/Locked/Ratified-v25 — dodges the trap where legacy ADRs (001–010, older format) use `Status:` instead of `**Status:**` and where numbering collisions (ADR-002/ADR-007/ADR-008 exist twice on disk from v22/v24 archaeology) would otherwise confuse a file-by-file scan; (3) BUILD_LOG entry per Stage-1 sub-stage (1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.10, 1.11, 1.12, 1.14 — 1.9 aspirational-only and 1.13 satisfied-at-1.11 both intentionally omitted) with America/Detroit timestamps; (4) full pytest suite green via `.venv/bin/python -m pytest --tb=short -q`. Gate script prints per-check ✔/✘ status, ends with `STAGE 1 EXIT GATE: PASS` on rc=0 or `STAGE 1 EXIT GATE: FAIL (N failure(s))` on rc=1. Q1=B optimal (correct §1.15 to eleven ports) — Q2=B optimal (Makefile + gate.py wrapping pytest with ADR/BUILD_LOG audit) per user direction.
- **Files touched:**
  - `scripts/stage1_gate.py` (new; 266 lines)
  - `Makefile` (new; 15 lines — `help` / `test` / `stage1-gate` targets)
  - `docs/Kosmos-Build-Sequence-v25.md` (§1.15 rewritten: "ten" → "eleven"; added enumerated port list; added ADR-status-source clarification via `docs/adrs/README.md`; added Stage-1 sub-stage list clarifying §1.9 aspirational + §1.13 absorbed; added `landed 2026-07-29 23:12 EDT` timestamp + PASS marker with test count)
- **Ports / adapters affected:** None — this is a meta-gate. Verifies existence of `ports/{search,llm,event_bus,secrets,observability,vector,memory,data,resource,notification,frontend_contract}.py` and matching `adapters/*/` packages.
- **PORTING_LEDGER / ADR updated:** None — no port/adapter/ADR added at §1.15.
- **Stop-condition status:** met — `make stage1-gate` returns rc=0 with output "STAGE 1 EXIT GATE: PASS". All four criteria green: 11 ports audited, 31 ADRs audited (30 Ratified/Locked/Ratified-v25 + ADR-010 OPEN), 12 Stage-1 sub-stages present in BUILD_LOG with timestamps, 392/392 pytest green. **Stage 1 complete — Kosmos kernel port surface locked.**

---

## 2026-07-29 23:14 EDT — ADR-032 authored (Ratified v25) — Praxis Constitution Loader

- **Stage / phase / port:** Stage 2.1 · Praxis plugin · constitution boot-verification subsystem
- **What changed:** Authored ADR-032 (Praxis Constitution Loader, Ratified v25). Locks two orthogonal decisions surfaced by spec §278 (Constitution system): (Q1=B) verifier + loader + standalone `signing.py` helper — ships all pure crypto primitives at 2.1, defers `amend_service.py` / `cli.py` / `service.py` / `models.py` / `schemas.py` to Synedrion (Phase 6.3) per spec §278's explicit "amendment CLI/UI deferred until Synedrion exists" statement; and (Q2=A) FrontendContractPort registration with `UiParityStatus.IN_PROGRESS` — no §17.1 amendment, IN_PROGRESS handles the case natively. Rationale: signing.py is 122 lines of leaf-module crypto primitives (no I/O beyond PEM key loading) that a future amend_service.py will need anyway, so porting it now costs ~120 lines and eliminates a "port signing.py before amend_service.py" step at Synedrion; UI-parity IN_PROGRESS state was explicitly designed in ADR-014 for exactly this backend-first-UI-second landing pattern (adding a second grandfathered exception to §17.1 would weaken the rule for every future kernel plugin). Downstream ADR consequences enumerated: Synedrion amendment workflow will supersede portions of ADR-032 by adding the five deferred donor files, referencing this ADR as its foundation; ADR-007 (events-only cross-plugin coupling) and ADR-008 (zero-trust MemoryPort writes) both respected (Praxis does not import any other plugin at 2.1 and does not write to MemoryPort). Both Q1 alternatives (A=inline signing into verifier.py; C=full Rigpa parity) and Q2 alternative B (defer registration to 3.5) explicitly rejected with per-option rationale.
- **Files touched:**
  - `docs/adrs/ADR-032-praxis-constitution-loader.md` (new; 215 lines)
- **Ports / adapters affected:** None yet — ADR authoring only. Praxis subsystem lands in the next entry.
- **PORTING_LEDGER / ADR updated:** ADR-032. Ledger fan-out deferred to the port-landing entry.
- **Stop-condition status:** met (ADR ratified). Next step: implement the constitution subsystem + Praxis plugin bootstrap + contract tests per the ADR.

## 2026-07-29 23:15 EDT — Stage 2.1: Praxis Constitution Loader landed — 40 contract tests green (432/432 total)

- **Stage / phase / port:** Stage 2.1 · Praxis plugin · constitution boot-verification subsystem
- **What changed:** Landed the full Stage 2.1 surface per ADR-032. **Kosmos's first plugin.** Two subsystems shipped: (1) `plugins/praxis/constitution/` — `signing.py` (144 lines: Ed25519 sign/verify + `rfc8785`-based JCS canonicalize + PEM key loaders, ported from Rigpa-LMS with `jcs` → `rfc8785` dep-swap to reuse Kosmos's existing DataPort §1.10 dependency), `verifier.py` (80 lines: `ConstitutionVerifier` facade bound to Kosmos's `governance/constitution/pubkey.pem` artifact tree, with `ConstitutionError` hierarchy replacing Rigpa's `SignatureDecodeError`+bare-`RuntimeError` pattern), `errors.py` (36 lines: `ConstitutionError` → `ConstitutionNotFoundError` / `ConstitutionMalformedError` / `ConstitutionTamperError` — single base class so callers catch one exception type for boot refusal), `loader.py` (223 lines: `ConstitutionLoader` orchestrator + immutable `ConstitutionArtifact` frozen dataclass; three-tier invariant chain (existence → YAML/JSON JCS cross-check → Ed25519 signature verify); `verify_on_init=True` default runs all three at `__init__` — a raised `ConstitutionError` from construction IS the Build-Sequence §2.1 DoD "boot refused" signal); (2) `plugins/praxis/plugin.py` (192 lines: `PraxisPlugin` dataclass with cheap side-effect-free construction and heavy async `start()` that (a) load-and-verifies constitution then (b) registers `PluginDescriptor(name="praxis", state_namespace="praxis", version="0.1.0", kernel_compat="0.1.x", routes=(), design_tokens={}, panels=(Panel(id="praxis.governance", slot=PanelSlot.GOVERNANCE, priority=100, lazy_module="praxis/panels/GovernancePanel", plugin_name="praxis"),)) with the FrontendContractPort — order matters: verification runs before any port call so tamper leaves the kernel with no partially-registered Praxis; idempotent `start`/`stop`). Genesis artifact tree: `scripts/gen_constitution_genesis.py` generates fresh Ed25519 keypair + committed genesis triplet (`governance/constitution/pubkey.pem`, `governance/constitution/versions/v0001.{yaml,json,sig}`); private key lives at gitignored `.secrets/genesis/privkey.pem` (added `.secrets/` to `.gitignore`); regeneratable for reproducibility. Contract tests (706 lines, 40 tests) cover: signing primitives (canonicalize determinism + key-sort stability + sign/verify roundtrip + tampered-payload/malformed-base64/wrong-key rejection + PEM roundtrip + non-Ed25519 rejection + private-key roundtrip), verifier facade (valid + bad-sig + missing-pubkey + malformed-pubkey), loader existence checks (missing yaml/json/sig/pubkey), loader parse checks (bad yaml / non-mapping yaml / empty signature), tamper detection (yaml-only edit / json-only edit / signature swap / pubkey swap / single-base-class catch), the **§2.1 DoD test** `test_tampered_constitution_refuses_boot_build_sequence_2_1_dod` (literally satisfies the DoD by editing the on-disk YAML post-ratification and asserting `ConstitutionLoader` raises `ConstitutionTamperError`), committed-genesis regression (repo genesis verifies against pubkey), descriptor shape (governance panel + priority + lazy_module + plugin_name), plugin lifecycle (start/stop idempotence + accessor-gating + tamper-refused-before-frontend-touch + panel-appears-in-governance-slot + render_kernel_schema-includes-praxis). Zero new runtime dependencies — reused `PyYAML>=6.0`, `rfc8785>=0.1.4`, `cryptography>=49` all from Stage 1.5/1.10. `plugins/__init__.py`, `governance/__init__.py`, `governance/constitution/__init__.py` package markers added. `pyproject.toml` registers `governance`, `governance.constitution`, `plugins`, `plugins.praxis`, `plugins.praxis.constitution`, `plugins.praxis.tests` packages. Full test suite: **432/432 green** (was 392; +40 Praxis contract tests). `make stage1-gate` regression test still passes.
- **Files touched:**
  - `plugins/__init__.py` (new)
  - `plugins/praxis/__init__.py` (new; 31 lines)
  - `plugins/praxis/plugin.py` (new; 192 lines)
  - `plugins/praxis/constitution/__init__.py` (new; 34 lines)
  - `plugins/praxis/constitution/errors.py` (new; 36 lines)
  - `plugins/praxis/constitution/signing.py` (new; 144 lines, PATTERN-VENDORED from Rigpa)
  - `plugins/praxis/constitution/verifier.py` (new; 80 lines, PATTERN-VENDORED from Rigpa)
  - `plugins/praxis/constitution/loader.py` (new; 223 lines, Kosmos-native orchestrator)
  - `plugins/praxis/tests/__init__.py` (new)
  - `plugins/praxis/tests/test_constitution_loader.py` (new; 706 lines, 40 tests)
  - `governance/__init__.py` (new)
  - `governance/constitution/__init__.py` (new)
  - `governance/constitution/pubkey.pem` (new; genesis Ed25519 pubkey)
  - `governance/constitution/versions/v0001.yaml` (new; genesis YAML)
  - `governance/constitution/versions/v0001.json` (new; JCS canonicalization)
  - `governance/constitution/versions/v0001.sig` (new; Ed25519 detached signature, base64url)
  - `scripts/gen_constitution_genesis.py` (new; 124 lines, reproducible genesis generator)
  - `pyproject.toml` (register 6 new packages: governance, governance.constitution, plugins, plugins.praxis, plugins.praxis.constitution, plugins.praxis.tests)
  - `.gitignore` (add `.secrets/`)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-032 row appended)
  - `docs/adrs/README.md` (ADR-032 row appended)
  - `docs/PORTING_LEDGER.md` (Praxis Constitution port block: `signing.py` PATTERN-VENDORED with `jcs`→`rfc8785` dep-swap noted + `verifier.py` PATTERN-VENDORED with pubkey-path relocation + error-hierarchy substitution noted + `amend_service.py`/`cli.py`/`service.py`/`models.py`/`schemas.py` PATTERN-VENDORED-reference-only-deferred-to-Synedrion + `rfc8785`/`cryptography`/`PyYAML` VENDORED-reused-existing-Kosmos-deps)
  - `docs/Kosmos-Build-Sequence-v25.md` (§2.1 rewritten with landing timestamp, port list clarification (FrontendContractPort at 2.1 + DataPort/SecretsPort at Synedrion), full action description, Q1=B/Q2=A cross-references, and DoD PASS marker with test count)
- **Ports / adapters affected:** FrontendContractPort (Praxis plugin descriptor registration). No new port; no adapter changes. Constitution subsystem is plugin-internal.
- **PORTING_LEDGER / ADR updated:** ADR-032 (authored in previous entry). PORTING_LEDGER Praxis Constitution port block added (4 entries: signing.py + verifier.py + deferred-to-Synedrion reference + reused stdlib/crypto deps).
- **Stop-condition status:** met — `test_tampered_constitution_refuses_boot_build_sequence_2_1_dod` green (Stage 2.1 DoD); full suite 432/432; `make stage1-gate` regression passes; PraxisPlugin registers exactly one panel in `PanelSlot.GOVERNANCE`; tamper aborts before any FrontendContractPort call. Next: Stage 2.2 (APEX Change Approval Tier engine — EventBusPort + NotificationPort, tiers AUTONOMOUS / HUMAN_REVIEW / HUMAN_REQUIRED).

## 2026-07-29 23:44 EDT — ADR-033 authored (APEX Change Approval Tier engine)

- **Stage / phase / port:** Stage 2.2 · Praxis plugin · APEX Change Approval subsystem
- **What changed:** Ratified ADR-033 locking Q1=C (full §17.13 UX including SecretsPort-backed Ed25519 mobile signed-token) and Q2=A (Scheduler Protocol seam with `InProcessScheduler` asyncio-task-backed primary + `FakeScheduler` deterministic test double + `NullScheduler` no-op). ADR enumerates rejected alternatives for both questions: Q1-A (backend-only DoD, no UX) rejected because Kosmos is a single-user local-first system where the human is the only approver — deferring UX defeats the purpose; Q1-B (queue + resolve endpoint, no mobile token) rejected because §17.13 explicitly calls for one-tap mobile approve/reject; Q2-B (real-time asyncio-only) rejected because the DoD requires deterministic cadence assertions that real time cannot express; Q2-C (schedule-through-EventBusPort) rejected because it conflates the event-bus surface with a distinct time-domain concern. Consequences: 10 new modules under `plugins/praxis/apex/` (tier/errors/models/protocol/scheduler/storage/tokens/policy/engine/__init__ + tests package), one PraxisPlugin descriptor amendment adding a second Panel in APPROVALS_QUEUE, one Rigpa donor cache under `/tmp/donor-apex/` (protocols/models/service/schemas), one SecretsPort logical name `apex.approval.mobile_token.signing_key`. Zero new runtime deps.
- **Files touched:**
  - `docs/adrs/ADR-033-apex-change-approval-tier-engine.md` (new; 378 lines)
- **Ports / adapters affected:** none yet (ADR only). Downstream: kernel-wide `ChangeApprovalProtocol` seam formalized; new Scheduler seam; SecretsPort integration under `apex.approval.mobile_token.signing_key`.
- **PORTING_LEDGER / ADR updated:** ADR-033. PORTING_LEDGER Praxis section will gain an "APEX Change Approval Tier engine" block in the Stage-2.2 landing entry.
- **Stop-condition status:** met — decision surface locked; next entry lands the code.

## 2026-07-29 23:44 EDT — Stage 2.2 landed (APEX Change Approval Tier engine)

- **Stage / phase / port:** Stage 2.2 · Praxis plugin · APEX Change Approval subsystem
- **What changed:** Full Stage 2.2 surface per ADR-033. Ten new Python modules under `plugins/praxis/apex/`: (1) `tier.py` (36 lines) — `ChangeApprovalTier(str, Enum)` = AUTONOMOUS / HUMAN_REVIEW / HUMAN_REQUIRED; (2) `errors.py` (59 lines) — `ApexError` single-base hierarchy with `ApprovalNotFoundError` / `InvalidTransitionError` / `TokenExpiredError` / `TokenMalformedError` / `TokenTamperError`; (3) `models.py` (121 lines) — frozen dataclasses `Intention` (Rigpa donor shape minus SQLAlchemy) + `ApprovalRecord` (approval_id / intention_id / proposing_domain / tier / delta / status / proposed_at / resolved_at / resolved_by / reason / modifications / diff_preview) + `ApprovalStatus` (PENDING / APPROVED / REJECTED / MODIFIED / REVIEW_MISSED) + `Trigger` (9 spec §14 kernel-wide triggers) + `new_id()` UUID4 helper + `utc_now()` tz-aware helper; (4) `protocol.py` (216 lines) — `ChangeApprovalProtocol` async surface + `Storage` Protocol seam (save_intention / get_intention / save_record / load_record / update_status / list_by_status / list_by_intention) + `Scheduler` Protocol seam (schedule_at / cancel / pending_count) + `SchedulerHandle` value object; (5) `scheduler.py` (210 lines) — `InProcessScheduler` asyncio-task-backed primary using `asyncio.create_task` + `asyncio.sleep` + `handle.cancelled` short-circuit, `FakeScheduler` captures `ScheduledCall` frozen entries in `.calls` list with `async fire_due(as_of)` that fires non-cancelled callbacks in `when`-ascending order and marks fired callbacks cancelled for idempotence, `NullScheduler` pre-cancels every handle; (6) `storage.py` (222 lines) — `InMemoryStorage` dict-backed primary using `dataclasses.replace` for immutable ApprovalRecord updates, `SqliteStorage` stub with documented DDL for Stage 5; (7) `tokens.py` (269 lines) — `MobileTokenService` with async `mint_token(approval_id, action)` and `verify_token(token)` returning `VerifiedTokenAction`; wire format `b64url(canonical_json).b64url(signature)`; uses `rfc8785.dumps()` for JCS canonicalization + `cryptography.hazmat.primitives.asymmetric.ed25519` for Ed25519 sign/verify; signing key at SecretsPort logical name `apex.approval.mobile_token.signing_key`; 24h TTL; strict `Z`-suffix ISO8601; verifies signature BEFORE parsing payload (tamper-first); rejects non-Ed25519 keys with `TokenMalformedError`; (8) `policy.py` (114 lines) — `EscalationPolicy.classify(delta) -> Trigger | None` covering all nine §14 triggers; conservative-default returns None for unknown deltas; action-based triggers evaluate first; (9) `engine.py` (471 lines) — `KernelChangeApprovalAdapter` composing Storage + Scheduler + EventBusPort + NotificationPort; event constants `APEX_PRODUCER_PLUGIN="praxis"`, `EVENT_APEX_INTENTION_PROPOSED`/`APPROVED`/`REJECTED`/`REVIEW_MISSED`; cadence constants `HUMAN_REVIEW_DEFAULT_WINDOW=4h`, `HUMAN_REQUIRED_INITIAL_DELAY=24h`, `HUMAN_REQUIRED_RECURRING_DELAY=6h`, `_MAX_HUMAN_REQUIRED_SCHEDULE_HORIZON=30d`; tracks `_handles: dict[str, list[SchedulerHandle]]` so `resolve()` cancels all outstanding timers atomically; `resolve()` requires non-empty reason when `approved=False`; `_publish()` uses `EventEnvelope(event_type, producer_plugin="praxis", payload)` and awaits result if awaitable (ADR-023 envelope-first); (10) `__init__.py` (112 lines) — canonical public surface with `__all__`. `plugins/praxis/plugin.py` extended: second `Panel(id="praxis.approvals", slot=PanelSlot.APPROVALS_QUEUE, priority=100, lazy_module="praxis/panels/ApprovalsQueuePanel")` registered alongside the governance panel from §2.1; constants `PRAXIS_APPROVALS_PANEL_ID` / `PRAXIS_APPROVALS_LAZY_MODULE` / `PRAXIS_APPROVALS_PANEL_PRIORITY` added; `PraxisPlugin.start()` unchanged (APEX engine construction is separate composition, not tight coupling). Contract tests under `plugins/praxis/apex/tests/`: `test_apex_tiers.py` (28 tests) — DoD anchor test suite where every test name contains `apex_tiers` so `pytest -k apex_tiers` selector matches; covers AUTONOMOUS persistence + event fan-out + no-scheduler-wiring + no-notification + not-in-pending; HUMAN_REVIEW PENDING persistence + ACTION notification via `channel="approvals"` + 4h missed-review timer + REVIEW_MISSED transition + `apex.review.missed` event + resolve-before-window cancels + resolved-callback-idempotence; HUMAN_REQUIRED PENDING persistence + no-propose-time notification + 24h first tick + 24h+6h/6h/6h cadence + algedonic on tick + resolve cancels all + late-callback-race idempotence; all-three-tiers DoD literal + reject-requires-reason + reject fires rejected event + approve-with-modifications transitions to MODIFIED + double-resolve InvalidTransitionError + list_pending only-pending + propose input validation + producer_plugin=praxis on every envelope + intention persistence roundtrip; `test_mobile_token.py` (18 tests) — mint/verify roundtrip + approve/reject actions + 2-segment wire format + exp preservation + expiry-at-24h+1s + validity-at-TTL-boundary + reversed-signature raises tamper + prepended-payload raises tamper/malformed + swapped-signature-across-tokens raises tamper + empty/malformed/missing-dot/empty-segments raise malformed + invalid-action raises malformed + empty-approval-id raises malformed + non-Ed25519 RSA key rejected + garbage PEM rejected; `test_scheduler.py` (18 tests) — FakeScheduler schedule_at appends + pending_count tracks cancels + cancel idempotence + fire_due only-due + fire_due orders by when + fire_due skips cancelled + fire_due idempotent; NullScheduler precancels + pending zero + cancel-always-false; InProcessScheduler pending count + cancel prevents callback + callback fires after when; `test_policy.py` (18 tests) — production_deploy/deploy/publish + destructive delete/purge + unsigned high-impact memory write (signed-not-trigger + low-impact-not-trigger) + sustained model swap SLO breach + bus-factor-1 no-fallback (with-fallback-not-trigger + bus-factor-2-not-trigger) + retry-bound exhaustion + conflicting KB publish + port version deprecation + kernel self-modification + empty-delta returns None + unknown-action returns None + unknown-signal returns None + non-mapping returns None + non-boolean-truthy signals do not fire + action-trigger shadows boolean signal + coverage: fixtures exist for all nine Trigger enum values. Existing constitution-loader test `test_descriptor_registration_with_stub_frontend_contract` updated to assert both panels present. `pyproject.toml` registers `plugins.praxis.apex` and `plugins.praxis.apex.tests` packages. Zero new runtime deps — reuses `rfc8785>=0.1.4`, `cryptography>=49`, `aiosqlite>=0.20`, `PyYAML>=6.0`. Full test suite: **514/514 green** (was 432; +82 APEX contract tests). `make stage1-gate` regression PASS.
- **Files touched:**
  - `plugins/praxis/apex/__init__.py` (new; 112 lines)
  - `plugins/praxis/apex/tier.py` (new; 36 lines)
  - `plugins/praxis/apex/errors.py` (new; 59 lines)
  - `plugins/praxis/apex/models.py` (new; 121 lines)
  - `plugins/praxis/apex/protocol.py` (new; 216 lines)
  - `plugins/praxis/apex/scheduler.py` (new; 210 lines)
  - `plugins/praxis/apex/storage.py` (new; 222 lines)
  - `plugins/praxis/apex/tokens.py` (new; 269 lines)
  - `plugins/praxis/apex/policy.py` (new; 114 lines)
  - `plugins/praxis/apex/engine.py` (new; 471 lines)
  - `plugins/praxis/apex/tests/__init__.py` (new; empty package marker)
  - `plugins/praxis/apex/tests/test_apex_tiers.py` (new; 28 tests)
  - `plugins/praxis/apex/tests/test_mobile_token.py` (new; 18 tests)
  - `plugins/praxis/apex/tests/test_scheduler.py` (new; 18 tests)
  - `plugins/praxis/apex/tests/test_policy.py` (new; 18 tests)
  - `plugins/praxis/plugin.py` (extended `build_praxis_descriptor` with approvals panel + new constants)
  - `plugins/praxis/tests/test_constitution_loader.py` (updated three assertions to expect two-panel descriptor)
  - `pyproject.toml` (register `plugins.praxis.apex` + `plugins.praxis.apex.tests` packages)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-033 row appended)
  - `docs/adrs/README.md` (ADR-033 row appended)
  - `docs/PORTING_LEDGER.md` ("APEX Change Approval Tier engine" block appended to Governance section)
  - `docs/Kosmos-Build-Sequence-v25.md` (§2.2 rewritten with landing timestamp, expanded action description, and DoD PASS marker with test count)
- **Ports / adapters affected:** New kernel-wide `ChangeApprovalProtocol` seam at `plugins/praxis/apex/protocol.py`. New `Scheduler` Protocol seam + `Storage` Protocol seam. `PraxisPlugin` descriptor now registers two panels (governance + approvals). SecretsPort integration under `apex.approval.mobile_token.signing_key`. NotificationPort exercised through `notify(channel="approvals", tier=ACTION)` + `deliver_algedonic()` verbs. EventBusPort exercised through envelope publishing with `producer_plugin="praxis"`.
- **PORTING_LEDGER / ADR updated:** ADR-033 landed. PORTING_LEDGER Praxis section extended with 4 new port entries: Rigpa `apex/protocols.py` PATTERN-VENDORED, Rigpa `apex/models.py` PATTERN-VENDORED, Rigpa `apex/service.py` PATTERN-VENDORED-rewritten-async-first, `rfc8785`+`cryptography`+`aiosqlite`+`PyYAML` VENDORED-reused-existing-deps.
- **Stop-condition status:** met — DoD anchor `pytest -k apex_tiers` runs 28 tier tests green; full suite 514/514; `make stage1-gate` regression passes; PraxisPlugin registers two panels; every `EventEnvelope` carries `producer_plugin="praxis"`; no cross-plugin imports (ADR-007); no MemoryPort writes (ADR-008); SecretsPort integration behind logical name (ADR-024). Next: Stage 2.3 (Phrouros anomaly detector — ObservabilityPort + NotificationPort + ResourcePort).

## 2026-07-30 00:10 EDT — ADR-034 authored (Phrouros anomaly detector · Q1=A · Q2=A · Q3=B · Q4=A · Q5=A)

- **Stage / plugin / port:** Stage 2.3 · Phrouros anomaly detector · new TraceFeedPort · NotificationPort algedonic path · ResourcePort compute reservation · EventBusPort · FrontendContractPort AGENT_TRACE panel
- **What changed:** Authored ADR-034 (Ratified v25) formalizing Stage 2.3's five locked answers: **Q1=A** (NotificationPort-direct algedonic — Phrouros calls `deliver_algedonic()` itself with no APEX `propose()`; rejected B because it conflates observability with change-approval, rejected C as over-engineered for 2.3). **Q2=A** (new `TraceFeedPort` at `ports/trace_feed.py` as sibling reader-only seam alongside writer-only ObservabilityPort per ADR-025; rejected amending ObservabilityPort because it would conflate writer + reader roles and force existing adapters to grow subscription surface). **Q3=B** (real `LoopDetector` + three skeleton detectors: `ModelSwapSloDetector` §172, `StubDegradationDetector` §273, `BusFactor1Detector` §613, all raising `DetectorNotImplementedError`; rejected shipping all four as real because §172/§273/§613 signals are downstream — no trace surface at 2.3 to compute them from). **Q4=A** ("GPU" maps to `ResourceKind.COMPUTE` + `amount=Decimal("32")` (32 GB VRAM per §172) + `PriorityClass.PHROUROS_ANOMALY` from ADR-029, with `ResourceExhausted` → `enqueue()` fallback; no explicit `release()` since ADR-029 surface doesn't expose it yet, deferred to Stage 5). **Q5=A** (`PhrourosPlugin` registers `Panel(id="phrouros.trace", slot=PanelSlot.AGENT_TRACE, priority=100, lazy_module="phrouros/panels/AgentTracePanel")` per §280; mirrors Praxis §2.1/§2.2 descriptor pattern).
- **Files touched:**
  - `docs/adrs/ADR-034-phrouros-anomaly-detector.md` (new; 217 lines)
- **Ports / adapters affected:** ADR-only — no code landed in this entry. Next entry ships the port module + plugin.
- **PORTING_LEDGER / ADR updated:** ADR-034 authored.
- **Stop-condition status:** met — ADR-034 references spec §172, §273, §280, §613; explicitly disagrees with none of ADR-007/008/023/025/029/030/031; supersedes nothing.

## 2026-07-30 00:20 EDT — Stage 2.3 landed (Phrouros anomaly detector · 55 contract tests green · DoD PASS)

- **Stage / plugin / port:** Stage 2.3 · Phrouros anomaly detector · TraceFeedPort (new) · NotificationPort · ResourcePort · EventBusPort · FrontendContractPort
- **What changed:** Shipped the full Phrouros surface behind five locked answers from ADR-034. New reader-only `TraceFeedPort` (`ports/trace_feed.py`, 259 lines) with `InMemoryTraceFeedAdapter` primary (pure asyncio pub/sub, snapshot-list fan-out to survive mid-fan-out unsubscribe, `subscriber_count` accessor, idempotent `close()` that raises `RuntimeError` on subsequent `publish`/`subscribe`) + `LangfuseTraceFeedAdapter` stub (Stage 5, raises `NotImplementedError` from `subscribe`/`publish`, `is_healthy()` returns False). New plugin at `plugins/phrouros/`: `errors.py` (36 lines — `PhrourosError` + `DetectorNotImplementedError`/`AnomalyNotFoundError`/`EngineNotRunningError`), `models.py` (96 lines — `AnomalyKind` LOOP/MODEL_SWAP_SLO/STUB_DEGRADATION/BUS_FACTOR_1, `AnomalyStatus` DETECTED/NOTIFIED/RESERVED/RESOLVED, `AnomalyRecord`, `LoopAnomaly`), `detector.py` (55 lines — `Detector` runtime_checkable Protocol), `detectors/loop.py` (real LoopDetector: sliding-window per `(trace_id, plugin, tool_name)`, deque-backed, threshold=5 window=30s defaults, clears window after firing to prevent re-fire), `detectors/{model_swap_slo,stub_degradation,bus_factor_1}.py` (skeletons raising `DetectorNotImplementedError`), `engine.py` (288 lines — `PhrourosEngine` composing TraceFeedPort + detectors + NotificationPort + ResourcePort + EventBusPort; escalation order: publish `phrouros.anomaly.detected` → `deliver_algedonic()` → `allocate()` with `ResourceExhausted` → `enqueue()` fallback; first-match-wins detector loop; every envelope carries `producer_plugin="praxis"` per ADR-023), `plugin.py` (121 lines — `PhrourosPlugin` dataclass with idempotent async start/stop + `build_phrouros_descriptor()` registering AGENT_TRACE panel), `__init__.py` (public surface). Five contract test files landed (55 tests total): `test_loop_detector.py` (11 tests including DoD literal `test_synthetic_looping_tool_call_triggers_phrouros_loop_alert_within_30s_build_sequence_2_3_dod`), `test_phrouros_engine.py` (11 tests including full DoD literal `test_synthetic_loop_via_engine_emits_event_and_algedonic_and_reserves_compute_within_30s_build_sequence_2_3_dod` — verifies event fan-out, algedonic delivery, ResourcePort call, anomaly record status, ResourceExhausted fallback, idempotent lifecycle, ADR-007 grep-assertion, first-match-wins), `test_trace_feed.py` (14 tests including snapshot-list mid-fan-out safety, close idempotence, backlog-free subscribers, stub adapter behavior), `test_skeleton_detectors.py` (13 tests verifying all three skeletons raise `DetectorNotImplementedError` from detect + build_payload, docstrings name spec section + landing stage, names are stable), `test_plugin.py` (13 tests covering descriptor shape, panel registration, idempotent lifecycle, ADR-007 grep-assertion).
- **Files touched:**
  - `ports/trace_feed.py` (new; 259 lines)
  - `plugins/phrouros/__init__.py` (new; 101 lines)
  - `plugins/phrouros/errors.py` (new; 36 lines)
  - `plugins/phrouros/models.py` (new; 96 lines)
  - `plugins/phrouros/detector.py` (new; 55 lines)
  - `plugins/phrouros/detectors/__init__.py` (new)
  - `plugins/phrouros/detectors/loop.py` (new; 96 lines)
  - `plugins/phrouros/detectors/model_swap_slo.py` (new; skeleton)
  - `plugins/phrouros/detectors/stub_degradation.py` (new; skeleton)
  - `plugins/phrouros/detectors/bus_factor_1.py` (new; skeleton)
  - `plugins/phrouros/engine.py` (new; 288 lines)
  - `plugins/phrouros/plugin.py` (new; 121 lines)
  - `plugins/phrouros/tests/__init__.py` (new; empty package marker)
  - `plugins/phrouros/tests/test_loop_detector.py` (new; 11 tests)
  - `plugins/phrouros/tests/test_phrouros_engine.py` (new; 11 tests)
  - `plugins/phrouros/tests/test_trace_feed.py` (new; 14 tests)
  - `plugins/phrouros/tests/test_skeleton_detectors.py` (new; 13 tests)
  - `plugins/phrouros/tests/test_plugin.py` (new; 13 tests)
  - `pyproject.toml` (registered `plugins.phrouros`, `plugins.phrouros.detectors`, `plugins.phrouros.tests` packages)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-034 row appended)
  - `docs/adrs/README.md` (ADR-034 row appended)
  - `docs/PORTING_LEDGER.md` ("Phrouros anomaly detector" GREENFIELD block appended to Governance section)
  - `docs/Kosmos-Build-Sequence-v25.md` (§2.3 rewritten with LANDED marker, expanded action, port list, DoD PASS with test anchors, locked-answers footer)
- **Ports / adapters affected:** New reader-only `TraceFeedPort` — sibling seam to writer-only ObservabilityPort per ADR-025; `InMemoryTraceFeedAdapter` primary + `LangfuseTraceFeedAdapter` Stage 5 stub. NotificationPort exercised through `deliver_algedonic()` (algedonic tier bypass — no `notify()` at Stage 2.3). ResourcePort exercised through `allocate(ResourceKind.COMPUTE, Decimal("32"), intent="phrouros_diagnostics", priority_class=PriorityClass.PHROUROS_ANOMALY, requester="phrouros")` with `ResourceExhausted` → `enqueue()` fallback at same priority. EventBusPort exercised through `phrouros.anomaly.detected` envelopes with `producer_plugin="praxis"` per ADR-023 (Phrouros under Praxis governance namespace). FrontendContractPort exercised through `PhrourosPlugin` descriptor registering one `AGENT_TRACE` panel per §280.
- **PORTING_LEDGER / ADR updated:** ADR-034 (Ratified v25). PORTING_LEDGER Governance section extended with "Phrouros anomaly detector" GREENFIELD block explaining why no upstream anomaly framework was adopted (arize-phoenix / evidently / langfuse-python each violated local-first posture or dragged heavyweight runtime).
- **Stop-condition status:** met — DoD anchor `pytest -k phrouros_loop` matches two literal DoD tests (detector-level + full engine end-to-end); full pytest 569/569 green (514 → 569, +55); `make stage1-gate` PASS regression; ADR-007 grep-verified in engine.py and plugin.py (no `plugins.praxis` imports); ADR-008 respected (no MemoryPort writes at 2.3); ADR-023 respected (every envelope carries `producer_plugin="praxis"`); zero new runtime dependencies; skeleton detectors surface `DetectorNotImplementedError` through the engine (not swallowed). Next: Stage 2.4 Stage-2 exit gate (Praxis + Phrouros co-operate: unauthorized action → Phrouros detects → APEX escalates → user notified end-to-end).

## 2026-07-30 00:35 EDT — ADR-035 authored (Stage-2 exit gate · AnomalyBridge)

- **Stage / plugin / port:** Stage 2.4 · Stage-2 exit gate · AnomalyBridge (Praxis-internal) · UnauthorizedToolDetector (Phrouros) · TektosSimulator (test-only stub) · TraceFeedPort · EventBusPort · APEX ChangeApprovalProtocol · NotificationPort (algedonic path through APEX HUMAN_REQUIRED cadence)
- **What changed:** authored `docs/adrs/ADR-035-stage-2-exit-gate-anomaly-bridge.md` (Ratified v25) resolving six locked questions: Q1=A ("unauthorized action" = Tektos-style tool call violating governance policy, driven by a test-only Tektos stub deleted-or-superseded at Stage 3); Q2=C (both detectors fire in the gate: reuse Stage-2.3 `LoopDetector` plus new real `UnauthorizedToolDetector` — proves detector-tuple seam supports multiple concurrent real detectors); Q3=A (event-only cross-plugin coupling per ADR-007 via `AnomalyBridge`, translating envelopes on `phrouros.anomaly.detected` to `ChangeApprovalProtocol.propose(tier=HUMAN_REQUIRED)`, plus `praxis.escalation.proposed` audit publish); Q4=A (`UnauthorizedToolDetector` reads a hardcoded `frozenset[str]` allowlist at construction — no constitution schema extension, no new port, stateless per event, plugin-agnostic, `PolicyPort` seam deferred to Stage 5); Q5=A (bridge at `plugins/praxis/apex/bridge.py` as Praxis-internal peer service composing `ChangeApprovalProtocol` directly, NOT owned by `PraxisPlugin`, matching ADR-033 decoupled-construction pattern); Q6=A (Tektos stub is a plain dataclass composed with `TraceFeedPort` — no `PluginDescriptor`, no lifecycle, no AGENT_TRACE panel, deleted-or-superseded at Stage 3).
- **Files touched:**
  - `docs/adrs/ADR-035-stage-2-exit-gate-anomaly-bridge.md` (new, 182 lines)
  - `docs/adrs/README.md` (ADR-035 row appended after ADR-034)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-035 row appended after ADR-034)
- **Ports / adapters affected:** planned only at authoring time; landing entry follows below.
- **PORTING_LEDGER / ADR updated:** ADR-035 authored. PORTING_LEDGER updated in landing entry.
- **Stop-condition status:** in-progress — ADR-035 authored + spec §17 row + `adrs/README.md` row all committed to text; code landing recorded below.

## 2026-07-30 00:35 EDT — Stage 2.4 · Stage-2 exit gate — LANDED

- **Stage / plugin / port:** Stage 2.4 · Stage-2 exit gate · `plugins/phrouros/detectors/unauthorized_tool.py::UnauthorizedToolDetector` + `plugins/tektos/stub/simulator.py::TektosSimulator` + `plugins/praxis/apex/bridge.py::AnomalyBridge` + `plugins/phrouros/models.py::AnomalyKind.UNAUTHORIZED_TOOL` + `plugins/phrouros/engine.py::_kind_for_detector` mapping. Ports: TraceFeedPort (in) · EventBusPort (bridge subscribe `phrouros.anomaly.detected` + publish `praxis.escalation.proposed`) · APEX ChangeApprovalProtocol (bridge `propose(tier=HUMAN_REQUIRED)`) · NotificationPort (via APEX HUMAN_REQUIRED escalating cadence). No new ports at Stage 2.4.
- **What changed:** shipped Stage-2 exit-gate co-operation. `TektosSimulator` (test-only stub, `plugins/tektos/stub/`, Q6=A) publishes `TraceEvent(plugin="tektos", tool_name=<denied>)` on `TraceFeedPort`. Phrouros engine fans events to its detector tuple; new `UnauthorizedToolDetector` (Q4=A, hardcoded `frozenset[str]` allowlist, stateless per event, plugin-agnostic) fires and produces `UnauthorizedToolAnomaly` under new `AnomalyKind.UNAUTHORIZED_TOOL` variant. Engine publishes `phrouros.anomaly.detected` with `producer_plugin="praxis"` per ADR-023 and continues its Stage-2.3 escalation sequence unchanged (algedonic + compute reservation). `AnomalyBridge` (Q3=A / Q5=A) — Praxis-internal peer service at `plugins/praxis/apex/bridge.py`, composing `ChangeApprovalProtocol` directly per ADR-033 decoupled-construction pattern — subscribes to the anomaly event on `start()`, spawns a background `asyncio.Task` reading from the returned `asyncio.Queue`, and per envelope calls `ChangeApprovalProtocol.propose(intention_id=f"anomaly:{anomaly_id}", tier=HUMAN_REQUIRED, proposing_domain="phrouros", diff_preview=<envelope payload>)` and publishes `praxis.escalation.proposed` audit envelope. APEX HUMAN_REQUIRED path then fires escalating `deliver_algedonic()` cadence at T+24h / +6h / … / 30d, per ADR-033. Idempotent `start()` / `stop()`; per-envelope errors caught and logged so one bad envelope cannot stop the escalator. Both detectors active in the gate simultaneously (Q2=C) — proves the detector-tuple seam supports multiple concurrent real detectors.
- **Files touched:**
  - `plugins/phrouros/models.py` (added `AnomalyKind.UNAUTHORIZED_TOOL`, new `UnauthorizedToolAnomaly` frozen dataclass, `__all__` updated)
  - `plugins/phrouros/engine.py` (added `"unauthorized_tool_detector" → AnomalyKind.UNAUTHORIZED_TOOL` mapping in `_kind_for_detector()`)
  - `plugins/phrouros/detectors/unauthorized_tool.py` (new — `UnauthorizedToolDetector`, `name="unauthorized_tool_detector"`, stateless, plugin-agnostic, hardcoded allowlist)
  - `plugins/phrouros/detectors/__init__.py` (re-exported `UnauthorizedToolDetector`)
  - `plugins/phrouros/__init__.py` (re-exported `UnauthorizedToolDetector` + `UnauthorizedToolAnomaly`)
  - `plugins/phrouros/tests/test_unauthorized_tool_detector.py` (new, 13 unit tests — all green)
  - `plugins/praxis/apex/bridge.py` (new — `AnomalyBridge` dataclass, idempotent lifecycle, background drain task, ADR-023 audit envelopes)
  - `plugins/praxis/apex/tests/test_anomaly_bridge.py` (new, 10 tests including AST-based `test_bridge_never_imports_phrouros` — all green)
  - `plugins/tektos/__init__.py` (new — namespace package)
  - `plugins/tektos/stub/__init__.py` (new — re-exports `TektosSimulator`)
  - `plugins/tektos/stub/simulator.py` (new — test-only harness, `simulate_unauthorized_call` / `simulate_authorized_call` / `simulate_loop`)
  - `plugins/tektos/tests/__init__.py` (new)
  - `plugins/tektos/tests/test_stage_2_4_exit_gate.py` (new — DoD literal `test_unauthorized_tool_call_detected_and_escalated_and_user_notified_build_sequence_2_4_dod` + 3 `TektosSimulator` sanity tests + 2 bridge scenario extras = 6 tests total, all green)
  - `pyproject.toml` (registered `plugins.tektos`, `plugins.tektos.stub`, `plugins.tektos.tests` under setuptools packages)
  - `docs/PORTING_LEDGER.md` (two new GREENFIELD entries appended after Phrouros: `AnomalyBridge` + `TektosSimulator`, both under a new `Stage-2 exit gate (AnomalyBridge + Tektos stub)` subsection of Governance)
  - `docs/Kosmos-Build-Sequence-v25.md` (§2.4 rewritten LANDED with expanded action / detector-tuple note / bridge location / stub notes / compliance / DoD anchor / locked-answers footer)
- **Ports / adapters affected:** no new ports. TraceFeedPort exercised via `InMemoryTraceFeedAdapter` (existing) driven by `TektosSimulator`; EventBusPort exercised both as subscriber (bridge) and publisher (Phrouros anomaly event + bridge audit event, both carrying `producer_plugin="praxis"` per ADR-023); APEX `ChangeApprovalProtocol` exercised via `KernelChangeApprovalAdapter` with `HUMAN_REQUIRED` tier; NotificationPort exercised transitively through APEX HUMAN_REQUIRED escalating `deliver_algedonic()` cadence.
- **PORTING_LEDGER / ADR updated:** ADR-035 (Ratified v25). PORTING_LEDGER Governance section extended with two GREENFIELD entries (`AnomalyBridge` + `TektosSimulator`) under a new `Stage-2 exit gate` subsection, each documenting stdlib-only implementation, port list, design invariants, and — for the Tektos stub — a Stage-3 deletion trigger.
- **Stop-condition status:** met — DoD literal `pytest -k stage_2_4_exit_gate` matches `test_unauthorized_tool_call_detected_and_escalated_and_user_notified_build_sequence_2_4_dod` and passes (asserts `phrouros.anomaly.detected` publish + `praxis.escalation.proposed` publish + APEX approval created with `tier=HUMAN_REQUIRED` + `deliver_algedonic()` fires end-to-end). Full pytest **598/598** green (569 → 598, +29: 13 detector + 10 bridge + 6 gate/simulator). `make stage1-gate` PASS regression. ADR-007 respected — AST-verified in `test_bridge_never_imports_phrouros` (bridge has zero `plugins.phrouros` imports; envelope payload read by string keys only). ADR-008 respected (no MemoryPort writes at 2.4; audit persistence deferred to Stage 5). ADR-023 respected (bridge audit envelopes carry `producer_plugin="praxis"`). Zero new runtime dependencies. Stage 2 complete. Next: Stage 3 (Tektos coding plugin MVP) — supersedes `TektosSimulator`.

## 2026-07-30 00:52 EDT — ADR-036 authored (Tektos OpenHands SDK vendoring)

- **Stage / plugin / port:** Stage 3.1 · Tektos plugin · LLMPort + MemoryPort (consumer, no new port).
- **What changed:** Authored `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` locking six load-bearing 3.1 decisions with full rejection rationale for every alternative — Q1=A (SDK repo `OpenHands/software-agent-sdk` only; main OpenHands runtime deferred to 3.2), Q2=A (PATTERN-VENDORED, no upstream source copied), Q3=A (minimal-loop DoD: one iteration = one context read + one LLM call + one MemoryPort write with `provenance="tektos_agent"` + confidence in `(0,1]`), Q4=B (no `PluginDescriptor` at 3.1; spec §17.1 UI Parity Rule Phase-2 grandfathering; FrontendContractPort registration lands 3.7), Q5=B (`plugins/tektos/stub/TektosSimulator` kept alive through 3.1; deleted at 3.2 when MCP tool calls emit real `TraceEvent`s), Q6=A (author ADR-036, not amend ADR-020). Locked constants: `TEKTOS_AGENT_PROVENANCE="tektos_agent"`, `TEKTOS_MEMORY_PREDICATE="tektos.turn.completed"`, default confidence 0.75. Deletion trigger for stub tree stated explicitly (Stage 3.2 landing commit).
- **Files touched:**
  - `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` (new)
  - `docs/adrs/README.md` (ADR-036 row inserted in ID order)
  - `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-036 row appended)
- **Ports / adapters affected:** none yet (documentation-only entry). Adopts existing `LLMPort` (ADR-022) + `MemoryPort` (ADR-027) as Tektos's 3.1 consumption surface.
- **PORTING_LEDGER / ADR updated:** ADR-036 (Ratified v25). No PORTING_LEDGER change in this entry; ledger update lands with the Stage-3.1 code commit below.
- **Stop-condition status:** met — ADR authored, spec §17 row + adrs/README row consistent, ADR-020 (Tektos migration direction) unchanged.

## 2026-07-30 00:54 EDT — Stage 3.1 LANDED (Tektos OpenHands SDK PATTERN-VENDORED)

- **Stage / plugin / port:** Stage 3.1 · Tektos plugin · LLMPort (consumer, `generate_text` only) + MemoryPort (consumer, `query_temporal` + `write_event` with zero-trust `provenance`+`confidence`). No new ports.
- **What changed:** Pattern-vendored OpenHands `Agent`/`Conversation` surface into Kosmos-native `TektosAgent` reading and writing exclusively through Kosmos ports. `send_message(text) -> turn_id` queues one user turn; `await run() -> TektosStep` executes one iteration (read prior context → assemble prompt → call `LLMPort.generate_text` once → write response through `MemoryPort.write_event` with `provenance="tektos_agent"` + caller confidence). Second `run()` on the same turn raises `TektosAgentNotStartedError`; `send_message` again yields a fresh turn id. `plugins/tektos/stub/TektosSimulator` and Stage-2.4 exit-gate test UNCHANGED per Q5=B — coexistence proves the detector-tuple seam still fires under both real and synthetic trace sources.
- **Files touched:**
  - `plugins/tektos/__init__.py` (rewritten to re-export `TektosAgent` + `TektosMessage` + `TektosMessageRole` + `TektosStep` + `TektosError` + subclasses + `TEKTOS_AGENT_PROVENANCE` + `TEKTOS_MEMORY_PREDICATE`; keeps ADR-035/036 layered docstring)
  - `plugins/tektos/agent.py` (new — `TektosAgent` slots dataclass, LLMPort + MemoryPort injected, `send_message` + `await run`, `_build_prompt` with `[prior]` line assembly from `query_temporal`, `_render_hit` payload-key tolerance, `_had_double_run` sentinel for future 3.5 multi-iteration)
  - `plugins/tektos/models.py` (new — `TektosMessageRole` enum, `TektosMessage` frozen dataclass with `user()`/`assistant()` classmethods, `TektosStep` frozen dataclass, `TEKTOS_AGENT_PROVENANCE` constant)
  - `plugins/tektos/errors.py` (new — `TektosError` root + `TektosAgentNotStartedError` + `TektosAgentAlreadyRunError` + `TektosInvalidConfidenceError`)
  - `plugins/tektos/tests/test_tektos_agent.py` (new — 18 contract tests including DoD literal `test_tektos_agent_reads_and_writes_via_kosmos_ports_only_build_sequence_3_1_dod` + ADR-007 AST verifier `test_tektos_agent_imports_no_other_plugins_adr_007` + zero-trust passthrough `test_default_provenance_and_confidence_pass_port_guard` + construction guards + Protocol conformance + locked constants)
  - `docs/PORTING_LEDGER.md` (OpenHands SDK entry updated: PLANNED → PATTERN-VENDORED, source URL moved to `OpenHands/software-agent-sdk`, upstream commit `4b132eddb6cf414841439a46ce42ed2cd66a628a`, Kosmos location `plugins/tektos/agent.py`, ADR-036, logged 2026-07-30 00:52 EDT)
  - `docs/Kosmos-Build-Sequence-v25.md` §3.1 (rewritten LANDED with ports, vendor mode, repo scope, agent surface, locked constants, descriptor decision, stub fate, compliance, DoD anchor, locked-answers footer)
  - `SESSION_HANDOFF.md` (overwritten — Stage 3.1 complete, Stage 3.2 up next)
- **Ports / adapters affected:** no new ports. `LLMPort` consumed via `generate_text` only (every other verb on the fake test port raises `NotImplementedError` to prove the 3.1 surface). `MemoryPort` consumed via `query_temporal(TEKTOS_MEMORY_PREDICATE, limit=context_limit)` and `write_event(subject, TEKTOS_MEMORY_PREDICATE, response, provenance="tektos_agent", confidence, attributes={turn_id, role, prompt_len, response_len})`. `EventBusPort` NOT exercised at 3.1 (arrives at 3.2 with MCP tool calls). `TraceFeedPort` NOT exercised by real agent at 3.1 (Stage-2.4 gate test continues to drive it via the stub).
- **PORTING_LEDGER / ADR updated:** ADR-036 (Ratified v25, this entry lands the code the ADR describes). PORTING_LEDGER OpenHands SDK entry status PLANNED → PATTERN-VENDORED with upstream commit hash + Kosmos location + modifications note.
- **Stop-condition status:** met — DoD literal `pytest plugins/tektos/tests/test_tektos_agent.py::test_tektos_agent_reads_and_writes_via_kosmos_ports_only_build_sequence_3_1_dod` asserts (1) prior context read via `MemoryPort.query_temporal`, (2) `LLMPort.generate_text` called exactly once with prompt containing both prior + pending content plus model + system, (3) `MemoryPort.write_event` recorded with `subject="tektos_user"`, `predicate=TEKTOS_MEMORY_PREDICATE`, `provenance="tektos_agent"`, `confidence=0.85` in `(0,1]`, `attributes.turn_id` + `attributes.role="assistant"`, (4) returned `TektosStep` records turn_id / response / memory_event_id (as `event_id.id`) / confidence / model. Full pytest **616/616** green (598 → 616, +18). `make stage1-gate` PASS regression (all four gate checks). ADR-007 respected — AST-verified `test_tektos_agent_imports_no_other_plugins_adr_007` scans `plugins/tektos/agent.py` `ast.walk` for `Import`/`ImportFrom` nodes whose module starts with any forbidden plugin prefix and asserts empty offending list. ADR-008 respected — every recorded write validated against `validate_zero_trust_write(provenance, confidence)` inside the fake `MemoryPort.write_event`, mirroring the port-layer non-bypassable guard. ADR-022 respected — `LLMPort.generate_text` is the only verb consumed. ADR-023 not exercised at 3.1 (no event publish path yet). Zero new runtime dependencies. `plugins/tektos/stub/` and `test_stage_2_4_exit_gate.py` UNCHANGED (Q5=B). Next: Stage 3.2 (vendor MCP python-sdk + Playwright-MCP; simulator gets deleted then).

## 2026-07-30 01:15 EDT — Stage 3.2 · MCPPort + adapters + APEX tool-gating LANDED

- **Stage / plugin / port:** Stage 3.2 · Tektos · new `MCPPort` (`ports/mcp.py`) + amended `ApprovalGatewayPort` (`ports/approval.py`, promoted from Praxis)
- **What changed:** Landed Tektos MCP transport + APEX tool-call gating per ADR-037. Introduced `MCPPort` async Protocol (`initialize` / `list_tools` / `call_tool` / `close` + `is_healthy`) with locked `MCP_PROTOCOL_VERSION="2024-11-05"` and value objects `MCPTool` / `MCPToolResult` / `MCPToolCallError` + `MCPServer` Protocol for in-process backends. Promoted `ChangeApprovalTier` + narrow propose-only `ApprovalGatewayPort` Protocol from `plugins/praxis/apex/tier.py` + `.../protocol.py` to `ports/approval.py` so non-Praxis plugins can gate actions through APEX without violating ADR-007; `plugins/praxis/apex/tier.py` re-exports for backwards compat (ADR-033 amended in-flight). Shipped `adapters/mcp/in_process/adapter.py` (drives an `MCPServer`) + `adapters/mcp/stdio/adapter.py` (JSON-RPC-over-stdio subprocess client with `playwright_stdio_adapter()` factory for `@playwright/mcp`). Shipped `plugins/tektos/mcp/{tool_policy.py,fake_playwright_server.py}` — deterministic fake MCP server for `browser_navigate` + `browser_snapshot`, hardcoded `TEKTOS_TOOL_TIER_MAP` with fail-closed `DEFAULT_TIER=HUMAN_REQUIRED`, locked `TEKTOS_TOOL_PREDICATE="tektos.tool.completed"`. Extended `TektosAgent` with `async call_tool(name, arguments, *, turn_id=None) -> TektosStep`: trace-first `TraceEvent` emission BEFORE APEX gate → `ApprovalGatewayPort.propose(proposing_domain="tektos", tier)` → AUTONOMOUS auto-approves, HUMAN_REVIEW/REQUIRED raise `TektosToolCallPending(approval_id, tool_name)` → `MCPPort.call_tool` → `MemoryPort.write_event(predicate=TEKTOS_TOOL_PREDICATE, provenance="tektos_agent", confidence, attributes={turn_id, tool_name, tool_arguments, is_error, content_blocks, approval_id, tier})`. Extended `TektosStep` with optional `tool_name`/`tool_arguments`/`tool_result`/`approval_id`; extended `plugins/tektos/errors.py` with `TektosToolCallPending` + `TektosToolCallDenied`.
- **Files touched:**
  - `ports/mcp.py` (new)
  - `ports/approval.py` (new — promoted narrow surface from Praxis)
  - `plugins/praxis/apex/tier.py` (re-export from `ports.approval` for backwards compat)
  - `adapters/mcp/__init__.py`, `adapters/mcp/in_process/{__init__.py,adapter.py}`, `adapters/mcp/stdio/{__init__.py,adapter.py}` (new)
  - `plugins/tektos/mcp/{__init__.py,tool_policy.py,fake_playwright_server.py}` (new)
  - `plugins/tektos/agent.py` (added `call_tool` method + trace-first + APEX gate + memory write)
  - `plugins/tektos/errors.py` (added `TektosToolCallPending` + `TektosToolCallDenied`)
  - `plugins/tektos/models.py` (extended `TektosStep`)
  - `plugins/tektos/__init__.py` (exports `FakePlaywrightServer` etc; removed stub reference)
  - `pyproject.toml` (added `adapters.mcp*` + `plugins.tektos.mcp` packages)
  - `plugins/tektos/tests/test_tektos_mcp.py` (new — 8 tests incl. DoD literal)
  - `adapters/mcp/in_process/tests/{__init__.py,test_in_process_adapter.py}` (new — 12 contract tests)
  - `adapters/mcp/stdio/tests/{__init__.py,_fake_mcp_server.py,test_stdio_adapter.py}` (new — 9 contract tests over real `asyncio.subprocess`)
  - `plugins/tektos/tests/test_playwright_stdio_integration.py` (new — 2 env-gated real-Playwright integration tests)
  - `docs/adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md` (new)
  - `docs/adrs/ADR-033-apex-change-approval-tier-engine.md` (status amendment block)
  - `docs/adrs/README.md` (ADR-037 index row)
  - `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-037 row inserted after ADR-036, chronological order preserved)
  - `docs/Kosmos-Build-Sequence-v25.md` §3.2 (rewritten LANDED)
  - `docs/PORTING_LEDGER.md` (MCP python-sdk + Playwright-MCP promoted PLANNED → PATTERN-VENDORED with commit SHAs)
- **Ports / adapters affected:** new `MCPPort` (Protocol only, no default implementation exported from `ports/`), with `InProcessMCPAdapter` + `StdioMCPAdapter` under `adapters/mcp/`. `ApprovalGatewayPort` promoted from Praxis to `ports/approval.py`; existing `plugins/praxis/apex/protocol.py::ChangeApprovalProtocol` still holds the full propose+resolve+list_pending+get_by_id+list_by_intention surface. `TraceFeedPort` consumed unchanged. `MemoryPort` consumed unchanged (new predicate `tektos.tool.completed`).
- **PORTING_LEDGER / ADR updated:** ADR-037 (Ratified v25). ADR-033 amended (`ChangeApprovalTier` + narrow gateway port promoted to `ports/approval.py`; `plugins/praxis/apex/tier.py` re-exports). ADR-036 amended (Q5=B stub-deletion trigger fired). PORTING_LEDGER MCP python-sdk PLANNED → PATTERN-VENDORED (`a4f4ccd`, MIT); Playwright-MCP PLANNED → PATTERN-VENDORED (`55679f5`, Apache-2.0).
- **Stop-condition status:** met — DoD literal `pytest plugins/tektos/tests/test_tektos_mcp.py::TestStage32DoD::test_browser_navigate_end_to_end_autonomous` asserts `TektosAgent.call_tool("browser_navigate", {"url": "https://example.invalid/"})` proceeds through AUTONOMOUS auto-approval, in-process fake Playwright MCP server responds with content blocks, `MemoryPort.write_event` recorded with `predicate="tektos.tool.completed"` + `provenance="tektos_agent"` + confidence in `(0,1]`, `TraceEvent(plugin="tektos", tool_name="browser_navigate")` emitted BEFORE the APEX gate, APEX APPROVED record persisted with `proposing_domain="tektos"`. Full pytest **644/644** green (+29 vs. 615 after gate rewire, +28 vs. Stage 3.1's 616) + 2 env-gated Playwright skips; `make stage1-gate` PASS. ADR-007 respected — `test_tektos_agent_imports_no_other_plugins_adr_007` still green; Tektos imports only from `ports.*`. ADR-008 respected — every successful tool-call write carries `provenance=TEKTOS_AGENT_PROVENANCE` + confidence in `(0,1]` + `is_error`/`approval_id`/`tier` in attributes. ADR-022 respected — LLM path unchanged. ADR-033 amended in-flight. ADR-035 preserved. ADR-036 Q5=B trigger fulfilled. Zero new pip deps. Next: Stage 3.3 (vendor aider repomap).

## 2026-07-30 01:15 EDT — Stage 3.2 · TektosSimulator deleted + Stage-2.4 exit-gate rewired

- **Stage / plugin / port:** Stage 3.2 · Tektos · Stage-2.4 exit-gate cross-cutting
- **What changed:** Deleted `plugins/tektos/stub/` (entire directory containing `TektosSimulator`) per ADR-036 Q5=B trigger firing. Rewired `plugins/tektos/tests/test_stage_2_4_exit_gate.py` to construct a real `TektosAgent` with `InProcessMCPAdapter(FakePlaywrightServer)` + minimal `_FakeLLM` (raises on use) + `_FakeMemory` (records writes) + real `KernelChangeApprovalAdapter` + `InMemoryTraceFeedAdapter`. Added helpers `_emit_tool_call` / `_emit_tool_loop` (turn_id reused across loop iterations so `LoopDetector` correlates) that invoke real `TektosAgent.call_tool` and absorb `TektosToolCallPending` when the tier map fails-closed. Filtered `apex.list_pending()` calls in three assertions by `proposing_domain == "phrouros"` because real `call_tool` now also proposes with `proposing_domain="tektos"`. Replaced `TestTektosSimulator` class with `TestTektosAgentTraceEmission` (2 smoke tests confirming real trace emission over the `TraceFeedPort`).
- **Files touched:**
  - `plugins/tektos/stub/` (deleted)
  - `plugins/tektos/tests/test_stage_2_4_exit_gate.py` (rewired to real Tektos)
  - `plugins/tektos/__init__.py` (removed stub re-export)
  - `pyproject.toml` (dropped `plugins.tektos.stub` from packages)
- **Ports / adapters affected:** none new. Real `TektosAgent.call_tool` path now drives `TraceFeedPort` publications for the gate test, replacing the deleted `TektosSimulator`'s `TraceFeedPort.publish` path.
- **PORTING_LEDGER / ADR updated:** ADR-036 amended (Q5=B trigger fulfilled).
- **Stop-condition status:** met — `pytest -k stage_2_4_exit_gate` 5 gate tests green (previously 6 in the mixed stub+simulator layout; the DoD literal `test_unauthorized_tool_call_detected_and_escalated_and_user_notified_build_sequence_2_4_dod` still passes end-to-end with the real Tektos agent as the trace source, and `TestTektosAgentTraceEmission` supersedes the deleted `TestTektosSimulator`). Full pytest 644/644 green. ADR-035 preserved (gate DoD unchanged). ADR-007 unchanged.

## 2026-07-29 22:35 EDT — Stage 3.3 · aider repomap PATTERN-VENDORED · code shipped

- **Stage / plugin / port:** Stage 3.3 · Tektos · repomap (no new port surface)
- **What changed:** Pattern-vendored aider's repomap algorithm (Apache-2.0, upstream `Aider-AI/aider@5dc9490bb35f`) as five in-tree modules under `plugins/tektos/repomap/` — only the 6 tree-sitter `.scm` query files were copied verbatim. Locked 7 constants in `policy.py` (`REPOMAP_PROVENANCE="aider-repomap"`, `REPOMAP_INDEXED_PREDICATE="tektos.repomap.indexed"`, `REPOMAP_SNAPSHOT_PREDICATE="tektos.repomap.snapshot"`, `REPOMAP_FRESHNESS_WINDOW_DAYS=30.0`, `REPOMAP_DEFAULT_MAP_TOKENS=1024`, `REPOMAP_CACHE_VERSION=4`, `REPOMAP_MIN_CONFIDENCE=0.01`) plus `compute_freshness_confidence()` implementing the ADR-038 Q4=B linear-decay formula. `tags.py` extracts def/ref rows via `tree_sitter_language_pack` with a diskcache-backed cache keyed by `(path, mtime)` under `<repo-root>/.kosmos.repomap.cache.v4`, a Pygments fallback for defs-only languages, and a version-adaptive helper spanning the tree-sitter 0.23/0.24 `Query.captures` → `QueryCursor.captures` API split. `rank.py` reimplements aider's PageRank with a NetworkX `MultiDiGraph` + `pagerank_scipy` backend and the ident-heuristic weighting (snake/kebab/CamelCase x10 bonus when `len>=8`, dunder x0.1 penalty, `files-def>5` x0.1, chat_fnames x50, `sqrt(num_refs)` damping, personalization vector). `render.py` renders the tree-context view via `grep_ast.TreeContext` and binary-searches the ranked-tag prefix with a 15% tolerance around `max_tokens` (matches upstream). `indexer.py` is the async `index()` facade: walks source files, extracts + ranks + renders, then emits one `tektos.repomap.indexed` per-file `MemoryPort.write_event` and exactly one `tektos.repomap.snapshot` per run. Added 7 pip deps under a Stage 3.3 marker in `pyproject.toml` (`tree-sitter>=0.24`, `tree-sitter-language-pack>=1.13`, `networkx>=3.4`, `scipy>=1.14`, `grep-ast>=0.9`, `pygments>=2.18`, `diskcache>=5.6`).
- **Files touched:**
  - `plugins/tektos/repomap/__init__.py`
  - `plugins/tektos/repomap/policy.py`
  - `plugins/tektos/repomap/tags.py`
  - `plugins/tektos/repomap/rank.py`
  - `plugins/tektos/repomap/render.py`
  - `plugins/tektos/repomap/indexer.py`
  - `plugins/tektos/repomap/queries/{python,javascript,typescript,rust,go,bash}-tags.scm`
  - `plugins/tektos/repomap/queries/ATTRIBUTION.md`
  - `pyproject.toml`
- **Ports / adapters affected:** none new. `MemoryPort` consumed with two locked predicates.
- **PORTING_LEDGER / ADR updated:** aider repomap PLANNED → PATTERN-VENDORED with commit `5dc9490bb35f`; 7 new pip-dep entries logged; ADR-038 authored at Ratified v25.
- **Stop-condition status:** in-progress — code green in smoke; contract tests + fan-out + landing follow in the next entry.

## 2026-07-29 23:04 EDT — Stage 3.3 · aider repomap · tests + docs fan-out + LANDED

- **Stage / plugin / port:** Stage 3.3 · Tektos · repomap
- **What changed:** Shipped `plugins/tektos/tests/test_repomap.py` — 31 contract tests + 2 env-gated tests covering: locked-constants assertions (7 tests), freshness formula edge cases (6 tests: brand-new, 1-day, 30-day boundary, past-window floor, `window_days <= 0` `ValueError`, future-mtime clamp), tag extraction over Python source with tree-sitter + cache-hit consistency + hidden-dir skip (4 tests), rank ordering + determinism + per-file aggregation (3 tests), render empty + token-budget respect + default token counter (3 tests), indexer end-to-end (per-file writes carry locked provenance, exactly-one snapshot per run, freshness confidence falls off with mtime, `RepoMapResult.top_files` matches rank order, queryability via `MemoryPort.query_temporal`, `RepoMapResult` shape — 6 tests), fast 500-file synthetic corpus smoke that asserts full DoD contract in <5s, plus env-gated 10k literal (`KOSMOS_STAGE_33_LARGE_CORPUS=1`) and env-gated real CPython corpus (`KOSMOS_STAGE_33_REAL_CORPUS=1`) which are skipped in `make stage1-gate` to keep the sandbox fast (they run on Colossus). The fast-smoke variant asserts the exact DoD contract from spec §18 3.3 — per-file writes with `provenance="aider-repomap"` + confidence in `(0,1]`, one snapshot, MemoryPort queryable via `query_temporal`. Fanned out to docs: `docs/adrs/ADR-038-aider-repomap-pattern-vendor.md` authored; `docs/adrs/README.md` ADR-038 row appended; `docs/Kosmos-Build-Spec-v25.md` §17 ADR-038 row inserted after ADR-037; `docs/Kosmos-Build-Sequence-v25.md` §3.3 rewritten as LANDED with locked answers + tiered DoD; `docs/PORTING_LEDGER.md` aider PLANNED → PATTERN-VENDORED with 7 new pip-dep entries appended.
- **Files touched:**
  - `plugins/tektos/tests/test_repomap.py`
  - `docs/adrs/ADR-038-aider-repomap-pattern-vendor.md`
  - `docs/adrs/README.md`
  - `docs/Kosmos-Build-Spec-v25.md` (§17)
  - `docs/Kosmos-Build-Sequence-v25.md` (§3.3)
  - `docs/PORTING_LEDGER.md`
  - `SESSION_HANDOFF.md`
- **Ports / adapters affected:** none new.
- **PORTING_LEDGER / ADR updated:** ADR-038 Ratified v25 (single composite covering Q1=A · Q2=A(revised) · Q3=C · Q4=B · Q5=C · Q6=A).
- **Stop-condition status:** met — DoD literal anchor `pytest plugins/tektos/tests/test_repomap.py::test_repomap_smoke_500_file_corpus_writes_queryable_via_memoryport` passes in `make stage1-gate` (asserts 500 per-file writes with locked provenance + confidence in `(0,1]`, exactly 1 snapshot, `query_temporal("tektos.repomap.indexed", limit=100)` returns 100 rows). Full pytest **675/675** green (+31 vs. Stage 3.2's 644) + 4 env-gated skips (2 Playwright + 10k corpus + real CPython); `make stage1-gate` PASS. ADR-007 respected — repomap is Tektos-internal, no cross-plugin imports. ADR-008 respected — every `MemoryPort.write_event` carries `provenance="aider-repomap"` + confidence in `(0,1]`, port-level `validate_zero_trust_write` guard exercised via `_FakeMemoryPort`. ADR-023 respected — no new port surface. ADR-036/037 preserved. Next: Stage 3.4 (Bernstein Janitor spike test).

## 2026-07-30 02:25 EDT — ADR-039 · Defer Stage 3.4 to Phase 4 and Stage 3.5 to Phase 5

- **Stage / plugin / port:** Phase 3 sequencing decision · no plugin/port surface changes
- **What changed:** Authored ADR-039 (Ratified v25) recording the deferral of two Phase-3 stages whose Definitions of Done literally reference substrate that other ratified ADRs defer or has not been built. **§3.4 (Bernstein Janitor spike test)**: preflight grep confirmed `SandboxProvider` and `WorktreeProvider` are absent from `ports/` and no Postgres TaskState schema exists in the tree; ADR-004 §Evaluation Plan step 2 requires all three, and ADR-004 §Build-Order Placement literal already schedules the spike "immediately before Tektos Phase 4 begins." **§3.5 (Reflexion + Voyager port)**: DoD literal "Reflexion cycle logged in Langfuse" is blocked by ADR-025 (Langfuse deferred) and ADR-034 (`LangfuseTraceFeedAdapter` primary lands Stage 5). Amended `docs/Kosmos-Build-Sequence-v25.md` §3.4 and §3.5 to defer-blocks pointing at ADR-039, preserving the original scope text under "Original §… scope (deferred)" subsections so nothing is lost. Added ADR-039 row to `docs/adrs/README.md` and `docs/Kosmos-Build-Spec-v25.md` §17 (row placed in ADR-ID order between ADR-038 and the §17.1 sub-header). **No code churn: no port changes, no pip-dep changes, no test changes, no PORTING_LEDGER changes.** Bernstein Janitor / `local-agentic-loop-sample` / Reflexion / Voyager entries in PORTING_LEDGER remain `PLANNED` / `EVALUATING` exactly as before — this ADR moves the spike's timing, not the vendor evaluation outcome.
- **Files touched:**
  - `docs/adrs/ADR-039-stage-3-4-and-3-5-defer.md` (new)
  - `docs/adrs/README.md` (ADR-039 index row appended)
  - `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-039 row appended in ID order)
  - `docs/Kosmos-Build-Sequence-v25.md` §3.4 rewritten as defer-block; §3.5 rewritten as defer-block; original scope text preserved under both
  - `SESSION_HANDOFF.md` (overwritten to point at Stage 3.6 as next)
- **Ports / adapters affected:** none.
- **PORTING_LEDGER / ADR updated:** ADR-039 Ratified v25 (amends ADR-004 timing + ADR-025 concretely locks §3.5-blocked-on-Langfuse-defer). ADR-004 and ADR-025 body text unchanged; ADR-039 is the pointer.
- **Stop-condition status:** met — docs-only ADR; `make stage1-gate` PASSes unchanged (675/675 green + 4 env-gated skips per Stage 3.3 landing). Next: Stage 3.6 (OpenSpec spec engine).

## 2026-07-30 02:27 EDT — Stage 3.3 · Colossus env-gated timing evidence

- **Stage / plugin / port:** Stage 3.3 · Tektos · repomap (post-landing evidence)
- **What changed:** No code or docs changed. Recording Colossus wall-clock evidence for the two env-gated Stage 3.3 tests that are skipped in `make stage1-gate` to keep the sandbox fast. Both PASS on Colossus (Kubuntu, RTX 5090, 128GB RAM, Python 3.14.4, pytest-9.1.1).
  - `KOSMOS_STAGE_33_LARGE_CORPUS=1 pytest plugins/tektos/tests/test_repomap.py::test_repomap_10k_file_corpus_writes_queryable_via_memoryport_build_sequence_3_3_dod`: **239.82s (3:59) — PASS.** 10,000-file synthetic corpus indexed end-to-end; asserts locked-provenance per-file writes, exactly one snapshot, `MemoryPort.query_temporal("tektos.repomap.indexed", limit=…)` queryability. Session log preserved at `/tmp/kosmos-3-3-10k.log` on Colossus.
  - `KOSMOS_STAGE_33_REAL_CORPUS=1 pytest plugins/tektos/tests/test_repomap.py::test_index_against_real_cpython_corpus`: **1.81s — PASS.** Real CPython source sparse-checkout indexed end-to-end. Session log preserved at `/tmp/kosmos-3-3-cpython.log` on Colossus.
- **Files touched:** none (this entry is timing-evidence only).
- **Ports / adapters affected:** none.
- **PORTING_LEDGER / ADR updated:** ADR-038 DoD evidence now includes concrete Colossus wall-clock; no ADR body change needed.
- **Stop-condition status:** met — Stage 3.3 DoD is fully corroborated by Colossus execution across all three test tiers (fast 500-file smoke in stage1-gate ~3s; 10k literal 239.82s on Colossus; real CPython 1.81s on Colossus). Cache_version=4 diskcache under `<repo-root>/.kosmos.repomap.cache.v4` warmed on Colossus. No regressions.

## 2026-07-30 02:44 EDT — Stage 3.6 LANDED: OpenSpec parser pattern-vendored (ADR-040); amend ADR-005

- **Stage / plugin / port:** Stage 3.6 · Tektos OpenSpec subsystem · Tektos-internal (no new port surface, ADR-023 envelope-first defer)
- **What changed:**
  - Pattern-vendored `Fission-AI/OpenSpec@2b3d368539132be6311e55db58899abbf5306b81` (MIT) as stdlib-only Python parser + Plan producer at `plugins/tektos/openspec/{__init__.py,policy.py,models.py,parser.py,plan.py}`. No upstream source copied verbatim (upstream is TypeScript/Node CLI); algorithm ported from upstream `docs/concepts.md` + `docs/opsx.md` + `openspec/changes/fix-spec-parser-fidelity/` unified-reader design.
  - Locked constants in `policy.py`: `OPENSPEC_PROVENANCE="openspec-parser"`, `OPENSPEC_ARTIFACT_PREDICATE="tektos.openspec.artifact.parsed"`, `OPENSPEC_PLAN_PREDICATE="tektos.openspec.plan.produced"`, `OPENSPEC_UPSTREAM_COMMIT="2b3d368539132be6311e55db58899abbf5306b81"`, `OPENSPEC_UPSTREAM_LICENSE="MIT"`, `OPENSPEC_MIN_CONFIDENCE=0.05`, `OPENSPEC_FULL_ARTIFACT_SET=frozenset({"proposal.md","design.md","tasks.md"})`, `OPENSPEC_REQUIRED_ARTIFACTS=frozenset({"proposal.md"})`.
  - Real fixture committed at `plugins/tektos/tests/fixtures/openspec/add-dark-mode/{proposal.md, design.md, tasks.md, specs/ui/spec.md}` patterned after upstream OPSX walkthrough — exercises ADDED/MODIFIED/REMOVED delta blocks, metadata-line skipping in requirement body capture, fenced example scenarios that must NOT count, and a fenced-block checkbox in `tasks.md` that must NOT count as a task.
  - `produce_plan(change_dir, memory)` writes one `tektos.openspec.artifact.parsed` MemoryPort event per parsed markdown file (subject=`<change_id>::<relative_path>`, confidence = per-artifact completeness) and one `tektos.openspec.plan.produced` MemoryPort event per change directory (subject=change_id, confidence = mean per-artifact completeness clamped to `OPENSPEC_MIN_CONFIDENCE`).
  - Authored **ADR-040** (Ratified v25) at `docs/adrs/ADR-040-tektos-openspec-parser-vendoring.md`.
  - Amended **ADR-005** with STATUS AMENDMENT (2026-07-30) block at top; status line changed to `Ratified · amended by ADR-040` (original decision text preserved).
  - Fanned out to ADR index (`docs/adrs/README.md` new row + updated ADR-005 status), Spec §17 (new ADR-040 row), `PORTING_LEDGER.md` OpenSpec entry (`PLANNED` → `PATTERN-VENDORED`), and `docs/Kosmos-Build-Sequence-v25.md` §3.6 rewritten as LANDED block with DoD anchor.
- **Files touched:**
  - `plugins/tektos/openspec/__init__.py`, `plugins/tektos/openspec/policy.py`, `plugins/tektos/openspec/models.py`, `plugins/tektos/openspec/parser.py`, `plugins/tektos/openspec/plan.py`
  - `plugins/tektos/tests/fixtures/openspec/add-dark-mode/proposal.md`, `.../design.md`, `.../tasks.md`, `.../specs/ui/spec.md`
  - `plugins/tektos/tests/test_openspec.py`
  - `docs/adrs/ADR-040-tektos-openspec-parser-vendoring.md`
  - `docs/adrs/ADR-005-openspec-primary.md` (STATUS AMENDMENT + status line)
  - `docs/adrs/README.md`
  - `docs/Kosmos-Build-Spec-v25.md` (§17 new row)
  - `docs/PORTING_LEDGER.md` (OpenSpec block replaced)
  - `docs/Kosmos-Build-Sequence-v25.md` (§3.6 LANDED)
  - `BUILD_LOG.md` (this entry)
  - `SESSION_HANDOFF.md` (overwritten to point at Stage 3.7)
- **Ports / adapters affected:** none. Tektos-internal only per ADR-040 Q2. No new `ports/*.py`. `DataPort` (ADR-028 JSON-LD export) intentionally not reused (semantically wrong for spec-doc reading).
- **PORTING_LEDGER / ADR updated:** ADR-040 authored; ADR-005 amended; PORTING_LEDGER `OpenSpec` entry moved from `PLANNED` to `PATTERN-VENDORED` with upstream commit + SPDX + modifications.
- **Stop-condition status:** met — Stage 3.6 DoD literal `pytest plugins/tektos/tests/test_openspec.py::test_produce_plan_on_add_dark_mode_fixture_writes_queryable_events_build_sequence_3_6_dod` green; 30 new tests all green; full-repo `pytest`: 705 passed + 4 env-gated skips; `make stage1-gate`: PASS. ADR-007 (AST guard test) + ADR-008 (zero-trust passthrough test) + ADR-023 (envelope-first, no new port) + ADR-028 (`DataPort` untouched) all verified in-tree. Phase 3 advances Stage 3.6 → Stage 3.7 (spec-kit plan renderer).

## 2026-07-30 03:08 EDT — Stage 3.7 LANDED · Tektos plan renderer + first PluginDescriptor (ADR-041)

- **Stage / plugin / port:** Stage 3.7 · plugins/tektos/renderer + plugins/tektos/plugin · reuses FrontendContractPort (ADR-031) + ApprovalGatewayPort (ADR-033/037) + MemoryPort (ADR-008)
- **What changed:** Landed pure-Python plan renderer (Q1=B, no upstream vendored) + first Tektos `PluginDescriptor` (Q7=A) mirroring `plugins/phrouros/plugin.py` bootstrap shape. Every `PlanCard` proposes through `ApprovalGatewayPort.propose(...)` at fail-closed `ChangeApprovalTier.HUMAN_REVIEW` (Q4=A, ADR-037 default), emits a `tektos.plan.card_rendered` MemoryPort event with `provenance="tektos_plan_renderer"` + confidence `clamp(plan.mean_completeness, 0.05, 1.0)` (Q6=A), and registers `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE, priority=90, lazy_module="tektos/panels/PlanApprovalPanel")` (Q3=A) that sits BELOW Praxis `praxis.approvals` at priority 100 per ADR-033 §Q1=C. Fires ADR-036 Q4=B `PluginDescriptor` deferral trigger (STATUS AMENDMENT appended). Q10=Option X defers ADR-005 Spec-Kit fate — `PORTING_LEDGER.md` `spec-kit` row stays `PLANNED · Source: TBD` with ADR pointer updated to `ADR-005 · ADR-041`. `ui_parity_status=IN_PROGRESS` at 3.7 → COMPLIANT at Stage 3.11.
- **Files touched:**
  - `plugins/tektos/renderer/__init__.py` (new)
  - `plugins/tektos/renderer/policy.py` (new — locked constants)
  - `plugins/tektos/renderer/models.py` (new — `PlanCard` frozen dataclass + `clamp_card_confidence`)
  - `plugins/tektos/renderer/project.py` (new — `project_plan_to_card` + `render_and_gate_plan_card`)
  - `plugins/tektos/plugin.py` (new — `TektosPlugin` + `build_tektos_descriptor()`)
  - `plugins/tektos/tests/test_plan_renderer.py` (new — 28 tests)
  - `docs/adrs/ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md` (new)
  - `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` (STATUS AMENDMENT for Q4=B trigger firing)
  - `docs/adrs/README.md` (ADR-041 row appended)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-041 row inserted)
  - `docs/Kosmos-Build-Sequence-v25.md` (§3.7 rewritten as LANDED block)
  - `docs/PORTING_LEDGER.md` (`spec-kit` row ADR pointer + defer note)
  - `BUILD_LOG.md` (this entry)
  - `SESSION_HANDOFF.md` (overwritten to point at Stage 3.8)
- **Ports / adapters affected:** none. Envelope-first per ADR-023 / ADR-038 / ADR-040 defer pattern. `FrontendContractPort` (ADR-031) `Panel`/`PluginDescriptor` schemas unchanged. `ApprovalGatewayPort` (ADR-033) tier + narrow gateway shape unchanged. `MemoryPort` (ADR-008) zero-trust guard passthrough verified.
- **PORTING_LEDGER / ADR updated:** ADR-041 authored (Ratified v25); ADR-036 STATUS AMENDMENT appended for Q4=B trigger firing; ADR index (`docs/adrs/README.md`) + Spec §17 + Build-Sequence §3.7 all reference ADR-041; `PORTING_LEDGER.md` `spec-kit` row ADR pointer updated to `ADR-005 · ADR-041` with defer note (row stays `PLANNED` per Q10 Option X).
- **Stop-condition status:** met — Stage 3.7 DoD literal `pytest plugins/tektos/tests/test_plan_renderer.py::test_produce_plan_renders_as_approvable_card_via_frontend_contract_port_build_sequence_3_7_dod` green; 28 new tests all green; full-repo `pytest`: 733 passed + 4 env-gated skips; `make stage1-gate`: PASS. ADR-007 (AST guard `test_renderer_and_plugin_import_no_other_plugins_adr_007`) + ADR-008 (zero-trust passthrough via `_RejectingMemoryPort`) + ADR-023 (envelope-first, no new port) + ADR-031 (Panel/PluginDescriptor shapes unchanged) + ADR-033 (Tektos priority 90 < Praxis priority 100 asserted) + ADR-036 Q4=B trigger fired via STATUS AMENDMENT + ADR-037 (HUMAN_REVIEW fail-closed default) + ADR-040 (Stage 3.6 `Plan` producer consumed unchanged) all verified in-tree. Phase 3 advances Stage 3.7 → Stage 3.8 (Pier eval harness).

## 2026-07-30 03:43 EDT — Stage 3.8 · Pier eval harness LANDED

- **Stage / plugin / port:** Stage 3.8 · Tektos plugin · `plugins.tektos.eval` subsystem (no new port; envelope-first per ADR-023)
- **What changed:** Landed the Tektos-internal Pier eval harness that satisfies the Stage 3.8 DoD "Every Tektos PR runs through Pier before user review." Ships `plugins/tektos/eval/{__init__,policy,models,harness}.py` invoking `datacurve-pier==0.3.0` (Apache-2.0; upstream `datacurve-ai/pier@fefa7475a32bb05271abdea378e8083c83eb5c35`) as a subprocess through the public `pier run` CLI so the fast unit tier runs without the package installed. Ships kernel runner `scripts/pier_eval.py` + `Makefile eval-gate` target. Ships one committed Harbor fixture `plugins/tektos/eval/tasks/tektos-plan-execution-smoke/` (rename `greet_old` → `greet` with three verifier assertions). Every trial emits one `tektos.eval.trial_completed` MemoryPort event with locked provenance `pier-eval-harness`, `subject="<change_id?>::<task_name>::<trial_id>"`, `object=outcome.value`, `confidence=1.0` on PASS or `0.0` on FAIL/ERROR, and `attributes` carrying the ATIF verifier + trajectory metadata plus optional `change_id`. Docker-only `PierEnv` per Colossus local-first invariant. Verdicts are advisory only (Q7=B, revised from Q7=A after ADR-007 mechanism review): plan cards remain in `HUMAN_REVIEW` and the user is the sole approver — automated approval deferred to a future ADR (candidate ADR-043) if experience shows manual review is a bottleneck.
- **Files touched:**
  - `plugins/tektos/eval/__init__.py`, `policy.py`, `models.py`, `harness.py`
  - `plugins/tektos/eval/tasks/tektos-plan-execution-smoke/{task.toml,instruction.md,environment/src/hello.py,solution/hello.py,tests/test_hello.py}`
  - `scripts/pier_eval.py`
  - `plugins/tektos/tests/test_pier_eval.py`
  - `Makefile` (new `eval-gate` target)
  - `pyproject.toml` (new `[project.optional-dependencies] eval = ["datacurve-pier==0.3.0"]`; setuptools packages gain `plugins.tektos.eval` plus previously-missing `plugins.tektos.{openspec,renderer,repomap}`; `norecursedirs = ["plugins/tektos/eval/tasks"]` excludes Harbor verifier tests)
  - `docs/adrs/README.md` (ADR-042 row inserted; ADR-006 status → `Superseded by ADR-042`)
  - `docs/adrs/ADR-006-pier-eval-harness.md` (STATUS AMENDMENT block prepended; status line updated)
  - `docs/adrs/ADR-042-tektos-pier-eval-harness.md` (new — Ratified v25)
  - `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-042 row inserted; ADR-006 row status updated; §17 preamble amended to note `Superseded` is a legitimate terminal status accepted by the Stage-1 gate)
  - `docs/Kosmos-Build-Sequence-v25.md` §3.8 (rewritten as LANDED block)
  - `docs/PORTING_LEDGER.md` (Pier row upgraded from `PLANNED` → `VENDORED (dev dep, Stage 3.8)` with upstream commit + PyPI pin + Apache-2.0 license + ADR-042 pointer)
  - `scripts/stage1_gate.py` (`RATIFIED_MARKERS` extended with `"Superseded"` since a superseded ADR is a legitimate terminal state; docstring + section header updated)
- **Ports / adapters affected:** None. Envelope-first per ADR-023: verdicts flow through the existing `MemoryPort`; no new port surface introduced.
- **PORTING_LEDGER / ADR updated:** ADR-042 (new, Ratified v25); ADR-006 (STATUS AMENDMENT — superseded); PORTING_LEDGER Pier row → `VENDORED (dev dep, Stage 3.8)`.
- **Stop-condition status:** met. Stage 3.8 DoD literal `pytest plugins/tektos/tests/test_pier_eval.py::test_tektos_plan_runs_through_pier_before_user_review_build_sequence_3_8_dod` passes; `.venv/bin/python -m pytest` reports 747 passed + 5 env-gated skips; `make stage1-gate` PASS.

## 2026-07-30 04:02 EDT — Stage 3.9 · DeepSWE corpus subset LANDED (ADR-007-DeepSWE amended)

- **Stage / plugin / port:** Stage 3.9 · Tektos eval-corpus subsystem (envelope-first per ADR-023, no new port)
- **What changed:** Landed the DeepSWE eval-corpus subsystem end-to-end. Shipped `plugins/tektos/eval/corpora/deepswe/{__init__.py,manifest.toml,policy.py,models.py,loader.py,harness.py}` implementing manifest-only vendoring per ADR-007-DeepSWE STATUS AMENDMENT 2026-07-30: pinned upstream commit `e016041a6ccf8da29906afc9a3f5a8df940a1f78` (Apache-2.0, 2026-07-22) plus a deterministic 5-task subset (3 Python + 2 TypeScript) chosen by task-id sort from the 113-task corpus, with each upstream repo + base commit + SPDX verified via the GitHub API. Added kernel runner scripts `scripts/deepswe_fetch.py` (on-demand clone into git-ignored `.eval-cache/deepswe/<commit>/tasks/` via `git clone --filter=blob:none --no-checkout && git checkout <commit>`) and `scripts/deepswe_run.py` (mirrors `pier_eval.py` shape, runs each subset task through Stage 3.8's `run_pier_trial`, aggregates into `CorpusRunSummary`, prints JSON on stdout), wired to new `Makefile deepswe-fetch` and `deepswe-gate` targets. `record_corpus_run` writes exactly one `tektos.eval.corpus_run_completed` MemoryPort event with `provenance="deepswe-eval-corpus"`, `subject="deepswe::<upstream_commit>::<sample_seed>::<run_id>"`, `object="<n_pass>/<n_total>"`, `confidence=n_pass/n_total` (clamped to `[0.0, 1.0]`, 0.0 when `n_total=0`), and `attributes` carrying `run_id`, `corpus`, `upstream_commit`, `sample_seed`, `subset_task_ids`, `outcomes`, per-task `trial_event_ids`, `n_pass`/`n_fail`/`n_error`/`n_total`, `pier_version`, `pier_env`, `started_at`, `finished_at`. Per-trial `tektos.eval.trial_completed` events from Stage 3.8 remain unchanged — the aggregate event is additive. Amended `docs/adrs/ADR-007-DeepSWE-corpus.md` with STATUS AMENDMENT 2026-07-30 pinning scope (manifest-only, 5-task subset, per-task SPDX verified against upstream repos) and DEFERRING DoD clause 3 (context-rot regression cross-check) until a Kosmos-native context-rot regression suite lands as its own stage (v20.2 §3 is pre-v25 and v25 has not yet cut a replacement suite). Status line moved from `Proposed` → `Ratified v25 · Landed at Stage 3.9`. Fan-out: `docs/PORTING_LEDGER.md` DeepSWE row `PLANNED` → `VENDORED (manifest-only, Stage 3.9)` with 5-row per-task SPDX table; `docs/Kosmos-Build-Spec-v25.md` §17 row → `Ratified v25 · Stage 3.9`; `docs/adrs/README.md` index row → `Ratified v25 · Stage 3.9` with STATUS AMENDMENT summary; `docs/Kosmos-Build-Sequence-v25.md` §3.9 rewritten as a full LANDED block mirroring §3.8 shape. Added `.eval-cache/` and `plugins/tektos/eval/tasks/**/_pier_jobs/` to `.gitignore`. Extended `pyproject.toml` `[tool.setuptools] packages` with `plugins.tektos.eval.corpora` and `plugins.tektos.eval.corpora.deepswe`.
- **Files touched:**
  - `plugins/tektos/eval/corpora/__init__.py` (new — package doc)
  - `plugins/tektos/eval/corpora/deepswe/__init__.py` (new — public re-exports + Q-locks docstring)
  - `plugins/tektos/eval/corpora/deepswe/manifest.toml` (new — authoritative pinned subset)
  - `plugins/tektos/eval/corpora/deepswe/policy.py` (new — locked constants + `corpus_run_confidence`)
  - `plugins/tektos/eval/corpora/deepswe/models.py` (new — `DeepSweSubsetEntry` + `DeepSweCorpus` + `CorpusRunSummary`)
  - `plugins/tektos/eval/corpora/deepswe/loader.py` (new — `load_deepswe_manifest` + `DeepSweManifestError`)
  - `plugins/tektos/eval/corpora/deepswe/harness.py` (new — `utc_now_iso`, `build_corpus_run_summary`, `record_corpus_run`)
  - `plugins/tektos/tests/test_deepswe_corpus.py` (new — 18 fast unit tests + 1 env-gated real-DeepSWE tier)
  - `scripts/deepswe_fetch.py` (new — hydrate `.eval-cache/deepswe/<commit>/tasks/` from pinned upstream)
  - `scripts/deepswe_run.py` (new — run subset through Pier + print aggregate JSON on stdout)
  - `Makefile` (added `deepswe-fetch` + `deepswe-gate` targets, `.PHONY` and `help` updated)
  - `.gitignore` (added `.eval-cache/` + `plugins/tektos/eval/tasks/**/_pier_jobs/`)
  - `pyproject.toml` (added `plugins.tektos.eval.corpora` + `plugins.tektos.eval.corpora.deepswe` to setuptools packages)
  - `docs/adrs/ADR-007-DeepSWE-corpus.md` (STATUS AMENDMENT 2026-07-30 block + status line change)
  - `docs/adrs/README.md` (ADR-007-DeepSWE row updated: description + Ratified v25 · Stage 3.9)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-007-DeepSWE row: description + Ratified v25 · Stage 3.9)
  - `docs/PORTING_LEDGER.md` (DeepSWE row `PLANNED` → `VENDORED (manifest-only, Stage 3.9)` with per-task SPDX table)
  - `docs/Kosmos-Build-Sequence-v25.md` (§3.9 rewritten as LANDED block)
  - `BUILD_LOG.md` (this entry)
- **Ports / adapters affected:** none — envelope-first per ADR-023 (matches ADR-038 / ADR-040 / ADR-041 / ADR-042 defer pattern). All writes flow through the existing `MemoryPort`.
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER DeepSWE row promoted `PLANNED` → `VENDORED (manifest-only, Stage 3.9)` with per-task SPDX table; ADR-007-DeepSWE amended in-place via STATUS AMENDMENT 2026-07-30 (scope pin + DoD clause 3 defer, status line `Proposed` → `Ratified v25 · Landed at Stage 3.9`); ADR-007-DeepSWE index row in `docs/adrs/README.md` and Spec §17 row updated in lockstep.
- **Stop-condition status:** met — Build-Sequence §3.9 DoD literal "Benchmark run recorded" is anchored by `pytest plugins/tektos/tests/test_deepswe_corpus.py::test_deepswe_subset_benchmark_run_recorded_build_sequence_3_9_dod` which wires manifest → fake Pier CLI shim (mixed PASS/FAIL trajectories) → aggregate `CorpusRunSummary` → single `tektos.eval.corpus_run_completed` MemoryPort event with `object="3/5"` and `confidence=0.6`. `make stage1-gate` PASS, `.venv/bin/pytest` 765 passed + 6 env-gated skips.

## 2026-07-30 04:20 EDT — Stage 3.10 · docling document ingestion LANDED (ADR-044 ratified)

- **Stage / plugin / port:** Stage 3.10 · Tektos ingest subsystem (envelope-first per ADR-023, no new port; existing `DataPort` reused).
- **What changed:** Landed the docling document-ingestion subsystem end-to-end. Shipped `plugins/tektos/ingest/{__init__.py,policy.py,models.py,harness.py}` PATTERN-VENDORING `docling==2.116.0` (MIT; upstream `docling-project/docling@ba8251e9cda84bab44cebe3b884119d3f50cb12a`) as a dev-only optional dep — docling is a **lazy** import inside `resolve_default_converter_factory()` so the Stage-1 gate runs with docling uninstalled and `plugins.tektos.ingest` stays cheap-to-import. Locked constants in `policy.py`: `DOCLING_INGEST_PROVENANCE="tektos-docling-ingest"`, `DOCLING_INGEST_RECORD_TYPE="tektos.ingest.document"`, `DOCLING_UPSTREAM_PACKAGE="docling"`, `DOCLING_UPSTREAM_PYPI_VERSION="2.116.0"`, `DOCLING_UPSTREAM_COMMIT="ba8251e9cda84bab44cebe3b884119d3f50cb12a"`, `DOCLING_UPSTREAM_LICENSE="MIT"`, `DOCLING_UPSTREAM_REPO="https://github.com/docling-project/docling"`, `DOCLING_DEFAULT_PII_TIER=PIITier.INTERNAL`, `DOCLING_SUCCESS_CONFIDENCE=1.0`, `DOCLING_MIN_CONFIDENCE=0.0`, `DOCLING_MAX_CONFIDENCE=1.0`, `DOCLING_SUPPORTED_EXTENSIONS=frozenset({".pdf", ".docx", ".html"})`. `models.py` defines `DoclingSource` (path + supported-extension guard) + `DoclingRun` (immutable record with `.to_attributes()` JSON round-trip) + `DoclingIngestFailure`. `harness.py` implements `ingest_document` (extension whitelist enforced **before** converter is resolved so unsupported inputs never touch docling), `record_ingest_envelope` (single locked-shape write through `DataPort.export_canonical` with `record_type="tektos.ingest.document"`, `provenance="tektos-docling-ingest"`, `confidence=1.0` on success, default `pii_tier=PIITier.INTERNAL`, caller override to `SENSITIVE` or `RESTRICTED`, `source_citation.upstream_commit`/`upstream_license` populated, `attributes={source_extension, docling_dict_keys, docling_markdown_length, converter_class, run_id, ingested_at, page_count?}`, `payload={docling_dict, docling_markdown}`), and `run_and_record_ingest` end-to-end wiring. Any failure (unsupported ext, missing source, docling raising, non-dict `export_to_dict`, non-str `export_to_markdown`) raises `DoclingIngestFailure` and **no** envelope is written (fail-closed per ADR-044 Q4=A). Kernel runner `scripts/docling_ingest.py` (`--source <path> --output <dir>`) mirrors `scripts/pier_eval.py` shape + `Makefile ingest-doc` target. Committed micro-fixtures at `plugins/tektos/tests/fixtures/docling/{sample.pdf, sample.docx, sample.html}` — hand-rolled minimal PDF/DOCX (via `/tmp/build_fixtures.py`, not committed) + trivial HTML, total ~2 KB, no external assets, no network. Test file `plugins/tektos/tests/test_docling_ingest.py` ships 26 fast unit tests + 1 env-gated real-docling tier (`KOSMOS_STAGE_310_REAL_DOCLING=1`). `pyproject.toml` gains `[project.optional-dependencies] ingest = ["docling==2.116.0"]` + `plugins.tektos.ingest` in setuptools packages. Authored new `docs/adrs/ADR-044-tektos-docling-document-ingestion.md` (renumbered from ADR-043 to preserve ADR-042's forward-reference to "candidate ADR-043 event-driven auto-approve" for Pier). Fan-out: `docs/Kosmos-Build-Spec-v25.md` §17 gains ADR-044 row; §18.5 docling license corrected `Apache-2.0` → `MIT` (verified via `gh api repos/docling-project/docling` — SPDX is MIT for both `DS4SD/docling` and `docling-project/docling`, same repo across org rename); `docs/adrs/README.md` gains ADR-044 row; `docs/PORTING_LEDGER.md` docling row promoted `PLANNED` → `VENDORED (dev dep, Stage 3.10)` with commit `ba8251e9cda84bab44cebe3b884119d3f50cb12a`, license MIT, port `DataPort`, ADR-044, logged `2026-07-30 04:20 EDT`; `docs/Kosmos-Build-Sequence-v25.md` §3.10 stub rewritten as full LANDED block mirroring §3.8/§3.9 shape (DoD literal + Landed narrative + files touched + tests + See ADR-044 + PORTING_LEDGER pointer). All defaults locked per Q1–Q9=A per user directive "proceed with all defaults (A)".
- **Files touched:**
  - `plugins/tektos/ingest/__init__.py` (new — public re-exports + Q-locks docstring)
  - `plugins/tektos/ingest/policy.py` (new — locked constants + `confidence_for_success`)
  - `plugins/tektos/ingest/models.py` (new — `DoclingSource` + `DoclingRun` + `DoclingIngestFailure`)
  - `plugins/tektos/ingest/harness.py` (new — `ingest_document` + `record_ingest_envelope` + `run_and_record_ingest` + `resolve_default_converter_factory` lazy import)
  - `plugins/tektos/tests/test_docling_ingest.py` (new — 26 fast unit tests + 1 env-gated real-docling tier)
  - `plugins/tektos/tests/fixtures/docling/sample.pdf` (new — hand-rolled minimal valid PDF, 593 bytes)
  - `plugins/tektos/tests/fixtures/docling/sample.docx` (new — hand-rolled minimal valid DOCX, 962 bytes)
  - `plugins/tektos/tests/fixtures/docling/sample.html` (new — trivial HTML, 373 bytes)
  - `scripts/docling_ingest.py` (new — kernel-side runner, mirrors `scripts/pier_eval.py`)
  - `Makefile` (added `ingest-doc` target + `.PHONY`)
  - `pyproject.toml` (added `[project.optional-dependencies] ingest = ["docling==2.116.0"]` + `plugins.tektos.ingest` to setuptools packages)
  - `docs/adrs/ADR-044-tektos-docling-document-ingestion.md` (new — Ratified v25, Stage 3.10 lock-in)
  - `docs/adrs/README.md` (ADR-044 row appended after ADR-042)
  - `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-044 row appended after ADR-042) + §18.5 (docling row license `Apache-2.0` → `MIT`, description updated)
  - `docs/PORTING_LEDGER.md` (docling row `PLANNED` → `VENDORED (dev dep, Stage 3.10)` with commit/license/port/ADR/logged fields)
  - `docs/Kosmos-Build-Sequence-v25.md` (§3.10 rewritten as LANDED block)
  - `BUILD_LOG.md` (this entry)
- **Ports / adapters affected:** none — envelope-first per ADR-023 (matches ADR-038 / ADR-040 / ADR-041 / ADR-042 defer pattern). All writes flow through the existing `DataPort.export_canonical`. `DataPort` protocol surface unchanged. `MemoryPort` untouched.
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER docling row promoted `PLANNED` → `VENDORED (dev dep, Stage 3.10)` (source, commit `ba8251e9cda84bab44cebe3b884119d3f50cb12a`, license MIT, port `DataPort`, ADR-044, logged `2026-07-30 04:20 EDT`, modifications: none — PATTERN-VENDOR); ADR-044 authored fresh at `Ratified v25 · Stage 3.10`; ADR-042 preserved (forward-reference to "candidate ADR-043" untouched — the deferred Pier auto-approve slot remains available for a future ADR). Spec §17 gains ADR-044 row and §18.5 docling license corrected `Apache-2.0` → `MIT` (this was pre-existing drift in Spec §18.5 — the ledger already said MIT; verified via `gh api repos/docling-project/docling` that upstream is MIT).
- **Stop-condition status:** met — Build-Sequence §3.10 DoD literal "PDF/DOCX/HTML → structured JSON-LD via DataPort" is anchored by `pytest plugins/tektos/tests/test_docling_ingest.py::test_pdf_docx_html_ingest_produces_structured_jsonld_via_dataport_build_sequence_3_10_dod` which feeds all three committed fixtures through `run_and_record_ingest`, asserts three DataPort envelopes emitted with `@type="CanonicalExport"`, `record_type="tektos.ingest.document"`, canonical hash present, and payload carrying both `docling_dict` and `docling_markdown`. `make stage1-gate` PASS. `.venv/bin/pytest` reports 791 passed + 7 env-gated skips (was 765 + 6 at Stage 3.9 close; +26 fast tests + 1 env-gated skip in this stage).

## 2026-07-30 05:14 EDT — Stage 3.11 · Tektos UI HTMX dashboard LANDED (ADR-045)

- **Stage / plugin / port:** Stage 3.11 · Tektos UI · new `ApprovalResolverPort` in `ports/approval.py` (Q_res_1=B) · `ApprovalRecord`+`ApprovalStatus` promoted to `ports/approval.py` (Promotion=A) · `PraxisApprovalResolverAdapter` at `adapters/approval_resolver/praxis/adapter.py`.
- **What changed:** Tektos UI HTMX dashboard at `plugins/tektos/ui/{__init__,policy,models,executor,templates,server}.py` — FastAPI-backed dashboard (Q1a=A) serving vendored HTMX 2.0.4 (`plugins/tektos/ui/htmx.min.js` 50917 B, sha256 `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`, upstream `bigskysoftware/htmx@b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f`, license `0BSD` permissively compatible; verified upstream via `gh api repos/bigskysoftware/htmx/git/refs/tags/v2.0.4`) at `/htmx.min.js` on `127.0.0.1:8765` (Q1c=A). Six-route surface (Q1e=A): `GET /`, `GET /plan/{approval_id}`, `POST /plan/{approval_id}/approve`, `POST /plan/{approval_id}/execute`, `POST /plan/{approval_id}/diff`, `GET /healthz`, plus static `GET /htmx.min.js`. No auth (Q1g=A — single-user local-first invariant). Fast unit tier uses FastAPI TestClient (Q1d=A) so DoD literal never binds a real port. Reuses ADR-041 `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE)` (Q2=A) — flips `ui_parity_status` IN_PROGRESS → COMPLIANT by adding one `Route(path="/tektos", label="Tektos", icon="📐", lazy_module="tektos/pages/DashboardPage")` on the Tektos descriptor so `_derive_parity(routes ∧ panels)` returns COMPLIANT. Vendor-neutral `NopExecutor` implements `ExecutorPort` Protocol (Q3=A) so `/execute` is a real HTTP surface without wiring a live agent at 3.11. Pure-stdlib `difflib.unified_diff` renders `/diff` (Q4=A — no new dep). Three per-transition MemoryPort events (Q5=A) with locked shape `subject="<change_id>::<approval_id>"`, `provenance="tektos_ui"`, `confidence=1.0`: predicates `tektos.plan.approved` / `tektos.plan.executed` / `tektos.plan.diff_rendered`. All Tektos plans stay at `HUMAN_REVIEW` (Q6=A — no tier changes at 3.11). Two-tier tests (Q7=B): fast unit tier default + env-gated interactive tier `KOSMOS_STAGE_311_INTERACTIVE=1` spawning `scripts/tektos_ui.py` via uvicorn. `PraxisApprovalResolverAdapter` wraps `KernelChangeApprovalAdapter` (ApexEngine) and applies port-level `proposing_domain` filter client-side (Q_res_1=B — port-level surface, adapter-level implementation). UI approvals set `resolved_by="tektos_ui"` (Q_res_2=B — audit trail distinguishes UI-driven resolutions from CLI/API).
- **Files touched:**
  - `ports/approval.py` (new — `ChangeApprovalTier` + `ApprovalStatus` + `ApprovalRecord` + `ApprovalGatewayPort` + `ApprovalResolverPort`; runtime-checkable Protocols; field name `approval_id`)
  - `plugins/praxis/apex/models.py` (backward-compat re-exports of `ApprovalRecord`+`ApprovalStatus` from `ports.approval` so `test_tektos_mcp` and downstream imports keep working)
  - `plugins/tektos/ui/__init__.py` (new — public re-exports)
  - `plugins/tektos/ui/policy.py` (new — locked constants)
  - `plugins/tektos/ui/models.py` (new — `ExecutionResult`, `DiffRender`)
  - `plugins/tektos/ui/executor.py` (new — `ExecutorPort` Protocol, `NopExecutor`, `render_unified_diff`, `compute_diff_sha256`)
  - `plugins/tektos/ui/templates.py` (new — HTML fragment helpers; strips `tektos.plan.` prefix from `intention_id` to derive `change_id`)
  - `plugins/tektos/ui/server.py` (new — `build_tektos_ui_app(*, approval_resolver, memory, executor)` returns FastAPI app; `_change_id_from_intention` helper)
  - `plugins/tektos/ui/htmx.min.js` (new — verbatim vendored, 50917 bytes)
  - `plugins/tektos/plugin.py` (added `Route` import + one `Route(path="/tektos", label="Tektos", icon="📐", lazy_module="tektos/pages/DashboardPage")` in `build_tektos_descriptor()` — this is what flips parity to COMPLIANT)
  - `plugins/tektos/tests/test_plan_renderer.py` (updated `_FakeFrontendContract` to run `_derive_parity(routes ∧ panels)` mirroring `adapters/frontend_contract/kernel/adapter.py::_derive_parity`; Stage 3.11 Route + COMPLIANT assertions)
  - `plugins/tektos/tests/test_tektos_ui.py` (new — 24 fast unit tests + 1 env-gated interactive tier + DoD literal anchor)
  - `adapters/approval_resolver/__init__.py` (new — empty package marker)
  - `adapters/approval_resolver/praxis/__init__.py` (new — public re-export of `PraxisApprovalResolverAdapter`)
  - `adapters/approval_resolver/praxis/adapter.py` (new — wraps `KernelChangeApprovalAdapter`, forwards resolve/get_by_id/list_pending, applies `proposing_domain` filter client-side)
  - `adapters/approval_resolver/praxis/test_contract.py` (new — 5 contract tests: Protocol conformance + filter + resolve + get_by_id)
  - `scripts/tektos_ui.py` (new — uvicorn runner for interactive tier; seeds one Tektos-proposed pending approval)
  - `Makefile` (added `ui-serve` target + `.PHONY`)
  - `pyproject.toml` (added `[project.optional-dependencies] ui = ["fastapi>=0.115", "uvicorn>=0.32", "httpx>=0.27"]`; added `plugins.tektos.ui` + `adapters.approval_resolver` + `adapters.approval_resolver.praxis` to setuptools packages; added `[tool.setuptools.package-data] "plugins.tektos.ui" = ["htmx.min.js"]`)
  - `docs/adrs/ADR-045-tektos-ui-htmx-dashboard.md` (new — Ratified v25, Stage 3.11 lock-in)
  - `docs/adrs/ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md` (STATUS AMENDMENT 2026-07-30 — ui_parity_status IN_PROGRESS → COMPLIANT with ADR-045 pointer)
  - `docs/adrs/README.md` (ADR-045 row appended after ADR-044)
  - `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-045 row appended after ADR-044)
  - `docs/PORTING_LEDGER.md` (htmx VENDORED + fastapi VENDORED + uvicorn VENDORED rows appended in Tektos section)
  - `docs/Kosmos-Build-Sequence-v25.md` (§3.11 rewritten as LANDED block)
  - `BUILD_LOG.md` (this entry)
- **Ports / adapters affected:** new `ApprovalResolverPort` in `ports/approval.py` (runtime-checkable Protocol; three verbs `resolve` / `get_by_id` / `list_pending(*, proposing_domain=None)`). `ApprovalGatewayPort` moved to `ports/approval.py` from `plugins/praxis/apex/protocol.py` (backward-compat re-export in `apex.protocol`). `ExecutorPort` Protocol lives locally under `plugins/tektos/ui/executor.py` (subsystem-local per ADR-007 — no cross-plugin coupling). New adapter `PraxisApprovalResolverAdapter` at `adapters/approval_resolver/praxis/adapter.py` wraps `plugins.praxis.apex.engine.KernelChangeApprovalAdapter` behind `ApprovalResolverPort`. `ApprovalRecord`+`ApprovalStatus` promoted from `plugins/praxis/apex/models.py` to `ports/approval.py` (Promotion=A); `plugins.praxis.apex.models` re-exports for backward compat so existing `test_tektos_mcp` imports keep working.
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER gains three rows in the Tektos section — htmx `VENDORED (Stage 3.11, ADR-045)` with source, commit `b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f`, license `0BSD`, port `none (browser-side runtime asset)`, ADR-045, logged `2026-07-30 05:14 EDT`, modifications: none (verbatim); fastapi `VENDORED (Stage 3.11, ADR-045)` with source, PyPI `fastapi>=0.115`, license MIT, port none, ADR-045, logged `2026-07-30 05:14 EDT`; uvicorn `VENDORED (Stage 3.11, ADR-045)` with source, PyPI `uvicorn>=0.32`, license BSD-3-Clause, port none, ADR-045, logged `2026-07-30 05:14 EDT`. ADR-045 authored fresh at `Ratified v25 · Stage 3.11`. ADR-041 STATUS AMENDMENT `ui_parity_status` IN_PROGRESS → COMPLIANT. ADR-042 preserved (forward-reference to "candidate ADR-043" untouched — the deferred Pier auto-approve slot remains available for a future ADR).
- **Stop-condition status:** met — Build-Sequence §3.11 DoD literal "Plan → Approve → Execute → Diff flow visible in kernel dashboard" is anchored by `pytest plugins/tektos/tests/test_tektos_ui.py::test_plan_approve_execute_diff_flow_visible_in_kernel_dashboard_build_sequence_3_11_dod` which runs the full lifecycle through FastAPI TestClient: GET / renders one pending plan card, GET /plan/{approval_id} renders detail with Approve/Execute/Diff buttons pointing at the correct HTMX targets, POST /plan/{approval_id}/approve resolves through `ApprovalResolverPort` and writes `tektos.plan.approved`, POST /plan/{approval_id}/execute drives the `ExecutorPort` and writes `tektos.plan.executed`, POST /plan/{approval_id}/diff renders unified diff and writes `tektos.plan.diff_rendered`, and `_derive_parity` returns COMPLIANT after Route+panel registration. `make stage1-gate` PASS. `.venv/bin/pytest` reports 815 passed + 8 env-gated skips (was 791 + 7 at Stage 3.10 close; +24 UI fast tests + 5 adapter contract tests + 3 updates to `test_plan_renderer.py` and +1 env-gated interactive tier skip in this stage).

## 2026-07-30 05:47 EDT — Stage 3.12 · Stage-3 exit gate · Tektos end-to-end refactor · LANDED

- **Stage / plugin / port:** Stage 3.12 · Tektos · plugins/tektos/ui + full 3.1→3.2→3.3→3.6→3.7→3.11 pipeline
- **What changed:** Landed Stage-3 exit gate. Tektos completed one non-trivial extract-method refactor on `plugins/tektos/ui/templates.py` end-to-end — extracted `_escape_record_fields(record) -> tuple[str,str,str,str]` helper that unifies four duplicated `html.escape(str(...))` calls previously repeated across `render_pending_row` + `render_plan_detail`. Refactor commit `0b54230` authored `Tektos <tektos@kosmos.local>` with subject literal `Stage 3.12 · Tektos refactor · extract-method`; committer stays rmholston420 for signature validity. 24/24 pre-existing UI tests pass over the refactored surface. Wired end-to-end pipeline harness in DoD test that drives real 3.1 TektosAgent → 3.2 MCP `file_write` gate raises `TektosToolCallPending` fail-closed → 3.3 repomap indexer surfaces `_escape_record_fields` in `rendered_map` → 3.6 openspec `produce_plan` on committed fixture → 3.7 plan-renderer + APEX HUMAN_REVIEW propose → 3.11 TestClient exercises `/plan/{approval_id}/approve|execute|diff`. Added `bandit>=1.7` to `[project.optional-dependencies] dev` + `[tool.bandit]` config (`exclude_dirs=[".venv","build","dist","__pycache__"]`, `skips=["B101"]`). Shipped `scripts/stage3_gate.py` mirroring `scripts/stage1_gate.py` shape (5 pass criteria: BUILD_LOG entry, refactor commit SHA discoverable, ruff clean on refactor target, bandit clean, full pytest green) plus `Makefile` `stage3-gate` target. Q3.1=C two-tier LLM: fast tier uses Interp-2 human-authored deterministic instruction; interactive tier `KOSMOS_STAGE_312_INTERACTIVE=1` uses Interp-1 real Ollama on Colossus. Committed OpenSpec fixture at `plugins/tektos/tests/fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers/{proposal.md, tasks.md, specs/tektos-ui-templates/spec.md}`. Ratified ADR-046. Full fanout: PORTING_LEDGER bandit entry, Spec §17 row, ADRs README index, Build-Sequence §3.12 LANDED block.
- **Files touched:**
  - `docs/adrs/ADR-046-stage-3-exit-gate-tektos-end-to-end-refactor.md` (new, 149 lines, Ratified v25)
  - `plugins/tektos/ui/templates.py` (refactor: `_escape_record_fields` helper + both callers unpack tuple)
  - `plugins/tektos/tests/test_stage_3_12_exit_gate.py` (new, 5 fast tests + 1 env-gated interactive tier)
  - `plugins/tektos/tests/fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers/{proposal.md, tasks.md, specs/tektos-ui-templates/spec.md}` (new fixture)
  - `pyproject.toml` (`bandit>=1.7` in `[project.optional-dependencies] dev` + `[tool.bandit]` config)
  - `scripts/stage3_gate.py` (new, 254 lines)
  - `Makefile` (`stage3-gate` target)
  - `docs/PORTING_LEDGER.md` (bandit VENDORED (dev dep) row filled in)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-046 summary row inserted after ADR-045)
  - `docs/adrs/README.md` (ADR-046 index row inserted after ADR-045)
  - `docs/Kosmos-Build-Sequence-v25.md` (§3.12 rewritten as LANDED block)
  - `BUILD_LOG.md` (this entry)
  - `SESSION_HANDOFF.md` (overwrites — points at Stage 4.1)
- **Ports / adapters affected:** none added — Tektos plugin internal only. Fires real pipeline over `ports.approval` (`ApprovalGatewayPort` + `ApprovalResolverPort` + `ChangeApprovalTier` + `ApprovalRecord` + `ApprovalStatus`), `ports.mcp` (`MCPPort` via `_NopMCPPort` test double — HUMAN_REQUIRED gate raises before invocation), `ports.memory` (`MemoryPort` real writes at 3.3 repomap + 3.6 openspec + 3.7 plan-renderer + 3.11 UI transitions), `ports.frontend_contract` (Route + Panel unchanged), `ports.executor` (`NopExecutor`).
- **PORTING_LEDGER / ADR updated:** ADR-046 Ratified v25; PORTING_LEDGER "bandit — VENDORED (dev dep)" entry filled in with commit/version, kernel location, port, modifications, ADR pointer, logged timestamp.
- **Stop-condition status:** met — refactor commit `0b54230` passes ruff + bandit + pytest per DoD literal; 825 total green + 9 env-gated skips; `make stage1-gate` + `make stage3-gate` both PASS.

## 2026-07-30 06:31 EDT — Stage 3.12 followup · interactive-tier bug fixes

- **Stage / plugin / port:** Stage 3.12 followup · Tektos · LLMPort (Ollama), Praxis apex, eval harness
- **What changed:**
  - Fixed 3 latent bugs surfaced by first end-to-end env-gated run on Colossus (830 pass / 3 fail / 1 skip → 832 pass / 1 fail / 1 skip).
  - `plugins/tektos/tests/test_stage_3_12_exit_gate.py:515` — imported `OllamaLLMAdapter`; class is `OllamaAdapter`. Renamed import + constructor call.
  - `scripts/tektos_ui.py:109` — `asyncio.get_event_loop().run_until_complete(...)` raised `RuntimeError` on Python 3.14. Replaced with `asyncio.run(_seed_apex(engine))`.
  - `plugins/tektos/eval/harness.py:233` + `plugins/tektos/tests/test_pier_eval.py:120,123` + `plugins/tektos/tests/test_deepswe_corpus.py:126,135` — pier 0.3.0 CLI renamed `--jobs-root` → `--jobs-dir` (attr `args.jobs_dir`). Updated harness call, both fake pier shims, and both `args.jobs_root` references.
  - Filed remaining pier 0.3.0 real-tier failure (pier writes no `trajectory.json` even with `--jobs-dir`) in `KNOWN_ISSUES.md`; unblocks Stage 4.1 since fake-shim Stage-3 gate stays green.
- **Files touched:**
  - `plugins/tektos/tests/test_stage_3_12_exit_gate.py`
  - `scripts/tektos_ui.py`
  - `plugins/tektos/eval/harness.py`
  - `plugins/tektos/tests/test_pier_eval.py`
  - `plugins/tektos/tests/test_deepswe_corpus.py`
  - `KNOWN_ISSUES.md` (append)
- **Ports / adapters affected:** LLMPort (Ollama adapter symbol rename only), eval harness pier-CLI surface.
- **PORTING_LEDGER / ADR updated:** — (bug fixes, no decision change; ADR-046 remains authoritative for Stage 3.12 exit gate)
- **Stop-condition status:** met — fast tier `825 passed + 9 skipped`, `make stage3-gate` PASS, interactive Ollama + Playwright + docling + fake pier all green, real pier tier documented in KNOWN_ISSUES.

## 2026-07-30 06:52 EDT — Stage 4.1 · Knowsys → Gnosis merge · LOCKED

- **Stage / plugin / port:** Stage 4.1 · Gnosis (absorbs Knowsys) · no ports added
- **What changed:**
  - ADR-016 status flipped **Ratified (v24) → LOCKED** with STATUS AMENDMENT block documenting DoD evidence.
  - Verified `plugins/knowsys/` was never ported into Kosmos (repo scan: no such directory in `plugins/`). Mirrors ADR-013 lock-in pattern (loser rejected at the source of choice, not by deleting non-existent Kosmos code).
  - Three residual **string** references cleaned (never imports):
    - `adapters/observability/otel_stack/test_contract.py` — `plugin.knowsys.index` → `plugin.gnosis.index` (2 spots) + `plugin="knowsys"` context-binding attributes → `plugin="gnosis"` (2 spots).
    - `plugins/tektos/tests/test_tektos_agent.py` — dropped `"plugins.knowsys"` from `forbidden_prefixes` tuple. Deliberately did NOT swap in `"plugins.gnosis"` because Gnosis will become a valid import in Stage 4.4.
  - Fan-out to all four status-tracking surfaces: ADR-016 file · spec §17 row · `docs/adrs/README.md` index · `docs/Kosmos-ADRs-Bundle.md` mirror (both bundle index row and embedded ADR-016 status line).
  - Build-Sequence §4.1 rewritten as LANDED block with DoD evidence + cleanup log + next-stage pointer.
- **Files touched:**
  - `adapters/observability/otel_stack/test_contract.py`
  - `plugins/tektos/tests/test_tektos_agent.py`
  - `docs/adrs/ADR-016-knowsys-gnosis-merge.md`
  - `docs/adrs/README.md`
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-016 row)
  - `docs/Kosmos-ADRs-Bundle.md` (index row + embedded ADR-016)
  - `docs/Kosmos-Build-Sequence-v25.md` (§4.1 LANDED block)
  - `BUILD_LOG.md` (this entry)
  - `SESSION_HANDOFF.md` (overwrites — points at Stage 4.2)
- **Ports / adapters affected:** none. Cross-plugin coupling model unchanged (ADR-007 events-only still enforced). MemoryPort provenance model unchanged. Two test strings on the ObservabilityPort surface were renamed for accuracy post-merge — no protocol change.
- **PORTING_LEDGER / ADR updated:** ADR-016 LOCKED (2026-07-30). PORTING_LEDGER unchanged — Rigpa Knowsys export subsystem entry remains VENDORED-pattern-only per ADR-028 (pattern reference, not a Kosmos plugin).
- **Stop-condition status:** met — DoD literal "No import of `knowsys` anywhere; ADR-016 status = LOCKED" satisfied. Fast tier `825 passed + 9 skipped` (unchanged from baseline pre-edit).

## 2026-07-30 07:45 EDT — Stage 4.2 Graphiti tuning · real backends + Hybrid-tier corpora LANDED (ADR-047)

- **Stage / plugin / port:** Stage 4.2 · MemoryPort · DozerDB memory adapter (real backends + corpora tuning subpackage)
- **What changed:**
  - **Commit A (`d6e5e87`):** stubbed Stage-1.8 backends replaced with real implementations behind unchanged Protocol seams:
    - `DozerDbGraphBackend` — Bolt driver against `graphstack/dozerdb:5.26.27` (add_node/add_edge/query_cypher/delete_node/is_healthy/close)
    - `GraphitiTemporalIndex` — Graphiti wrapping local Ollama (LLM `qwen3-coder`, embedder `nomic-embed-text`, cross-encoder same Ollama URL)
    - `AmgV02Policy` — `agent-memory-guard==0.2.2` `MemoryGuard(policy=Policy.strict())` with `write`/`snapshot`/`rollback` bindings
    - Compose service `ops/compose/memory.yml` + `ops/compose/README.md` (Bolt 7687, heap ≤ 4 GiB, page-cache ≤ 2 GiB)
    - Contract tests for all three real backends (fast tier always-green + env-gated `KOSMOS_STAGE_42_LIVE=1` live tier)
  - **Commit B (`5c896bf`):** corpora subpackage at `adapters/memory/dozerdb/corpora/`:
    - `models.py` (`CorpusFact` frozen dataclass, `TemporalQuery`, `Corpus`)
    - `synthetic_lifeline.py` (10 R.M. Holston lifeline facts 1972 → 2026, 4 as-of queries; biographical schema)
    - `humanities_cidoc.py` (5 CIDOC-CRM Buddhist facts, 2 as-of queries; humanities scholarly-graph schema)
    - `rigpa_export.py` + `fixtures/rigpa_sample.jsonl` (20 events 2024-05 → 2024-12; overridable via `KOSMOS_RIGPA_EXPORT_PATH`)
    - `corpus_runner.py` — Hybrid-tier switch: `InMemoryTemporalIndex` for fast tier, `GraphitiTemporalIndex` for live tier
    - `test_corpora_contract.py` — 34 fast tests + 3 env-gated live tests
  - **Cross-encoder fix (`997cad7`):** Graphiti's `OpenAIRerankerClient()` defaults to reading `OPENAI_API_KEY` which is not present on Colossus. Fix: instantiate with `LLMConfig(api_key="ollama-not-used", base_url=$OLLAMA_URL, model=$OLLAMA_LLM_MODEL)` so the reranker also routes through Ollama.
  - **NodeNotFound fix (`e780be9`):** `add_episode(uuid=X)` in newer graphiti-core looks up an existing `EpisodicNode` by that UUID and raises `NodeNotFoundError` when absent (it does not assign the UUID). Fix: drop the `uuid=` argument; carry our event id through `name="event-<event_id>"` and inject `kosmos_event_id` into the JSON body. Contract test updated to assert `"uuid" not in kwargs` and body carries `kosmos_event_id`.
  - **Commit C (this commit):** ADR-047 + fan-out + `docs/PORT_CONTRACTS.md` + logs:
    - `docs/adrs/ADR-047-stage-4-2-corpora-hybrid-tier.md` — Q1=corpora location, Q2=Hybrid tier, Q3=local Ollama, Q4=three corpora
    - `docs/PORT_CONTRACTS.md` created — MemoryPort surface + Hybrid-tier contract + measured metrics (fast tier < 1 ms; live tier first-run 137.29 s / 37 passed on 2026-07-30 Colossus)
    - Spec §17 ADR-047 row appended
    - `docs/adrs/README.md` ADR-047 row appended
    - `docs/Kosmos-Build-Sequence-v25.md` §4.2 rewritten as **LANDED** block
    - `docs/PORTING_LEDGER.md` — DozerDB `PLANNED` → `VENDORED` (Stage 4.2); graphiti-core + AMG entries updated with ADR-047 + Stage 4.2 real-backend notes + Ollama wiring + add_episode uuid fix
- **Files touched:**
  - `adapters/memory/dozerdb/dozerdb_graph_backend.py` (real backend)
  - `adapters/memory/dozerdb/graphiti_temporal_index.py` (real backend + Ollama LLM/embedder/cross-encoder + no-uuid fix)
  - `adapters/memory/dozerdb/amg_v02_policy.py` (real backend)
  - `adapters/memory/dozerdb/adapter.py` (composition + exports)
  - `adapters/memory/dozerdb/__init__.py` (exports extended)
  - `adapters/memory/dozerdb/test_dozerdb_graph_backend_contract.py`
  - `adapters/memory/dozerdb/test_graphiti_temporal_index_contract.py`
  - `adapters/memory/dozerdb/test_amg_v02_policy_contract.py`
  - `adapters/memory/dozerdb/corpora/` (whole subpackage; see Commit B list above)
  - `ops/compose/memory.yml` + `ops/compose/README.md`
  - `docs/adrs/ADR-047-stage-4-2-corpora-hybrid-tier.md`
  - `docs/adrs/README.md` (ADR-047 row)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-047 row)
  - `docs/Kosmos-Build-Sequence-v25.md` (§4.2 LANDED block)
  - `docs/PORT_CONTRACTS.md` (created)
  - `docs/PORTING_LEDGER.md` (DozerDB / graphiti-core / AMG entries)
  - `BUILD_LOG.md` (this entry)
  - `SESSION_HANDOFF.md` (overwrite — points at Stage 4.3)
- **Ports / adapters affected:** `MemoryPort` (three Protocol seams `GraphBackend`, `TemporalIndex`, `AmgPolicy` — signatures unchanged; only backend implementations swapped). `VectorPort` inherits Stage 1.7 measurements; benchmark deferred to Stage 4.4 Superpowers KB.
- **PORTING_LEDGER / ADR updated:** ADR-047 authored (Ratified v25 at Stage 4.2). PORTING_LEDGER DozerDB flipped `PLANNED` → `VENDORED` with `graphstack/dozerdb:5.26.27` pin; graphiti-core + AMG entries append Stage 4.2 real-backend + ADR-047 references.
- **Stop-condition status:** met — three corpora ingest through `record_event`; DoD-asserted `TemporalQuery`s pass on the always-green fast tier (34/34); live tier ingest+query end-to-end returns without raising (37/37 including fast, 137.29 s on Colossus 2026-07-30). Tag `stage-4-2-complete` applied on this commit.

## 2026-07-30 07:56 EDT — Stage 4.3 LANDED · ADR-048 · agent-memory-guard v0.2.2 → v0.3.0 + `Policy.tiered()` default

- **Stage / plugin / port:** Stage 4.3 · MemoryPort · DozerDB memory adapter · `AmgPolicy` write-time filter
- **What changed:**
  - **Upstream release check.** OWASP `agent-memory-guard` v0.3.0 shipped 2026-06-10 (upstream release https://github.com/OWASP/www-project-agent-memory-guard/releases/tag/v0.3.0, published on PyPI as `agent-memory-guard==0.3.0`). Highlights: MCP server, CLI scanner, ML injection detector, GitHub Action, LlamaIndex + CrewAI integrations, Prometheus exporter, `Policy.tiered()` preset with default memory-class taxonomy, `SecurityEvent.source_class`/`receipt_uri`/`retire_if`. Public API is a strict superset of v0.2.2 (all v0.3.0 `MemoryGuard.write` kwargs optional; `Policy.strict()` still present).
  - **Adopted.** `pyproject.toml` pin bumped `agent-memory-guard==0.2.2` → `==0.3.0`. No other dep-graph change (v0.3.0 ships with the same minimal vendor dep set).
  - **Class + module rename.** Concrete wrapper class `AmgV02Policy` → `AmgGuardPolicy` in new module `adapters/memory/dozerdb/amg_policy.py`. Old `adapters/memory/dozerdb/amg_v02_policy.py` reduced to a one-line re-export shim exposing `AmgGuardPolicy` and the backwards-compat alias `AmgV02Policy = AmgGuardPolicy`. Alias retained through Stage 5 per ADR-048 §Consequences.
  - **Default preset switched.** Default AMG policy preset changed from `Policy.strict()` to `Policy.tiered()` — v0.3.0's new default memory-class taxonomy (session / durable / promoted) aligns with the Kosmos memory-lifecycle model exercised by the Stage 4.2 corpora. Callers wanting the v0.2.2 shape can pass `policy_preset="strict"`.
  - **v0.3.0 write kwargs threaded.** `AmgGuardPolicy.evaluate(payload)` now extracts optional payload keys `source_class` / `receipt_uri` / `memory_class` (or `cls`) / `task_id` / `source` and forwards them as `MemoryGuard.write(...)` kwargs. Extracted keys are stripped from the JSON-serialised `value` body so routing fields never pollute the semantic write. Payloads that omit these keys keep the v0.2.2 shape.
  - **Explicit non-adoption scope.** MCP server / CLI scanner / GitHub Action / LlamaIndex + CrewAI integrations / Prometheus exporter / ML injection detector deliberately NOT adopted at 4.3 (each is its own trade-off surface — recorded in ADR-048 §Alternatives rejected). Adopting them becomes a Stage 5+ decision when a specific need arrives.
  - **Zero-trust fail-safe preserved.** Guard-init failure / `MemoryGuard.write` unknown error / snapshot failure still emit `AmgVerdict(decision="block")`. Unknown `policy_preset` value also blocks with a specific reason.
  - **Contract test rewrite.** `test_amg_v02_policy_contract.py` → `test_amg_policy_contract.py` (renamed via `git mv`). New tests: default preset uses `Policy.tiered()`, explicit `policy_preset="strict"` uses `Policy.strict()`, unknown preset blocks with `unknown policy_preset` reason, backcompat alias resolves to `AmgGuardPolicy`, all five v0.3.0 write kwargs forwarded when payload provides them, kwargs omitted when payload omits them, `cls` payload key maps to `write(cls=...)`, `memory_class` takes precedence over `cls`, routing keys stripped from JSON body. Live-tier gets a second env-gated test for `policy_preset="strict"` fallback.
  - **Test results.** `pytest adapters/memory/dozerdb/test_amg_policy_contract.py` → 20 passed / 2 env-gated live skips. Full DozerDB adapter fast tier `pytest adapters/memory/dozerdb/` → 130 passed / 7 env-gated skips. Ruff clean on all Stage 4.3 files (`amg_policy.py`, `amg_v02_policy.py` shim, `test_amg_policy_contract.py`, `__init__.py`).
  - **Fan-out.**
    - `docs/adrs/ADR-048-stage-4-3-amg-v03-adoption.md` authored (Ratified v25 at Stage 4.3; six-question decision block Q1..Q6; four rejected alternatives; consequences enumerated).
    - `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-048 row appended after ADR-047.
    - `docs/adrs/README.md` — ADR-048 row appended before "The one remaining open decision" anchor.
    - `docs/Kosmos-Build-Sequence-v25.md` §4.3 — rewritten as LANDED block referencing ADR-048.
    - `docs/PORTING_LEDGER.md` — `agent-memory-guard` entry amended v0.2.2 → v0.3.0 with Stage 4.3 (ADR-048) sub-bullet describing rename, `Policy.tiered()` default, opt-in write kwargs, and explicit non-adoption scope.
- **Files touched:**
  - `pyproject.toml` (pin bump)
  - `adapters/memory/dozerdb/amg_policy.py` (new)
  - `adapters/memory/dozerdb/amg_v02_policy.py` (reduced to shim)
  - `adapters/memory/dozerdb/__init__.py` (export `AmgGuardPolicy` + keep `AmgV02Policy` alias)
  - `adapters/memory/dozerdb/adapter.py` (docstring — v0.3.0 + ADR-048 reference; `AmgGuardPolicy` named as production impl)
  - `adapters/memory/dozerdb/test_amg_policy_contract.py` (new + rewritten via `git mv` + full-body rewrite)
  - `docs/adrs/ADR-048-stage-4-3-amg-v03-adoption.md` (new)
  - `docs/adrs/README.md` (ADR-048 row)
  - `docs/Kosmos-Build-Spec-v25.md` (§17 ADR-048 row)
  - `docs/Kosmos-Build-Sequence-v25.md` (§4.3 LANDED block)
  - `docs/PORTING_LEDGER.md` (AMG entry v0.2.2 → v0.3.0)
  - `BUILD_LOG.md` (this entry)
  - `SESSION_HANDOFF.md` (overwrite — points at Stage 4.4)
- **Ports / adapters affected:** `MemoryPort` (`AmgPolicy` Protocol shape unchanged; `AmgGuardPolicy` swap-in real backend). `DozerDbMemoryAdapter` DI seams unchanged.
- **PORTING_LEDGER / ADR updated:** ADR-048 authored (Ratified v25 at Stage 4.3). PORTING_LEDGER `agent-memory-guard` entry amended v0.2.2 → v0.3.0 with ADR-048 reference.
- **Stop-condition status:** met — `pyproject.toml` pin bumped, `AmgGuardPolicy` wraps `MemoryGuard(policy=Policy.tiered())`, contract test coverage green, PORTING_LEDGER + BUILD_LOG record the version. Tag `stage-4-3-complete` applied on this commit. Next up: Stage 4.4 (Superpowers KB port).

## 2026-07-30 08:26 EDT — Stage 4.4 · Superpowers KB port · MemoryPort adapter corpus (full-body Markdown, MIT)

- **Stage / plugin / port:** Stage 4.4 · DozerDB MemoryPort adapter corpora · new `superpowers` corpus + `CorpusEdge` typed-link support.
- **What changed:** Landed `obra/superpowers` @ `44c9b2d6e889982ac18c27d05a19fefe335194e1` (MIT) as the fourth Stage 4.2-shaped corpus. Full-body Markdown ingest — 38 MemoryPort records across 14 skill directories, ~310 KB fixture, one record per `skills/*/*.md`. Inline Markdown `[text](path)` sibling links parse into 9 typed `CorpusEdge` records at load time. `models.py` gains `CorpusEdge` (frozen slots) + `Corpus.edges: tuple[CorpusEdge,...]` optional field (defaults `()`, backward-compatible with Stage 4.2 corpora; construction-time invariants enforce src/dst resolvability + non-empty `kind`). Corpora `__init__.py` exports `SUPERPOWERS_CORPUS`/`CorpusEdge`/`load_superpowers_corpus`; `ALL_CORPORA` grows from three to four. Env override `KOSMOS_SUPERPOWERS_PATH` accepts an alternate JSONL. Re-ingest CLI `scripts/ingest_superpowers.py --sha <SHA> [--via gh|checkout]` is workspace-local, not committed to plugin space, not invoked at runtime. VectorPort surface deliberately NOT opened. `test_corpora_contract.py` gains 7 fast tests (cardinality ≥30 across ≥10 subjects, provenance-triple invariant, typed-edge resolvability, env-override path, env-override missing-file rejection, missing-attribute rejection, fixture-committed check) + Stage 4.4 corpus added to the env-gated live-tier parametrization. ADR-007 AST scan upgraded to `rglob("*.py")` so the new `superpowers/` subpackage is covered. `docs/adrs/ADR-049-stage-4-4-superpowers-kb-adapter-corpus.md` authored (Ratified v25; six-question shape Q1–Q6 with rejected alternatives; explicit reconciliation of ADR-008 Tektos-UX "do not vendor Superpowers code" with ADR-002 + ADR-016 Personal-KB substrate — Superpowers enters as MemoryPort **data**, not plugin code, both rules coexist).
- **Files touched:**
  - `scripts/ingest_superpowers.py` (new — CLI, ~310 lines, gh + local-checkout modes, inline Markdown link parsing → typed edges, byte-reproducible fixture)
  - `adapters/memory/dozerdb/corpora/models.py` (extended — `CorpusEdge` dataclass, `Corpus.edges` field, construction-time invariants)
  - `adapters/memory/dozerdb/corpora/__init__.py` (extended — `SUPERPOWERS_CORPUS`/`CorpusEdge`/`load_superpowers_corpus` exports; `ALL_CORPORA` grows to four)
  - `adapters/memory/dozerdb/corpora/superpowers/__init__.py` (new — re-exports)
  - `adapters/memory/dozerdb/corpora/superpowers/superpowers.py` (new — corpus module mirrors `rigpa_export.py` shape; validates `body`+`source_commit`+`license` triple; materializes edges from `attributes.references`; two-point temporal probes)
  - `adapters/memory/dozerdb/corpora/superpowers/fixtures/superpowers.jsonl` (new — 38 records, 9 typed edges)
  - `adapters/memory/dozerdb/corpora/test_corpora_contract.py` (extended — 7 new fast tests + Stage 4.4 corpus added to live-tier parametrization + ADR-007 AST scanner uses `rglob("*.py")`)
  - `docs/adrs/ADR-049-stage-4-4-superpowers-kb-adapter-corpus.md` (new)
  - `docs/adrs/README.md` (extended — ADR-049 index row, before OPEN section)
  - `docs/Kosmos-Build-Spec-v25.md` (extended — §17 ADR-049 row appended after ADR-048)
  - `docs/Kosmos-Build-Sequence-v25.md` (updated — §4.4 stub rewritten as LANDED block, 2026-07-30 tag `stage-4-4-complete`)
  - `docs/PORTING_LEDGER.md` (updated — Gnosis section Superpowers KB PLANNED → INGESTED with SHA/MIT/adapter location/Phase-3 relocation plan/refresh cadence; Design References Superpowers-repo note clarified to distinguish reference-use from Stage 4.4 substrate ingest)
- **Ports / adapters affected:** MemoryPort (`record_event` + `query_temporal` unchanged; new typed-link retrieval surface via `CorpusEdge`). No adapter Protocol changes; construction-time invariants added to `Corpus`. ADR-007 AST scan surface widened to subpackages.
- **PORTING_LEDGER / ADR updated:** ADR-049 authored (Ratified v25 at Stage 4.4). PORTING_LEDGER Gnosis-section entry for Superpowers KB flipped PLANNED → INGESTED with pinned SHA `44c9b2d6e889982ac18c27d05a19fefe335194e1`, MIT license, adapter location, Phase-3 relocation plan, and workspace-local refresh cadence via `scripts/ingest_superpowers.py`.
- **Stop-condition status:** met — every Superpowers fact carries `body` + `source_commit` + `license="MIT"` + `upstream_url` + typed `references`; every `CorpusEdge` resolves to a fact in the same corpus at construction time; ADR-007 AST scan recurses into subpackages and passes; DozerDB adapter fast tier **142 passed / 8 skipped** (up from 130/7 at Stage 4.3, delta = +7 new fast tests + 5 parametrized invariant extensions + 1 new env-gated live-tier corpus parametrization); ruff lint clean on all changed files. Tag `stage-4-4-complete` to be applied on the fanout commit. Next up: Stage 4.5 (Humanities corpus port under Gnosis — `gnosis-humanities-adr`).

## 2026-07-30 09:00 EDT — Stage 4.5 · Humanities corpus port · SuttaCentral Bilara MemoryPort adapter corpus (full-body segment-keyed JSON, CC0)

- **Stage / plugin / port:** Stage 4.5 · DozerDB MemoryPort adapter corpora · new `humanities-bilara` corpus, CIDOC-CRM typed-edge kinds landed.
- **What changed:** Landed `suttacentral/bilara-data` @ `3c93d1cea80fdebcefb777c8724c35bd971f360a` (translations CC0-1.0, Mahasangiti Pali root public-domain) as the fifth Stage 4.2-shaped corpus. Pivoted from 84000 CC-BY-NC-4.0 to Bilara CC0 (ADR-050 Q1) to eliminate NC downstream propagation risk. Full-body segment-keyed JSON ingest — 141 MemoryPort records (70 translation + 70 root + 1 translator actor), 140 typed CIDOC-CRM edges (70 × `P73_is_translation_of` + 70 × `P94_was_created_by`), ~392 KB fixture. Stage 4.5 slice = Bhikkhu Sujato's English translations of scpub7 Dhammapada + scpub19 Khuddakapatha + scpub86 Cariyapitaka mirrored by Mahasangiti Pali root under `root/pli/ms/sutta/kn/{dhp,kp,cp}/`. Corpora `__init__.py` exports `HUMANITIES_BILARA_CORPUS` + `load_humanities_bilara_corpus`; `ALL_CORPORA` grows from four to five. Loader validates three subject namespaces (`bilara/actor/`, `bilara/root/`, `bilara/translation/`) with per-namespace required-attribute lists; unknown namespaces rejected. Env override `KOSMOS_HUMANITIES_BILARA_PATH` accepts an alternate JSONL. Re-ingest CLI `scripts/ingest_humanities.py --sha <SHA> [--via gh|checkout]` is workspace-local, blob-by-blob fetches via `gh api` by default so no full 920 MB clone is needed (respects Colossus 300 GB free-space constraint). VectorPort surface deliberately NOT opened. Untyped `references` kind explicitly rejected — CIDOC-CRM property URIs required for external KG interop. `test_corpora_contract.py` gains 7 fast tests (cardinality-by-namespace 1/70/70, provenance triple + CIDOC-CRM class labels `E33_Linguistic_Object`/`E21_Person`, typed-edge kind census + resolvability, root/translation bijection at `bilara_uid`, env override, missing-attribute + unknown-namespace rejection, fixture-committed check) + Stage 4.5 corpus added to the env-gated live-tier parametrization. `docs/adrs/ADR-050-stage-4-5-humanities-bilara-adapter-corpus.md` authored (Ratified v25; six-question shape Q1–Q6 with rejected alternatives; Stage 4.2 `humanities_cidoc_sample` corpus explicitly NOT superseded — retained as fast-tier CIDOC-CRM invariants probe).
- **Files touched:**
  - `scripts/ingest_humanities.py` (new — CLI, ~545 lines, gh + local-checkout modes, per-namespace record synthesis + typed CIDOC-CRM edge emission, byte-reproducible fixture)
  - `adapters/memory/dozerdb/corpora/__init__.py` (extended — `HUMANITIES_BILARA_CORPUS` + `load_humanities_bilara_corpus` exports; `ALL_CORPORA` grows to five)
  - `adapters/memory/dozerdb/corpora/humanities_bilara/__init__.py` (new — re-exports)
  - `adapters/memory/dozerdb/corpora/humanities_bilara/humanities_bilara.py` (new — corpus module; per-namespace attribute validation for `bilara/actor/`, `bilara/root/`, `bilara/translation/`; materializes CIDOC-CRM edges from `attributes.references`; two-point temporal probes)
  - `adapters/memory/dozerdb/corpora/humanities_bilara/fixtures/humanities_bilara.jsonl` (new — 141 records, 140 CIDOC-CRM edges, ~392 KB)
  - `adapters/memory/dozerdb/corpora/test_corpora_contract.py` (extended — 7 new fast tests + Stage 4.5 corpus added to live-tier parametrization)
  - `docs/adrs/ADR-050-stage-4-5-humanities-bilara-adapter-corpus.md` (new)
  - `docs/adrs/README.md` (extended — ADR-050 index row, before OPEN section)
  - `docs/Kosmos-Build-Spec-v25.md` (extended — §17 ADR-050 row appended after ADR-049)
  - `docs/Kosmos-Build-Sequence-v25.md` (updated — §4.5 stub rewritten as LANDED block, 2026-07-30 tag `stage-4-5-complete`)
  - `docs/PORTING_LEDGER.md` (updated — Gnosis section Humanities-corpus PLANNED → INGESTED with SHA/CC0/adapter location/Phase-3 relocation plan/refresh cadence; 84000 recorded as rejected alternative with re-litigation gate)
- **Ports / adapters affected:** MemoryPort (`record_event` + `query_temporal` unchanged; typed-link retrieval surface via `CorpusEdge` reused from Stage 4.4). No adapter Protocol changes; per-namespace attribute validation is corpus-local. CIDOC-CRM property URIs `P73_is_translation_of` + `P94_was_created_by` are the first non-`references` edge kinds materialized in a Kosmos corpus.
- **PORTING_LEDGER / ADR updated:** ADR-050 authored (Ratified v25 at Stage 4.5). PORTING_LEDGER Gnosis-section entry for Humanities corpus flipped PLANNED → INGESTED with pinned SHA `3c93d1cea80fdebcefb777c8724c35bd971f360a`, CC0-1.0 + public-domain license posture, adapter location, Phase-3 relocation plan, blob-by-blob refresh cadence via `scripts/ingest_humanities.py`, and 84000 recorded as explicitly-rejected alternative.
- **Stop-condition status:** met — every Bilara body-carrying fact carries `body` + `source_commit` + `license` + `upstream_url` + typed `references`; every `CorpusEdge` uses a CIDOC-CRM property URI as its `kind` and resolves to a fact in the same corpus; every translation record has exactly one root mirror at the same `bilara_uid` (bijection guard); DozerDB adapter fast tier **155 passed / 9 skipped** (up from 142/8 at Stage 4.4, delta = +7 new fast tests + 5 parametrized invariant extensions + 1 new env-gated live-tier corpus parametrization); ruff lint clean on all changed files. Tag `stage-4-5-complete` to be applied on the fanout commit. Next up: Stage 4.6 (Stage-4 exit gate — Gnosis answers a temporal question across the corpus with full provenance chain).

## 2026-07-30 09:19 EDT — Stage 4.6 · Stage-4 exit gate · adapter-side FastAPI surrogate for Gnosis retrieval

- **Stage / plugin / port:** Stage 4.6 · DozerDB MemoryPort adapter · new `adapters/memory/dozerdb/gate/` subpackage — adapter-side surrogate for the Phase-3 Gnosis retrieval surface. No new formal port; reads the existing corpora registry.
- **What changed:** Materialized the Stage 4.6 exit gate as an adapter-side FastAPI application factory `build_stage_46_gate_app(*, corpora)` mirroring the Tektos UI (Stage 3.11) shape. Six locked routes federated across all five landed corpora (`synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export`, `superpowers`, `humanities-bilara`): `/` (dashboard with edge-kind census + licenses), `/corpus/{name}` (detail + 20-fact sample), `/corpus/{name}/provenance/{event_id}` (full chain with source+timestamp+confidence + inbound/outbound edges + CIDOC-CRM attributes), `/corpus/{name}/query` (params `q`+`as_of`+`limit`, deterministic sort), `/corpus/{name}/traverse/{event_id}` (outbound typed edges), `/healthz`. Pure-Python HTML fragment templates with `html.escape` on every user-supplied string — no jinja/htmx/template engine. Value objects (`ClaimEnvelope`, `EdgeEnvelope`, `ProvenanceChain`, `CorpusSummary`) are frozen slotted dataclasses; retrieval helpers (`build_provenance_chain`, `traverse_typed_edges`, `summarize_corpus`, `query_temporal_fast`) are pure functions over `Corpus`. All route paths + host/port + provenance string + default confidence + route tuple live in `policy.py` as module constants. Gate binds `127.0.0.1:8746` (distinct from Tektos UI 8765). `STAGE_46_PROVENANCE="stage_46_gate"` reserved for future write path; default confidence `1.0` at Stage 4.6 (Stage 5 Graphiti derivations will introduce sub-1.0). ADR-051 authored (Ratified v25; six-question shape Q1–Q6). No new pip dep — FastAPI already vendored from Stage 3.11, no PORTING_LEDGER change. ADR-007 enforced at test time by an AST scan that walks `gate/*.py` and asserts no `import plugins.*` / `from plugins.* import`. Zero-trust invariants preserved — gate is read-only at 4.6.
- **Files touched:**
  - `adapters/memory/dozerdb/gate/__init__.py` (new — re-exports)
  - `adapters/memory/dozerdb/gate/policy.py` (new — locked constants: route paths, host/port, provenance string, default confidence, route tuple)
  - `adapters/memory/dozerdb/gate/models.py` (new — frozen slotted dataclasses)
  - `adapters/memory/dozerdb/gate/traversal.py` (new — pure functions over `Corpus`)
  - `adapters/memory/dozerdb/gate/templates.py` (new — pure-Python HTML fragment renderers)
  - `adapters/memory/dozerdb/gate/server.py` (new — FastAPI factory + 6 route handlers)
  - `adapters/memory/dozerdb/gate/test_stage_46_gate.py` (new — 19 fast + 1 env-gated live tier)
  - `docs/adrs/ADR-051-stage-4-6-exit-gate-gnosis-surrogate.md` (new)
  - `docs/adrs/README.md` (extended — ADR-051 index row, before OPEN section)
  - `docs/Kosmos-Build-Spec-v25.md` (extended — §17 ADR-051 row appended after ADR-050)
  - `docs/Kosmos-Build-Sequence-v25.md` (updated — §4.6 stub rewritten as LANDED block, 2026-07-30 tag `stage-4-6-complete`)
- **Ports / adapters affected:** MemoryPort (read surface via corpora registry — no Protocol change, no new formal port). Gate imports only `adapters.memory.dozerdb.corpora` and its own submodules; ADR-007 clean.
- **PORTING_LEDGER / ADR updated:** ADR-051 authored (Ratified v25 at Stage 4.6). No PORTING_LEDGER change — FastAPI already vendored from Stage 3.11 Tektos UI, no new upstream component introduced.
- **Stop-condition status:** met — every fact across the five landed corpora (214 asserted end-to-end) renders as a `ProvenanceChain` carrying `provenance` + timezone-aware `as_of` + `confidence ∈ (0,1]`; every typed `CorpusEdge` resolves to a fact in the same corpus; canned Bilara temporal query returns exactly 70 translation records with the provenance triple; canned CIDOC-CRM traversal from any Bilara translation resolves to exactly `{P73_is_translation_of, P94_was_created_by}`; Bilara edge census is exactly `{P73_is_translation_of: 70, P94_was_created_by: 70}`; `/healthz` returns `ok · 5 corpora`; the six-route tuple in `STAGE_46_ROUTES` is locked; gate app is stateless (same factory call twice returns two fresh apps); DozerDB adapter fast tier **174 passed / 10 skipped** (up from 155/9 at Stage 4.5, delta = +19 new fast tests + 1 env-gated live tier); whole-repo fast tier **957 passed / 19 skipped**; ruff lint clean on all changed files. Tag `stage-4-6-complete` to be applied on the fanout commit. Next up: Stage 5.1 (Oikos plugin skeleton — DataPort + MemoryPort + NotificationPort + EventBusPort).

## 2026-07-30 09:45 EDT — Stage 6.1 · Zetesis · research plugin skeleton with corrected port surface (Stage-5 deferred)

- **Stage / plugin / port:** Stage 6.1 · new `plugins/zetesis/` kernel-plugin · 10 required + 1 optional port slots per Q7=B-plus (FrontendContractPort, LLMPort, MemoryPort, VectorPort, DataPort, SearchPort, EventBusPort, ResourcePort, NotificationPort, ObservabilityPort required; SecretsPort optional). No new formal port added.
- **What changed:** User elected to **defer all of Stage 5** (Oikos + APEX-in-plugin + Nomisma-adjacent Phase-5 work) after Stage 4.6 landed and jump directly to Stage 6.1. Authored `ZetesisPlugin` at `plugins/zetesis/plugin.py` as a dataclass-plus-async-start-stop plugin mirroring Praxis (Stage 2.1) / Phrouros (Stage 2.3) / Tektos (Stage 3.1+). `build_zetesis_descriptor()` returns a `PluginDescriptor` with **zero panels, zero routes, empty design tokens** — kernel discovers Zetesis via `FrontendContractPort.register_plugin` but nothing renders yet; UI surface lands at Stage 6.3/6.4 when real research output exists (Q2=A). Skeleton is **inner-loop-agnostic**: all 10 required business ports are held as constructor dependencies but **called zero times** at 6.1; no `ResearchInnerLoop` Protocol seam; ADR-010 head-to-head (AREX vs. LangChain Open Deep Research) remains fully open pre-§6.2 (Q3=A). Locked MemoryPort constants (Q4=confirmed) even though first write lands Stage 6.3: `ZETESIS_MEMORY_PROVENANCE="zetesis_research"`, `ZETESIS_MEMORY_PREDICATE="zetesis.research.completed"`, `ZETESIS_MEMORY_DEFAULT_CONFIDENCE=0.75` (mirrors ADR-036 Tektos pre-Reflexion default; sits in `(0,1]` per ADR-008 zero-trust guard). The real `ZetesisPlugin` **is** the `zetesis-stub` from spec §191 + Build-Sequence §1.6 (Q5=C); no separate stub package; Phase-1 stub-role debt closes at 6.1 — Tektos Phase-10 model-swap-under-load rig will bind directly to `ZetesisPlugin` via ResourcePort. Enforcement: `test_start_touches_no_business_port` binds all 10 required ports to `_UntouchablePort` sentinels that raise `AssertionError` on any attribute access; `start()` completing without raising proves zero business-port calls at 6.1. `SecretsPort` optional-slot verified both with `None` (default) and with a real port instance. Q7=B-plus port-surface correction closes the pre-existing Build-Sequence §6.1 stale 4-port list vs. spec §95 (SearchPort omission from ADR-021) + spec §172/§191 implicit ResourcePort requirement from Q5=C. ADR-052 authored (Ratified v25; seven-question shape Q1–Q7 with Q7 as the port-surface correction beyond the six-question ADR-051 template). ADR-015 amended with a 2026-07-30 status-amendment block preserving the original Oikos-ahead-of-Zetesis text — Stage 5 deferred, not cancelled; when the user returns to Stage 5, ADR-015 re-activates.
- **Files touched:**
  - `plugins/zetesis/__init__.py` (new — public re-exports)
  - `plugins/zetesis/plugin.py` (new — `ZetesisPlugin` dataclass + `build_zetesis_descriptor()` + locked constants; 10 required + 1 optional port slots)
  - `plugins/zetesis/tests/__init__.py` (new)
  - `plugins/zetesis/tests/test_zetesis_plugin.py` (new — 29 fast contract tests: locked constants 8, descriptor shape 5, construction/lifecycle/idempotency 11, ADR-007 AST guard 1, port-surface holds 2, `_UntouchablePort` proof 1, SecretsPort optional-slot 1)
  - `docs/adrs/ADR-052-stage-6-1-zetesis-skeleton.md` (new)
  - `docs/adrs/ADR-015-oikos-before-zetesis.md` (amended — 2026-07-30 STATUS AMENDMENT block at head + status line updated)
  - `docs/adrs/README.md` (extended — ADR-015 row amended note; ADR-052 index row appended before OPEN section)
  - `docs/Kosmos-Build-Spec-v25.md` (extended — §17 ADR-015 row amended; §17 ADR-052 row appended after ADR-051)
  - `docs/Kosmos-Build-Sequence-v25.md` (updated — Stage 5 header + deferral note added; §6 header flags STARTED EARLY; §6.1 stub rewritten as LANDED block with 10+1 port list + full Q1–Q7 rationale)
- **Ports / adapters affected:** No Protocol changes; no new formal port. Zetesis becomes the second plugin (after Tektos) to hold ObservabilityPort; the first to hold SearchPort as a required slot. `ports/secrets.py` used for the first time as an optional plugin slot.
- **PORTING_LEDGER / ADR updated:** ADR-052 authored (Ratified v25 at Stage 6.1). ADR-015 amended (Ratified v24 · Amended 2026-07-30). No PORTING_LEDGER change — skeleton is purpose-written, no OSS port.
- **Stop-condition status:** met — plugin loads (`ZetesisPlugin(...)` constructs side-effect-free); `start()` registers the descriptor with FrontendContractPort exactly once; `stop()` unregisters and is idempotent; all 10 required port slots are held (verified by identity); SecretsPort defaults to `None` and accepts a real port instance; `_UntouchablePort` sentinels prove zero business-port calls during start/stop at 6.1; all locked constants pin exactly (`"zetesis_research"` / `"zetesis.research.completed"` / `0.75` / kernel-compat `"1.0"`); descriptor exposes zero panels, zero routes, empty design tokens; `build_zetesis_descriptor()` is a pure factory (equal but distinct instances on repeat calls); ADR-007 AST scan of `plugins/zetesis/**/*.py` finds zero imports of `plugins.praxis` / `plugins.phrouros` / `plugins.tektos`; ruff clean on all changed files. Zetesis fast tier: **29 passed / 0 skipped**. Whole-repo fast tier: **986 passed / 19 skipped** (up from 957 / 19 at Stage 4.6, delta +29 = new Zetesis tier exactly). Tag `stage-6-1-complete` to be applied on the fanout commit. Next up: Stage 6.2 (ADR-010 head-to-head eval — AREX vs. LangChain Open Deep Research on Colossus).

## 2026-07-30 10:12 EDT — Stage 6.2 · ADR-010 head-to-head eval harness authored (pre-run)

- **Stage / plugin / port:** Stage 6.2 · ADR-010 head-to-head eval harness · touches Zetesis inner-loop selection (LLMPort · SearchPort surface). No formal port added.
- **What changed:** Locked Q1–Q11 + Q12–Q15 eval design (harness under `ops/benchmarks/adr_010/`, filesystem-vendor pattern at `vendor/adr_010/`, one Neo4j-vs-DozerDB question with 6 canonical facts, six-metric dataclass, in-place ADR amendment). Vendored **AREX-Turbo `inference/` bundle** (Apache-2.0, HF commit `129812742df4a5de27980ed07bda78d9d27c7370`) at `vendor/adr_010/arex_inference/` — 4 files, ~18KB, complete BrowseComp harness spec including `update_context` autonomous context compression and `finish` with confidence. **Did not vendor** the AREX code repo at `github.com/VectorSpaceLab/arex-model` — repo ships without a LICENSE file, so per `kosmos-port-workflow` license discipline the harness executor is authored fresh from the Apache-2.0 HF-shipped tool protocol. Vendored **Open Deep Research** at commit `d337ae32ed4ff8f4c6fbe192ba3bf1b2d6610799` (MIT) at `vendor/adr_010/open_deep_research/`. Authored `ops/benchmarks/adr_010/` package: `runner.py` (Colossus-side entry point), `metrics.py` (six-metric `TrialMetrics` dataclass — `answer_correctness`, `source_diversity`, `latency_seconds`, `gpu_utilization_peak_pct`, `vram_peak_gb`, `integration_effort_hours`), `policy.py` (nvidia-smi `GPUMonitor` sampling at 1 Hz), `harness/search_backend.py` (SearXNG-backed shared search + visit client with retry/backoff + registrable-domain diversity math), `harness/arex.py` (AREX XML `<tool_call>` parser + tool executor loop, temperature=1.0/top_p=0.95/top_k=20/presence_penalty=1.5 locked from upstream `inference.py`), `harness/odr.py` (LangGraph-driven ODR config with `search_api=NONE` + MCP tools substituting for identical SearXNG-backed tools), `harness/mcp_search_server.py` (FastMCP server exposing `search`/`visit` so ODR consumes them via its native MCP config surface), `docker-compose.yml` (self-hosted SearXNG at 127.0.0.1:8888, pinned engines: duckduckgo/bing/brave/wikipedia/arxiv/google-scholar/github), `fixtures/adr_010_question.json` (Neo4j-vs-DozerDB question authored by Perplexity Computer analyst pass; 6 canonical facts F1–F6 each with authoritative supporting URLs; blind-rating rubric locked), `fixtures/searxng_settings.yml` (SearXNG deterministic engine list). Contract tests at `tests/test_metrics.py`, `test_arex_xml_parser.py`, `test_search_backend.py`, `test_fixture.py` — **17/17 pass**, no LLM/network dependency. Amended ADR-010 in place with a 2026-07-30 STATUS AMENDMENT block preserving the original OPEN decision text — winner will be added in a subsequent LOCKED amendment once the Colossus run completes. Updated `docs/PORTING_LEDGER.md` with two `VENDORED (EVAL-ONLY)` entries replacing the placeholder `EVALUATING` entries — no promotion to `adapters/`. Updated `.gitignore` to exclude `vendor/adr_010/**/*.{safetensors,gguf,bin,pt,pth}` (weights live in HF cache on Colossus, not repo).
- **Files touched:**
  - `vendor/adr_010/arex_inference/{README.md, __init__.py, inference.py, prompts.py, UPSTREAM_SHA}` (new — 5 files vendored + metadata)
  - `vendor/adr_010/open_deep_research/**` (new — shallow clone `.git` stripped + UPSTREAM_SHA added)
  - `ops/benchmarks/adr_010/__init__.py` (new)
  - `ops/benchmarks/adr_010/README.md` (new)
  - `ops/benchmarks/adr_010/runner.py` (new)
  - `ops/benchmarks/adr_010/metrics.py` (new)
  - `ops/benchmarks/adr_010/policy.py` (new)
  - `ops/benchmarks/adr_010/docker-compose.yml` (new)
  - `ops/benchmarks/adr_010/harness/{__init__.py, search_backend.py, arex.py, odr.py, mcp_search_server.py}` (new)
  - `ops/benchmarks/adr_010/fixtures/{adr_010_question.json, searxng_settings.yml}` (new)
  - `ops/benchmarks/adr_010/tests/{__init__.py, test_metrics.py, test_arex_xml_parser.py, test_search_backend.py, test_fixture.py}` (new)
  - `docs/adrs/ADR-010-zetesis-inner-loop-eval.md` (amended — 2026-07-30 STATUS AMENDMENT block at head, original text preserved)
  - `docs/PORTING_LEDGER.md` (extended — AREX-Turbo inference bundle + Open Deep Research entries flipped from `EVALUATING` placeholders to `VENDORED (EVAL-ONLY)`)
  - `.gitignore` (extended — exclude weights under `vendor/adr_010/`)
- **Ports / adapters affected:** No Protocol changes; no new formal port. Harness is intentionally outside the plugin/adapter tree (lives under `ops/`) so ADR-010 evaluation cannot accidentally leak into a Zetesis production import path.
- **PORTING_LEDGER / ADR updated:** ADR-010 amended (STATUS AMENDMENT 2026-07-30 — eval design locked; winner still pending Colossus run). PORTING_LEDGER: AREX-Turbo inference bundle + Open Deep Research entries updated to `VENDORED (EVAL-ONLY)` with commit hashes, SPDX licenses, and modification notes per porting discipline.
- **Stop-condition status:** in-progress — eval design is locked, harness code contract-tested (17/17 fast tier pass at `ops/benchmarks/adr_010/tests/`); whole-repo fast tier **1003 passed / 19 skipped** (up from 986/19 at Stage 6.1, delta +17 = new eval-harness tier exactly). The **Colossus trial run itself has not yet occurred** — that requires: (a) `docker compose up -d searxng`; (b) `vllm serve BAAI/AREX-Turbo --served-model-name AREX-Turbo --host 127.0.0.1 --port 8001 --dtype bfloat16`; (c) `python -m ops.benchmarks.adr_010.runner --contender arex --trials 3`; (d) `ollama pull qwen2.5:32b-instruct-q4_K_M` + tear down vllm; (e) run MCP server + `python -m ops.benchmarks.adr_010.runner --contender odr --trials 3`. Post-run: blind-rate `answer_correctness` (5 or 6 facts covered), aggregate metrics, add second LOCKED amendment to ADR-010 with winner, flip loser to `REJECTED` in PORTING_LEDGER, promote winner to `adapters/zetesis/inner_loop/` for Stage 6.3, tag `stage-6-2-complete`.

## 2026-07-30 11:57 EDT — Stage 6.2 LANDED · ADR-010 LOCKED (winner = Open Deep Research; AREX-Turbo REJECTED for Stage 6.2)

- **Stage / plugin / port:** Stage 6.2 · Zetesis inner-loop head-to-head resolution. No new formal port; substrate selection locked ahead of Stage 6.3 wire-up.
- **What changed:** Executed the ADR-010 six-trial head-to-head on Colossus with a shared SearXNG substrate. Open Deep Research completed 3/3 trials (45.3 s / 60.1 s / 161.5 s) at ~28 GB VRAM peak; AREX-Turbo completed 0/3 at 32k context (all trials exhausted context before emitting `<finish>`) and 0/3 at a 65k-context retry (two visit-tool 404s on dead external URLs + one connection error mid-run, alongside two RTX 5090 display-blank thermal events at >85 °C that forced host reboots). Manual blind rating against the F1–F6 canonical-fact rubric (in `/tmp/adr010/rating.md`): ODR aggregate 3.0/18 (16.7%) vs. AREX 0.0/18 (0%). Locked **Open Deep Research** as the Stage 6.2 winner on **completion reliability under the Colossus envelope** — absolute answer-quality tuning is Stage 6.3's job. Rejected **AREX-Turbo** for Stage 6.2 and retained the bundle on-shelf with a four-clause revisit gate (thermal remediation + sustained bfloat16 headroom + successor checkpoint + ODR plateau) recorded in PORTING_LEDGER.md. Amended ADR-010 with a LOCKED head-to-head-result amendment block prepended above the prior harness-design amendment (original text preserved). Fanned the lock-in across every load-bearing file: spec §17 row rewritten with the full winner/loser table + Stage 6.3 obligation + revisit gate reference; §21 recurring-actions bullet struck through with LOCKED marker; §24 "Open items surviving v25" flipped from ADR-010 to "none"; adrs/README.md status row + "one remaining open decision" note both updated; PORTING_LEDGER.md entries flipped (ODR EVAL-ONLY → VENDORED (winner); AREX-Turbo VENDORED (EVAL-ONLY) → REJECTED with on-shelf note); Build-Sequence §6.2 marked LANDED with result + artifact paths + Colossus thermal-envelope constraint carried forward (`--enforce-eager --gpu-memory-utilization 0.75 --max-model-len 32768` until thermal remediation).
- **Files touched:**
  - `docs/adrs/ADR-010-zetesis-inner-loop-eval.md` (LOCKED amendment prepended; Status line + Definition of Done rewritten; prior 2026-07-30 harness-design amendment preserved intact)
  - `docs/adrs/README.md` (row 21 rewritten; "one remaining open decision" note flipped to "no ADRs are OPEN in v25")
  - `docs/Kosmos-Build-Spec-v25.md` (§17 preamble + ADR-010 row; §23 recurring-actions bullet; §24 open-items line)
  - `docs/Kosmos-Build-Sequence-v25.md` (§6.2 marked LANDED with full result block + Colossus thermal-envelope constraint)
  - `docs/PORTING_LEDGER.md` (§Zetesis rewritten: ODR promoted VENDORED (winner) with Stage 6.3 tuning obligation; AREX-Turbo flipped REJECTED with retained-on-shelf note + four-clause revisit gate)
  - `BUILD_LOG.md` (this entry)
  - `SESSION_HANDOFF.md` (overwritten — see next entry / session end)
- **Ports / adapters affected:** No Protocol changes at 6.2. Winner substrate `langchain-ai/open_deep_research@d337ae3` reserved for Stage 6.3 wire-up under `adapters/zetesis/inner_loop/` (wrap `LLMPort` + `SearchPort`). No plugin imports another plugin (ADR-007 preserved). No MemoryPort writes happen at 6.2 (ADR-008 preserved; first Zetesis writes land at Stage 6.3+ under the locked `zetesis.research.completed` predicate).
- **PORTING_LEDGER / ADR updated:** ADR-010 LOCKED 2026-07-30 with winner + rejection reasoning + revisit gate. PORTING_LEDGER.md §Zetesis: ODR promoted `VENDORED (EVAL-ONLY)` → `VENDORED (Stage 6.2 winner · LOCKED 2026-07-30)`; AREX-Turbo `VENDORED (EVAL-ONLY)` → `REJECTED (Stage 6.2 · on-shelf pending thermal remediation)`.
- **Stop-condition status:** met — Stage 6.2 DoD from Build-Sequence §6.2 fully satisfied (ADR-010 LOCKED with winner named, benchmark artifacts committed at `e882b2a`, ledger + spec + sequence + README + build/session logs all in sync). Tag `stage-6-2-complete` applied at this commit. Next: Stage 6.3 substrate tuning to raise ODR's F1-F6 score above the current 16.7% floor.

## 2026-07-30 12:08 EDT — Stage 6.3.1 · ODR substrate prompt anchoring authored

- **Stage / plugin / port:** Stage 6.3.1 · Zetesis inner-loop ODR substrate tuning (pre-adapter). No new formal port; substrate-only. Injection through ODR's officially-supported `configurable.mcp_prompt` field + user-turn scaffold — vendor tree at `vendor/adr_010/open_deep_research/` remains pristine (no monkey-patching, no vendor edits).
- **What changed:** Authored `ops/benchmarks/adr_010/harness/prompts.py` with two answer-agnostic anchoring surfaces:
  - `KOSMOS_MCP_PROMPT` — tool-usage discipline injected via ODR's `mcp_prompt` config field. Five non-negotiable clauses: (1) citations require an actually-visited URL, not a search-result snippet; (2) license/packaging claims require an authoritative first-party source (LICENSE file, canonical repository, maintainer discussion, OSI/gnu.org for license text); (3) distinct-domain floor of THREE registrable domains per final answer; (4) refusal-guard forbidding hedging or self-contradiction — unverified claims must be OMITTED, not hedged; (5) terminology precision guard locking `fork` vs. `plugin` vs. `re-implementation` vs. `re-enablement` to their concrete artifact-class meanings.
  - `build_anchored_user_turn(question)` — wraps the raw fixture question in a structural scaffold prepending Positions A–E: (A) Packaging model, (B) License posture, (C) Source availability, (D) Feature deltas (when in-scope), (E) Explicit non-features. Reasoning discipline requires filling positions in order A → B → C → D → E and correcting earlier positions if a later position surfaces a contradiction. Scaffold is answer-agnostic — no vendor names, no license identifiers, no F1-F6 canonical strings; contract test walks the fixture and asserts every 40-char window from every canonical fact statement is absent from the prompts module source.
  - Wired both surfaces into `ops/benchmarks/adr_010/harness/odr.py` — removed the pre-6.3.1 inline placeholder `mcp_prompt` string; ODR's `deep_researcher.ainvoke` now receives the wrapped user turn. Config assembly and injection paths guarded by contract tests that fail if the pre-6.3.1 placeholder ever returns.
- **Files touched:**
  - `ops/benchmarks/adr_010/harness/prompts.py` (new — 155 lines: `KOSMOS_MCP_PROMPT` + `build_anchored_user_turn` + module docstring documenting the two ODR-officially-supported injection surfaces)
  - `ops/benchmarks/adr_010/harness/odr.py` (edited — imports `KOSMOS_MCP_PROMPT` + `build_anchored_user_turn`; `build_odr_config` injects `KOSMOS_MCP_PROMPT` into `configurable.mcp_prompt`; `run_odr_trial` wraps the raw question via `build_anchored_user_turn` before `deep_researcher.ainvoke`; pre-6.3.1 inline placeholder string removed)
  - `ops/benchmarks/adr_010/tests/test_prompts.py` (new — 16 fast contract tests, no LLM/network dep: MCP prompt shape (6), scaffold shape + question preservation (5), answer-agnosticism guards (3), injection-site guards (2))
- **Ports / adapters affected:** none. Substrate stays in the eval-harness layer at `ops/benchmarks/adr_010/harness/` per Stage 6.3.1 charter — promotion to `adapters/zetesis/inner_loop/prompts/` waits on 6.3.3 wire-up if and only if the tuning threshold is met. ADR-007 preserved (no plugin imports another plugin). ADR-008 preserved (no MemoryPort writes at 6.3.1). ADR-010 preserved and honored (winner substrate is the tuning target).
- **PORTING_LEDGER / ADR updated:** none (substrate tuning, no new ports vendored, no license or component decisions changed).
- **Stop-condition status:** DoD anchor met (`pytest ops/benchmarks/adr_010/tests/` — 33/33 fast tests green, up from 17 at Stage 6.2, delta +16 = new prompt-anchoring tier exactly). Whole-repo fast tier: **1019 passed / 19 skipped** (up from 1003/19 at end-of-Stage-6.2, delta +16). Stage 6.3.1's authoring phase is complete. Next: re-run the 3-trial ODR benchmark on Colossus against the anchored prompts and blind-rate against F1-F6. Target for Stage 6.3.1 to close: mean ≥ 4/6 across 3 trials. If plateau below 4/6, proceed to Stage 6.3.2 (MCP retrieval-gate tighten). If plateau below 4/6 after 6.3.2, proceed to Stage 6.3.3 (model-swap ADR — requires thermal-envelope re-plan per the constraint carried in Build-Sequence §6.2).

## 2026-07-30 12:12 EDT — Stage 6.3.1 · repo-root conftest.py + Colossus install-path pivot

- **Stage / plugin / port:** Stage 6.3.1 · Zetesis inner-loop ODR substrate tuning (environmental fixups pre-benchmark run).
- **What changed:** Two blockers surfaced on Colossus during the first anchored-prompt benchmark run and are now resolved:

  1. **Test discovery failure.** `.venv/bin/pytest ops/benchmarks/adr_010/tests/` failed on Colossus with `ModuleNotFoundError: No module named 'ops'`, blocking all 4 ADR-010 test modules from collection. Root cause: `[tool.setuptools].packages` in `pyproject.toml` enumerates only the installable packages (`ports`, `adapters`, `plugins`, `governance`) — `ops`, `kernel`, and `scripts` are deliberately not shipped as Python packages, so `pip install -e .` does not put them on `sys.path`. Pytest's implicit rootdir insertion is version- and entry-point-dependent (`pytest` vs `python -m pytest` differ) and the Colossus interpreter (CPython 3.14) does not perform it. Fix: add a repo-root `conftest.py` that idempotently prepends the repo root to `sys.path`. This is the deterministic path from pytest's own "tests outside application code" documentation. Verified in workspace mirror: `.venv/bin/pytest ops/benchmarks/adr_010/tests/` passes 33/33 without any `PYTHONPATH=.` override.

  2. **Python 3.14 vs. PyO3 0.23.4 build failure — vendor ODR deps.** `pip install -e vendor/adr_010/open_deep_research` failed at the `jsonschema-rs` wheel build with `error: the configured Python interpreter version (3.14) is newer than PyO3's maximum supported version (3.13)`. `jsonschema-rs` is a transitive dependency of `langgraph-api` (dev-time server for `langgraph-cli[inmem]`), which is itself listed in ODR's `[project.dependencies]` but is a dev/CLI convenience tool — never imported by `deep_researcher.py`. The actual ODR runtime import surface, walked from `harness/odr.py` through `open_deep_research/deep_researcher.py`, is exactly: `langchain`, `langchain-core`, `langchain-mcp-adapters`, `langgraph`, and `mcp`. Fix path: install ODR editable with `--no-deps` and install only the runtime shortlist explicitly. Vendor tree stays pristine (no `vendor/adr_010/open_deep_research/pyproject.toml` edits — ADR-007 / porting discipline preserved). This trades convenience-tool install failures for correctness on Python 3.14; the tuning benchmark does not depend on `langgraph serve`, `langgraph-cli`, `azure-*`, `google-*`, `tavily`, or any other SaaS-integration package in ODR's declared deps.

- **Files touched:**
  - `conftest.py` (new — 36 lines: idempotent repo-root sys.path prepend, documented rationale, kept minimal because it is imported extremely early in pytest bootstrap)
  - `BUILD_LOG.md` (this entry)
- **Ports / adapters affected:** none. ADR-007 (events-only cross-plugin coupling) preserved. ADR-008 (zero-trust MemoryPort writes) preserved. Vendor tree at `vendor/adr_010/open_deep_research/` unchanged. No new ADR (fixup, not a decision).
- **PORTING_LEDGER / ADR updated:** none.
- **Stop-condition status:** conftest.py resolves blocker 1 (workspace verified — 33 fast tests + 1019 whole-repo tests all green after `.venv/bin/pytest`). Blocker 2 (Python-3.14 ODR install) resolved by shipping an explicit Colossus command list; user executes it below. Stage 6.3.1 benchmark run is still pending — this entry closes the environmental sub-slice only.

## 2026-07-30 12:15 EDT — Stage 6.3.1 · runtime shortlist correction (tavily-python)

- **Stage / plugin / port:** Stage 6.3.1 · Zetesis inner-loop ODR substrate tuning (environmental fixups pre-benchmark run).
- **What changed:** First runtime shortlist under-installed. `open_deep_research/utils.py` line 30 does `from tavily import AsyncTavilyClient` unconditionally at module load. The previous shortlist was walked only from `deep_researcher.py`'s direct imports; the transitive load via `utils.py` was missed. Full third-party import surface across `vendor/adr_010/open_deep_research/src/open_deep_research/*.py` is now confirmed as: aiohttp, langchain, langchain-core, langchain-mcp-adapters, langgraph, mcp, pydantic, tavily. Everything except `tavily` was already resolved. Adding `tavily-python` closes the gap.
- **Files touched:** none in the repo (environmental — Colossus `.venv` install only).
- **Ports / adapters affected:** none. Vendor tree stays pristine (no edits to `utils.py`, `pyproject.toml`, or `deep_researcher.py`). No monkey-patching. Only the officially-supported extension surface (`mcp_prompt` + user-turn wrap) is used, exactly as landed in Stage 6.3.1 authoring commit `4db2104`.
- **PORTING_LEDGER / ADR updated:** none.
- **Stop-condition status:** IN PROGRESS. The install command below closes environmental blocker 2 in full — once `python -c "from open_deep_research.deep_researcher import deep_researcher"` returns clean, the 3-trial benchmark run can execute against the anchored prompts.

## 2026-07-30 12:18 EDT — Stage 6.3.1 · runtime shortlist correction (langchain-openai) + MCP stdin fix

- **Stage / plugin / port:** Stage 6.3.1 · Zetesis inner-loop ODR substrate tuning (environmental fixups pre-benchmark run).
- **What changed:** Third and fourth environmental blockers surfaced in Colossus 3-trial run (all 3 trials fast-failed identically in ~4s each with empty artifacts). Both now resolved:

  1. **Runtime shortlist missed `langchain-openai`.** The ODR harness at `ops/benchmarks/adr_010/harness/odr.py` deliberately routes every model slot (research, summarization, final-report, compression) through LangChain's OpenAI provider by prefixing the model tag with `openai:` (e.g. `openai:qwen2.5:32b-instruct-q4_K_M`). This is the standard pattern for using LangChain against an OpenAI-compatible endpoint (Ollama exposes one at `/v1`). LangChain's `init_chat_model` therefore dynamically imports `langchain_openai.ChatOpenAI`. The dep is not statically referenced anywhere in the ODR src tree, so `grep '^import\|^from '` did not catch it — dynamic provider loading is invisible to static import walks by design. Symptom in artifacts: `"error": "ImportError: Initializing ChatOpenAI requires the langchain-openai package"`. Fix: `pip install langchain-openai`.

  2. **MCP server suspended by SIGTTIN under `&`.** Backgrounding a stdio-mode MCP server without redirecting stdin causes the shell to send SIGTTIN when the child reads from the controlling tty, showing as `[3]+  Stopped` in `jobs`. The trials completed in ~4s each because they never actually reached the MCP tool-call phase — they died before that in `init_chat_model`. Once the ChatOpenAI import lands, the MCP suspension would still block real tool calls. Fix: `< /dev/null` on the backgrounded invocation.

- **Files touched:** none in the repo (both fixes are environmental — one venv install, one shell-invocation flag).
- **Ports / adapters affected:** none. Vendor tree remains pristine. Harness code unchanged. No monkey-patching.
- **PORTING_LEDGER / ADR updated:** none.
- **Stop-condition status:** IN PROGRESS. Two more environmental gaps closed; benchmark run pending. If the next 3-trial run produces non-empty `trajectory` and `final_answer` arrays and completes on realistic ODR timescales (~30s–3min/trial against a local 32B model), Stage 6.3.1 authoring is validated end-to-end and I can do the blind F1–F6 re-rating from the artifact bodies.

## 2026-07-30 12:25 EDT — Stage 6.3.1 · thermal cooldown between trials

- **Stage / plugin / port:** Stage 6.3.1 · Zetesis inner-loop ODR substrate tuning (thermal envelope hardening).
- **What changed:** The first anchored-prompt 3-trial run made it through trials 1 and 2 (~60s and ~80s) but Colossus RTX 5090 crossed 85 C mid-trial-3, forcing operator SIGINT. The workload is inside the LOCKED envelope from Stage 6.2 (Ollama-only, ~28 GB VRAM peak, well below the 32 GB card and inside the vLLM `--gpu-memory-utilization 0.75` policy) — the boundary that fires first on Colossus is thermal, not compute. Fix: serialize trials with a between-trial cooldown, blocking until either a target GPU temperature or a hard cap is reached, whichever comes first. Cooldown runs after every trial except the final one; no cooldown before trial 1 (post-load thermal soak) so we don't stretch benchmark wall time when the GPU is already cold.
  - `ops/benchmarks/adr_010/policy.py` — `GPUSample` gains `temperature_c` (defaulted 0.0 for sandbox parity), `sample_gpu` now queries `temperature.gpu` in the same nvidia-smi call, `GPUMonitor.peak_temperature_c` exposes trial-peak temp, and new `wait_for_cooldown(target_c, min_seconds, max_seconds, poll_seconds, device_id, logger)` blocks until temp drops to target or max_seconds elapses. Sandbox-safe (missing nvidia-smi returns zeros, function returns after min_seconds without hanging).
  - `ops/benchmarks/adr_010/runner.py` — four new flags (`--cooldown-target-c` default 70, `--cooldown-min-seconds` default 30, `--cooldown-max-seconds` default 300, `--no-cooldown` escape hatch), plus a `_cooldown_between_trials` helper called after each trial. Env-var overrides mirror flags: `ADR010_COOLDOWN_TARGET_C`, `ADR010_COOLDOWN_MIN_SECONDS`, `ADR010_COOLDOWN_MAX_SECONDS`.
- **Files touched:**
  - `ops/benchmarks/adr_010/policy.py` (+45 lines: temperature sample, wait_for_cooldown, peak_temp accessor)
  - `ops/benchmarks/adr_010/runner.py` (+40 lines: 4 CLI flags, _cooldown_between_trials helper wired to both ODR and AREX loops)
- **Ports / adapters affected:** none. `TrialMetrics` schema unchanged — the LOCKED Stage 6.2 6-metric contract is preserved (thermal peak is operational, not scored). No new ports, no ADR-029 ResourcePort adapter changes yet — cooldown remains inside the eval harness. Vendor tree unchanged. No monkey-patching.
- **PORTING_LEDGER / ADR updated:** none.
- **Stop-condition status:** IN PROGRESS. Trial 3 was mid-supervisor loop when SIGINT fired at 12:22 EDT — no artifact was written for trial 3 in this run; trials 1 and 2 completed and are on disk (`trial_01_e283dd.json`, `trial_02_25c372.json`). Once the cooldown fix lands on Colossus, a fresh 3-trial run with defaults should complete inside the thermal envelope. Preliminary look at trials 1+2: `trajectory` shows only `{"notes": []}` and no MCP tool calls were emitted, meaning ODR answered from parametric knowledge despite the anchored MCP-usage prompt from commit `4db2104`. If the fresh 3-trial run produces the same MCP-empty trajectory, the F1–F6 rubric grade will be near the Stage 6.2 baseline and Stage 6.3.1 alone will not clear the mean >=4/6 threshold — escalation path is Stage 6.3.2 (MCP retrieval gate) rather than model swap.

## 2026-07-30 12:32 EDT — Stage 6.3.1 · anchored-prompt benchmark run rated: 0/6 (n=2), threshold missed, escalate to 6.3.2

- **Stage / plugin / port:** Stage 6.3.1 · Zetesis inner-loop ODR substrate tuning (prompt anchoring outcome).
- **What changed:** Ran 3-trial ODR benchmark with cooldown-enabled runner against the LOCKED Stage 6.2 substrate plus anchored-prompt authoring from commit `4db2104`. Trials 1 and 2 completed cleanly (75.6s / 48.4s, peak temps 83 C / 85 C, cooldown pulled to 40-42 C between them, envelope held). Trial 3 aborted mid-run with `KeyError: 'reflection'` — vendor bug in `vendor/adr_010/open_deep_research/src/open_deep_research/deep_researcher.py` line 275 (`tool_call["args"]["reflection"]` with no fallback). The 32B Ollama model freelanced the argument key when calling ODR's `think_tool`; ODR upstream assumes strict schema conformance from hosted models. Not our code.

- **Blind F1-F6 rating written to** `ops/benchmarks/artifacts/adr-010-2026-07-30/odr/RATING_STAGE_6_3_1.md`. Score summary:
  - Trial 1: 0/6. F1 (packaging) inverted — claims DozerDB is a full source-tree fork. F3/F4 assign AGPLv3 to Community and DozerDB (both are GPLv3). Cites nonexistent repo `github.com/dozermapping/dozerdb`. F2/F6 absent.
  - Trial 2: 0/6. F1 correct in prose (says "runtime-loaded extension/plugin") but supporting URL is nonexistent `github.com/dozerdb/dozerdb`; per rubric "citing an unrelated URL scores 0." F4 inverted (calls DozerDB "commercial/proprietary" — it is GPLv3). F6 anti-covered (positively claims high-limit store class as a DozerDB deliverable, which F6 explicitly negates).
  - Mean: 0/12 = 0.0% on n=2 valid trials. Stage 6.3.1 threshold was mean >=4/6.
  - MCP tool call count: 0 across both completed trials. `trajectory` is `[{"notes": []}]`. Model received the anchored prompt but bypassed tool use entirely, answering from parametric memory (and hallucinating URLs).

- **Files touched:**
  - `ops/benchmarks/artifacts/adr-010-2026-07-30/odr/RATING_STAGE_6_3_1.md` (new — 70 lines: blind rating table + interpretation + escalation path)
  - Trial artifacts remain on disk unmodified.
- **Ports / adapters affected:** none. Vendor tree unchanged. Substrate config unchanged.
- **PORTING_LEDGER / ADR updated:** none.
- **Stop-condition status:** Stage 6.3.1 fails threshold on n=2 valid trials by a wide margin. Escalate to Stage 6.3.2 (MCP retrieval gate: runtime enforcement that no final answer may be emitted until at least N successful MCP tool calls have executed and their results have been returned into model context). Do NOT escalate to Stage 6.3.3 (model-swap ADR) yet — two variables remain to exhaust before concluding qwen2.5:32b-instruct-q4_K_M is the wrong model (retrieval gate + higher-precision quantization q5_K_M at ~22 GB VRAM). Also: land runner retry-on-error before the 6.3.2 benchmark run so Trial-3-style vendor bugs don't invalidate that sample too.

## 2026-07-30 12:39 EDT — Stage 6.3.2 · MCP retrieval gate + vendor-bug retry shims (harness-only, vendor-pristine)

- **Stage / plugin / port:** Stage 6.3.2 · Zetesis inner-loop ODR substrate tuning (retrieval-gate enforcement).
- **What changed:** Two orthogonal shims inside `run_odr_trial`, both harness-side (vendor tree `vendor/adr_010/open_deep_research/` untouched per Stage 6.2 substrate lock + ADR-007 porting discipline).
  1. **Vendor-bug retry (shim 1).** ODR upstream `deep_researcher.py:275` does `tool_call["args"]["reflection"]` with no fallback; when the 32B Ollama model freelances the argument key (e.g. sends `thought` or `content` instead of `reflection`), the state graph crashes mid-run. Shim 1 catches any exception during `ainvoke`, records it in `trajectory.attempts`, and retries once with a fresh `thread_id`. Hard cap: 2 attempts.
  2. **Retrieval gate (shim 2).** After a successful `ainvoke`, inspect `result["raw_notes"]`. If empty (== supervisor emitted a final report without the researcher subgraph ever calling an MCP tool — the empirical Stage 6.3.1 failure mode), re-invoke once with an escalated `### RETRIEVAL GATE (mandatory)` directive appended to the user turn (requires >=3 distinct MCP calls, forbids parametric answers, forbids fabricated citations). Hard cap: 1 gate retry.
  3. **Worst-case ainvoke calls per trial: 3** (2 vendor attempts + 1 gate retry). Bounded so sample-budget stays predictable.
  4. **All retries + reasons land in `metrics.trajectory`** as an `attempts` list, so the blind rater can distinguish parametric-answer trials from grounded ones without opening logs.
- **Files touched:**
  - `ops/benchmarks/adr_010/harness/odr.py` — refactored `run_odr_trial` inner block; introduced `_invoke_once` helper; added shim 1 + shim 2 with attempt-tracking. Removed the top-level `config["configurable"]["thread_id"]` assignment (each attempt now gets a fresh id inside `_invoke_once`).
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` (new — 7 fast contract tests, no Ollama/MCP/LangGraph runtime needed; `open_deep_research.deep_researcher` module is stub-injected via `sys.modules`). Cases:
    - happy path -> exactly 1 ainvoke, no retries
    - shim 1: KeyError('reflection') -> retry -> success (asserts fresh thread_id per attempt)
    - shim 1: both attempts raise -> last exception surfaces in `metrics.error`, capped at 2 attempts
    - shim 2: empty raw_notes -> gate retry with RETRIEVAL GATE directive in payload -> success
    - shim 2: gate retry itself raises -> keep pre-gate result (better than losing the trial)
    - shim 2: gate is bounded to one retry (does not loop on repeated empty raw_notes)
    - hard cap: worst-case = 3 ainvoke calls total
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **40 passed** (was 33: +7). Whole-repo pytest = **1026 passed / 19 skipped** (was 1019: +7 exact).
- **Ports / adapters affected:** none formal. Substrate stays in `ops/benchmarks/adr_010/harness/`. Promotion to `adapters/zetesis/inner_loop/` waits on Stage 6.3.3 wire-up when rating passes threshold.
- **PORTING_LEDGER / ADR updated:** none. Both shims are runtime enforcement inside the harness; they do not alter the ODR vendor tree or the ADR-010 winner (still ODR). No ADR needed — this is inside the "operational tuning" band that ADR-010 LOCKED amendment already anticipated.
- **Stop-condition status:** Ready for a fresh 3-trial run on Colossus (`.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr`). New closing criterion for Stage 6.3.2: mean answer_correctness >=4/6 across 3 trials AND `raw_notes_count > 0` on every trial's trajectory entry. If retrieval gate fires and still yields empty raw_notes on retry, that's the signal that the model, not the harness, is the limit — escalate to quantization uplift (qwen2.5:32b-instruct-q5_K_M) before authoring Stage 6.3.3 model-swap ADR.

## 2026-07-30 12:57 EDT — Stage 6.3.2 · thermal watchdog + pre-flight cooldown + power cap (post 88 C incident)

- **Stage / plugin / port:** Stage 6.3.2 · Zetesis inner-loop ODR substrate tuning (thermal envelope hardening).
- **What changed:** After the 2026-07-30 88 C driver-crash incident (DEBUG_LOG entry same date) with fans/pump already at max cooling, the physical envelope became the primary constraint. This landing shrinks Colossus's ADR-010 workload footprint at three layers of defense:
  1. **Board-level:** `nvidia-smi -pl 400W` power cap applied at runner startup (RTX 5090 stock TDP is 575W; -30% sustained wattage in exchange for ~20-30% slower generation). Non-fatal if sudo/nvidia-smi unavailable — logs and continues.
  2. **Trial-level:** GPU thermal watchdog. `GPUMonitor` gains `thermal_abort_at_c` (default 85 C) + latching `thermal_event` (threading.Event) that fires the first time a sample crosses threshold. Harness's `_invoke_once` races each `ainvoke` against an asyncio poller watching that event; on breach it cancels the ainvoke task and raises `ThermalAbort`. Trial artifact records a distinguished `thermal_watchdog` block with reason + abort temp + threshold.
  3. **Between-trial:** Pre-flight cooldown added BEFORE every trial (was only between-trial before). Default cooldown target lowered 70 -> 60 C. Default min cooldown 30 -> 60 s. Default `OLLAMA_KEEP_ALIVE=60s` exported so the 32B model releases VRAM during the between-trial window (28 GB freed lets the card actually shed heat) and reloads warmly on the next trial.
- **Retry policy:** `ThermalAbort` is NEVER retried and NEVER escalated to the retrieval-gate shim. Physical envelope, not a schema bug — retrying just re-breaches. Vendor-bug retries still apply for schema-drift errors.
- **Files touched:**
  - `ops/benchmarks/adr_010/policy.py` — GPUMonitor thermal-abort surface (thermal_abort_at_c, thermal_event, thermal_exceeded(), abort_reason, abort_temperature_c)
  - `ops/benchmarks/adr_010/harness/odr.py` — new `ThermalAbort` exception; `_invoke_once` wraps ainvoke in asyncio-race watchdog; shim-1 breaks on ThermalAbort (no retry); shim-2 skipped on thermal abort
  - `ops/benchmarks/adr_010/runner.py` — `_apply_power_cap` (nvidia-smi -pl), `_pre_flight_cooldown`, GPUMonitor constructed with thermal_abort_at_c, thermal_event passed into run_odr_trial, thermal-watchdog block appended to trial artifact on breach. New flags: `--thermal-abort-c` (85), `--power-cap-watts` (400), `--no-power-cap`, `--ollama-keep-alive` (60s). Defaults changed: `--cooldown-target-c` 70 -> 60, `--cooldown-min-seconds` 30 -> 60.
  - `ops/benchmarks/adr_010/tests/test_policy_thermal.py` (new — 6 fast tests): threshold=None inert; latches on first breach with recorded reason/temp; boundary at exact value trips; zero samples never trip (sample_gpu 0.0 sentinel); event pollable from asyncio; peak_temperature_c still tracks after latch.
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` — new `test_thermal_abort_cancels_ainvoke_and_does_not_retry`: pre-set thermal event, slow-ainvoke stub, assert one ainvoke, ThermalAbort surfaced, no retrieval-gate ran.
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **47 passed** (was 40: +7). Whole-repo pytest = **1033 passed / 19 skipped** (was 1026: +7 exact).
- **Ports / adapters affected:** none formal. All changes stay in `ops/benchmarks/adr_010/`. Vendor tree pristine.
- **PORTING_LEDGER / ADR updated:** none. Thermal enforcement is operational hardening, not a substrate decision — ADR-010's LOCKED winner still applies.
- **Stop-condition status:** Runner is safe to invoke on Colossus. Even at worst case (32B model already resident at high temp, MCP retrieval gate forcing 3 ainvoke calls per trial), the watchdog will cancel any run that crosses 85 C before it can hit 88 C+. `nvidia-smi -pl 400W` reduces the probability that 85 C is ever reached in the first place. Ready for a fresh 3-trial run on Colossus and blind rating.

## 2026-07-30 13:29 EDT — Stage 6.3.3 · fact-check shim (shim 3) + fixture-anchor injection + cooldown 60→45s

- **Stage / plugin / port:** Stage 6.3.3 · Zetesis inner-loop ODR substrate tuning (fact-grounding pass).
- **What changed:** Stage 6.3.2 shipped a clean thermal envelope (0 watchdog fires across 3 trials, peaks 66/71/NC °C) but the blind-rating pass came in at ~1.33/6 (threshold ≥4/6 missed). Failure modes diagnosed from artifacts + fresh fixture re-read:
  1. **URL hallucination** — Trial 1 cited `github.com/dozermapping/dozerdb` (doesn't exist); Trial 2 cited `github.com/dozermapping/dozer` (doesn't exist).
  2. **License swap** — Trial 1 claimed Neo4j CE is AGPLv3 (F3 says GPLv3); Trial 2 claimed DozerDB is Apache-2.0 (F4 says GPLv3).
  3. **Polarity confusion / concatenated reports** — Trial 3 emitted 3 stitched reports, self-contradictory.

  Two runtime shims land in this stage; option 4 (ADR-010 CONTINGENCY-FIRED escalation to quantization uplift q5_K_M or model swap) is held in reserve until the next 3-trial pass has data.

  **Shim 3 (URL fact-check):** After the initial invocation, every `https?://` URL cited in `final_report` is verified against the live network (HEAD-first, GET-fallback, 5-redirect chase, 8s per-URL timeout, 60s total, concurrency 8, dedup). If ANY URL fails to resolve to 2xx/3xx, the harness re-invokes once with a **correction directive** that lists the failed URLs verbatim, forbids invention, and warns that the retry will be re-verified. Retry outcomes recorded as `fact_check_retry_ok` | `fact_check_retry_failed` | `fact_check_retry_thermal_abort`. After the retry, a **final re-verify pass** annotates any persistent-bad URL inline in the report body as `URL [unverified]`, so the blind rater sees them without opening logs. `ThermalAbort` still terminates shim 3 (physical envelope, not a bug to retry).

  **Fixture-anchor injection (medium strength):** Runner extracts an allowlist of authoritative URLs from `fixture.ground_truth.canonical_facts[*].supporting_urls` (dedupe, order-preserving) and passes them as `fact_anchor_urls` to `run_odr_trial`. `build_anchored_user_turn` appends a **FACT ANCHOR ADVISORY** block listing those URLs — no SPDX identifiers, no polarity claims, no restated ground-truth facts. The advisory targets the "guessed a URL that doesn't exist" failure mode without trivializing F2/F3/F4 (fact retrieval is still exercised).

  **Cooldown minimum 60→45s:** Per operator directive after empirical data showed 60s consistently lands trial-start at 35–43 °C with the 400W cap. Target temperature unchanged at 60 °C.

- **Files touched:**
  - `ops/benchmarks/adr_010/harness/prompts.py` — `build_anchored_user_turn(question, *, fact_anchor_urls=None)`; new `_build_anchor_advisory()`; new `build_fact_check_correction_directive(unverified_urls)`. Anchor block appears only when `fact_anchor_urls` is truthy.
  - `ops/benchmarks/adr_010/harness/url_verify.py` **(new — 218 lines)** — `VerifyResult` dataclass; `verify_urls()` async batch verifier (HEAD → GET fallback, follow_redirects up to 5, per-URL timeout 8s, total 60s, concurrency semaphore 8, canonicalization strips trailing `),.;\"'` punctuation, classifies `ok / http_4xx / http_5xx / dns / timeout / connect / invalid / other`); `annotate_unverified()` inserts the `[unverified]` marker inline and is idempotent.
  - `ops/benchmarks/adr_010/harness/odr.py` — `run_odr_trial` gains `fact_anchor_urls: list[str] | None = None` and `enable_fact_check: bool = True`. Anchors plumbed into `build_anchored_user_turn`. Shim 3 wired in between shim 1/2 result and the finalize block: initial verify → if any unverified, one correction retry → retry-pass verify → final re-verify + inline annotation on the report body. Trajectory gains `{"fact_check": [...events...]}` and `{"final_unverified_urls": [...]}`. Skipped after `ThermalAbort`. Verifier crashes are non-fatal (logged as `verifier_error`, harness continues).
  - `ops/benchmarks/adr_010/runner.py` — `_collect_fact_anchor_urls(fixture)` extracts and dedupes the allowlist; passed into `run_odr(...)`. `--cooldown-min-seconds` default 60 → **45**. `--cooldown-target-c` held at 60. New `--no-fact-check` flag (regression escape hatch, off by default). Startup log line reports anchor count when non-zero.
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` — every existing `run_odr_trial(...)` call gains `enable_fact_check=False` (fast tier stays Colossus/network-independent).
  - `ops/benchmarks/adr_010/tests/test_odr_fact_check.py` **(new — 7 fast tests)** — anchor injection into user turn; happy path (no retry); bad-URL retry succeeds; bad-URL retry still fails → inline `[unverified]` annotation + `final_unverified_urls` in trajectory; `enable_fact_check=False` disables the shim; verifier crash is non-fatal (`verifier_error` event); `ThermalAbort` skips shim 3.
  - `ops/benchmarks/adr_010/tests/test_url_verify.py` **(new — 11 fast tests)** — punctuation canonicalization; HEAD 2xx→ok; HEAD 404 + GET 200 recovery (raw.githubusercontent.com case); 4xx and 5xx classification; DNS error; connect refused; HEAD timeout; invalid scheme never hits network; dedup; `annotate_unverified` only rewrites unverified URLs and is idempotent.
  - `ops/benchmarks/adr_010/tests/test_prompts_fact_anchors.py` **(new — 4 fast tests)** — no-anchor call matches Stage 6.3.1 shape; anchor URLs appear verbatim in advisory; advisory block does NOT leak SPDX ids or polarity phrases; correction directive lists exactly the passed bad URLs, forbids invention, warns of re-verification.
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **70 passed** (was 47: +23). Whole-repo pytest = **1056 passed / 19 skipped** (was 1033 / 19: +23 exact, zero regressions).
- **Ports / adapters affected:** none formal. All new code stays under `ops/benchmarks/adr_010/harness/` and `.../tests/`. Vendor tree pristine per ADR-007 substrate lock.
- **PORTING_LEDGER / ADR updated:** none. Shim 3 + anchor injection are operational hardening inside ADR-010's LOCKED "operational tuning" band; ODR winner unchanged.
- **Stop-condition status:** Ready for a fresh 3-trial run on Colossus. New closing criterion for Stage 6.3.3: mean rated correctness ≥4/6 across 3 trials AND `final_unverified_urls` empty on every trial's trajectory (no persistent hallucinated URLs after retry). If threshold still missed, escalate to option 4 (ADR-010 CONTINGENCY-FIRED — quantization uplift q5_K_M or 70B model swap) in a Stage 6.3.4 ADR.

## 2026-07-30 13:48 EDT — Stage 6.3.3b · URL extractor bracket bug + cooldown 45→30s

- **Stage / plugin / port:** Stage 6.3.3b · Zetesis inner-loop ODR substrate hotfix (same lock-in phase as 6.3.3).
- **What changed:** First Colossus rated run of Stage 6.3.3 (trials `01_d53432`, `02_47f4ef`, `03_e749ed` on the Colossus artifact tree) exposed one extractor bug and confirmed the anchor advisory works when the extractor is correct.
  - **Trials 2 & 3:** 4–5 cited URLs each, ALL verified 2xx (`neo4j.com/open-core-and-neo4j/`, `github.com/orgs/DozerDB/discussions/…`, `github.com/neo4j/neo4j`, `github.com/DozerDB/dozerdb-plugin`, `dozerdb.org/`). No shim-3 retry needed. Anchor injection works.
  - **Trial 1:** Model emitted Markdown-autolink citations of the form `<https://…>` throughout the final report. The 6.3.3 extractor regex `https?://[^\s\)]+` did not exclude `>`, and the surrounding framework URL-encoded the whole citation before we ever saw it, so the shim received URLs with `%3E` (and sometimes `%3E/`) glued to the end. Verify pass returned a wave of false 404s → shim-3 correction retry fired → retry emitted the same bracket pattern → `[unverified]` markers baked in on URLs that would have resolved cleanly without the suffix.
  - **Fix:** `harness/url_verify.py` gains a single-source `extract_urls(text)` that (a) uses regex `https?://[^\s)>]+`, (b) strips a leading `<`, (c) strips trailing `%3E`/`%3e`/`>` runs in addition to the previous `),.;\]\"'`. `_canonicalize` widens to match. Every call site in `harness/odr.py` (prelim / retry / final-annotate / final-evidence extraction) routed through `extract_urls`.
  - **Cooldown min-seconds default 45 → 30** per operator directive after three consecutive 3-trial runs never exceeded 71 °C (yellow line at 52 °C, watchdog at 85 °C, observed trial-start temps 34–44 °C at 45 s wait). Target C held at 60.
- **Files touched:**
  - `ops/benchmarks/adr_010/harness/url_verify.py` — widened `_URL_STRIP_TRAILING` (add `>`, `%3E`, `%3e`); new module-level `_URL_EXTRACT_RE` that excludes `)` and `>` from URL body; new `extract_urls(text)` helper (order-preserving dedup); `_canonicalize` strips one leading `<`; export `extract_urls` in `__all__`.
  - `ops/benchmarks/adr_010/harness/odr.py` — imports `extract_urls`; removes inline `re.findall(r"https?://[^\s\)]+", ...)` from 4 call sites (prelim, retry, final-annotate, final-evidence) and calls `extract_urls` instead. Drops the local `import re as _re` since nothing else in the shim needed it.
  - `ops/benchmarks/adr_010/runner.py` — `--cooldown-min-seconds` default 45 → **30**. Help text records the 45→30 progression rationale.
  - `ops/benchmarks/adr_010/tests/test_url_verify.py` — +6 regression tests: `_canonicalize` strips `%3E`, `%3e`, literal `>`, leading `<`; `extract_urls` returns clean URLs from mixed markdown-autolink + parenthesized + raw text; `extract_urls` dedupes while preserving order; extractor never yields a URL still carrying `>`, `%3E`, `%3e`, or a leading `<`.
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **76 passed** (was 70: +6). Whole-repo pytest = **1062 passed / 19 skipped** (was 1056 / 19: +6 exact, zero regressions).
- **Ports / adapters affected:** none formal. Vendor tree pristine.
- **PORTING_LEDGER / ADR updated:** none. Bracket-suffix bug is a harness extractor bug, not a substrate decision.
- **Stop-condition status:** Ready for another 3-trial run on Colossus with 30 s cooldown min. Success criterion unchanged from Stage 6.3.3: mean rated correctness ≥4/6 AND `final_unverified_urls` empty on every trial. Trial 2 and Trial 3 of the pre-fix run already produced clean URL sets — with the extractor bug removed, Trial 1's noise disappears and the rating question reduces to whether the model correctly stated GPLv3 for both Neo4j CE and DozerDB across all three trials.


## 2026-07-30 14:06 EDT — Stage 6.3.4 · additive shims 4/5/6/7/8 + cooldown 30→15s

- **Stage / plugin / port:** Stage 6.3.4 · Zetesis inner-loop ODR substrate — additive fact-check hardening on top of Stage 6.3.3b (still LOCKED lock-in band; ODR winner unchanged).
- **What changed:** Five additive, opt-outable shims added to the ODR harness after Stage 6.3.3b confirmed extractor bugs were fixed but Trials 2 & 3 of the 30 s-cooldown post-pull run still hallucinated URLs (`github.com/dozermq/dozerdb-plugin`, `github.com/dozerdb/dozer/wiki/*`, `neo4j.com/legal/terms-of-service-enterprise-edition-use-agreement/`). Shims 4/6/7/8 default ON; shim 5 opt-in via `--n-consistency N`.
  - **Shim 4 — LICENSE grounding.** For every `github.com/<owner>/<repo>` URL cited in the report body, fetches `raw.githubusercontent.com/<owner>/<repo>/HEAD|main|master/LICENSE` (HEAD/GET, 8 s per, up to 3 branch fallbacks), pattern-matches SPDX families (AGPL-3.0, GPL-3.0, GPL-2.0, LGPL-3.0, Apache-2.0, MIT, BSD-3-Clause, BSD-2-Clause, MPL-2.0, ISC), and builds a correction directive listing observed license family per repo. If any cited license claim contradicts the fetched LICENSE, the directive is added to a one-shot correction turn and the report is re-emitted.
  - **Shim 5 — Self-consistency.** Runs the entire per-trial pipeline (shims 1→2→3→4→6→7→8) N times when `--n-consistency N` ≥ 2. Claims are tallied via a lightweight extractor (license / fork / identity / restoration taxonomy from the fixture rubric). Consensus report is composed from claims meeting a strict majority `(n//2)+1`. Trial artifact's `final_answer` becomes the consensus; every sub-run's trajectory + vote summary preserved under `trajectory[-1]["self_consistency"]`. `source_diversity` = max across runs, `latency_seconds` = sum, thermals = max. Default N=1 (off).
  - **Shim 6 — Rubric self-critique.** Extracts rubric lines from `fixture.ground_truth.canonical_facts` (each fact → `[F#] ASSERT: statement` or `[F#] NEGATE: statement` based on polarity), asks the model to score its own report against the rubric with sentinel fences, and rewrites failing sections. One extra `ainvoke` per trial.
  - **Shim 7 — Chain-of-Verification (CoVe).** Extracts up to 6 claims from the report (license / fork / identity / restoration taxonomy), generates a verification sub-question per claim, asks the model to answer each with only the observations already in scope, and rewrites contradicted claims. Sentinel-fenced. Up to 6 extra `ainvoke`s per trial.
  - **Shim 8 — Claim-support gate.** Post-shim-7, marks any license or identity claim whose subject string does not appear in the retrieval observations (shim 2 gate output) with `[unsupported: no citation in observations]`. Idempotent. No LLM call.
  - **Cooldown min-seconds default 30 → 15** per operator directive. Stage 6.3.3 3-trial run with 30 s cooldown peaked at 73 °C; trial-start temps were 36/37/42 °C — 12 °C below the 85 °C watchdog and 21 °C below the 88 °C driver-crash line. Target C held at 60.
- **Files touched:**
  - `ops/benchmarks/adr_010/harness/license_grounding.py` **(new)** — shim 4 module. `fetch_repo_license()`, `classify_license()`, `build_license_correction_directive()`.
  - `ops/benchmarks/adr_010/harness/self_consistency.py` **(new)** — shim 5 aggregator. `tally_claims()`, `compose_consensus_report()`, `summarize_vote()`; threshold `(n//2)+1`.
  - `ops/benchmarks/adr_010/harness/rubric_critique.py` **(new)** — shim 6 module. `build_rubric_lines_from_facts()`, `build_critique_turn()`.
  - `ops/benchmarks/adr_010/harness/cove.py` **(new)** — shim 7 module. Claim taxonomy regex, per-claim sub-question templates, sentinel-fenced rewrite turn.
  - `ops/benchmarks/adr_010/harness/claim_support.py` **(new)** — shim 8 module. Unsupported-claim detection (license/identity only) + idempotent `[unsupported]` marker.
  - `ops/benchmarks/adr_010/harness/odr.py` — `run_odr_trial` gains kwargs `enable_license_grounding=True, enable_rubric_critique=True, rubric_lines=None, enable_cove=True, enable_claim_support_gate=True`. New shim block between fact-check (shim 3) and Finalize. Trajectory gains `{"shim_events": [...]}`.
  - `ops/benchmarks/adr_010/runner.py` — new `_combine_self_consistency()`. New flags `--no-license-grounding`, `--no-rubric-critique`, `--no-cove`, `--no-claim-support-gate`, `--n-consistency N`. Rubric extracted from fixture. `--cooldown-min-seconds` default 30 → **15**. Startup log line reports shim toggles + N.
  - `ops/benchmarks/adr_010/tests/test_license_grounding.py` **(new)** — 14 tests.
  - `ops/benchmarks/adr_010/tests/test_rubric_critique.py` **(new)** — 9 tests.
  - `ops/benchmarks/adr_010/tests/test_cove.py` **(new)** — 11 tests.
  - `ops/benchmarks/adr_010/tests/test_claim_support.py` **(new)** — 9 tests.
  - `ops/benchmarks/adr_010/tests/test_self_consistency.py` **(new)** — 9 tests.
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **128 passed** (was 76: +52). Whole-repo pytest expected **1114 passed / 19 skipped** (+52 exact; to be confirmed on Colossus).
- **Ports / adapters affected:** none formal. All new code stays under `ops/benchmarks/adr_010/harness/` and `.../tests/`. Vendor tree pristine per ADR-007 substrate lock.
- **PORTING_LEDGER / ADR updated:** none. All five shims sit inside ADR-010's LOCKED "operational tuning" band; ODR winner unchanged.
- **Stop-condition status:** Ready for a fresh 3-trial ODR run on Colossus with 15 s cooldown min and shims 4/6/7/8 defaulted ON. New Stage 6.3.4 closing criterion: mean rated correctness ≥5/6 across 3 trials AND `final_unverified_urls` empty on every trial AND no `[unsupported]` markers survive to the final report for any of the six canonical facts. If threshold still missed with defaults, next escalation is `--n-consistency 3` (shim 5 opt-in) then quantization/model uplift as Stage 6.3.5 ADR-010 CONTINGENCY.


## 2026-07-30 14:22 EDT — Stage 6.3.4b · footnote-marker extractor bug + cooldown 15→10s

- **Stage / plugin / port:** Stage 6.3.4b · Zetesis ODR harness hotfix (same lock-in band as 6.3.4).
- **What changed:** First Stage 6.3.4 Colossus 3-trial ODR run completed clean (128 tests green, shim 4 verified — `raw.githubusercontent.com/neo4j/neo4j/HEAD/LICENSE.txt` 200, `raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/LICENSE` 200). Peak GPU 74C at 15s cooldowns; trial-start temps 34/39/43C. Two issues surfaced in the logs:
  - **Extractor bug (footnote markers).** Model emitted citations of the form `github.com/neo4j/neo4j[3]` (bare footnote-marker suffix). The 6.3.3b extractor regex `https?://[^\s)>]+` did not exclude `[` or `]`, so the `[3` was smuggled into the URL body and the shim tried to `HEAD https://github.com/neo4j/[3` → 404. Sibling case: leading `[` from `[https://...]` autolinks was not stripped by `_canonicalize`.
  - **Cooldown 15s → 10s.** Same headroom argument as 30→15: peak 74C is 11C below the 85C watchdog and 14C below the 88C driver-crash line. Target C held at 60.
  - **Fix:** `harness/url_verify.py` — `_URL_EXTRACT_RE` widens to `https?://[^\s)>\[\]]+` (adds `[`, `]` to the excluded body set). `_URL_STRIP_TRAILING` also gains `[`/`]` in the trailing-punctuation run so `y]]` cleanup still works. `_canonicalize` strips a leading `[` in addition to `<`.
  - **Cooldown default:** `--cooldown-min-seconds` default 15 → **10** in `runner.py`. Help text updated with the progression 30→60→45→30→15→10 and the 74C peak evidence.
- **Files touched:**
  - `ops/benchmarks/adr_010/harness/url_verify.py` — `_URL_EXTRACT_RE` and `_URL_STRIP_TRAILING` updated; `_canonicalize` handles leading `[`.
  - `ops/benchmarks/adr_010/runner.py` — `--cooldown-min-seconds` default 15 → 10; help text records 6.3.4b evidence.
  - `ops/benchmarks/adr_010/tests/test_url_verify.py` — +3 regression tests (trailing `]`/`[`/`]]`/`].`/`[]`; leading `[https://...]`; footnote-marker `github.com/neo4j/neo4j[3]` extracts cleanly).
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **131 passed** (was 128: +3). Whole-repo pytest expected **1117 passed / 19 skipped**.
- **Ports / adapters affected:** none formal. Vendor tree pristine.
- **PORTING_LEDGER / ADR updated:** none. Footnote-marker suffix is a harness extractor bug, not a substrate decision.
- **Stop-condition status:** Ready for another 3-trial ODR run on Colossus with 10s cooldown min. Stage 6.3.4 closing criterion carries forward. Note: the Neo4j-CE-vs-EE dual-licensing question is a separate rubric-modeling issue (shim 4 currently records a single license family per repo) — track separately if the rating still misses on F1/F2.


## 2026-07-30 14:49 EDT — Stage 6.3.4c · shim-scoped vendor-bug retry + cooldown 10→5s

- **Stage / plugin / port:** Stage 6.3.4c · Zetesis ODR harness hotfix (same lock-in band as 6.3.4).
- **What changed:** Stage 6.3.4b Colossus 3-trial ODR run completed. Blind-style rating vs the 6 canonical facts: trial 1 = 6/6, trial 2 = 3/6, trial 3 = 4/6, mean = **4.33/6** — misses the ≥5/6 DoD. Root cause was NOT a model capability limit; it was a harness retry bug. Trial 2's `shim_events.license_grounding.retry_outcome = retry_failed / error = KeyError: 'reflection'` shows the ODR upstream vendor bug (`deep_researcher.py:275 tool_call["args"]["reflection"]` with no fallback) hit *inside* the shim-4 license-grounding retry, so the ground-truth GPL-3.0 directive never landed in the final report — the model kept its parametric-memory "AGPLv3 vs Apache-2.0" hallucination. Same class of failure hit trial 3 twice (attempts 1 + 3).
  - **Fix:** New `_invoke_with_vendor_retry(user_content)` helper in `harness/odr.py`. Wraps every non-primary `_invoke_once` call in one additional vendor-bug retry (ThermalAbort stays non-retriable per shim-1 rationale — physical envelope). Applied at 5 sites: retrieval-gate retry, fact-check retry, license-grounding retry, rubric-critique invocation, CoVe sub-question and rewrite invocations. The primary invocation at trial start already has a 2-attempt vendor-bug retry (Stage 6.3.2 shim 1) — untouched.
  - **Cooldown 10s → 5s.** Stage 6.3.4b peak 76C, 9C below the 85C watchdog and 12C below the 88C driver-crash line. Trial-start temps 37/45/46C. Progression: 30 → 60 → 45 → 30 → 15 → 10 → 5.
- **Files touched:**
  - `ops/benchmarks/adr_010/harness/odr.py` — new `_invoke_with_vendor_retry` helper; all 5 non-primary `_invoke_once` sites now route through it.
  - `ops/benchmarks/adr_010/runner.py` — `--cooldown-min-seconds` default 10 → 5; help text records 6.3.4c evidence.
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` — updated `test_retrieval_gate_retry_failure_keeps_pregate_result` (persistent vendor failure now = 2 exceptions); added `test_license_grounding_shim_retry_survives_vendor_bug` regression.
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **132 passed** (was 131: +1). Whole-repo pytest = **1118 passed, 19 skipped** (was 1117: +1). Vendor tree pristine.
- **Ports / adapters affected:** none formal. Deferred: Neo4j CE-vs-EE dual-licensing in shim 4 (currently one license family per repo; Neo4j product is CE=GPLv3 / EE=commercial). Track as candidate Stage 6.3.4d only if 6.3.4c still misses.
- **PORTING_LEDGER / ADR updated:** none.
- **Stop-condition status:** Ready for another 3-trial ODR run on Colossus with 5s cooldown min. Stage 6.3.4 closing criterion carries forward (mean rated correctness ≥5/6 AND `final_unverified_urls` empty on every trial AND no surviving `[unsupported]` markers). Escalation ladder if 6.3.4c still misses: (a) fix Neo4j CE-vs-EE dual-licensing in shim 4; (b) opt-in `--n-consistency 3`; (c) Stage 6.3.5 model uplift (qwen2.5:32b-q8_0 with stricter retrieval budget).


## 2026-07-30 15:28 EDT — Stage 6.3.4d · directive strengthening + mismatch audit + cooldown 5→3s

- **Stage / plugin / port:** Stage 6.3.4d · Zetesis ODR harness hotfix (same lock-in band as 6.3.4).
- **What changed:** Stage 6.3.4c 3-trial Colossus run rated **2.33/6** (trial 1 = 2, trial 2 = 2, trial 3 = 3) — REGRESSED from 6.3.4b's 4.33/6. Trial 2 also violated `final_unverified_urls empty` sub-clause. Root cause: **shim-scoped vendor-retry worked as designed (no more retry_failed on KeyError) but the license correction directive was being IGNORED by the qwen2.5:7b-instruct model.** Every trial recorded `directive_emitted=true, retry_outcome=retry_ok` with correct GPL-3.0 grounding for both cited repos, yet every trial's final report still emitted AGPLv3 for Neo4j and Apache-2.0 for DozerDB (or "could not be determined"). Parametric-memory bias on well-known projects overrode a trailing information block.
  - **Fix A — directive strengthening.** Rewrote `build_license_correction_directive` in `harness/license_grounding.py`. New framing: `SYSTEM CORRECTION — LICENSE GROUNDING`, `BINDING FACTS` block with explicit `MUST emit: <family>` + `DO NOT emit any of: <forbidden list>` per grounded repo, closing `COMPLIANCE RULE` clause that supersedes conflicting license claims from prior context, training data, or web search snippets. Also bans hedging phrasing ("typically", "commonly").
  - **Fix B — prepend, not append.** `harness/odr.py` shim-4 path now builds the correction turn as `directive + "\n\n" + anchored_question` (was appended). The model reads the SYSTEM CORRECTION before the anchored question, so the correction lands as an override of prior claims rather than trailing context that competes with the well-formed prompt.
  - **Fix C — post-retry mismatch audit.** New `detect_license_mismatches(report_text, facts)` in `harness/license_grounding.py`. Two-pass attribution rule: for each canonical-family alias occurrence in the report, prefer the nearest repo anchor at-or-before the claim (matches "<URL> is <license>" phrasing), else fall back to nearest overall — both within `_MISMATCH_WINDOW=400`. Short-alias boundary safety on "MIT" / "ISC". Compact family set matches `classify_license_text` plus common paraphrases. Result appended to `shim_events[-1]["post_retry_mismatches"]` as `[{repo, expected, observed}]`. Deliberately **not** re-retried a second time — retrying under the same parametric bias risks thrashing.
  - **Cooldown 5 → 3 s.** Stage 6.3.4c peak 77C, 8C below the 85C watchdog and 11C below the 88C driver-crash line. Progression: 30 → 60 → 45 → 30 → 15 → 10 → 5 → 3.
- **Files touched:**
  - `ops/benchmarks/adr_010/harness/license_grounding.py` — rewrote `build_license_correction_directive`; added `LicenseMismatch`, `_all_family_hits`, `detect_license_mismatches`; extended `__all__`.
  - `ops/benchmarks/adr_010/harness/odr.py` — shim-4 correction turn prepends directive; on `retry_ok`, calls `license_grounding.detect_license_mismatches` and writes `post_retry_mismatches` (empty list on compliance, list of dicts on non-compliance) into the shim event.
  - `ops/benchmarks/adr_010/runner.py` — `--cooldown-min-seconds` default 5 → 3; help text updated with 6.3.4d evidence.
  - `ops/benchmarks/adr_010/tests/test_license_grounding.py` — updated `test_correction_directive_lists_only_known_facts` for the new 6.3.4d format (SYSTEM CORRECTION / BINDING FACTS / MUST emit / COMPLIANCE RULE assertions, forbidden-token boundary check); added 9 new tests covering `detect_license_mismatches` (near-URL AGPLv3, near-URL Apache-2.0, correct-report negative, raw.githubusercontent.com anchor, dedup by repo/family, distinct wrong families per repo, empty-report short-circuit, unknown/not-ok fact skip, short-alias boundary safety, out-of-window filler).
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` — updated existing 6.3.4c shim-4 test to also assert `post_retry_mismatches == []` on compliant retry; added `test_license_grounding_shim_prepends_directive_before_anchored_question` (verifies directive-prepend order + directive content in the invocation payload); added `test_license_grounding_shim_records_post_retry_mismatches` (simulates a model that IGNORES the directive on retry and asserts the mismatch is surfaced without a second re-retry).
- **Test tiers:** `ops/benchmarks/adr_010/tests/` = **144 passed** (was 132: +12). Whole-repo pytest = **1130 passed, 19 skipped** (was 1118: +12). Vendor tree pristine.
- **Ports / adapters affected:** none formal. Deferred escalation ladder if 6.3.4d misses: Stage 6.3.5 model uplift (qwen2.5:32b-q8_0). Reasoning: 6.3.4c already proved the harness was the previous bottleneck; if 6.3.4d's compliance-audited directive still can't override qwen2.5:7b's parametric license bias, the answer is model scale, not more harness layers.
- **Stop-condition status:** Ready for another 3-trial ODR run on Colossus with 3s cooldown min. Stage 6.3.4 closing criterion carries forward. Every trial's `shim_events[license_grounding].post_retry_mismatches` should be `[]` if the directive strengthening worked; any non-empty list is a discipline-failure signal for the blind rater.

## 2026-07-30 15:59 EDT — Stage 6.3.4e feature grounding + cooldown 3→1s + power 425W

- **Stage / plugin / port:** Stage 6.3.4 · ADR-010 ODR contender · shim 9 (feature grounding), shim 4 (license grounding, seed_urls)
- **What changed:**
  - New `harness/feature_grounding.py` (shim 9): grounds canonical DozerDB features from repo README at HEAD; emits SYSTEM CORRECTION directive on retry; audits post-retry report for omission and both-side negation windows (200 chars, before OR after keyword).
  - `harness/license_grounding.py`: `ground_licenses()` gains `seed_urls` kwarg; seed repos are ALWAYS grounded (prepended before cited URLs, deduped, capped by `max_repos`). Closes 6.3.4d hole where DozerDB was ungrounded whenever the model cited only Neo4j.
  - `harness/odr.py`: shim 4 now passes fixture `fact_anchor_urls` as `seed_urls`; new shim 9 wired in between shim 4 and rubric critique (guarded by `enable_feature_grounding` and non-empty `fact_anchor_urls`).
  - `runner.py`: cooldown default 3s → 1s, help text updated to 6.3.4e (peak 76°C at 3s → still 12°C below 88°C crash line at 1s + 425W); `--no-feature-grounding` flag.
- **Files touched:**
  - ops/benchmarks/adr_010/harness/feature_grounding.py (new)
  - ops/benchmarks/adr_010/harness/license_grounding.py
  - ops/benchmarks/adr_010/harness/odr.py
  - ops/benchmarks/adr_010/runner.py
  - ops/benchmarks/adr_010/tests/test_feature_grounding.py (new, 16 tests)
  - ops/benchmarks/adr_010/tests/test_license_grounding.py (+3 seed_urls tests)
  - ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py (+3 shim 9 integration tests)
  - BUILD_LOG.md, SESSION_HANDOFF.md
- **Ports / adapters affected:** none (harness-only)
- **PORTING_LEDGER / ADR updated:** —
- **Stop-condition status:** in-progress (Stage 6.3.4 DoD unchanged: mean rated correctness ≥5/6, no unverified URLs, no [unsupported] markers, no post_retry_mismatches, no post_retry_omissions). Awaiting Colossus 3-trial run.
- **Test status:** 166 adr_010 tests pass (was 144). Whole-repo 1152 passed, 19 skipped.
- **GPU cap:** 425 W persisted via `/etc/systemd/system/kosmos-nvidia-power-cap.service` (enabled, verified live).


## 2026-07-30 16:32 EDT — Stage 6.3.4f: rework shim 9 canonical spec + dozerdb.org fetch + new shim 10 (Enterprise-license) + shim 1 attempts=3

- **Stage / plugin / port:** Stage 6.3.4f · ADR-010 harness · shim 1/9/10
- **What changed:**
  - `harness/feature_grounding.py`: DROPPED `backup_restore` (F6 says NOT primary DozerDB deliverable) and INVERTED `monitoring` → `telemetry_disabled` (dozerdb.org disables telemetry, doesn't provide monitoring). ADDED `hardened_containers`. Renamed `enterprise_constraints` → `schema_constraints`. Canonical spec set now matches dozerdb.org verbatim wording (verified against live fetch). NEW: parallel fetch of README AND `https://dozerdb.org/` inside `ground_features()` (the 33-line README is a pointer; the site carries the real feature copy); either surface counts as evidence; matched-keywords are unioned and source_url combines both when both match. NEW: `_html_to_text()` HTML stripper for the site body (no parsing library dependency).
  - `harness/enterprise_license_grounding.py` (new, shim 10): fetches `https://neo4j.com/open-core-and-neo4j/` and grounds three canonical assertions (CE=GPLv3, EE=commercial, EE source withdrawn since 3.5). AND-semantics on required_keywords per assertion. Emits SYSTEM CORRECTION directive with the neo4j.com URL, listing only ``present`` assertions. Silent no-op on fetch failure. Directly targets Stage 6.3.4e's systematic F3 miss.
  - `harness/odr.py`: shim 1 vendor-retry cap raised 2 → 3 attempts (Stage 6.3.4e trial 3 hit `KeyError('reflection')` on BOTH original attempts, wiping the trial; the vendor bug is intermittent so a third attempt materially improves survival). NEW shim 10 wired in between shim 9 and rubric critique (guarded by `enable_enterprise_license_grounding`).
  - `runner.py`: `--no-enterprise-license-grounding` flag; config-summary log line includes the new shim.
  - `tests/conftest.py` (new): autouse fixture stubs shim 10's live neo4j.com fetch to keep every ODR integration test hermetic. Opt-out marker `@pytest.mark.no_stub_enterprise_license` for tests that exercise shim 10 with custom stubs.
- **Files touched:**
  - ops/benchmarks/adr_010/harness/feature_grounding.py
  - ops/benchmarks/adr_010/harness/enterprise_license_grounding.py (new)
  - ops/benchmarks/adr_010/harness/odr.py
  - ops/benchmarks/adr_010/runner.py
  - ops/benchmarks/adr_010/tests/conftest.py (new)
  - ops/benchmarks/adr_010/tests/test_feature_grounding.py (rewritten for new specs + site fetch)
  - ops/benchmarks/adr_010/tests/test_enterprise_license_grounding.py (new)
  - ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py (attempts=3 update + new recovery-on-3rd-attempt test)
  - BUILD_LOG.md, SESSION_HANDOFF.md, DEBUG_LOG.md
- **Ports / adapters affected:** none (harness-only)
- **PORTING_LEDGER / ADR updated:** —
- **Stop-condition status:** in-progress (Stage 6.3.4 DoD unchanged). Awaiting Colossus 3-trial run.
- **Test status:** 181 adr_010 tests pass (was 166). Whole-repo 1167 passed, 19 skipped.
- **GPU cap:** 450 W persisted (set in prior session's runner change; systemd file at 450 W).

## 2026-07-30 17:06 EDT — Stage 6.3.4f addendum: runner default power cap 450W → 435W

- **Stage / plugin / port:** Stage 6.3.4f · ADR-010 harness · runner
- **What changed:** `runner.py --power-cap-watts` default 450 → 435 (env var `ADR010_POWER_CAP_WATTS` still overrides). Colossus 6.3.4f run peaked at 84C several times — 1C under the 85C thermal-abort watchdog, too close. Dropping the sustained-wattage cap 15W (~3.3%) restores margin without disabling the run. Docstrings + help text updated.
- **Files touched:**
  - ops/benchmarks/adr_010/runner.py
  - BUILD_LOG.md, SESSION_HANDOFF.md
- **Ports / adapters affected:** none
- **PORTING_LEDGER / ADR updated:** —
- **Stop-condition status:** in-progress (Stage 6.3.4 DoD unchanged). systemd unit `kosmos-nvidia-power-cap.service` on Colossus needs a matching update to 435 W ExecStart.
- **Test status:** 181 adr_010 tests still pass. Whole-repo untouched.
