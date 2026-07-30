# ADR-008-DozerDB — DozerDB Fork as MemoryPort Graph Store

**Status:** Ratified v25 · **Lock-in phase:** Stage 1 · **Supersedes:** open question in v22–v24

## Context

MemoryPort requires a graph store that supports:

- Typed nodes/edges with per-property provenance and confidence.
- Temporal queries (Graphiti sits atop it).
- Full Cypher semantics (Rigpa-LMS query bodies port over unchanged).
- Enterprise-grade features (constraints, procedures, subgraph exports) **without** Neo4j Enterprise's proprietary license and per-core cost, which is inappropriate for a single-user local system.

Options considered:

| Option | Verdict |
|---|---|
| Neo4j Community | No enterprise features (constraint types missing, no APOC-parity) |
| Neo4j Enterprise | License incompatible with single-user local + long-horizon storage; commercial dependency |
| DozerDB (community fork of Neo4j with enterprise features backported) | Chosen |
| Memgraph | Cypher-compat drift; commercial-first orientation |
| Custom RDF store | Violates "vendor before hand-build" |

## Decision

Adopt **DozerDB** (community fork of Neo4j including enterprise-tier features) as the graph adapter behind `MemoryPort`.

- Deployed as a Docker Compose service in dev; systemd unit in production Colossus.
- Wrapped behind `MemoryPort` (never accessed directly from plugins).
- `MemoryPort` enforces provenance + confidence fields on every write (rejection at protocol layer).
- Agent Memory Guard (see PORTING_LEDGER) sits as a write-time policy filter atop the adapter.
- Graphiti sits atop DozerDB (via MemoryPort adapter) for temporal knowledge-graph capabilities.

## Rationale

- **Local-first + free** — no license fees, no commercial control plane.
- **Neo4j Cypher compatibility** — Rigpa-LMS query bodies port unchanged.
- **Enterprise features** — constraints, procedures, subgraph exports available.
- **Provenance atop existing storage** — provenance/confidence enforced at MemoryPort, not at DB layer; adapter change is possible later without rewriting policy.

## Consequences

- **License audit required at vendoring** — Neo4j core is GPL-3; DozerDB's fork additions must be permissive. If verification fails (upgrade path unclear or forks become non-permissive), escalate: revisit Memgraph or wrap Neo4j Community.
- Neo4j-specific storage plans (page cache, tx log sizing) must be tuned for Colossus's 128 GB RAM envelope in `ops/dozerdb-tuning.md`.
- Backup format is Neo4j-native; quarterly DR drill (Spec §23) exercises restore.
- Memory-guard version is pinned in PORTING_LEDGER; **check release page immediately before Gnosis Phase 3** for newer than v0.2.2.

## Lock-in phase

Stage 1.8 — DozerDB deployed, MemoryPort adapter wired, provenance rejection tests green.

## References

- ADR-001 (Typed Claim-Graph Memory) — schema
- ADR-013 (memory/bridge.py vs Gnosis schema) — schema selection
- PORTING_LEDGER: DozerDB, Agent Memory Guard, Graphiti
