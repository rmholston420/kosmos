# Session Handoff — Tektos 3.12+ (fresh session start)

Read `docs/seeds/tektos-3.12.md` first — the full seed with scope,
DoD, and rationale. This file is the transient handoff pointer.

## Enter here

1. `cd ~/dev/kosmos && git checkout stage-1-6-p3-code && git pull`
2. Baseline: `pytest plugins/tektos/tests/ -q` (all green)
3. Read `docs/seeds/tektos-3.12.md`
4. Start on stage 3.12.

## Ordered next slices

- **3.12** — `POST /api/tektos/intentions` + `<IntentionForm />` on `/tektos`.
- **3.13** — `RealExecutor` (LLMPort + MemoryPort + repo_root) replaces `NopExecutor`.
- **3.14** — `POST /api/tektos/apply/{approval_id}` + Apply button on `/tektos/detail`.

## Stop condition (single sentence)

The user opens `/tektos`, types a coding intention, watches a plan
appear, approves it, clicks Execute, reviews the real diff, clicks
Apply, and the diff is written to the working tree.

## Constraints (from user this session)

- Every backend slice must ship its frontend GUI in the same commit.
- Credits are tight — one plan, one commit per stage, no exploratory reads.
- Colossus-only. Ollama for LLM. Never cloud.
- Single-user local-first. No CI dependency.

## Verify pattern (Colossus)

```bash
cd ~/dev/kosmos
git checkout stage-1-6-p3-code && git pull
sudo systemctl restart kosmos-kernel
sleep 3
pytest plugins/tektos/tests/ -q
(cd ui && npm run build && npx playwright test 28-tektos-intention)
KOSMOS_STAGE_312_INTERACTIVE=1 pytest tests/integration/test_tektos_312_live.py -q
```

## Current branch state

- Branch: `stage-1-6-p3-code` (PR #34 open)
- Latest commit: `470ef7f` — ADR-076 D6 landed
- Stage 1.6 Phase 3 complete except D7 (kernel version bump 6.12 → 6.13
  + PORT_CONTRACTS audit). D7 is optional before 3.12; a version bump
  to 6.13.0 will happen naturally when 3.14 lands, so 3.12 does not
  block on D7.

## Anti-goals for this session

- Do not touch memory subsystem code (Phase 3 is done — that surface
  is stable).
- Do not open new ADRs.
- Do not add cloud fallbacks.
- Do not expand scope past 3.14 apply.
