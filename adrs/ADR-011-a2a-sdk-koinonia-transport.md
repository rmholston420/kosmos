# ADR-011 — a2a-sdk as Koinonia Standalone Transport

**Status:** Ratified v25 · **Lock-in phase:** 6.3

## Context

Koinonia is the agent-to-agent coordination plugin. It needs a transport for cross-agent messages that:

- Carries structured payloads with schema.
- Supports request/response and stream patterns.
- Is compatible with agents implemented outside Kosmos (future interop).
- Does not couple Koinonia to any single plugin.

Options:

- **a2a-sdk** — Google's Agent-to-Agent SDK; permissive license; explicit A2A protocol.
- **Moltbook transport** — internal message-bus construct; less standardized; would tie Koinonia to a proprietary shape.
- Roll our own on top of EventBusPort — violates "vendor before hand-build".

## Decision

Adopt **a2a-sdk** as Koinonia's transport, **standalone** — not layered onto Moltbook.

- Bridged to `EventBusPort` where broadcast semantics are needed.
- a2a-sdk's protocol used verbatim; Kosmos does not fork the wire format.
- Message payloads carry Kosmos-standard headers: `provenance`, `confidence` (where applicable), `governance_tier`.

## Rationale

- Standardized, permissively-licensed protocol → future interop (Kosmos ↔ external A2A agents).
- Avoids invention of a new transport for a solved problem.
- Standalone (not on Moltbook) → we control the entire path; no hidden third-party assumptions.
- Fits ADR-007 (events-only) — a2a-sdk is an event-shaped protocol.

## Consequences

- Koinonia's plugin package vendors a2a-sdk under `plugins/koinonia/vendor/a2a/` (PORTING_LEDGER).
- Cross-agent security: a2a-sdk auth tokens signed with Ed25519 (Spec §7).
- Message replay / dedup: EventBusPort handles idempotency; a2a-sdk provides message IDs; adapter reconciles.

## Lock-in phase

Phase 6.3 — Koinonia MVP.

## References

- ADR-007 (Events-Only)
- Spec §7 (Ed25519 asymmetric)
- PORTING_LEDGER: a2a-sdk
