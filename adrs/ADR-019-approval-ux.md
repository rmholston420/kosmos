# ADR-019 — Approval UX Specification

**Status:** Ratified · **Lock-in phase:** Phase 3 (with UI shell)

## Context

APEX Change Approval Tier (Spec §14) requires `HUMAN_REVIEW` and `HUMAN_REQUIRED` tiers. The user must be able to review, approve, reject, or modify pending actions from the kernel dashboard — and receive escalation notifications when they miss approvals. Without a specified UX, plugins invent inconsistent approval surfaces.

## Decision

Standardize the approval UX as follows.

### Surface

Kernel dashboard **Approvals Queue** tab lists pending Intentions. Each entry shows:

- Plugin name and action summary
- **Diff preview** — Monaco editor for code; JSON tree view for data writes; rendered form for UI actions
- Governance-tier trigger reason (why this action escalated)
- Requested-at timestamp
- Countdown-to-escalation timer

### Escalation timeout

- `HUMAN_REVIEW`: default **4 hours**. After timeout, escalates per plugin's escalation policy (usually re-tier to HUMAN_REQUIRED).
- `HUMAN_REQUIRED`: **no auto-escalation** (single-user context — user is the only one who can approve).
- Missed `HUMAN_REQUIRED` past **24 hours**: re-fires `NotificationPort` on all channels. Repeats every **6 hours** thereafter.

### Decision actions

- **Approve** — sign action, execute.
- **Reject** — mandatory reason field; reason written to audit log.
- **Approve-with-modification** — inline edits before approval; edits must be **non-destructive** (adjust parameters, not swap actions). Destructive changes require reject + new proposal.

### Mobile fallback

External adapter (SMS / ntfy) sends a one-tap approve/reject link with a short-lived **Ed25519-signed token**, valid 24h, usable without opening the dashboard.

### DoD

- Fixture `HUMAN_REQUIRED` action renders fully in Approvals Queue with diff preview.
- Approve, reject, and modify each produce correctly signed audit-log entries.
- Simulated missed approval triggers the correct 24h + every-6h notification cadence.
- Signed mobile link approves the action end-to-end with token verification.

## Rationale

- Consistent user experience across all plugins.
- Diff-first review supports safe delegation of high-tier actions.
- Ed25519 mobile tokens enable off-dashboard approvals without weakening auth.
- Time-boxed cadence prevents indefinite pileup of HUMAN_REQUIRED backlog.

## Consequences

- Every plugin's FrontendContractPort component may contribute Approvals Queue entries.
- `NotificationPort` adapters must support ntfy and SMS (or an equivalent user-selected channel).
- Audit log entries are Ed25519-signed and never deleted (Spec §15).

## Lock-in phase

Phase 3 — with first UI shell that includes Approvals Queue.

## References

- Spec §14 (Governance Autonomy Ladder)
- Spec §17.13 (Approval UX in-line summary)
- ADR-014 (UI Parity Rule)
