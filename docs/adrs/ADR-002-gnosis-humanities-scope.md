# ADR-002 — Gnosis-Humanities Scope Assignment (Gnoma Feature Absorption)

**Status:** Ratified · **Lock-in phase:** 6.6 · **Superseded by:** —

## Context

An earlier proposal split humanities-domain knowledge (classical texts, translations, OCR pipelines for scanned material) into a separate plugin ("Gnoma"). Kosmos operates under a **one-person-module** scope constraint: additional plugins increase surface area without proportional benefit when the domain fits inside an existing plugin.

Gnosis already owns the general knowledge graph, provenance, and evaluation. Humanities corpora are a specialization of that same domain — same ingestion (docling), same graph store (DozerDB via MemoryPort), same evaluation loop.

## Decision

Fold all Gnoma-scope features into **Gnosis** as a `humanities/` module. No separate plugin.

- Gnosis absorbs: classical Buddhist text digitization pipeline, OCR/translation adapters, canonical-edition provenance, scholarly-citation link types.
- Additional link types added to Gnosis's typed claim-graph (per ADR-001) rather than a parallel graph.
- UI parity (ADR-014) applies to Gnosis; no separate humanities dashboard tab required, but a humanities view within Gnosis is permitted.

## Rationale

- One-person-module rule: two plugins doing knowledge work violate scope.
- Provenance model is already generic (see ADR-001); no need to re-derive.
- Cross-linking humanities and general knowledge is trivial inside one graph, painful across two.

## Consequences

- Gnosis's schema gains humanities-specific claim types (`Translation`, `EditionOf`, `AttributedTo`, etc.). All go through the same provenance/confidence enforcement.
- OCR/translation adapters live under `plugins/gnosis/humanities/adapters/`.
- `docling` (PORTING_LEDGER) handles common document formats; specialized classical-text OCR (if required) uses a separately vendored tool, logged in PORTING_LEDGER.

## Lock-in phase

Phase 6.6 — after Gnosis Phase 4 exit gate; before any humanities corpus is loaded in earnest.

## References

- ADR-001 (Typed Claim-Graph Memory)
- ADR-016 (Knowsys–Gnosis Merge — same absorption pattern)
- Knowledge Wiki: `concepts/classical-buddhist-text-digitization`
