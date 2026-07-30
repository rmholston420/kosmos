# ADR: Beads as a Tektos Phase 3 TaskState/Plan-History Vendor Candidate

## Status
Proposed (requires Tier-2 ADR ratification; contingent on spike-test outcome)

## Context
Tektos v1 Phase 3 (Spec Studio, Durable TaskState, UI Tab) plans to extend Kosmos's shared TaskState pattern with Tektos-local additive columns (`spec_ref`, `plan_json`, `worktree_path`) in its own Postgres schema. Beads (`steveyegge/beads`, MIT, ~17.8K GitHub stars, v1.0.5 as of May 2026) is a purpose-built, actively maintained distributed graph issue tracker designed specifically for AI coding agents: hierarchical dependency-aware task IDs, atomic work-claiming, a `bd ready` command surfacing only unblocked work, and a Dolt-backed (version-controlled SQL) storage layer supporting cross-machine sync and git-independent operation. This is a closer functional match to Tektos's TaskState/plan-history problem than the current plan of hand-extending a generic pattern.

## Decision
Do not adopt Beads as Tektos's canonical TaskState store. Evaluate Beads's dependency-graph data model and `bd ready`-style unblocked-work query pattern as a design reference for Tektos's Postgres schema extension, but do not introduce Dolt as a second database technology inside Tektos's Tektos-local-Postgres-only rule.

## Rationale Against Direct Adoption
1. **Storage-technology conflict**: Tektos v1's core principle is "Postgres for Tektos-local state only." Beads's storage backend is Dolt (a version-controlled SQL engine), not Postgres. Adopting Beads directly would introduce a second database technology into Tektos-local state, contradicting the existing rule and adding a new entry to the quarterly DR-drill scope (already extended to four stores in the v20.1 Addendum) without proportionate benefit.
2. **Documented operational fragility**: A GitHub issue on the Beads repository (#1812, "AI Recommends To Drop Beads") documents real user-reported complexity from Beads's CGO/Dolt dependency, with the reporting user's own AI assistant recommending an alternative issue tracker. This is a credible signal of integration risk for a system (Kosmos) that already carries deliberate minimalism as a governing principle.
3. **Single-writer constraint**: Beads's embedded Dolt mode is single-writer only (file-locking enforced), which is a poor fit for Tektos's own multi-agent worktree model (Phase 4) where concurrent subtasks must merge without observing each other's uncommitted state — Beads would require server mode (a running Dolt SQL server) to avoid this constraint, adding an operational dependency Kosmos does not otherwise need.
4. **What is genuinely valuable**: Beads's core insight — replace markdown TODO plans with a dependency-aware graph so agents "never get lost" across context resets — is already Tektos's stated goal for durable TaskState. The valuable part is the *data model* (hierarchical IDs, dependency edges, atomic claim/close semantics, a computed "ready" view over blocked/unblocked work), not the Dolt storage engine.

## Adopted Pattern (Design Reference, Not Vendored Code)
Tektos's Postgres schema extension for TaskState (Phase 3) adds:
- Hierarchical task IDs (epic → task → subtask), mirroring Beads's `bd-a3f8`, `bd-a3f8.1`, `bd-a3f8.1.1` pattern, implemented as a Postgres ltree or adjacency-list column rather than a new ID scheme.
- A computed "ready work" view equivalent to `bd ready`: a query surfacing only tasks whose dependency edges are all resolved, backed by a `blocked_issues_cache`-style materialized view for performance on large task graphs (Beads added this optimization after measuring `bd ready` performance degradation at scale).
- Atomic claim/close semantics enforced at the Postgres transaction level, avoiding Beads's single-writer file-lock constraint entirely since Postgres already handles concurrent writers correctly.

## Build-Order Placement
No change to Rollout Plan sequencing. This is a design-reference adoption at Tektos Phase 3 (Durable TaskState), not a new vendored dependency, so no `PORTING_LEDGER.md` entry is required — the schema pattern is Kosmos-original, informed by Beads's public design, not derivative code.

## Definition of Done
- Tektos's TaskState schema (Phase 3) implements hierarchical task IDs and a computed ready-work view.
- A fixture task graph with 100+ nodes and mixed dependency chains resolves `ready` queries with acceptable latency, validated against the same performance concern that prompted Beads's own `blocked_issues_cache` optimization.
- No Dolt dependency is introduced anywhere in Tektos's stack.
