# Kosmos Session Handoff — 2026-08-01 03:55 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.5.7 · Gnosis retrieval surrogate (PR #8, 3 hotfixes pushed)
- **Plugin / kernel component:** `kernel/app.py` (four `/api/gnosis/*` routes + env-gated boot seeder) + `adapters/memory/dozerdb/graphiti_temporal_index.py` (payload provenance hydration)
- **Port(s) in progress:** MemoryPort (consumer side) · TemporalIndex (adapter fix)

## Completed this session
- PR #8 opened with ADR-064 + Gnosis routes + boot seeder + 21 tests.
- **Hotfix 1 (03:15):** hoisted `import os` to module top — fixed `NameError` in seeder.
- **Hotfix 2 (03:32):** test file env preamble pins `KOSMOS_MEMORY_BACKEND=in_memory` + `KOSMOS_GNOSIS_SEED=0` before `from kernel.app import ...`. Fast tier now 21/21 green in 0.29s.
- **Live smoke (03:50–03:53):** four `/api/gnosis/*` routes verified against DozerDB with 214 pre-seeded facts. `/corpora` manifest correct, unfiltered `/query` returns hits, `/stats` returns all 8 keys, unknown-corpus returns 400 with valid list. Corpus filter bug isolated: `q=Rigpa&corpus=rigpa-export` returned empty because `GraphitiTemporalIndex.query_temporal` never surfaced provenance in `MemoryHit.payload`.
- **Hotfix 3 (03:55):** `graphiti_temporal_index.py` now batch-hydrates `EpisodicNode`s via `EpisodicNode.get_by_uuids` and injects `provenance` + `provenances` into `MemoryHit.payload`. `kernel/app.py` corpus filter uses set membership + wider `raw_limit`.

## Remaining before current Definition of Done
- Colossus retest with hotfix 3 (fresh shell, venv active):
  1. Fast tier — `pytest tests/kernel/test_stage_6_5_7_gnosis_retrieval.py -v` all 21 still green (adapter changes are additive; kernel filter accepts singular provenance via fallback).
  2. Live tier — `q=Rigpa&corpus=rigpa-export` returns non-empty (facts matching Rigpa in the rigpa-export corpus), `q=meditation&corpus=rigpa-export` returns rigpa-export meditation facts, `q=founded&corpus=synthetic-lifeline` returns Holston lifeline hits.
- Merge PR #8, tag `stage-6-5-7-gnosis-retrieval-surrogate`.
- Author ADR-065 (Stage 6.5.8 · Tektos live UI mount) — user confirmed ordering.

## Known non-blockers (Stage 4.5 concern, not 6.5.7)
- Boot seeder is slow: `write_event` internally calls Graphiti's `add_episode` which triggers LLM entity extraction (`qwen2.5:32b`) for every fact. 214 seed facts × ~10-30s each ≈ 10–20 min. Only affects the first seed of a fresh DozerDB. Idempotency shortcut works — later boots with `KOSMOS_GNOSIS_SEED=1` skip already-seeded corpora quickly (verified: `seeded_this_boot={}`). Not fixed here.

## Open questions / awaiting user answer
- none.

## Exact next action
- Colossus retest (fresh shell, venv active — the previous shell already has it):

  ```bash
  cd /home/rmholston/dev/kosmos
  source .venv/bin/activate

  git checkout main && git branch -D pr-8 2>/dev/null
  git fetch origin pull/8/head:pr-8
  git checkout pr-8

  # 1. Fast tier — env-scrubbed, quick
  env -u KOSMOS_MEMORY_BACKEND -u KOSMOS_GNOSIS_SEED \
      -u KOSMOS_DOZERDB_URI -u KOSMOS_DOZERDB_USER -u KOSMOS_DOZERDB_PASSWORD \
      -u KOSMOS_DOZERDB_DATABASE -u KOSMOS_OLLAMA_BASE_URL \
      -u KOSMOS_OLLAMA_DEFAULT_MODEL -u KOSMOS_TEKTOS_MODEL -u KOSMOS_EMBED_MODEL \
      pytest tests/kernel/test_stage_6_5_7_gnosis_retrieval.py -v

  # 2. Live smoke — seeder OFF (DB already has 214 facts)
  unset KOSMOS_GNOSIS_SEED
  export KOSMOS_MEMORY_BACKEND=dozerdb
  export KOSMOS_DOZERDB_URI=bolt://127.0.0.1:7687
  export KOSMOS_DOZERDB_USER=neo4j
  export KOSMOS_DOZERDB_PASSWORD=kosmos-dev-password
  export KOSMOS_OLLAMA_BASE_URL=http://127.0.0.1:11434
  export KOSMOS_OLLAMA_DEFAULT_MODEL=qwen2.5:32b-instruct-q4_K_M
  export KOSMOS_EMBED_MODEL=nomic-embed-text

  uvicorn kernel.app:app --host 127.0.0.1 --port 8000 &
  UPID=$!; sleep 15

  echo "=== q=Rigpa&corpus=rigpa-export ==="
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=Rigpa&corpus=rigpa-export&limit=5' | python3 -m json.tool
  echo "=== q=meditation&corpus=rigpa-export ==="
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=meditation&corpus=rigpa-export&limit=5' | python3 -m json.tool
  echo "=== q=founded&corpus=synthetic-lifeline ==="
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=founded&corpus=synthetic-lifeline&limit=5' | python3 -m json.tool
  echo "=== q=Rigpa (unfiltered — should now show provenance in payload) ==="
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=Rigpa&limit=3' | python3 -m json.tool

  kill $UPID; wait $UPID 2>/dev/null
  ```

  If corpus filter returns non-empty results, merge PR #8 and tag `stage-6-5-7-gnosis-retrieval-surrogate`, then move to ADR-065 authoring for Stage 6.5.8.
