> **v25 STATUS AMENDMENT:** RATIFIED — spike-test APPROVED. Run head-to-head fixture (Bernstein Janitor vs. `local-agentic-loop-sample`) at Tektos Phase 4 per Build Sequence §3.4. Adopt Bernstein Janitor iff fixture wins. Benchmark artifact required in `ops/benchmarks/bernstein-vs-lals-<date>.md`.

---

# ADR: Bernstein as a Tektos Phase 4 Multi-Agent Safety Vendor Candidate

## Status
Proposed (requires Tier-2 ADR ratification per Kosmos v20 ADR practice; contingent on spike-test outcome, see Evaluation Plan)

## Context
Tektos v1's Phase 4 scope (Knowledge Base, KB Authoring, Self-Improvement, Multi-Agent Safety) currently plans to build Loop Guard and pre-merge conflict simulation by porting `dngoins/local-agentic-loop-sample` (MIT), covering branch isolation and trusted-actor gating. Bernstein (`chernistry/bernstein`, Apache-2.0) is an actively maintained, production-used open-source orchestrator that implements a materially similar architecture — deterministic Python scheduling, isolated git worktrees per agent, and a "Janitor" verification step (lint, type-check, tests) gating every merge — with 37+ CLI coding-agent adapters, an HMAC-chained audit log, signed agent cards, and measured results (1.78x throughput vs. single-agent baseline, 23% lower cost via mixed model routing, 4,250+ tests in its own repo)[cite:167][cite:168]. Per Kosmos's vendor-before-build principle, this warrants formal evaluation before Tektos Phase 4 build begins.

## Decision
Do not adopt Bernstein wholesale as a replacement for Tektos's existing agent-loop and governance stack. Instead, spike-test Bernstein's Janitor/worktree-orchestration subsystem as a candidate vendor component for Tektos's Multi-Agent Safety module specifically, in place of hand-porting `local-agentic-loop-sample`, contingent on the fixture evaluation defined below.

## Comparison: Bernstein vs. Current Tektos Plan

| Dimension | Tektos v1 current plan | Bernstein | Assessment |
|---|---|---|---|
| Agent loop / planning | OpenHands SDK (vendored, Phase 0.5) | Bernstein defers to underlying CLI agents (Claude Code, Codex, etc.) for planning; only initial goal-decomposition touches an LLM | No conflict — Bernstein operates one layer above the agent loop, not a replacement for OpenHands SDK |
| Coordination determinism | Not yet specified; Loop Guard planned from `local-agentic-loop-sample` | Deterministic Python scheduler, zero LLM tokens spent on coordination after initial decomposition[cite:167] | Bernstein's approach directly addresses the "excessive subagent spawning/distraction" failure mode Anthropic documented, more concretely than the current plan specifies |
| Isolation model | Sandboxed execution + worktrees (Tektos Phase 2, kernel capability broker-mediated) | Isolated git worktrees per agent, functionally equivalent | High overlap — Bernstein's worktree model must be reconciled with Kosmos's capability-broker-gated sandbox, not adopted as a parallel isolation layer |
| Pre-merge verification | Planned: pre-merge conflict simulation via ported sample | Janitor: lint, type-check, tests, optional cross-model review before merge, already implemented and tested[cite:167] | Bernstein's Janitor is more mature than the currently-planned port; strongest candidate for direct reuse |
| Audit trail | Kosmos kernel audit log (Merkle-anchored, ADR-007 events-only coupling) | HMAC-chained audit log, signed agent cards, per-artefact lineage[cite:160][cite:172] | Overlapping concern — Bernstein's audit chain would need to feed into Kosmos's kernel audit log via `EventBusPort`, not run as a parallel audit system |
| State storage | Postgres (Tektos-local schema) + `MemoryPort` | File-based state in `.sdd/` directory, plain repo files[cite:168] | Conflicts with Tektos's "Postgres for Tektos-local state only" rule; Bernstein's file-based state would need translation into Tektos's existing schema, not adopted as-is |
| License | N/A | Apache-2.0 | Compatible with Kosmos's PORTING_LEDGER.md requirements |
| Maturity signal | N/A (unbuilt) | ~33K monthly PyPI downloads, 254 GitHub stars, 4,250+ internal tests, verified 2026-05-02[cite:170] | Reasonable confidence for a Tier-1 vendor candidate; not yet at the scale of OpenHands SDK's MLSys-paper-backed maturity |

## Rationale for Partial (Not Wholesale) Adoption
1. **Events-only coupling (ADR-007)**: Bernstein's HMAC audit chain, worktree orchestrator, and file-based `.sdd/` state are each a parallel subsystem to something Kosmos already owns at the kernel level (audit log, capability-broker-mediated sandboxing, `MemoryPort`/Postgres). Wholesale adoption would violate the "no plugin-local kernel" principle Tektos v1 already establishes. Only the Janitor verification pattern is cleanly separable from Bernstein's own orchestration/audit/state layers.
2. **Bernstein's own design assumes it is the top-level orchestrator** coordinating external CLI agents (Claude Code, Codex, Gemini CLI, etc.) — Tektos's role inside Kosmos is the reverse: Tektos *is* the agent, operating inside Kosmos's kernel-mediated sandbox, not a CLI tool Kosmos would orchestrate externally. This mismatch limits reuse to the Janitor sub-pattern rather than the full orchestrator.
3. **Vendor-before-build still applies at the sub-component level**: even if wholesale adoption is inappropriate, porting Bernstein's Janitor verification logic (lint/type-check/test gate before merge) is cheaper than hand-building an equivalent from `local-agentic-loop-sample`, which primarily covers branch isolation and trusted-actor gating, not verification gating.

## Evaluation Plan (Spike Test, Pre-Phase-4)
1. Extract Bernstein's Janitor module in isolation (not the full orchestrator, scheduler, or audit chain).
2. Adapt it to run inside Tektos's existing `SandboxProvider`/`WorktreeProvider` protocol (Tektos Phase 2), replacing file-based `.sdd/` state with a write-through to Tektos's Postgres TaskState schema.
3. Run a fixture scenario: two concurrent Tektos subtasks produce conflicting diffs; confirm the adapted Janitor correctly blocks the losing merge pending human review, equivalent to Tektos Phase 4's existing "two concurrent subtasks merge without observing each other's uncommitted changes" Definition of Done.
4. Compare implementation cost and test coverage against the originally planned `local-agentic-loop-sample` port.
5. Decision gate: adopt the adapted Janitor pattern only if the spike passes the fixture scenario with lower implementation cost than the original plan; otherwise proceed with `local-agentic-loop-sample` as originally scoped.

## Build-Order Placement
This ADR does not change Rollout Plan Phase sequencing. The spike test is scheduled immediately before Tektos Phase 4 begins (per Tektos v1's own Implementation Order), not before. No dependency is introduced on Bernstein's scheduler, audit chain, or CLI-agent adapters — only a possible sub-component port of its Janitor verification logic, pending spike-test results.

## Definition of Done
- Spike test completed with a documented pass/fail against the fixture scenario in the Evaluation Plan.
- If adopted: Bernstein's Janitor logic is logged in `PORTING_LEDGER.md` with source URL, commit hash, SPDX license identifier (Apache-2.0), and modification notes describing the Postgres-state adaptation.
- If adopted: Tektos Phase 4's Definition of Done (multi-agent safety fixture scenarios) is re-run against the adapted Janitor with identical pass criteria to the originally planned port.
- If rejected: this ADR is marked Superseded with a one-line rationale, and Tektos Phase 4 proceeds with `local-agentic-loop-sample` as originally scoped.
