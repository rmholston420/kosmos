# ADR-014 — UI Parity Standing Rule

**Status:** Ratified (v24) · **Lock-in phase:** Every phase after Tektos Phase 2

## Context

Kosmos is a single-user LMS with a kernel dashboard. A plugin that lacks a UI component becomes invisible to the user and drifts from lived operational use — the plugin exists but is not integrated into daily workflow.

## Decision

**Every plugin's Definition of Done requires a `FrontendContractPort` component before Tier-2 (production) promotion.**

- Component declares the plugin's UI surface: dashboard tab(s), forms, list views, approval cards.
- Rendered by the kernel dashboard shell (React + shadcn/ui).
- No plugin ships without at least a minimum viable dashboard presence.

### Sole grandfathered exception

- **Tektos Phase 2's UI-less proof** — logged explicitly in `PORT_CONTRACTS.md` with `ui_parity_status = grandfathered`. Any other UI-less exception requires a new ADR.

### Enforcement

- `PORT_CONTRACTS.md` includes a `ui_parity_status` column with values: `present`, `pending`, `grandfathered`.
- Tier-2 promotion checklist blocks on `ui_parity_status = present` for all plugins except the grandfathered entry.
- Kernel dashboard renders a "missing UI" tile for any registered plugin without a component, ensuring the gap is visible.

## Rationale

- Force integration into the actual dashboard the user sees every day.
- Prevent "backend-only" plugin drift.
- Standardize UI declaration through a port, so kernel can enforce and render uniformly.

## Consequences

- Design-references-only entries (CMSgov, 18F SNAP — see PORTING_LEDGER) inform UI shape; no vendored UI library beyond shadcn/ui and Kosmos's own patterns.
- Approval UX (ADR-019) is one of the FrontendContractPort components required for any plugin producing approvable actions.

## Lock-in phase

Enforced starting immediately **after** Tektos Phase 2 (the grandfathered phase). All subsequent phases across all plugins comply.

## References

- Spec §17.1 (UI Parity Rule summary)
- ADR-019 (Approval UX)
- PORT_CONTRACTS.md
