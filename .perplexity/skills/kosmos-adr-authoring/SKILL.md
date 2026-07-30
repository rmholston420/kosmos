---
name: kosmos-adr-authoring
description: Load before making any architectural decision in Kosmos that reshapes ports, adapters, plugin scope, governance tiers, storage backends, or the porting-vs-hand-build boundary. Enforces the ADR template, filing procedure, and index update. Also load when amending an existing ADR (status change, contingency triggered, or scope shift). Common triggers: choosing between two OSS candidates, adding a new formal port, changing a plugin boundary, altering approval thresholds, resolving a Kosmos v25 OPEN item.
---

# Kosmos ADR Authoring

## When to use

Load this skill when:

- A decision reshapes architecture (port added, adapter swapped, plugin scope changed, storage backend changed, encryption/PII tier changed).
- An existing ADR needs amendment (status change, contingency fired, benchmark result).
- The spec flags an `OPEN` item that needs resolution (see `adrs/README.md` — currently only ADR-010).

Do **not** author an ADR for reversible code-level choices (function naming, refactoring patterns, lint-level style).

## ADR file structure

Filename: `adrs/ADR-###-kebab-case-title.md`
- `###` is the next unused zero-padded number in sequence.
- Kebab-case, no dates, no author names.

Template body:

```markdown
# ADR-### — <Human Title>

**Status:** <Proposed | Ratified | Ratified v25 | Amended | Superseded by ADR-### | OPEN>
**Lock-in phase:** <Stage / Phase>
**Supersedes:** <ADR-### or —>

## Context
<Why this decision is required. Constraints, options considered.>

## Decision
<The decision, in plain language. Enforceable.>

## Rationale
<Why this option over alternatives.>

## Consequences
<What changes: files, procedures, PORTING_LEDGER, tests, downstream ADRs.>

## Lock-in phase
<Which stage/phase locks this in.>

## References
<Spec sections, other ADRs, PORTING_LEDGER entries.>
```

## Authoring workflow

### 1. Confirm ADR is needed

- Read `adrs/README.md` — is there already an ADR covering this?
- If yes → this is an **amendment**, not a new ADR.
- If no → proceed.

### 2. Draft the ADR

- Use the template above.
- Restate the exact scope: which stage/phase, which port, which files.
- List **at least two** alternatives and why they were not chosen.
- Consequences section must enumerate files/procedures/logs that will change.

### 3. Update the ADR index

Add the row to `adrs/README.md` in ID order.

### 4. Update the master spec (if load-bearing)

If the ADR changes a decision surfaced in `Kosmos-Build-Spec-v25.md` §17 (ADR summary table) or §21 (Rollout Plan), amend the spec inline and note the ADR reference. Use `kosmos-spec-diff` skill for the edit.

### 5. Update PORTING_LEDGER (if it affects a port)

If the decision adopts, rejects, or replaces an OSS component, update `PORTING_LEDGER.md`:
- Rejected → status `REJECTED` with ADR reference.
- Superseded → old entry `SUPERSEDED by <link>`.
- New adoption → new entry with `PLANNED` or `VENDORED`.

### 6. Amend, not overwrite

Amending an existing ADR:
- Add a `> **STATUS AMENDMENT (YYYY-MM-DD):** ...` block at the top.
- Do not delete the original decision text.
- Update the status line.
- If the decision reverses, author a new ADR that supersedes; mark the old one `Amended · superseded by ADR-###`.

### 7. BUILD_LOG entry

Delegated to `kosmos-log-maintenance`. Every ADR author or amend gets a BUILD_LOG entry.

## Stop conditions

- Decision requires input from the user (spec flags it as user-decision) → stop, ask.
- Two ADRs would conflict → stop, resolve at spec level first.
- Decision would violate ADR-007 (events-only) or zero-trust memory writes → stop, redesign.
- Non-permissive license involved → stop, ask user for explicit override.

## References

- `Kosmos-Build-Spec-v25.md` §17
- `adrs/README.md`
- `PORTING_LEDGER.md`
