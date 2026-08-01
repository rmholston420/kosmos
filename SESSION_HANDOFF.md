# Kosmos Session Handoff — 2026-08-01 03:35 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.5.7 · Gnosis retrieval surrogate (PR #8 open, 2 hotfixes pushed)
- **Plugin / kernel component:** `kernel/app.py` (four `/api/gnosis/*` routes + env-gated boot seeder)
- **Port(s) in progress:** MemoryPort (consumer side only)

## Completed this session
- Merged PR #7 (Stage 6.5.6) and tagged `stage-6-5-6-tektos-kernel-mount`.
- Authored ADR-064 (Stage 6.5.7).
- Patched `kernel/app.py`: four Gnosis routes, env-gated boot seeder, two new `_BootRegistry` fields, version 6.5.6 → 6.5.7.
- Added `tests/kernel/test_stage_6_5_7_gnosis_retrieval.py` (21 tests over `_FakeMemoryPort`).
- Updated `docs/adrs/README.md`.
- Pushed PR #8: https://github.com/rmholston420/kosmos/pull/8
- **Hotfix 1 (03:15 EDT):** hoisted `import os` to module top — fixed `NameError` in Gnosis boot seeder.
- **Colossus retest (03:20 EDT) hung 18 min in `test_query_happy_path` against real DozerDB + Ollama.** Root cause: shell had `KOSMOS_MEMORY_BACKEND=dozerdb` + `KOSMOS_GNOSIS_SEED=1` still exported; `kernel.app` builds its FastAPI app at import time; `TestClient(app)` lifespan booted real backends before the fake port swap could run.
- **Hotfix 2 (03:32 EDT):** added env preamble at the top of the test file that pins `KOSMOS_MEMORY_BACKEND=in_memory` and `KOSMOS_GNOSIS_SEED=0` before `from kernel.app import ...`. Second `DEBUG_LOG.md` entry logged.
- Pushed hotfix 2 onto PR #8 branch.

## Remaining before current Definition of Done
- Colossus retest with fresh shell:
  1. Fast tier — `pytest tests/kernel/test_stage_6_5_7_gnosis_retrieval.py -v` all 21 green.
  2. Live tier — restart kernel with `KOSMOS_GNOSIS_SEED=1`; confirm boot completes, `/api/gnosis/corpora` returns non-zero `fact_count` + `last_ingested_at`, `/api/gnosis/query?q=Rigpa&limit=5` returns hits, `/api/gnosis/query?q=meditation&corpus=rigpa-export&limit=5` filters cleanly, `/api/gnosis/stats` returns the 8 keys.
- Merge PR #8, tag `stage-6-5-7-gnosis-retrieval-surrogate`.
- Author ADR-065 (Stage 6.5.8 · Tektos live UI mount) — user confirmed ordering.

## Open questions / awaiting user answer
- none.

## Exact next action
- On Colossus, **open a fresh shell** (do NOT reuse the previous one — it has live-smoke env vars):

  ```bash
  cd /home/rmholston/dev/kosmos

  pkill -f 'uvicorn kernel.app:app' 2>/dev/null; sleep 1
  lsof -i :8000 -t | xargs -r kill -9 2>/dev/null

  git checkout main && git branch -D pr-8 2>/dev/null
  git fetch origin pull/8/head:pr-8
  git checkout pr-8

  # 1. Fast tier — completely clean env
  env -u KOSMOS_MEMORY_BACKEND \
      -u KOSMOS_GNOSIS_SEED \
      -u KOSMOS_DOZERDB_URI \
      -u KOSMOS_DOZERDB_USER \
      -u KOSMOS_DOZERDB_PASSWORD \
      -u KOSMOS_DOZERDB_DATABASE \
      -u KOSMOS_OLLAMA_BASE_URL \
      -u KOSMOS_OLLAMA_DEFAULT_MODEL \
      -u KOSMOS_TEKTOS_MODEL \
      -u KOSMOS_EMBED_MODEL \
      pytest tests/kernel/test_stage_6_5_7_gnosis_retrieval.py -v --timeout=60

  # 2. Live smoke — separate shell if any test failed above
  export KOSMOS_OLLAMA_BASE_URL=http://127.0.0.1:11434
  export KOSMOS_OLLAMA_DEFAULT_MODEL=qwen2.5:32b-instruct-q4_K_M
  export KOSMOS_MEMORY_BACKEND=dozerdb
  export KOSMOS_DOZERDB_URI=bolt://127.0.0.1:7687
  export KOSMOS_DOZERDB_USER=neo4j
  export KOSMOS_DOZERDB_PASSWORD=kosmos-dev-password
  export KOSMOS_EMBED_MODEL=nomic-embed-text
  export KOSMOS_GNOSIS_SEED=1

  uvicorn kernel.app:app --host 127.0.0.1 --port 8000 &
  UPID=$!; sleep 15
  curl -s http://127.0.0.1:8000/api/gnosis/corpora | python3 -m json.tool
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=Rigpa&limit=5' | python3 -m json.tool
  curl -s 'http://127.0.0.1:8000/api/gnosis/query?q=meditation&corpus=rigpa-export&limit=5' | python3 -m json.tool
  curl -s http://127.0.0.1:8000/api/gnosis/stats | python3 -m json.tool
  kill $UPID; wait $UPID 2>/dev/null
  ```

  If both tiers green → `gh pr merge 8 --squash --delete-branch --repo rmholston420/kosmos && git tag stage-6-5-7-gnosis-retrieval-surrogate && git push --tags`.
