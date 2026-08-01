# Kosmos Session Handoff — 2026-08-01 17:43 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 3.14b (executor loop)
- **Plugin / kernel component:** `plugins.tektos.executor`
- **Port(s) in progress:** consumes `SandboxProvider` (ADR-079), `LLMPort`, `MemoryPort`, `ApprovalResolverPort`, `TraceFeedPort`. No new port.

## Completed this session
- Stage 3.14a step 1 — `ports/sandbox.py` + ADR-079 + ADR-039 amendment (`ad8f384`).
- Stage 3.14a step 2 — `GitWorktreeSandboxAdapter` + bwrap boundary + 21 contract tests + systemd drop-in + PORTING_LEDGER bwrap entry (`b95e9b5`). Verified 21/21 on Colossus with real bwrap.
- Stage 3.14b step 0 — ADR-080 scope lock (executor loop + model + retry + Colossus resource guard + two-identity commits) (`8de714c`).
- Stage 3.14b step 1 — executor package scaffold + policy constants + endpoint stubs + ADR-007 AST guard + 21 executor tests (`d8b5aa6`). ADR-080 amended in-flight: model swapped to `qwen3-coder:latest` (already resident on Colossus, 18 GB), VRAM floor lowered 22000 → 20000 MiB.
- Audited Forge-OH and PlexClaw for reusable executor code. Forge-OH `loop_guard.py` (44 lines) is the one clean vendor candidate for step 2; PlexClaw's `git_routes.py` is GPL-3.0-tainted and cannot be vendored.
- Added MIT `LICENSE` + `"license": "MIT"` to Forge-OH `main` (Forge-OH `9e7209d`) so downstream Kosmos vendoring is SPDX-clear.
- Logged Forge-OH `loop_guard.py` as PLANNED in Kosmos `PORTING_LEDGER.md` under new "Stage 3.14b · Tektos Executor" section (`21835a1`).

## Remaining before current Definition of Done (Stage 3.14b)
- **Step 2:** `plugins/tektos/executor/loop.py` (TektosExecutorLoop.run_plan), `patcher.py` (`git apply --check` + `git apply` + two-identity commit via `GIT_AUTHOR_*`/`GIT_COMMITTER_*` env), `resource_guard.py` (ColossusResourceGuard: `nvidia-smi` free VRAM + `/proc/meminfo` MemAvailable), `loop_guard.py` (vendor Forge-OH `bff/services/loop_guard.py`@`9e7209d`, MIT, keep `ActionFingerprint`/`LoopGuard` API, executor-namespaced). Flip 501 stubs to 200 for `/execute` and `/diff`. Contract tests (fake LLM + fake sandbox), patcher tests against a real tmp repo, resource guard tests with mocked `nvidia-smi`, loop_guard tests (fingerprint dedup + threshold), endpoint 200-path tests. When `loop_guard.py` lands, flip the PORTING_LEDGER entry from PLANNED to VENDORED.
- **Step 3:** UI wiring in `ui/lib/kernel-client.ts` (`executeTektosPlan(approvalId)` + `getTektosDiff(approvalId)`) + `/tektos/detail` Execute + Diff buttons wired + Playwright smoke.

## Open questions / awaiting user answer
- none.

## Exact next action
- Colossus verify: `cd ~/dev/kosmos && git pull && .venv/bin/python -m pytest plugins/tektos/executor/tests/ -q` — expect 21/21 green. Then `sudo systemctl restart kosmos-kernel` and confirm `POST /api/tektos/plan/nope/execute` returns 404 and `GET /api/tektos/plan/nope/diff` returns 404.
- Then start Stage 3.14b step 2 in a fresh session: begin with `plugins/tektos/executor/resource_guard.py` (simplest, no LLM), then `loop_guard.py` (vendored from Forge-OH `9e7209d`, MIT), then `patcher.py`, then `loop.py`, then flip the 501s. Flip the PORTING_LEDGER `loop_guard` entry PLANNED → VENDORED when the code lands.
