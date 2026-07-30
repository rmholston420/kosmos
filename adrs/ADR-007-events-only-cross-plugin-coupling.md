# ADR-007 — Events-Only Cross-Plugin Coupling

**Status:** Ratified (foundational) · **Lock-in phase:** Stage 1 · **Supersedes:** —

## Context

Rigpa-LMS (the current-state donor code, per project instructions) contains direct cross-plugin Python imports. This creates hard coupling: a change to plugin A's internals breaks plugin B; both cannot be maintained by a single person independently.

Kosmos is architected as a fractal Viable System Model where each plugin is a self-contained System-1 unit. Cross-plugin dependency must be **explicit, contractual, and asynchronous**.

## Decision

**No plugin may import any other plugin's Python package, module, or symbol under any circumstance.**

All cross-plugin interaction goes through exactly one of:

1. **`EventBusPort`** — publish/subscribe events (Valkey Streams adapter, see PORTING_LEDGER).
2. **Formal ports** defined in `ports/` (LLMPort, MemoryPort, VectorPort, DataPort, SecretsPort, ObservabilityPort, FrontendContractPort, ResourcePort, NotificationPort).

Direct HTTP/gRPC/socket calls between plugins are also forbidden — everything is bus- or port-mediated.

### Enforcement

- Static: `ruff` custom rule (or `import-linter`) forbids `plugins/<a>/**` importing from `plugins/<b>/**`. CI-equivalent runs pre-commit.
- Runtime: import audit at plugin startup logs and refuses cross-plugin imports.
- Test: every plugin ships a `test_plugin_isolation.py` that greps the plugin's source for forbidden imports.

## Rationale

- **One-person-module scope** — each plugin must be readable, buildable, and replaceable by one maintainer.
- **Independent replaceability** — a plugin can be rewritten, replaced, or removed without touching another plugin.
- **VSM coherence** — System-1 units communicate through System-2 coordination (bus), not by reaching into each other.
- **Testability** — plugins mock each other via bus/port fixtures, not internal imports.

## Consequences

- Cross-plugin workflows (e.g., Zetesis asks Tektos to prototype) require declared event schemas — logged in `docs/event-schemas/`.
- Shared code that is not a domain concern (utilities, types) lives in a kernel module (`kernel/common/`) or is copied into each plugin. **No shared "utils" plugin.**
- Any temptation to violate this rule triggers an ADR amendment, not a code change.

## Lock-in phase

Stage 1 — enforced from first commit of first plugin. Pre-commit hook installed at Stage 0.1.

## References

- Project custom instructions (verbatim: "Never let a plugin import another plugin's package directly — all cross-plugin coupling goes through the event bus or formal ports per ADR-007")
- ADR-011 (a2a-sdk transport — a superset of bus coupling for cross-agent messaging)
