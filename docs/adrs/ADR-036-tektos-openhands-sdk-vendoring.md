# ADR-036 — Tektos OpenHands SDK Vendoring (Stage 3.1)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.1
**Supersedes:** —

## Context

Stage 3 lands Tektos, the Kosmos coding plugin (spec §18). Stage 3.1 is the first slice: get an OpenHands-shaped agent reading and writing exclusively through Kosmos ports.

Spec §432 pins the upstream: `OpenHands/software-agent-sdk` (a.k.a. `openhands-agent-sdk`), MIT-licensed, core agent loop with `Agent` / `Conversation` / `LLM` / `Tool` surface (import path `openhands.sdk`). Spec §566 also lists the main `OpenHands/OpenHands` repo (MIT outside `enterprise/`) for runtime patterns.

Six decisions are load-bearing at 3.1:

1. **Which repo to vendor now** — SDK only, main repo, or both.
2. **Vendor mode** — pattern-vendor (rewrite behind ports) vs. verbatim copy vs. pip dependency.
3. **DoD scope** — minimal loop vs. full task decomposition vs. loop-plus-tool-calls.
4. **Plugin descriptor** — register at 3.1 or defer to a later 3.x.
5. **Fate of `plugins/tektos/stub/`** — the Stage-2.4 test-only `TektosSimulator` (ADR-035 Q6=A).
6. **New ADR vs. amend** — dedicated ADR-036 vs. amend ADR-020 (Tektos migration).

Constraints: local-first / single-user Colossus posture (128 GB RAM, RTX 5090); ADR-007 (no cross-plugin imports); ADR-008 (zero-trust memory writes: `provenance` + `confidence` required); one-person-module scope per plugin; Rigpa-LMS is current-state to refactor, not to imitate; every vendored component logged in `PORTING_LEDGER.md` with source + commit + SPDX + modifications.

## Decision

**Q1 = A — Vendor `OpenHands/software-agent-sdk` only at 3.1.** Main-repo runtime patterns deferred to Stage 3.2 where MCP transport lands (spec §18 3.2). Kosmos location: `plugins/tektos/`.

**Q2 = A — PATTERN-VENDORED (rewrite behind ports).** Do not copy upstream source into the tree. Reimplement the agent-loop surface Kosmos actually needs (`Agent`, `Conversation`, `send_message`, `run`, one iteration) in Kosmos-native Python, exclusively over `LLMPort` and `MemoryPort`. Cite upstream repo + commit + license in `PORTING_LEDGER.md`. Match every prior port pattern (Rigpa constitution loader, APEX engine, memory bridge — all `PATTERN-VENDORED`).

**Q3 = A — Minimal-loop DoD.** DoD literal: one test instantiates `TektosAgent` with a fake `LLMPort` (canned response) and a fake `MemoryPort` (in-memory), calls `send_message(...)` + `run()` for exactly one iteration, and asserts (1) the agent read prior context from memory, (2) the LLM was called once with the resulting prompt, (3) the response was written back through `MemoryPort.write_event` with `provenance="tektos_agent"` and `confidence` in `(0, 1]`. No MCP, no sandbox, no real tools.

**Q4 = B — No `PluginDescriptor` at 3.1.** Tektos is behind-the-ports scaffolding at 3.1. FrontendContractPort registration + `AGENT_TRACE` panel land at Stage 3.7 (spec-kit renderer) when real UI cards exist. Spec §17.1 UI Parity Rule Phase-2 grandfathering covers this explicitly.

**Q5 = B — Keep `plugins/tektos/stub/` alive at 3.1; delete at 3.2.** Preserve the Stage-2.4 exit-gate test (`test_stage_2_4_exit_gate.py`) unchanged. The stub is superseded organically at Stage 3.2 when MCP tool calls emit real `TraceEvent`s through `TraceFeedPort` — at that point the simulator becomes redundant and is deleted, and the Stage-2.4 gate test is rewired to instantiate the real Tektos agent.

**Q6 = A — Author ADR-036 (this ADR).** Do not amend ADR-020. ADR-020 covers the Tektos migration direction; this ADR locks the concrete vendoring surface, plugin layout, DoD test, and stub-fate policy for Stage 3.1.

## Rationale

**Q1 rejects B (both repos) and C (main-repo only).** The SDK repo carries the exact `Agent`/`Conversation` shape spec §432 anchors on. Main-repo runtime patterns (workspace abstractions, event bus, sandboxed runtime) belong at 3.2 alongside MCP transport — pulling them at 3.1 blows past the one-slice-at-a-time discipline every prior stage honored. B doubles the vendor surface without a 3.1 DoD reason.

**Q2 rejects B (verbatim vendor) and C (pip dep).** B (`plugins/tektos/vendor/openhands/`) forces upstream churn tracking, dual-license bookkeeping (SDK + every transitive), and inflates the plugin past one-person-module scope. The SDK's Pydantic + LiteLLM transitive deps overlap Kosmos-owned ports (LLMPort already fronts LiteLLM territory via ADR-022), so verbatim vendoring creates parallel abstractions. C violates the local-first posture — a PyPI resolve at import time is a network dependency, and `openhands-agent-sdk`'s version-drift cadence would drag Kosmos with it. Pattern-vendoring matches Rigpa constitution loader (ADR-032), APEX engine (ADR-033), and MemoryBridge (ADR-013) — the prevailing Kosmos pattern.

**Q3 rejects B (full task decomposition) and C (loop + tool-calling).** B pulls task decomposition + auto-compression + LiteLLM tool-choice into 3.1, which is 3.5 (Reflexion + Voyager) and 3.6/3.7 (OpenSpec + spec-kit) territory. C creeps into 3.2 (MCP transport) — tool-calling scaffolding is only useful once real tools exist. The spec DoD literal ("OpenHands agent can read/write via Kosmos ports only") is exactly satisfied by A: one read, one LLM call, one write.

**Q4 rejects A (register now) and C (register with AGENT_TRACE panel).** A ships a descriptor with `panels=()` — a no-op registration that costs a FrontendContractPort call at every boot for zero user-visible value. C is worse: it adds a stub `lazy_module` path that resolves to nothing until 3.7. Spec §17.1 UI Parity Rule Phase-2 grandfathering exists specifically to keep Tektos backend-only until real UI lands. Defer.

**Q5 rejects A (delete at 3.1) and C (move to tests/_fixtures immediately).** Both touch the just-landed Stage-2.4 gate test. Every prior stage-boundary transition (Stage 1 → 2, Stage 2.3 → 2.4) preserved the previous stage's DoD tests verbatim. B does the same: real Tektos + test-only `TektosSimulator` coexist at 3.1, and the simulator's presence proves the detector-tuple seam still fires under both real and synthetic trace sources. Deletion happens at 3.2 when MCP tool calls emit real `TraceEvent`s and the simulator becomes redundant.

**Q6 rejects B (amend ADR-020) and C (no ADR).** B would bloat ADR-020 with implementation details (vendor mode, DoD scope, stub fate) that don't fit "migration direction". C violates `kosmos-spec-diff` skill rule that any new plugin or new upstream vendor is a structural decision requiring an ADR — the pre-commit fan-out check depends on the ADR-to-spec-§17 agreement.

## Consequences

**Files added (Stage 3.1 landing):**
- `plugins/tektos/agent.py` — `TektosAgent` dataclass, LLMPort + MemoryPort injected; matches OpenHands SDK `Agent` + `Conversation` surface via `send_message(text: str)` + `run()`.
- `plugins/tektos/models.py` — `TektosMessage`, `TektosStep` frozen dataclasses; `TektosMessageRole` enum.
- `plugins/tektos/errors.py` — `TektosError` root + subclasses for agent-loop violations.
- `plugins/tektos/tests/test_tektos_agent.py` — DoD literal test + supporting fake ports.

**Files unchanged this stage:**
- `plugins/tektos/stub/` (Stage 2.4 test-only simulator) — kept alive per Q5=B; deleted at 3.2.
- `plugins/tektos/tests/test_stage_2_4_exit_gate.py` — unchanged; still binds to `TektosSimulator`.
- All Phrouros / Praxis / APEX code — untouched.

**Files modified:**
- `plugins/tektos/__init__.py` — re-export `TektosAgent`, `TektosMessage`, `TektosStep`, `TektosMessageRole`, `TektosError`; keep existing stub re-export.
- `docs/PORTING_LEDGER.md` — the PLANNED "OpenHands SDK" entry (Tektos section) becomes `PATTERN-VENDORED` with source, commit, license, Kosmos location, port list, modifications.
- `docs/Kosmos-Build-Spec-v25.md` §17 — new ADR-036 row.
- `docs/Kosmos-Build-Sequence-v25.md` §3.1 — rewritten LANDED with expanded action / DoD anchor / locked-answers footer.
- `docs/adrs/README.md` — ADR-036 row.
- `BUILD_LOG.md` — 2 entries (ADR-036 authored + Stage 3.1 landed).
- `SESSION_HANDOFF.md` — overwritten to reflect Stage 3.2 as next.

**Port surface at 3.1:**
- Consumer of `LLMPort` (async `generate_text` at 3.1 — simplest verb; `chat` reserved for 3.2 multi-turn).
- Consumer of `MemoryPort` (async `write_event` with `provenance="tektos_agent"` + `confidence`; async `query_temporal` for context read). Zero-trust guard enforced at port level per ADR-008.
- No new port introduced.
- No EventBusPort at 3.1 (event emission arrives at 3.2 when MCP tool calls generate observable actions).
- No TraceFeedPort emission from the real agent at 3.1 (the Stage-2.4 gate test uses `TektosSimulator` for that).

**Compliance:**
- ADR-007 respected — `plugins/tektos/agent.py` imports zero other plugins. Grep-verifiable in landing commit.
- ADR-008 respected — every `MemoryPort.write_event` call carries `provenance="tektos_agent"` and a `confidence` value in `(0, 1]`. Port-level guard rejects the alternative.
- ADR-022 (LLMPort surface) respected — Tektos consumes the port's declared verbs, does not extend or bypass.
- ADR-020 (Tektos migration) reference — ADR-036 is the concrete 3.1 slice inside the migration direction ADR-020 laid out.

**Deletion trigger for `plugins/tektos/stub/`:** Stage 3.2 landing commit deletes the tree once MCP tool calls emit real `TraceEvent`s. The Stage-2.4 gate test is rewired to instantiate the real Tektos agent at that point.

## Lock-in phase

Stage 3.1 (Weeks 3-4). Landing commit is the lock-in event.

## References

- `Kosmos-Build-Spec-v25.md` §17 (this ADR row), §18 (Tektos plugin), §432 (OpenHands SDK core-agent-loop lineage), §566 (OpenHands + agent-governance-toolkit + MCP), §17.1 (UI Parity Rule Phase-2 grandfathering)
- `Kosmos-Build-Sequence-v25.md` §3.1 (LANDED entry)
- `docs/PORTING_LEDGER.md` — "OpenHands SDK — PATTERN-VENDORED" entry (Tektos section)
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (DozerDB MemoryPort + zero-trust write contract)
- ADR-020 (Tektos migration direction)
- ADR-022 (LLMPort surface expansion)
- ADR-035 (Stage-2 exit gate; established `plugins/tektos/stub/` and stub-fate policy for 3.2)
- Upstream: [`OpenHands/software-agent-sdk`](https://github.com/OpenHands/software-agent-sdk) — MIT
