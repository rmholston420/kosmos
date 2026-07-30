---
name: kosmos-port-workflow
description: Load before writing any new component in the Kosmos monorepo. Enforces the vendor-before-hand-build rule from Kosmos-Build-Spec-v25.md — inspects donor repos (Rigpa-LMS, Forge-OH, PlexClaw, axiom, plus permissively-licensed OSS candidates), logs the port in PORTING_LEDGER.md with source URL / commit SHA / SPDX license / modification notes, then wraps the port behind a formal port from ports/. Use for any task worded as "add X", "implement Y", "wire up Z", or "port from A" inside the Kosmos project.
---

# Kosmos Port Workflow

## When to use

Load this skill **before** writing any new adapter, plugin subsystem, or utility inside the `kosmos/` monorepo. Do not write greenfield code without first running the workflow below.

## The workflow

### 1. Restate scope

Confirm from `Kosmos-Build-Spec-v25.md`:
- Which **stage / plugin / port** the work belongs to.
- Which **Definition of Done** applies.
- Which **stop condition** ends the current sub-task.

If ambiguous, stop and ask the user before proceeding.

### 2. Inspect donor code first

Search for existing implementations before writing anything new:

```bash
# Rigpa-LMS is current-state code to refactor, not reference
find /path/to/Rigpa-LMS -type f -name "*.py" | xargs grep -l "<pattern>" 2>/dev/null

# Sibling projects for permissively-licensed patterns
find /path/to/{Forge-OH,PlexClaw,axiom} -type f -name "*.py" | xargs grep -l "<pattern>" 2>/dev/null
```

Read every match with the `read` tool. Do **not** copy without reading.

### 3. Search for an OSS port

If donor code does not cover it, search for a permissively-licensed OSS component:

- Search terms: focus on the port contract, not implementation flavor.
- License filter: MIT · BSD-2/3 · Apache-2.0 · ISC · MPL-2.0. **Refuse** GPL/AGPL/BUSL/SSPL without explicit user override + ADR.
- Prefer components already listed in `PORTING_LEDGER.md` as `PLANNED` for the current stage.

### 4. Log the port in PORTING_LEDGER.md BEFORE first commit

```markdown
#### <Component Name> — VENDORED
- **Source:** <upstream URL>
- **Commit / Version:** <SHA or tag>
- **License:** <SPDX>
- **Kosmos location:** `<path in monorepo>`
- **Port(s):** <formal port name(s)>
- **Modifications:** <bullet list; "none" if unmodified>
- **ADR:** <ADR-###> or `—`
- **Logged:** <YYYY-MM-DD HH:MM EDT>
```

Append to the appropriate section of `PORTING_LEDGER.md`. Do not re-order for prettiness.

### 5. Wrap behind a formal port

Every vendored component sits behind exactly one adapter under `adapters/<port>/<component>/` that implements the corresponding `Protocol` in `ports/`. Plugins must not import the vendor directly.

If no port fits, stop and escalate — a new port requires an ADR.

### 6. Enforce ADR-007 (events-only cross-plugin coupling)

- **No plugin may import another plugin.**
- Cross-plugin needs → `EventBusPort` or a formal port.
- Pre-commit hook must fail if this rule is violated.

### 7. Enforce zero-trust MemoryPort writes

Any code path writing through `MemoryPort` must supply:
- `provenance` — where this fact came from
- `confidence` — 0.0–1.0

Reject at protocol layer if either is missing.

### 8. Test contract

- Write a contract test in `adapters/<port>/<component>/test_contract.py`.
- Test must pass with the adapter and pass again after swapping to a different adapter for the same port (protocol conformance test).

### 9. Append to BUILD_LOG.md

Delegated to `kosmos-log-maintenance` skill. Do not skip.

## Stop conditions

- License is not permissive → stop, escalate to user with ADR proposal.
- No formal port fits → stop, escalate.
- Vendored component would import into plugin space without adapter → stop.
- Contract test fails → stop; do not commit.
- Colossus resource envelope (128GB RAM / 32GB VRAM) would be exceeded → stop.

## References

- `Kosmos-Build-Spec-v25.md` §4 (Ports), §17 (ADRs)
- `Kosmos-Build-Sequence-v25.md` (cross-cutting duties)
- `PORTING_LEDGER.md`
- `adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `adrs/ADR-008-DozerDB-memory-port.md` (memory write contract)
