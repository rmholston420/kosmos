# Kosmos ADR Index

All Architecture Decision Records for Kosmos v25. Newer ADRs supersede older ones only when explicitly stated.

**Status legend:** `Ratified` = decided and load-bearing · `Ratified v25` = newly ratified in this cut · `OPEN` = requires resolution before named lock-in phase · `N/A` = not applicable in greenfield · `Amended` = superseded scope

| ID | File | Title | Status | Lock-in Phase |
|---|---|---|---|---|
| ADR-001 | `ADR-001-typed-claim-graph-memory.md` | Typed Claim-Graph Memory + Grounded Evaluator | Ratified | Gnosis Phase 3 |
| ADR-002 | `ADR-002-gnosis-humanities-scope.md` | Gnosis absorbs Gnoma/humanities scope | Ratified | 6.6 |
| ADR-002 (supplement) | `ADR-002-supplement-humanities-detail.md` | Humanities implementation details | Ratified | 6.6 |
| ADR-003 | `ADR-003-beads-taskstate-reference.md` | Beads as TaskState design reference | Ratified | Tektos Phase 3 |
| ADR-004 | `ADR-004-bernstein-janitor-spike.md` | Bernstein Janitor spike-test | **Ratified v25 (spike approved)** | Tektos Phase 4 |
| ADR-005 | `ADR-005-openspec-primary.md` | OpenSpec as primary SDD engine | Ratified | Tektos Phase 3 |
| ADR-006 | `ADR-006-pier-eval-harness.md` | Pier eval-on-deploy | Ratified | Tektos Phase 4 |
| ADR-007 | `ADR-007-events-only-cross-plugin-coupling.md` | Events-only cross-plugin coupling | Ratified (foundational) | Stage 1 |
| ADR-007-DeepSWE | `ADR-007-DeepSWE-corpus.md` | DeepSWE as eval-corpus candidate | Ratified | Tektos Phase 4 |
| ADR-008 | `ADR-008-superpowers-kb-reference.md` | Superpowers as KB methodology reference | Ratified | Tektos Phase 4 |
| ADR-008-DozerDB | `ADR-008-DozerDB-memory-port.md` | DozerDB fork as MemoryPort store | **Ratified v25** | Stage 1 |
| ADR-009 | `ADR-009-llama-swap-primary.md` | llama-swap primary + router-mode fallback | **Ratified v25 (contingent)** | Stage 1 (benchmark-gated) |
| ADR-010 | `ADR-010-zetesis-inner-loop-eval.md` | AREX vs. Open Deep Research inner loop | **OPEN — head-to-head pre-Phase-6.2** | Phase 6.2 |
| ADR-011 | `ADR-011-a2a-sdk-koinonia-transport.md` | a2a-sdk standalone transport for Koinonia | **Ratified v25** | Phase 6.3 |
| ADR-012 | `ADR-012-donor-adapter-consolidation.md` | Consolidate ollama.py/searxng.py duplicates | **Ratified v25** | Stage 1.1 |
| ADR-013 | `ADR-013-memory-bridge-selection.md` | Choose memory/bridge.py vs. Gnosis schema | **Ratified v25** | Stage 1 pre-Phase-2 |
| ADR-014 | `ADR-014-ui-parity-rule.md` | UI Parity standing rule | Ratified (v24) | Every phase after Tektos Phase 2 |
| ADR-015 | `ADR-015-oikos-before-zetesis.md` | Oikos ahead of Zetesis sequencing | Ratified (v24) | Stage 5 |
| ADR-016 | `ADR-016-knowsys-gnosis-merge.md` | Knowsys merged into Gnosis | Ratified (v24) | Phase 3.3 |
| ADR-017 | `ADR-017-llm-council-reference.md` | karpathy/llm-council as design reference only | Ratified | Phase 6.4 |
| ADR-018 | `ADR-018-oikos-benefit-references.md` | sure/Maybe rejected; CMSgov/18F as references | Ratified | Phase 5.3 |
| ADR-019 | `ADR-019-approval-ux.md` | Approval UX specification | Ratified | Phase 3 |
| ADR-020 | `ADR-020-tektohs-migration.md` | TektOHs v18 → Tektos v1 migration | Ratified (N/A greenfield) | Tektos Phase 3 |

## The one remaining open decision

**ADR-010** is the only ADR left OPEN in v25. All other decisions are resolved and load-bearing on Stage-1-executable build.

## Amending an ADR

1. Never edit a Ratified ADR in place except to add a `> **STATUS AMENDMENT:**` block at the top.
2. Amendments require a `BUILD_LOG.md` entry (timestamp + reason).
3. If the amendment reverses the decision, author a new ADR that supersedes the old one and mark the old one `Amended · superseded by ADR-###`.
4. The `kosmos-adr-authoring` Perplexity Computer skill enforces this workflow.
