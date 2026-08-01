# ADR-058 — Stage 6.5 Zetesis Kernel Mount

**Status:** Ratified
**Lock-in phase:** Stage 6.5
**Supersedes:** —

## Context

Stage 6.4 (ADR-057) landed the kernel FastAPI shell: `/health` +
five `/api/kernel/*` introspection endpoints + resource/approval/
notification surfaces, backed by six kernel subsystems booted behind
per-subsystem try/except. All 11 endpoints return 200 on Colossus.

Zetesis is the first System-4 plugin (deep research). It already ships:
- A ratified 6.3.9-envelope factory (`build_stage_6_3_9_zetesis_plugin`)
  wiring 5 real adapters + 5 plugin-local stubs against the ADR-054
  5.33/6 rater floor.
- A full port surface via `ZetesisPlugin` (10 required ports + 1 optional).
- A locked descriptor (`build_zetesis_descriptor`) declaring one route
  path `/zetesis`.

Stage 6.5's job is to mount Zetesis into the running kernel so
`/api/kernel/routes` and `/api/kernel/plugins` return the descriptor,
without regressing the six-subsystem boot pattern.

Three decisions are load-bearing enough to lock in an ADR.

## Decision

### D1. Backend-health policy: graceful per-subsystem

The Zetesis plugin mount is a **seventh** subsystem in the same
try/except pattern as the existing six. A failure to mount surfaces
under `registry.errors["zetesis"]` and returns `zetesis: false` on
`/health.subsystems`. The kernel keeps running; `/api/kernel/plugins`
returns `[]`; every other endpoint stays 200.

**Rationale.** Matches the ADR-057 boot pattern verbatim. Prevents a
transient DozerDB/Ollama outage from taking the whole GUI down. The
one-line diff (`_try("zetesis")` → registry) is trivially reversible.

### D2. Adapter selection for the five previously-stubbed ports

At 6.3.9, MemoryPort/VectorPort/DataPort/ResourcePort/NotificationPort
were plugin-local stubs because the ADR-054 rater does not exercise
them and the deploy target had no running backends. At 6.5 we bind
real adapters, but pick backends that do not require a running daemon:

| Port | Adapter | Backend |
|---|---|---|
| MemoryPort | `DozerDbMemoryAdapter` | `InMemoryGraphBackend` + `InMemoryTemporalIndex` + `NoOpAmgPolicy` |
| VectorPort | `QdrantVectorAdapter` | `InMemoryQdrantBackend` (spec-endorsed until Compose lands) |
| DataPort | `FilesystemDataAdapter` | Rooted at `~/.local/state/kosmos/data` |
| ResourcePort | `SqliteResourceAdapter` | Shared with kernel `_boot_resource` |
| NotificationPort | `KernelNotificationAdapter` | Shared with kernel `_boot_notification` |

Every real adapter still enforces its zero-trust port-layer guard
(`validate_zero_trust_write` on MemoryPort, `validate_zero_trust_payload`
on VectorPort). Real DozerDB/Graphiti/AMG backends land at Stage 6.5.1
once neo4j-compose is on Colossus.

**Rationale.** Real *adapter classes* prove the port contracts. Real
*backends* land when their compose services do. This preserves ADR-054
5.33/6 parity when the 6.5.1 trial reruns.

### D3. Shared kernel-adapter reuse

Four ports (FrontendContractPort, EventBusPort, ResourcePort,
NotificationPort) reuse the kernel's live adapter instance rather than
constructing plugin-local copies. This is the *only* way the plugin's
descriptor becomes visible on the kernel's `/api/kernel/plugins`
endpoint — the FrontendContractPort holds state per-instance.

**Rationale.** Sharing FC is *required* for the descriptor to route
through the kernel's HTTP surface. Sharing event_bus/resource/
notification is *preferred* because there's one kernel-wide ledger,
one Valkey stream namespace, and one algedonic sink; multiple
instances would fragment state and multiply resource consumption on
Colossus's fixed envelope.

## Consequences

- New factory function `build_stage_6_5_zetesis_plugin()` in
  `plugins/zetesis/adapters/real/factory.py`; the 6.3.9 factory is
  preserved verbatim for ADR-054 trial parity.
- `kernel/app.py` lifespan gains a seventh block mounting the plugin
  after `frontend_contract`, and a shutdown block calling
  `plugin.stop()`. Kernel version bumps 6.4.0 → 6.5.0.
- `_BootRegistry` gains a `zetesis` field and `/health.subsystems`
  gains a `zetesis` bool.
- `PORTING_LEDGER.md` amended: DozerDbMemoryAdapter,
  QdrantVectorAdapter, FilesystemDataAdapter promoted from `PLANNED` /
  `VENDORED` to `WIRED` in Stage 6.5.
- Integration tests: mount lifespan smoke + descriptor registration
  check + `/api/kernel/{routes,plugins}` visibility.
- DoD: `/api/kernel/routes` contains an entry with `path == "/zetesis"`;
  `/api/kernel/plugins` contains an entry with `name ==
  "kosmos.plugin.zetesis"`; kernel boots without adding boot errors on
  Colossus.
- ADR-054 5.33/6 rater trial reruns at Stage 6.5.1 against the real
  DozerDB backend to verify no regression.

## Alternatives considered

1. **Fail-fast on plugin mount error.** Rejected — one plugin should
   not gate the whole kernel per the ADR-057 subsystem-independence
   principle.
2. **Fully-real backends at Stage 6.5.** Rejected — no
   `RealQdrantBackend` ships yet, and forcing Colossus to run DozerDB
   compose during 6.5 mount conflates two independent stages.
3. **Plugin-owned FrontendContractPort instance.** Rejected — the
   descriptor would only appear in the plugin's private store,
   invisible to `/api/kernel/plugins`.

## Lock-in phase

Stage 6.5 (Zetesis mount). Locked once
`bin/kernel-smoke-11.sh` on Colossus returns 200 for all endpoints
and `/api/kernel/plugins` returns a non-empty list containing
`kosmos.plugin.zetesis`.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary)
- ADR-046 (Phrouros deferral)
- ADR-052 (Zetesis port surface)
- ADR-054 (5.33/6 rater floor)
- ADR-057 (Stage 6.4 kernel shell)
- `plugins/zetesis/adapters/real/factory.py`
- `kernel/app.py`
- `PORTING_LEDGER.md`
