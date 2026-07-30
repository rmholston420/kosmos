# ADR-048 — Stage 4.3 · Agent Memory Guard v0.3.0 adoption + `Policy.tiered()` default

**Status:** Ratified v25
**Lock-in phase:** Stage 4.3 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.3 in `Kosmos-Build-Sequence-v25.md` mandates a pre-Phase-3 check of
[OWASP `agent-memory-guard`](https://github.com/OWASP/www-project-agent-memory-guard)
releases: "if newer than v0.2.2 → adopt, log to PORTING_LEDGER + BUILD_LOG."

State on **2026-07-30 07:52 EDT**:

- Upstream `v0.3.0` shipped 2026-06-10 and is published on PyPI as
  `agent-memory-guard==0.3.0`.
- The v0.3.0 release ("MCP Server, CLI Scanner, ML Detection, GitHub Action")
  adds substantial capability (MCP server, CLI scanner, ML injection
  detector, GitHub Action, LlamaIndex + CrewAI integrations, Prometheus
  exporter, `Policy.tiered()` preset with default memory-class taxonomy,
  `SecurityEvent` gains `source_class` / `receipt_uri` / `retire_if`,
  provenance-based memory classes, self-reinforcement detector).
- The v0.3.0 public API is a **strict superset** of v0.2.2:
  - `Policy.strict()` still exists (v0.2.2-compatible baseline).
  - `MemoryGuard(policy=...)` constructor signature is compatible.
  - `MemoryGuard.write(key, value, ...)` gains **optional** kwargs
    (`source_class`, `receipt_uri`, `cls`, `task_id`) — no required kwargs
    added.
  - `MemoryGuard.snapshot(label=...)` and `MemoryGuard.rollback(snapshot_id=...)`
    are unchanged.
  - `PolicyViolation` still raised for blocks.

Adopting v0.3.0 is a **vendor version bump on a load-bearing adapter**
(`AmgV02Policy` at `adapters/memory/dozerdb/amg_v02_policy.py`, wired into
`DozerDbMemoryAdapter` alongside `DozerDbGraphBackend` and
`GraphitiTemporalIndex` at Stage 4.2 per ADR-027 and ADR-047). Kosmos custom
instructions require an ADR for any adapter swap or version pin change on a
formal port, even when the API surface is backwards-compatible.

## Decision

Adopt `agent-memory-guard==0.3.0` at Stage 4.3, immediately after Stage 4.2
landed. Concretely:

**Q1 — Adopt v0.3.0?** Yes. Bump `pyproject.toml` pin
`agent-memory-guard==0.2.2` → `agent-memory-guard==0.3.0`. No other dep
graph change (v0.3.0 ships with the same minimal dep set on the vendor
side).

**Q2 — Default policy preset?** `Policy.tiered()` becomes the default for
the Kosmos AMG wrapper. Rationale: `Policy.tiered()` was purpose-built in
v0.3.0 to expose the new default memory-class taxonomy (session /
durable / promoted). Kosmos zero-trust writes (spec §7 + ADR-008) already
carry provenance and confidence; the tiered promotion model matches the
Kosmos memory-lifecycle semantics far better than the flat
`Policy.strict()` block-list. `Policy.strict()` remains available via
`AmgGuardPolicy(policy_preset="strict")` for callers that want the
v0.2.2-shaped behaviour.

**Q3 — Adapter naming?** Rename the concrete class to `AmgGuardPolicy` in
a new module `adapters/memory/dozerdb/amg_policy.py`. Retain
`AmgV02Policy` as a module-level alias pointing at `AmgGuardPolicy` for
**one release cycle** (removed at Stage 5) so downstream call sites
importing `from adapters.memory.dozerdb import AmgV02Policy` keep working
during the transition. The old `amg_v02_policy.py` module becomes a
one-line re-export shim.

**Q4 — Surface the new write kwargs?** Yes, opt-in via payload keys.
`AmgGuardPolicy.evaluate(payload)` extracts optional payload keys
`source_class` / `receipt_uri` / `memory_class` (or `cls`) / `task_id` /
`source` and forwards them as `MemoryGuard.write(...)` kwargs. Payloads
that omit these keys behave exactly as before (all v0.3.0 write kwargs
are optional). Extracted keys are stripped from the JSON-serialised
`value` body so routing fields never pollute the semantic write payload.

**Q5 — Adopt MCP server / CLI scanner / GitHub Action / integrations?**
No. Out of scope for Stage 4.3. Kosmos remains a single-user local-first
system (project custom instructions); we do not run cross-project CI, do
not expose an MCP server surface, and do not adopt LlamaIndex / CrewAI
directly. If future stages need the CLI scanner as an ops utility we
will author a follow-up ADR.

**Q6 — Adopt ML injection detector?** Not automatically. The default
detector set includes the string-pattern `PromptInjectionDetector` from
v0.2.2. The v0.3.0 `MLInjectionDetector` requires a model artifact and a
first-run download; we do not enable it by default under Stage 4.3.
Adopting it becomes a Stage 5+ decision when we have a bench for
false-positive rates against the R.M. Holston lifeline corpus.

## Rationale

**Why bump now vs later:** Stage 4.3 is the spec-defined lock-in phase for
this check (Build-Sequence §4.3, spec §643). v0.3.0 has been out ~7 weeks
and is on PyPI with a stable API surface. Deferring the bump risks it
becoming a merge-conflict during Stage 4.4 (Superpowers KB port) which
also touches MemoryPort wiring.

**Why `Policy.tiered()` default:** aligns with the Kosmos memory-lifecycle
model (short-lived agent scratch → durable long-term facts) that Stage 4.2
just measured against three corpora. `Policy.strict()` was chosen at
Stage 1.8 only because it was the sole preset available in v0.2.2.

**Why keep `AmgV02Policy` alias for one release:** minimises blast radius
during the bump. Downstream callers (Compose docs, contract tests,
plugin wiring in later stages) can import either name during the
transition window. Removing the alias at Stage 5 forces the rename
without an urgent flag day now.

**Why not adopt MCP / CLI / ML detector today:** each is its own trade-off
surface (network surface for MCP, ML model artifact for detector) and
belongs behind its own ADR when the need arrives. Adopting the whole
v0.3.0 surface here would violate the "one-person-module scope" rule.

## Alternatives rejected

**A. Keep v0.2.2 (spec-literal, log-only).** Rejected: v0.3.0 is a
supported release, the API is backwards-compatible, and the tiered
memory-class model is a meaningful upgrade to the write-path guarantees
we already advertise. Deferring the bump has no benefit and accumulates
future-merge risk.

**B. Bump but keep `Policy.strict()` as the default.** Rejected: leaves
the tiered promotion model unused and forces every future caller to
explicitly opt in. `Policy.strict()` remains selectable via
`policy_preset="strict"` for callers that want the v0.2.2 shape.

**C. Full v0.3.0 adoption (MCP server + CLI + ML detector + LlamaIndex +
CrewAI + Prometheus exporter).** Rejected: violates one-person-module
scope and adds several distinct evaluation surfaces to a single
adapter-level bump. Each of those integrations is a Stage 5+ decision
with its own ADR.

**D. Skip the alias and rename immediately.** Rejected: minor churn
avoidance. Keeping the alias through Stage 5 costs ~4 lines of code and
one deprecation entry.

## Consequences

**Files changed:**

- `pyproject.toml` — pin `agent-memory-guard==0.2.2` → `==0.3.0`.
- `adapters/memory/dozerdb/amg_policy.py` — **new** module hosting
  `AmgGuardPolicy` with `policy_preset="tiered"` default,
  `source_class` / `receipt_uri` / `cls` / `task_id` / `source` payload
  kwargs threading, and body-key stripping.
- `adapters/memory/dozerdb/amg_v02_policy.py` — reduced to a re-export
  shim (`AmgV02Policy = AmgGuardPolicy`) that will be deleted at Stage 5.
- `adapters/memory/dozerdb/__init__.py` — export `AmgGuardPolicy` and
  keep exporting `AmgV02Policy` for the transition window.
- `adapters/memory/dozerdb/adapter.py` — docstring updated (AMG v0.3.0 +
  ADR-048 reference; `AmgGuardPolicy` named as the production
  implementation).
- `adapters/memory/dozerdb/test_amg_policy_contract.py` — renamed from
  `test_amg_v02_policy_contract.py`; new tests for tiered default,
  strict opt-in, backcompat alias, and all five v0.3.0 write kwargs.
  20 fast tests + 2 env-gated live tests.
- `docs/PORTING_LEDGER.md` — `agent-memory-guard` entry amended
  v0.2.2 → v0.3.0 with the release-notes summary + ADR-048 reference.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-048 row appended.
- `docs/adrs/README.md` — ADR-048 row appended.
- `docs/Kosmos-Build-Sequence-v25.md` §4.3 — rewritten as LANDED.
- `BUILD_LOG.md` — Stage 4.3 append.
- `SESSION_HANDOFF.md` — overwrite pointing at Stage 4.4.

**Behaviour changes:**

- Default AMG policy shifts from strict block-list to tiered promotion
  model. Any call site that constructed `AmgV02Policy()` and relied on
  strict-block-list semantics must migrate to
  `AmgGuardPolicy(policy_preset="strict")`. There are no such call sites
  in-tree today (only contract tests, which cover both presets).
- Payloads may now include the AMG routing keys listed above. Those keys
  will be extracted before the payload is JSON-serialised into the AMG
  `value`, so the on-disk body shape changes for callers who used those
  key names in the semantic payload. There are no such callers in-tree.

**Non-changes:**

- `AmgPolicy` Protocol shape (`evaluate(payload) → AmgVerdict`) unchanged.
- `DozerDbMemoryAdapter` construction / DI seams unchanged.
- Zero-trust fail-safe (init failure / write error / snapshot failure)
  unchanged; all still emit `AmgVerdict(decision="block")`.
- `AmgV02Policy` symbol still importable through Stage 5.

## Lock-in phase

Stage 4.3 (this ADR). Removal of the `AmgV02Policy` alias locks in at
Stage 5 (which will be its own ADR only if additional cleanup is needed).

## References

- `Kosmos-Build-Spec-v25.md` §643 (Stage 4.3 · Gnosis Phase 3 prerequisite)
- `Kosmos-Build-Sequence-v25.md` §4.3
- ADR-008 `ADR-008-DozerDB-memory-port.md` (MemoryPort zero-trust contract)
- ADR-027 `ADR-027-memoryport-dozerdb-graphiti-amg.md` (Stage 1.8 pin)
- ADR-047 `ADR-047-stage-4-2-corpora-hybrid-tier.md` (Stage 4.2 real backends)
- Upstream release notes: https://github.com/OWASP/www-project-agent-memory-guard/releases/tag/v0.3.0
- PyPI: https://pypi.org/project/agent-memory-guard/0.3.0/
