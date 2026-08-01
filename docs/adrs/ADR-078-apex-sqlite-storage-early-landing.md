# ADR-078 — Early landing of `SqliteStorage` for APEX approval records

**Status:** Accepted
**Date:** 2026-08-01
**Stage tag:** Stage 3.13.2 (follow-up to Stage 3.13.1, ADR-077 D2a)
**Supersedes:** — (docstring in `plugins/praxis/apex/storage.py` pinning
`SqliteStorage` to "Stage 5 durable wiring"; this ADR pulls it in early
without changing the Stage 5 scope).

## Context

Stage 3.13 (ADR-077) landed `POST /api/tektos/intention` and the
approval-gated PlanCard flow. Stage 3.13.1 landed
`GET /api/tektos/plan/{approval_id}` + a readable detail page.

Both surfaces rely on `plugins.praxis.apex` (APEX) as the approval
store. APEX's default `Storage` adapter is `InMemoryStorage`
(`plugins/praxis/apex/storage.py`), whose dict-backed state is wiped
on every `systemctl restart kosmos-kernel`. In practice this makes
`/tektos/detail?id=<approval_id>` 404 the moment the kernel restarts
for any other reason (fix deployment, unit reload, machine reboot),
so the Tektos workflow can only be exercised inside a single kernel
lifetime. That is fine for tests but not usable as a real review
loop.

`SqliteStorage` in the same module was already declared as the
intended non-in-memory adapter (schema in its docstring), but every
verb raised `NotImplementedError` with the comment "Stage 5 durable
wiring will replace the bodies."

## Decision

Implement `SqliteStorage` now (Stage 3.13.2), ahead of the Stage 5
durable-wiring ADR, on a strict superset of the following constraints:

1. **No engine refactor.** The `KernelChangeApprovalAdapter` engine
   already accepts any `plugins.praxis.apex.protocol.Storage`
   implementation. Only `_boot_approval` picks the adapter.
2. **Opt-in wiring.** Boot switch: `KOSMOS_APEX_DB_PATH`. Empty /
   unset → `InMemoryStorage` (test defaults unchanged). Non-empty →
   `SqliteStorage(path)`. This matches Kosmos custom instructions
   ("never introduce cloud control planes, multi-user assumptions",
   and "always give exact step-by-step commands" via the systemd
   drop-in below).
3. **Idempotent schema.** All `CREATE TABLE`/`CREATE INDEX`
   statements use `IF NOT EXISTS`. First connect enables
   `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`, then
   applies the schema in a single transaction. No migration tool
   yet — the schema is `v1` and any change lands as ADR-078a or a
   Stage 5 ADR.
4. **Aiosqlite is already a dep** (`pyproject.toml` line 26).
   No new vendor / port entry required.
5. **Contract parity.** `tests/plugins/praxis/apex/test_storage_contract.py`
   parametrizes every test over `["memory", "sqlite"]` so the two
   adapters remain interchangeable at the Protocol seam.
6. **No new port.** Reuses the existing `Storage` protocol in
   `plugins/praxis/apex/protocol.py`. No ADR-007 impact (single-plugin
   internal seam; no cross-plugin import path added).

## Deployment (Colossus)

Ship the systemd drop-in as part of this stage so a fresh install
picks up durable storage automatically:

    deploy/systemd/kosmos-kernel.service.d/20-apex-db-path.conf

Contents:

    [Service]
    Environment=KOSMOS_APEX_DB_PATH=/var/lib/kosmos/apex/approvals.sqlite
    StateDirectory=kosmos/apex
    StateDirectoryMode=0750

Deploy:

    sudo mkdir -p /etc/systemd/system/kosmos-kernel.service.d
    sudo cp deploy/systemd/kosmos-kernel.service.d/20-apex-db-path.conf \
      /etc/systemd/system/kosmos-kernel.service.d/
    sudo systemctl daemon-reload && sudo systemctl restart kosmos-kernel

`StateDirectory=kosmos/apex` makes systemd create + own
`/var/lib/kosmos/apex/` at 0750 on unit start and add it to the
unit's `ReadWritePaths` under `ProtectSystem=strict`. The
`SqliteStorage.__init__` code additionally calls `mkdir(parents=True,
exist_ok=True)` on the DB's parent as a safety net for non-systemd
launches (dev shell, tests).

## Migration path to DozerDB (Stage 5+)

Kosmos already runs DozerDB as its `MemoryPort` graph backend for
`plugins.gnosis`. Two open options for Stage 5:

- **(M1) Keep `SqliteStorage` permanently.** Approval records are
  not retrieval-shaped facts (no semantic search, no provenance
  chains at the record level — provenance already lives on each
  memory write, not on the approval envelope). Sqlite fits the shape
  and adds no operational surface.
- **(M2) Migrate to a DozerDB-backed `Storage` adapter.** Records
  become graph nodes; approvals gain uniform provenance / audit
  through the same MemoryPort discipline as facts.

That choice is explicitly deferred to a Stage 5 ADR — Kosmos custom
instructions flag "DozerDB vs. Neo4j Enterprise" (ADR-008) style
choices as requiring a formal ADR, and picking one now would front-run
that decision. Whichever path Stage 5 chooses, the Protocol seam does
not move: `_boot_approval` swaps the adapter class and everything else
stays the same.

## Consequences

- Tektos plans (Stage 3.13 / 3.13.1) become usable across restarts —
  fixes the observed `/tektos/detail` 404 on any post-restart id.
- No test-suite drift: default remains `InMemoryStorage` (no test uses
  the env var), and the new contract tests run against both.
- New file on disk under `/var/lib/kosmos/apex/` on Colossus after
  the systemd drop-in ships. Ownership `rmholston:rmholston`, mode
  0750, matches the Stage 3.13 intention-root layout.
- Stage 5 durable-wiring ADR now inherits a working baseline instead
  of a stub. The M1/M2 choice above is a real decision on top of a
  known-good local-first implementation.
