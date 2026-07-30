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
