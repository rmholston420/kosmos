# ADR-018 — Sure/Maybe Finance Rejection + CMSgov/18F Design References for Oikos Rules Engine

**Status:** Ratified · **Lock-in phase:** Phase 5.3 (Oikos)

## Context

Oikos handles household administration including benefit programs, bills, and rules-driven reminders. Candidates considered:

- **we-promise/sure** — benefit-eligibility rules engine.
- **Maybe Finance** — personal finance / rules engine.
- **CMSgov BenefitAssist** — CMS.gov open-source benefit UX patterns.
- **18F SNAP** — 18F open-source SNAP benefit UX.

## Decision

- **Reject** `we-promise/sure` and Maybe Finance for vendoring into Oikos. Do not adopt without a new ADR.
- **Adopt** CMSgov BenefitAssist and 18F SNAP as **design references only** (UX flow patterns, form design, plain-language explanations). Not vendored as code.

### Rejection rationale (sure, Maybe Finance)

- **sure** — model does not fit Oikos's zero-trust memory constraint (rules would require assumptions incompatible with provenance-first writes); domain model is US-federal-benefit-shaped and adds complexity beyond single-user household use.
- **Maybe Finance** — sizable dependency footprint; overlaps with future Nomisma (finance plugin); would fork Oikos scope prematurely.

### Adoption rationale (CMSgov / 18F)

- Public-sector UX patterns are permissively licensed and plain-language.
- Inform Oikos's benefit/bill flow presentation without importing code.

## Consequences

- Oikos rules engine is **hand-built minimally**, native to MemoryPort + DataPort.
- PORTING_LEDGER: we-promise/sure marked REJECTED with reference to this ADR; CMSgov BenefitAssist and 18F SNAP marked DESIGN REFERENCE.
- If future need arises to vendor an eligibility-rules engine, this ADR is amended, not silently overridden.

## Lock-in phase

Phase 5.3 — Oikos benefit-assist patterns implementation.

## References

- Kosmos-Build-Sequence-v25.md §5.5
- PORTING_LEDGER (Design References — Do Not Vendor)
