# ADR: Typed Claim-Graph Memory & Grounded Evaluator (Graph Engineering Pattern)

## Status
Proposed (requires Tier-2 ADR ratification per Kosmos v20 ADR practice)

## Context
External analysis of multi-agent architectures ("Graph Engineering") identifies a six-step pattern for scaling agent reliability: self-review loop → tools → parallel worktrees → typed claim graph (not transcripts) → evaluator grounded in graph edges → persistent cross-session graph. Kosmos already implements steps 1–3 and 6 via Tektos's core agent loop, port-mediated tools, worktree isolation, and Gnosis's CIDOC CRM graph (Graphiti + DozerDB) surviving sessions. Steps 4 and 5 are only partially specified: Gnosis's semantic memory stores structured facts/entities/relationships, but no standing rule requires every agent-asserted claim to be written as a typed node/edge pair with an explicit source pointer, and Phrouros's evaluation logic is not yet specified to check claims against graph edges rather than qualitative judgment.

## Decision
Adopt the typed claim-graph convention as a standing schema rule for Gnosis's `MemoryPort.write_event()`, and extend Phrouros with a grounded-evaluator mode that verifies claims against existing graph edges before allowing promotion to durable semantic memory.

## Schema Rule: Claims as Typed Triples
Every write from an agent (Tektos, and future Zetesis/Synedrion/Koinonia) that asserts a factual finding must be decomposed into a typed triple before it reaches semantic memory:

| Element | Requirement |
|---|---|
| Subject node | Typed per existing CIDOC CRM classes (Actor/Place/TimeSpan/Event/Thing) or a declared extension type |
| Predicate/edge | Typed relationship label, drawn from a versioned edge-type registry (`EDGE_TYPES.md`, new artifact) — no free-text predicates |
| Object node | Typed node, same constraint as subject |
| Source pointer | Mandatory `source_citation` field referencing the originating tool call, document, or agent run ID — identical provenance requirement already enforced by Agent Memory Guard on `write_event()` |
| Confidence | Existing `confidence` field, unchanged |

Free-text transcript logging is still permitted for episodic memory (task narration, chat-style logs), but any claim intended for semantic-memory promotion must pass through this triple decomposition step first. This is an additive constraint on the existing `write_event()` contract, not a new port.

## Evaluator Rule: Grounded Verification, Not Vibes
Phrouros gains a new check mode, **Claim Grounding Check**, run before any quarantined or pending claim is promoted to durable semantic memory:

- For each candidate claim, Phrouros queries Gnosis's graph for the exact subject-predicate-object edge or a chain of edges that entails it.
- If the edge is found: claim passes grounding check, proceeds to normal Agent Memory Guard provenance/PII checks.
- If the edge is not found: Phrouros emits a structured `ClaimNotGrounded` finding (analogous to "Triple not found") rather than a scalar confidence judgment, and the claim is routed to the existing quarantine lane for Tier-1/Tier-2 human review.
- This check is deterministic graph lookup, consistent with Phrouros's existing deterministic-before-LLM principle — no LLM judgment call is used to decide grounding status, only to assist a human reviewer's downstream disposition.

## Build-Order Placement
This ADR does not change Rollout Plan Phase sequencing. The schema rule applies to Gnosis from its Phase 3 minimal-core build onward (cheap to bake in now since Gnosis is not yet built). The Phrouros grounding-check mode is added to Phrouros's existing Phase 4 scope, alongside its other fault-injection and memory-integrity checks. Zetesis and Koinonia (Phase 6) inherit the claim-graph convention as a contract requirement from their first `MemoryPort` write, avoiding retrofit cost.

## Rationale
1. **Cheaper before build than after**: Gnosis, Zetesis, and Koinonia are not yet built (Rollout Plan Phase 3 and Phase 6), so this is a schema-definition change, not a migration.
2. **Consistent with existing zero-trust memory discipline**: Kosmos already treats every `write_event()` as untrusted until provenance-checked; typed triples make that check mechanically verifiable (edge exists or does not) rather than relying on qualitative confidence scores alone.
3. **Directly extends Phrouros's stated role**: Phrouros already runs adversarial probes and consumes memory-integrity signals from Agent Memory Guard; claim grounding is a natural, low-cost extension of its existing deterministic-before-LLM anomaly detection.
4. **No new port or subsystem required**: This is entirely additive to `MemoryPort` and Phrouros's existing scope — no new formal port, no violation of the ports-and-adapters mandate.

## Definition of Done
- `EDGE_TYPES.md` exists as a versioned registry of allowed predicate types, referenced by `PORT_CONTRACTS.md`.
- Gnosis's `write_event()` rejects any semantic-memory-bound claim lacking a typed subject/predicate/object/source_citation quadruple.
- Phrouros's Claim Grounding Check runs against a fixture set of grounded and ungrounded claims, correctly emitting `ClaimNotGrounded` for the latter and routing them to the existing quarantine lane.
- A fixture Tektos-originated claim (e.g., a KB rule finding) passes through triple decomposition, grounding check, and Agent Memory Guard provenance check end to end before promotion to durable semantic memory.
- Rollout Plan Phase 3 (Gnosis minimal core) and Phase 4 (Phrouros) entries are amended to reference this ADR.
