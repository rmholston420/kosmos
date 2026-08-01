# Session Handoff — Stage 1.6 Phase 3

## Current stage/plugin/port
Stage 1.6 Phase 3. Sequence: D4 ✅ → D5 ✅ → **D6.5 (CODE LANDED, verify pending)** → D6 → 3.12 real executor.

## Completed this session
- **D4 fully closed** (all 3 tiers green including live).
- **D5 fully closed** (fast-tier 11/11, Playwright 3/3, live-tier 2/2, UI build green). Query-parameter route `/memory/provenance?event=<id>` used to stay compatible with `output: 'export'`.
- **D6.5 code landed:**
  - `PhrourosAnomaliesTable` component (table, detector filter, WS live-invalidate on `phrouros.anomaly.detected`, flash highlight)
  - Mounted on `/observe/page.tsx` below `JobPage`
  - Backend untouched — `/api/phrouros/anomalies` and WS topic already live from Stage 2.4
- BUILD_LOG appended.

## Remaining before D6.5 DoD
Colossus verify:
```bash
cd ~/dev/kosmos
git fetch origin stage-1-6-p3-code && git checkout stage-1-6-p3-code && git pull
(cd ui && npm run build && npx playwright test 26-phrouros-anomalies)
KOSMOS_STAGE_16_LIVE=1 pytest tests/integration/test_phrouros_anomalies_live.py -q
```

## Open questions
None.

## Next action
Once D6.5 verify is green, begin **D6 — AMG status route + pill** (ADR-076 §D6):
- Backend: `GET /api/memory/amg/status` (kernel builds from `agent_memory_guard.__version__`, `AmgGuardPolicy._policy_preset`/`_policy.detectors` accessors, module-level `_verdict_counter`, D4's `list_quarantined(limit=0).total_count`)
- Adapter: add public accessors on `AmgGuardPolicy`; new `total_count` field on `QuarantinedPage`
- UI: header "AMG status" pill on `/memory` (color-coded by quarantined_count > 0)

## Git state
- Branch: `stage-1-6-p3-code`
- To be pushed: D6.5 code
- Previous: `a9ed4fc` (D5 test cleanup), `3c1b45c` (D5 static-export refactor), `fee591a` (D5), `31d593e` (D4 pseudo-cypher fix), `c52be79` (D4)
