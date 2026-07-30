# ADR-037 — Tektos MCP Transport, Playwright-MCP, APEX Tool-Call Gating (Stage 3.2)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.2
**Supersedes:** —

## Context

Stage 3.2 lands three intertwined surfaces: (1) MCP transport into Kosmos, (2) Playwright-MCP as its first real tool provider, (3) the Praxis approval path that gates every Tektos tool call. It also fires the ADR-036 Q5=B deletion trigger for `plugins/tektos/stub/TektosSimulator` and rewires the Stage-2.4 exit-gate test to consume the real Tektos agent.

Spec anchors: §432 (`modelcontextprotocol/python-sdk` + `microsoft/playwright-mcp` both MIT), §281 (short-lived Ed25519 bearer tokens for MCP), §155 (MCP server config files immutable), §566 (main OpenHands runtime patterns deferred to Stage 3.2 alongside MCP transport). Build-Sequence §3.2 DoD literal: "MCP transport carries at least one Playwright tool call through Praxis approval."

Six decisions are load-bearing:

1. **MCP vendor mode** — PATTERN-VENDORED vs. pip dependency vs. verbatim vendor.
2. **Playwright-MCP surface** — real subprocess only, fake only, or both.
3. **Approval path** — every tool call through APEX, allowlist-gated APEX, or event-driven APEX.
4. **Stub deletion + Stage-2.4 gate rewire** — locked by ADR-036 Q5=B; the "how" is scoped here.
5. **Port surface** — new formal `MCPPort` vs. Tektos-internal composition.
6. **ADR shape** — one per stage vs. split vs. amend.

Constraints: local-first Colossus (no cloud control plane); ADR-007 (plugins depend on Protocols, not other plugins); ADR-008 (every `MemoryPort.write_event` carries `provenance` + `confidence`); ADR-022 (LLMPort surface); ADR-033 (APEX `ChangeApprovalProtocol` three-tier ladder); ADR-036 (Tektos plugin layout + stub-fate policy).

## Decision

**Q1 = A — MCP transport PATTERN-VENDORED.** No `mcp` pip dependency; no verbatim copy. The MCP client surface Kosmos actually needs at 3.2 (initialize handshake, `tools/list`, `tools/call`, close) is reimplemented in Kosmos-native Python behind a new `MCPPort` Protocol. Upstream reference: `modelcontextprotocol/python-sdk` @ commit `a4f4ccd091138771535e17191123f20b30fda68e`, MIT.

**Q2 = C — Both fake in-process and real Playwright-MCP subprocess (env-gated).** The Stage-3.2 DoD test drives an in-process fake MCP server (`plugins/tektos/mcp/fake_playwright_server.py`) via `InProcessMCPAdapter` — deterministic, no Node dependency, no Chromium install, runs in CI. The real Playwright-MCP subprocess adapter (`adapters/mcp/stdio/PlaywrightStdioAdapter`) is wired at 3.2 but its integration test is gated by `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1` — skipped in default `pytest` and `make stage1-gate` runs; user opts in when they have Node + Chromium ready. Both adapters implement the same `MCPPort`, so Stage 3.7 spec-kit UI cards inherit the working transport by swapping the adapter instance.

**Q3 = A — Every MCP tool call flows through APEX `ChangeApprovalProtocol.propose()`.** `TektosAgent.call_tool(name, arguments)` — before invoking `MCPPort.call_tool` — calls `apex.propose(intention_id=f"tektos.tool:{turn_id}:{name}", tier=<mapped>, proposing_domain="tektos")`. The tier is resolved by `plugins/tektos/mcp/tool_policy.py::resolve_tier(tool_name)`, a hardcoded `dict[str, ChangeApprovalTier]` at Stage 3.2 (matches ADR-035 Q4=A hardcoded-allowlist pattern; a `PolicyPort` seam is deferred to Stage 5 governance-key wiring). Default tier for unmapped tools = `HUMAN_REQUIRED` (fail-closed). On `AUTONOMOUS` auto-approval, tool executes; on `HUMAN_REVIEW`/`HUMAN_REQUIRED`, the tool call raises `TektosToolCallPending` and the agent waits for the approval resolution on a subsequent turn (not part of the 3.2 DoD literal — the DoD test uses an AUTONOMOUS-tiered tool).

**Q4 = A — Delete `plugins/tektos/stub/` and rewire Stage-2.4 exit-gate test to consume the real Tektos agent.** ADR-036 Q5=B locked the trigger to Stage 3.2 landing; this ADR locks the rewire shape. The Stage-2.4 gate test replaces `TektosSimulator.simulate_unauthorized_call(...)` with `TektosAgent.call_tool("shell_exec", ...)` where `shell_exec` maps to `HUMAN_REQUIRED` in `tool_policy` **and** is absent from `UnauthorizedToolDetector`'s allowlist. The real agent's `call_tool` path publishes a `TraceEvent(plugin="tektos", tool_name="shell_exec", ...)` on the injected `TraceFeedPort` **before** invoking `MCPPort.call_tool`, so Phrouros observes it identically to the simulator's synthesis. The `TektosSimulator` class, its tests, and `plugins/tektos/stub/` package are removed atomically in the Stage-3.2 landing commit.

**Q5 = A — New `MCPPort` Protocol + `adapters/mcp/<impl>/`; ADR-033 amended in-flight to promote `ChangeApprovalProtocol` + `ChangeApprovalTier` from `plugins/praxis/apex/*` to `ports/approval.py`.** Tektos consuming `ChangeApprovalProtocol` requires a port surface (ADR-007 forbids cross-plugin imports). Rather than a stringly-typed workaround, this ADR amends ADR-033: the Protocol + enum now live in `ports/approval.py` and `plugins/praxis/apex/*` re-exports for backwards compatibility. All existing APEX modules and tests continue to import from `plugins.praxis.apex` unchanged.

**Q5 detail —** `ports/mcp.py` declares `MCPPort` (async `initialize`, `list_tools`, `call_tool`, `close`; sync `is_healthy`) sibling to every other Kosmos port. `MCPTool` and `MCPToolResult` frozen dataclasses live alongside. Two adapters ship at 3.2: `InProcessMCPAdapter` (backed by an in-process `MCPServer` Protocol; Playwright fake driver satisfies the DoD test) and `StdioMCPAdapter` (JSON-RPC over `asyncio.subprocess`; drives the real Playwright-MCP via `npx @playwright/mcp` when env-gated). Zero new PyPI dependencies. Stage-4+ consumers (Forge-OH, Neurolink) inherit the port without touching Tektos code.

**Q6 = A — Single new ADR-037 covering all six 3.2 decisions.** Matches ADR-035 (Stage 2.4) and ADR-036 (Stage 3.1) precedent — one ADR per stage boundary.

## Rationale

**Q1 rejects B (pip dep) and C (verbatim vendor).** B lands `mcp>=1.0`, its Pydantic v2 pin, and its anyio + starlette + uvicorn + pywin32 transitives; on Colossus that inflates the resolver graph and creates cross-couples with Kosmos's own asyncio-first primitives (`ports/notification.py`, `plugins/praxis/apex/scheduler.py`). Local-first posture rejects a network resolve at import time. C (verbatim copy) forces manual patch tracking for a fast-moving protocol; upstream ships fixes weekly. Pattern-vendoring the four verbs Tektos needs (`initialize`, `tools/list`, `tools/call`, close) is ~200 lines and matches Rigpa constitution loader (ADR-032), APEX (ADR-033), MemoryBridge (ADR-013), Tektos agent (ADR-036).

**Q2 rejects A (real only) and B (fake only).** A adds Node.js, `npx`, and Chromium to Colossus as CI prerequisites — violates "single-user local-first" posture and makes every future contributor's first `pytest` run fail until they install a browser stack. B leaves Stage 3.7 (spec-kit UI cards) with no proven real-transport code path, forcing a fresh port and a fresh ADR at 3.7. C ships both: fake for CI/DoD (deterministic), real behind an opt-in env flag `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1` (feature-flag test skipped by default). Matches the Stage-1.13 ResourcePort pattern where the real 5090 probe lives behind opt-in while the primary test path uses fakes.

**Q3 rejects B (allowlist-gated) and C (event-driven).** B is architecturally inverted — the DoD literal says "carries a Playwright tool call **through** Praxis approval", implying the happy path traverses APEX, not just the exception path. Reusing `UnauthorizedToolDetector` for the happy path leaves the AUTONOMOUS tier unexercised at 3.2 (it's the whole point of ADR-033 §14.1). C (event-driven `tektos.tool.requested` → `tektos.tool.approved` round-trip) is the eventual Stage-5+ shape when Synedrion coordination lands, but adds a second event-bus round-trip inside the agent's sync call path at 3.2 with no additional safety. A directly composes `ChangeApprovalProtocol` (already Ratified as ADR-033), uses `AUTONOMOUS` for the DoD happy path, and preserves the option for `HUMAN_REVIEW`/`HUMAN_REQUIRED` tiers to raise `TektosToolCallPending` for the real Stage-5+ resolve-on-later-turn flow.

**Q4 rejects B (delete stub, keep gate test on fake MCP server) and C (defer stub deletion to 3.3).** B leaves the Stage-2.4 gate test wired to a synthetic trace source when the real thing (Tektos + MCPPort) now exists — misses the ADR-036 Q5=B point that "MCP tool calls emit real `TraceEvent`s through `TraceFeedPort`" is *why* the stub becomes redundant. C amends a just-Ratified ADR to defer its own trigger — violates the newer-wins rule and the `kosmos-spec-diff` skill's stop condition against reviving older-spec positions without amending v25 first. A is the ADR-036-honoring path: rewire the gate to consume the real agent, prove the same end-to-end path (unauthorized tool → Phrouros → APEX → algedonic) fires under real Tektos.

**Q5 rejects B (Tektos-internal, no port) and C (port defined, adapters stubbed).** B saves ~50 lines of ports+adapters scaffolding today but creates plugin surgery when Forge-OH (Stage 4.3) and Neurolink (Stage 4.6) both consume MCP per spec §432/§566 — retrofitting a port under existing plugin call sites costs far more than defining it up front. C defines the port but ships no real adapter; the Q2=C answer already ships a real `StdioMCPAdapter`, so C would leave that adapter in adapter limbo. A defines the port, ships two adapters (fake in-process + real stdio), matches every prior port (LLMPort has ollama + stub adapters, MemoryPort has DozerDB + in-memory adapters).

**Q6 rejects B (split ADR-037/038) and C (amend-only).** B splits MCP-transport from APEX-tool-gating across two ADRs, but the two are inseparable at 3.2 — the DoD test wires them together and `TektosAgent.call_tool` implements both surfaces in one method. C skips a new ADR entirely; violates `kosmos-adr-authoring` skill rule (new port + new upstream vendors + new plugin subsystem = structural decision requiring an ADR).

## Consequences

**Files added:**
- `ports/mcp.py` — `MCPPort` Protocol + `MCPTool` + `MCPToolResult` + `MCPToolCallError` + `MCPServer` Protocol (in-process server contract).
- `adapters/mcp/__init__.py` — namespace.
- `adapters/mcp/stdio/__init__.py`, `adapters/mcp/stdio/adapter.py` — `StdioMCPAdapter` (JSON-RPC over `asyncio.subprocess`).
- `adapters/mcp/stdio/playwright.py` — `PlaywrightStdioAdapter` factory (spawns `npx @playwright/mcp` when `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1`).
- `adapters/mcp/in_process/__init__.py`, `adapters/mcp/in_process/adapter.py` — `InProcessMCPAdapter` (composes with an `MCPServer` instance in-process; no subprocess).
- `plugins/tektos/mcp/__init__.py` — re-exports.
- `plugins/tektos/mcp/tool_policy.py` — `resolve_tier(tool_name)`, `TEKTOS_TOOL_TIER_MAP: dict[str, ChangeApprovalTier]`, fail-closed default `HUMAN_REQUIRED`.
- `plugins/tektos/mcp/fake_playwright_server.py` — `FakePlaywrightServer(MCPServer)` with canned `browser_navigate` tool.
- `plugins/tektos/tests/test_tektos_mcp.py` — DoD literal + ~15 supporting contract tests.
- `plugins/tektos/tests/test_playwright_stdio_integration.py` — env-gated real-subprocess test (skipped by default).
- `adapters/mcp/stdio/tests/test_stdio_adapter.py` — JSON-RPC codec + subprocess lifecycle contract tests using a Python fake MCP server subprocess.
- `adapters/mcp/in_process/tests/test_in_process_adapter.py` — Protocol conformance + happy-path contract tests.

**Files modified:**
- `plugins/tektos/agent.py` — `TektosAgent` gains optional `mcp: MCPPort | None`, `apex: ChangeApprovalProtocol | None`, `trace_feed: TraceFeedPort | None` + `call_tool(name, arguments, *, turn_id=None) -> TektosStep` method. Existing `send_message` + `run` LLM-loop surface preserved; the DoD test from 3.1 still passes. New `TektosToolCallPending` and `TektosToolCallDenied` errors added to `plugins/tektos/errors.py`.
- `plugins/tektos/models.py` — `TektosStep` extended with optional `tool_name`, `tool_arguments`, `tool_result` fields (backwards-compatible defaults).
- `plugins/tektos/__init__.py` — re-export `TektosToolCallPending`, `TektosToolCallDenied`, `TEKTOS_TOOL_TIER_MAP`, `resolve_tier`, `InProcessMCPAdapter`, `FakePlaywrightServer` (test-fixture-usable). Remove the `plugins.tektos.stub` re-export block and docstring reference.
- `plugins/tektos/tests/test_stage_2_4_exit_gate.py` — replace `TektosSimulator` imports and call sites with `TektosAgent` + `InProcessMCPAdapter` + `FakePlaywrightServer`. The DoD literal test name is unchanged; assertions on `phrouros.anomaly.detected` + `praxis.escalation.proposed` + APEX `HUMAN_REQUIRED` PENDING + `deliver_algedonic()` are unchanged.
- `pyproject.toml` — register new packages: `adapters.mcp`, `adapters.mcp.stdio`, `adapters.mcp.stdio.tests`, `adapters.mcp.in_process`, `adapters.mcp.in_process.tests`, `plugins.tektos.mcp`. No new runtime deps.

**Files deleted:**
- `plugins/tektos/stub/__init__.py`
- `plugins/tektos/stub/simulator.py`

**Docs fan-out:**
- `docs/adrs/README.md` — ADR-037 row.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-037 row appended after ADR-036.
- `docs/Kosmos-Build-Sequence-v25.md` §3.2 — rewritten LANDED with expanded action / DoD anchor / locked-answers footer.
- `docs/PORTING_LEDGER.md` — two new `PATTERN-VENDORED` entries under the Tektos section: `MCP python-sdk` (was PLANNED) and `Playwright-MCP` (was PLANNED). MCP transport commit hash: `a4f4ccd091138771535e17191123f20b30fda68e`. Playwright-MCP commit hash: `55679f5f3d4b4f3e2534ec0ce2fc5683ba2eaf3f`.
- `BUILD_LOG.md` — three entries (ADR-037 authored + MCPPort + adapters landed + Stage-3.2 gate-rewire commit).
- `SESSION_HANDOFF.md` — overwritten to reflect Stage 3.3 as next.

**Compliance:**
- ADR-007 respected — Tektos does not import Phrouros or Praxis packages directly; APEX access is via the `ChangeApprovalProtocol` interface passed at construction. AST-verified in the extended `test_tektos_agent_imports_no_other_plugins_adr_007`.
- ADR-008 respected — every `MemoryPort.write_event` from `call_tool` carries `provenance="tektos_agent"` + confidence. Tool-call events use predicate `tektos.tool.completed` (new) alongside the existing `tektos.turn.completed`.
- ADR-022 respected — LLMPort surface untouched.
- ADR-023 respected — APEX event envelopes continue to carry `producer_plugin="praxis"` (Tektos does not gain its own envelope producer at 3.2).
- ADR-033 respected — `AUTONOMOUS`/`HUMAN_REVIEW`/`HUMAN_REQUIRED` tier semantics preserved; the `resolve_tier` mapping is a policy layer over the engine, not a shortcut around it.
- ADR-036 respected — the `TektosAgent` surface added at 3.1 is preserved (all 18 Stage-3.1 tests still green after 3.2 landing); `send_message` + `run` LLM loop unchanged.

**Locked constants:**
- `TEKTOS_TOOL_PREDICATE = "tektos.tool.completed"` (canonical predicate for completed tool-call writes).
- `TEKTOS_TOOL_TIER_MAP: dict[str, ChangeApprovalTier]` (Stage 3.2 hardcoded): `browser_navigate → AUTONOMOUS`, `browser_snapshot → AUTONOMOUS`, `browser_click → HUMAN_REVIEW`, `browser_type → HUMAN_REVIEW`, `shell_exec → HUMAN_REQUIRED`, `file_write → HUMAN_REQUIRED`. Default (unmapped) = `HUMAN_REQUIRED`.
- `MCP_PROTOCOL_VERSION = "2024-11-05"` (upstream MCP protocol version pin at Stage 3.2; upgraded via ADR amendment).

**Deletion triggers for future stages:**
- `plugins/tektos/mcp/fake_playwright_server.py` and `InProcessMCPAdapter` are NOT deleted at Stage 3.7 — they remain the deterministic CI test path. Real Playwright-MCP subprocess adapter becomes the default `MCPPort` binding for user-facing Tektos at Stage 3.7.
- `TEKTOS_TOOL_TIER_MAP` hardcoded dict is replaced by `PolicyPort` at Stage 5.

## Lock-in phase

Stage 3.2 (Weeks 3-4). Landing commit is the lock-in event.

## References

- `Kosmos-Build-Spec-v25.md` §17 (this ADR row), §18 (Tektos), §281 (MCP security), §432 (upstream vendors), §566 (main OpenHands runtime deferred here)
- `Kosmos-Build-Sequence-v25.md` §3.2 (LANDED entry)
- `docs/PORTING_LEDGER.md` — MCP python-sdk + Playwright-MCP entries
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (zero-trust MemoryPort writes)
- ADR-022 (LLMPort surface)
- ADR-033 (APEX ChangeApprovalProtocol three-tier ladder)
- ADR-035 (Stage-2 exit gate; the gate test rewired here)
- ADR-036 (Tektos plugin layout; stub deletion trigger fires here)
- Upstream: [`modelcontextprotocol/python-sdk`](https://github.com/modelcontextprotocol/python-sdk) MIT · [`microsoft/playwright-mcp`](https://github.com/microsoft/playwright-mcp) MIT
