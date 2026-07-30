# Kosmos Session Handoff — 2026-07-30 10:12 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.2 (ADR-010 head-to-head eval)
- **Plugin / kernel component:** Zetesis inner-loop selection (harness lives under `ops/benchmarks/adr_010/`, not inside `plugins/zetesis/`)
- **Port(s) in progress:** none — harness is `ops/`-tier; no Protocol changes; no adapter promotion until winner is locked and Stage 6.3 begins

## Completed this session
- Stage 6.2 · ADR-010 head-to-head eval harness authored (pre-run) — see BUILD_LOG entry `2026-07-30 10:12 EDT`

## Remaining before current Definition of Done
1. **Colossus trial run** — the harness itself is authored and contract-tested in-sandbox; the six-metric trials themselves must run on Colossus. See `ops/benchmarks/adr_010/README.md` for the exact command sequence.
2. **Blind-rate `answer_correctness`** — after both contenders emit their `trial_*.json` files under `ops/benchmarks/artifacts/adr-010-2026-07-30/{arex,odr}/`, score each trial against the six canonical facts in `fixtures/adr_010_question.json`.
3. **Aggregate + winner selection** — compute mean/median across trials for each of the six metrics; declare a winner per the ADR-010 selection criteria (weighted correctness + diversity primary; latency + VRAM as tiebreakers).
4. **Second ADR-010 amendment (LOCKED)** — add `LOCKED (2026-07-30 · winner: <X>)` header and `## Head-to-Head Result` section; flip loser to `REJECTED` in `docs/PORTING_LEDGER.md`; promote winner's vendoring path (or its contract) into a first-class `adapters/zetesis/inner_loop/` seam ready for Stage 6.3 to consume.
5. **Fanout** — spec §17 ADR-010 row updated from OPEN to LOCKED; Build-Sequence §6.2 flipped to LANDED with winner named; BUILD_LOG append; SESSION_HANDOFF overwrite pointing at Stage 6.3.
6. **Commit + tag** — `stage-6-2-complete` tag on the fanout commit; push.
7. **Refresh shared assets** — v25 zip + ADRs bundle regenerate; submit project files; `share_file` with the existing three shared-asset names to chain versions.

## Open questions / awaiting user answer
None — all Q1–Q15 lock-in questions resolved this session. User has standing "make the optimal choices" instruction for any residual optima within the eval design.

## Exact next action
Run the Colossus trial sequence documented in `ops/benchmarks/adr_010/README.md`:

```bash
cd ~/kosmos-scan
docker compose -f ops/benchmarks/adr_010/docker-compose.yml up -d searxng
curl -s "http://127.0.0.1:8888/search?q=test&format=json" | head -c 200

CUDA_VISIBLE_DEVICES=0 python -m vllm.entrypoints.openai.api_server \
  --model BAAI/AREX-Turbo --served-model-name AREX-Turbo \
  --host 127.0.0.1 --port 8001 --dtype bfloat16 &
sleep 60
.venv/bin/python -m ops.benchmarks.adr_010.runner --contender arex --trials 3
kill %1

ollama pull qwen2.5:32b-instruct-q4_K_M  # ~20GB, one-time
.venv/bin/python -m ops.benchmarks.adr_010.harness.mcp_search_server --transport sse &
sleep 5
.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr --trials 3
kill %1

git add ops/benchmarks/artifacts/
git -c user.email=lawapa.naljor@gmail.com -c user.name=rmholston420 commit \
  -m "ADR-010 eval artifacts (Colossus run 2026-07-30)"
git push
```

After push, notify Perplexity Computer session — the artifact JSONs will be blind-rated, ADR-010 will be locked with the winner, and Stage 6.2 will close.
