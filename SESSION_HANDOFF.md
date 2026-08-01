# Kosmos Session Handoff — 2026-08-01 16:40 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 3.13 (ADR-077 D2) — **shipped on branch `stage-3-13-tektos-intention`** + one follow-up fix commit (approval_gateway surface). Awaiting user pull + observed on Colossus.
- **Plugin / kernel component:** `plugins/tektos/intention/` + `kernel/app.py::tektos_intention` + `ui/components/IntentionForm.tsx`.
- **Port(s) in progress:** MemoryPort + ApprovalGatewayPort (reused as-is via `render_and_gate_plan_card`). No new ports this stage.

## Completed this session

- BUILD_LOG entry `2026-08-01 16:00 EDT` — Stage 3.13 intention scaffolder + kernel endpoint + GUI (ADR-077).
- BUILD_LOG entry `2026-08-01 15:44 EDT` — test-fake MemoryPort protocol fakes reapplied.
- BUILD_LOG entry `2026-08-01 16:40 EDT` — kernel now exposes `registry.approval_gateway` (ApprovalGatewayPort) alongside `registry.approval` (ApprovalResolverPort); intention endpoint uses it.
- DEBUG_LOG entry `2026-08-01 15:44 EDT` — MemoryPort protocol conformance failures resurfaced (supersedes `2026-08-01 11:59 EDT`).
- DEBUG_LOG entry `2026-08-01 16:36 EDT` — `'PraxisApprovalResolverAdapter' object has no attribute 'propose'` root-caused and fixed.
- ADR-077 written and ratified.
- 31/31 pytest scaffolder tests pass locally in `/tmp/kosmos-work/`.
- Colossus deployment note: `KOSMOS_TEKTOS_INTENTION_ROOT=/var/lib/kosmos/tektos/intentions` + `StateDirectory=kosmos/tektos/intentions` in `/etc/systemd/system/kosmos-kernel.service.d/10-tektos-intention-root.conf` (needed because `ProtectHome=read-only` on the unit). Consider baking into the repo as part of Stage 3.14.
- Branch `stage-3-13-tektos-intention` off `origin/stage-1-6-p3-code` pushed to GitHub.

## Remaining before current Definition of Done

- User pulls `stage-3-13-tektos-intention` on Colossus.
- User restarts `kosmos-kernel`.
- User runs `pytest plugins/tektos/tests/` (expect 31/31 new + previously-green tests still green).
- User runs `npm run build && npx playwright test 28-tektos-intention` (expect 5/5 smokes green; existing 27 specs should also stay green).
- User opens `/tektos`, types an intention (≥8 chars), submits, sees the gated PlanCard on `/tektos/detail?id=<approval_id>`.

## Open questions / awaiting user answer

- Whether to collapse Stage 3.14 (sandbox executor) into the next
  session or split it into 3.14a (SandboxProvider + adapter) + 3.14b
  (execution loop + `git apply`). Recommend split — smaller commits,
  cleaner rollback.
- The 5 stale `stage-1-5-*` branches on GitHub. Housekeeping deferred
  to a separate session (all confirmed squash-merged into
  `stage-1-6-p3-code`; safe to delete when the user chooses).

## Exact next action

- User: pull and observe.
  ```
  cd ~/dev/kosmos && git fetch origin && git checkout stage-3-13-tektos-intention && sudo systemctl restart kosmos-kernel && sleep 3 && pytest plugins/tektos/tests/ -q && (cd ui && npm run build && npx playwright test 28-tektos-intention)
  ```
- Agent (next session): begin Stage 3.14 — write `SandboxProvider`
  port + `git worktree` adapter under `adapters/sandbox/gitworktree/`
  + contract test.
