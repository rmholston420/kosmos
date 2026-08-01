# ADR-063 — Stage 6.5.6 · Tektos kernel mount + turn endpoint

**Status:** Ratified
**Lock-in phase:** Stage 6.5.6
**Supersedes:** —

## Context

The GUI shell (about to start at 6.6) needs a live Tektos surface:

- `tektos` plugin descriptor must appear on `/api/kernel/plugins` so
  the shell can lazy-load the Tektos route + panel.
- A REST verb must exist to drive one `TektosAgent` turn end-to-end
  (message in → assistant response + memory-event-id out).

At Stage 6.5.5 tip:

- `TektosPlugin` and `TektosAgent` are shipped in-tree with tests
  and contracts (Stage 3.1 + 3.7 landed).
- Neither is booted by the kernel; `/api/kernel/plugins` does not
  list `tektos`; there is no HTTP verb calling `TektosAgent.run()`.
- `registry` does not carry `LLMPort` or `MemoryPort` adapters,
  though Zetesis constructs its own internally.

This slice mounts Tektos on the kernel, adds kernel-owned `LLMPort`
and `MemoryPort` adapters (shared surface for future plugins), and
opens `POST /api/tektos/turn`.

## Decision

### D1. Registry additions

Five new fields on `_BootRegistry`:

- `llm: LLMPort | None` — `OllamaAdapter`
- `memory: MemoryPort | None` — `DozerDbMemoryAdapter` with in-memory
  backends (matches Zetesis Stage 6.5 pattern — real DozerDB attaches
  when neo4j-compose lands on Colossus)
- `tektos: TektosPlugin | None` — descriptor registration
- `tektos_agent: TektosAgent | None` — long-lived agent instance
- `tektos_agent_lock: asyncio.Lock | None` — serializes concurrent
  turn requests

### D2. Boot order

Appended to `lifespan()` after Phrouros wire, before Zetesis mount:

1. `llm` — via `_boot_llm` closure using env vars
   `KOSMOS_OLLAMA_BASE_URL` (default `http://127.0.0.1:11434/v1`) and
   `KOSMOS_TEKTOS_MODEL` (default `qwen2.5:32b-instruct-q4_K_M`).
   `OllamaAdapter` construction is side-effect-free (no HTTP call at
   `__init__`) so boot never blocks on Ollama availability.
2. `memory` — via `_boot_memory` closure constructing
   `DozerDbMemoryAdapter(graph=InMemoryGraphBackend(),
   amg=NoOpAmgPolicy(), temporal=InMemoryTemporalIndex())`.
3. **Tektos mount** — depends on `frontend_contract` + `llm` +
   `memory`. If any dependency missing, records failure reason on
   `registry.errors["tektos"]` and continues. Otherwise instantiates
   `TektosPlugin(frontend_contract_port=…)`, awaits `.start()`
   (descriptor registration), stores it on `registry.tektos`,
   constructs `TektosAgent(llm=…, memory=…)` and stores on
   `registry.tektos_agent`, and creates `registry.tektos_agent_lock`.

### D3. Shutdown

Before existing Zetesis stop:

- `tektos.stop()` — deregisters descriptor from
  `FrontendContractPort`. Idempotent per plugin contract.
- `llm.close()` — closes the shared `httpx.AsyncClient` on the Ollama
  adapter. Best-effort.

### D4. Endpoint

`POST /api/tektos/turn`:

- Body: `{"content": <non-empty str>}`.
- Serialized via `registry.tektos_agent_lock` so a caller never sees
  `TektosAgentAlreadyRunError` from an overlapping request.
- Response 200 with `TektosStep` JSON (via `_dataclass_to_dict`).
- 400 on missing/empty content, non-string content, non-JSON body,
  or `ValueError` / `TektosAgent*Error` from the agent.
- 502 on upstream adapter failure (Ollama unreachable, memory write
  failure) — kernel is up, dependency failed.
- 503 when `registry.tektos_agent is None` (subsystem down).

### D5. Health surface

`/health.subsystems` gains three bools: `llm`, `memory`, `tektos`.
`boot_errors["tektos"|"llm"|"memory"]` surface via the same
`registry.errors` map as every other subsystem.

### D6. Kernel-plugin coupling

The kernel imports `plugins.tektos.plugin.TektosPlugin` and
`plugins.tektos.agent.TektosAgent` only from the boot block. The
`/api/tektos/turn` handler catches `TektosAgent*Error` by class name
(`type(exc).__name__`) to keep the exception import out of
`kernel/app.py`. `ValueError` uses `isinstance` since it's stdlib.
Consistent with ADR-062's approach to Praxis APEX errors.

### D7. Version

`kernel/app.py` version 6.5.5 → 6.5.6.

### D8. Tests

Kernel-side integration tests use monkey-patched fake `LLMPort` and
`MemoryPort` (matching the `_FakeLLMPort` / `_FakeMemoryPort` pattern
from `plugins/tektos/tests/test_tektos_agent.py`) injected before
`TestClient` startup so the tests never hit Ollama or the real
memory backend. Uses `pytest` fixtures that patch
`kernel.app.registry` after startup, since fakes need to be swapped
into `registry.llm` / `registry.memory` / rebuild the agent before
the endpoint runs.

## Rationale

**Why kernel-owned LLM + Memory adapters** — Tektos is the second
consumer of both ports (Zetesis was first, but Zetesis constructs
them internally). A third consumer is imminent (Praxis will need
LLM at 6.6). Promoting them to registry avoids each plugin
constructing (and later closing) its own `httpx` client. Matches
the `event_bus` + `resource` + `notification` sharing pattern
from ADR-058.

**Why in-memory Memory backends at 6.5.6** — real DozerDB attaches
when `neo4j-compose` lands on Colossus. This mirrors the Zetesis
Stage 6.5 pattern: mount now, swap backends later without touching
plugin code. `NoOpAmgPolicy` is safe because Tektos always writes
with provenance + confidence per its own contract.

**Why an asyncio.Lock around the agent** — `TektosAgent` at Stage
3.1 is single-turn: `send_message()` overwrites any pending turn,
and a concurrent `run()` after `send_message()` from a second
request would race. The lock serializes without changing the agent
contract; multi-agent parallelism is a Stage 3.5+ concern.

**Why 502 on upstream adapter failure** — matches HTTP semantics:
502 means "the gateway (kernel) got a bad response from an
upstream service" (Ollama, memory backend). The kernel itself is
healthy, so 500 would misdirect the client.

**Why env-var overrides for Ollama** — Colossus default matches
Zetesis's ADR-058 default (`qwen2.5:32b-instruct-q4_K_M`). Env-var
overrides let CI or a smoke script point at a stub without
hard-coding a test-only path in production kernel boot.

**Why not the Zetesis pattern of an internal factory** — Zetesis's
internal factory predates the kernel-shared adapter pattern
introduced in ADR-058. A Stage 6.6+ ADR may refactor Zetesis to
consume kernel-owned `LLMPort` + `MemoryPort` too; deferred.

**Alternatives rejected:**

- Inline `TektosAgent` construction on every request — wastes the
  httpx pool and defeats the Stage 3.5 multi-turn design.
- Per-request `model`/`system_prompt` override — Stage 3.1
  `TektosAgent` locks these at construction. Multi-model routing is
  a Stage 3.5+ concern; deferred to a future ADR.
- Mount Tektos through `plugins.tektos.plugin.build_stage_*_factory`
  — no such factory exists at 6.5.6; the plugin's public surface is
  the dataclass constructor. Adding a factory now would be premature.

## Consequences

- Two new lines under `/health.subsystems` in every kernel probe.
- `/api/kernel/plugins` now lists `tektos` (unblocks the GUI shell's
  Tektos route lazy-load).
- `/api/kernel/routes` now includes `/tektos` per the descriptor
  registration.
- One new POST route.
- Version bump 6.5.5 → 6.5.6.
- `PORTING_LEDGER.md` unchanged — the adapters (`OllamaAdapter`,
  `DozerDbMemoryAdapter`) are already `VENDORED`/`WIRED` per
  ADR-058; this ADR only wires them at kernel boot.

## Lock-in phase

Stage 6.5.6 — this ADR ratified, `/api/tektos/turn` returns 200 with
a valid `TektosStep` on Colossus (against real Ollama), and
`/api/kernel/plugins` lists `tektos`.

## References

- Kosmos-Build-Spec-v25.md §21 (Rollout Plan · Stage 6.5)
- ADR-007 (events-only cross-plugin coupling)
- ADR-031 (FrontendContract descriptor shape)
- ADR-036 (Tektos agent Stage 3.1)
- ADR-041 (Tektos descriptor Stage 3.7)
- ADR-057 (kernel-owned route surface)
- ADR-058 (kernel-shared adapters)
- ADR-062 (approval resolve endpoints — kernel-plugin decoupling
  precedent)
- `plugins/tektos/plugin.py`
- `plugins/tektos/agent.py`
- `adapters/llm/ollama/adapter.py`
- `adapters/memory/dozerdb/adapter.py`
