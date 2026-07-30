# ADR-010 · Head-to-Head Eval Harness

Runs the ADR-010 comparison between AREX-Turbo (native BrowseComp harness) and
Open Deep Research + `qwen2.5:32b-instruct-q4_K_M`.

**Not for Perplexity sandbox execution.** The runner requires Colossus (GPU,
Ollama, vLLM). Contract tests in `tests/` are sandbox-safe (no LLM calls).

## Layout

```
ops/benchmarks/adr_010/
├── README.md            (this file)
├── runner.py            Colossus-side entry: --contender {arex,odr} --trials N
├── metrics.py           TrialMetrics dataclass (6 metrics per ADR-010 lock-in)
├── policy.py            ResourcePort background-priority policy for the run
├── harness/
│   ├── search_backend.py  SearXNG-backed search + visit tools (shared)
│   ├── arex.py            AREX-Turbo XML tool-call loop over vendored inference/
│   └── odr.py             Open Deep Research config over vendored open_deep_research/
├── fixtures/
│   ├── adr_010_question.json  The Neo4j-vs-DozerDB question + ground-truth answer
│   └── searxng_settings.yml   SearXNG service configuration
├── docker-compose.yml   Local SearXNG service (port 8888)
└── tests/
    ├── test_metrics.py
    ├── test_arex_xml_parser.py
    └── test_searxng_client.py
```

## Colossus run sequence

```bash
# 1. Boot shared SearXNG (single container, both contenders reuse)
cd ops/benchmarks/adr_010
docker compose up -d searxng
curl -s "http://127.0.0.1:8888/search?q=test&format=json" | head -c 200  # sanity

# 2. AREX contender
CUDA_VISIBLE_DEVICES=0 python -m vllm.entrypoints.openai.api_server \
  --model BAAI/AREX-Turbo --served-model-name AREX-Turbo \
  --host 127.0.0.1 --port 8001 --dtype bfloat16 &
sleep 60  # wait for weights load
.venv/bin/python -m ops.benchmarks.adr_010.runner --contender arex --trials 3
kill %1  # stop vllm before booting ODR backend

# 3. ODR contender (assumes ollama already serving)
ollama pull qwen2.5:32b-instruct-q4_K_M  # ~20GB, one-time
.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr --trials 3

# 4. Push artifacts back for blind rating
git add ops/benchmarks/artifacts/adr-010-2026-07-30/
git commit -c user.email=lawapa.naljor@gmail.com -c user.name=rmholston420 \
  -m "ADR-010 eval artifacts (Colossus run)"
git push
```

## Artifacts

`ops/benchmarks/artifacts/adr-010-2026-07-30/{arex,odr}/trial_{n}.json` — one
per trial with the 6 locked metrics + full trajectory + emitted `finish`
answer/evidences/confidence.

## Contract tests (sandbox-safe)

```bash
.venv/bin/pytest ops/benchmarks/adr_010/tests/ -x -q
```
