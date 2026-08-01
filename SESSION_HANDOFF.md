# Kosmos Session Handoff — 2026-08-01 03:05 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.5.7 · Gnosis retrieval surrogate (PR #8 open)
- **Plugin / kernel component:** `kernel/app.py` (four `/api/gnosis/*` routes + env-gated boot seeder)
- **Port(s) in progress:** MemoryPort (consumer side only — surrogate for future `plugins/gnosis/` at Phase 3)

## Completed this session
- Merged PR #7 (Stage 6.5.6 · Tektos kernel mount) and tagged
  `stage-6-5-6-tektos-kernel-mount` on Colossus after live smoke green
  (Ollama + DozerDB · Graphiti retrieved 5 corpus facts including
  Bodhicaryāvatāra + RTX 5090 lifeline).
- Audited backend for Gnosis surface. Discovered `ALL_CORPORA` (5
  corpora, ~40 facts) ships as static data but has no boot-time
  ingestion path — Tektos smoke retrieved facts persisted from prior
  contract-test runs, not a documented boot ingest.
- Authored ADR-064 (Stage 6.5.7 · Gnosis retrieval surrogate HTTP
  mount + boot seeder).
- Amended `kernel/app.py`:
  - Added `GNOSIS_CORPORA_MANIFEST` (5 entries), `_GNOSIS_CORPUS_BY_NAME`
    lookup, `_GNOSIS_EVENT_ID_RE`, `_GNOSIS_SEED_IGNORABLE`, and
    `_gnosis_hit_to_dict` helper.
  - Four new routes: `GET /api/gnosis/query?q&as_of&limit&corpus`,
    `GET /api/gnosis/corpora`, `GET /api/gnosis/stats`,
    `GET /api/gnosis/event/{event_id}`.
  - Env-gated boot seeder (`KOSMOS_GNOSIS_SEED=1`, default off) that
    ingests `ALL_CORPORA` via `MemoryPort.write_event` with class-name
    idempotency matching (`MemoryWriteBlocked` / `ClientError` /
    `ConstraintValidationFailed`).
  - `_BootRegistry` gains `gnosis_corpus_counts: dict[str, int]` and
    `gnosis_last_seeded_at: str | None`.
  - Version 6.5.6 → 6.5.7; module docstring updated.
- Added `tests/kernel/test_stage_6_5_7_gnosis_retrieval.py` (~20
  tests, fake `MemoryPort`).
- Updated `docs/adrs/README.md` (ADR-064 row inserted before ADR-063).
- Appended BUILD_LOG entry.
- Pushed PR #8:
  https://github.com/rmholston420/kosmos/pull/8

## Remaining before current Definition of Done
- On Colossus:
  1. Fast tier (fake memory) — `pytest tests/kernel/test_stage_6_5_7_gnosis_retrieval.py -v` all green.
  2. Live tier (real DozerDB + Ollama) — restart kernel with
     `KOSMOS_GNOSIS_SEED=1` set; assert `/api/gnosis/corpora` returns
     non-zero `fact_count` and `last_ingested_at`; assert
     `/api/gnosis/query?q=Rigpa&limit=5` returns hits;
     `/api/gnosis/query?q=Rigpa&corpus=rigpa-export` filters cleanly;
     `/api/gnosis/stats` returns the 8 keys.
- Merge PR #8, tag `stage-6-5-7-gnosis-retrieval-surrogate`.

## Open questions / awaiting user answer
- Frontend GUI stage ordering — recommended sequence for Stage 6.5.8+
  is (a) mount `plugins/tektos/ui/server.py` at `/tektos-ui/`, (b) add
  Praxis intentions + constitution routes, (c) Phrouros detector detail
  routes, (d) Zetesis research history. Confirm ordering before 6.5.8
  ADR authoring.

## Exact next action
- On Colossus:

  ```bash
  cd /home/rmholston/dev/kosmos
  git checkout main && git branch -D pr-8 2>/dev/null
  git fetch origin pull/8/head:pr-8
  git checkout pr-8

  pkill -f 'uvicorn kernel.app:app' 2>/dev/null; sleep 1
  lsof -i :8000 -t | xargs -r kill -9 2>/dev/null

  export KOSMOS_OLLAMA_BASE_URL=http://127.0.0.1:11434
  export KOSMOS_OLLAMA_DEFAULT_MODEL=qwen2.5:32b-instruct-q4_K_M
  export KOSMOS_MEMORY_BACKEND=dozerdb
  export KOSMOS_DOZERDB_URI=bolt://127.0.0.1:7687
  export KOSMOS_DOZERDB_USER=neo4j
  export KOSMOS_DOZERDB_PASSWORD=kosmos-dev-password
  export KOSMOS_EMBED_MODEL=nomic-embed-text
  export KOSMOS_GNOSIS_SEED=1

  # 1. Fast tier (in-memory port swap)
  unset KOSMOS_MEMORY_BACKEND; pytest tests/kernel/test_stage_6_5_7_gnosis_retrieval.py -v
  export KOSMOS_MEMORY_BACKEND=dozerdb

  # 2. Live smoke (real DozerDB + boot seeder)
  uvicorn kernel.app:app --host 127.0.0.1 --port 8000 &
  UPID=$!; sleep 6
  curl -s http://127.0.0.1:8000/api/gnosis/corpora | python3 -m json.tool
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=Rigpa&limit=5' | python3 -m json.tool
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=meditation&corpus=rigpa-export&limit=5' | python3 -m json.tool
  curl -s http://127.0.0.1:8000/api/gnosis/stats | python3 -m json.tool
  kill $UPID; wait $UPID 2>/dev/null
  ```

  If both tiers green, merge PR #8 and tag.
