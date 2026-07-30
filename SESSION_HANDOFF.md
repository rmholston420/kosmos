# Kosmos Session Handoff — 2026-07-30 00:22 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 2.3 — **LANDED**. Next up: Stage 2.4 (Stage-2 exit gate).
- **Plugin / kernel component:** Phrouros anomaly detector (System 4) landed. Stage-2 exit gate remains.
- **Port(s) in progress:** none currently in flight. Stage 2.4 will exercise the full chain: **TraceFeedPort (Phrouros) → NotificationPort (algedonic) → ResourcePort (compute reservation) → EventBusPort → APEX ChangeApprovalProtocol (Praxis) → NotificationPort (user notification)** end-to-end.

## Completed this session
- **2026-07-30 00:10 EDT** — ADR-034 authored (Phrouros anomaly detector, Ratified v25) with all five locked answers (Q1=A · Q2=A · Q3=B · Q4=A · Q5=A) and rejection rationale for each rejected option.
- **2026-07-30 00:20 EDT** — Stage 2.3 landed end-to-end:
  - New reader-only `TraceFeedPort` at `ports/trace_feed.py` (259 lines): `InMemoryTraceFeedAdapter` primary (asyncio pub/sub, snapshot-list fan-out, idempotent close) + `LangfuseTraceFeedAdapter` Stage-5 stub.
  - New plugin at `plugins/phrouros/` — 12 modules landed (errors, models, detector protocol, 4 detectors including real LoopDetector + 3 skeletons, engine, plugin, `__init__`, tests package).
  - 55 new contract tests across 5 test files.
  - Full pytest suite 514 → 569 (+55); `make stage1-gate` PASS regression.
  - Doc fan-out complete: spec §17 ADR-034 row · `docs/adrs/README.md` ADR-034 row · Build-Sequence §2.3 rewrite with LANDED marker + DoD PASS + locked-answers footer · `PORTING_LEDGER.md` "Phrouros anomaly detector" GREENFIELD block.
  - Two BUILD_LOG entries appended.

## Remaining before current Definition of Done
- Stage 2.3 DoD met. **Nothing remaining at Stage 2.3.**

## Open questions / awaiting user answer
- **Stage 2.4 planning question:** the current Build-Sequence entry is a one-liner ("Praxis + Phrouros co-operate: unauthorized action → Phrouros detects → APEX escalates → user notified. End-to-end scenario passes."). Before starting Stage 2.4 I need three answers to lock scope, mirroring the Q1–Q5 pattern used for 2.1 / 2.2 / 2.3:
  - **Q1:** does "unauthorized action" mean (A) a Tektos-style tool call that violates governance policy — with Tektos stub inserted at Stage 2.4 as a fake; or (B) a synthetic non-plugin actor emitting trace events directly into the feed (no Tektos stub required); or (C) defer Stage 2.4 until Stage 3 lands Tektos and revisit?
  - **Q2:** which detector fires? (A) `LoopDetector` on a synthetic loop — reuses Stage 2.3 code path exactly; (B) a new `UnauthorizedToolDetector` real detector — needs its own §-anchor and skeleton-first ADR; or (C) both, showing the seam supports multiple detector types simultaneously?
  - **Q3:** is the "APEX escalates" step (A) Phrouros publishes `phrouros.anomaly.detected` and an `AnomalyBridge` translator listens and calls `APEX.propose(intention=..., tier=HUMAN_REQUIRED)` — canonical event-only cross-plugin coupling per ADR-007; or (B) Phrouros calls APEX directly through a formal port (requires a new port + ADR); or (C) the user-notification step already IS the escalation and no APEX round-trip is needed at 2.4?

## Exact next action
Ask user to lock **Q1 / Q2 / Q3** for Stage 2.4 before writing any code. Do NOT start 2.4 without those three answers.

After answers: author ADR-035 (Stage-2 exit-gate scenario), then land the end-to-end test.
