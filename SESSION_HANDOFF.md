# Kosmos Session Handoff — 2026-07-30 11:57 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.2 **LANDED** → next: Stage 6.3 (Wire winning inner-loop into Zetesis)
- **Plugin / kernel component:** Zetesis (`plugins/zetesis/`)
- **Port(s) in progress:** none at 6.2 (substrate selection only). Stage 6.3 wires the winner behind `adapters/zetesis/inner_loop/` over `LLMPort` + `SearchPort` (+ optional `SearchPort` MCP transport substrate).

## Winner locked
- **Substrate:** `langchain-ai/open_deep_research@d337ae32ed4ff8f4c6fbe192ba3bf1b2d6610799` (MIT)
- **LLM:** `qwen2.5:32b-instruct-q4_K_M` via local Ollama
- **Tools:** `langchain-mcp` streamable-http against the shared SearXNG substrate (container `kosmos-adr010-searxng` on `127.0.0.1:8888`)
- **Rejected:** BAAI/AREX-Turbo — on-shelf at `vendor/adr_010/arex_inference/` with four-clause revisit gate in `PORTING_LEDGER.md` §Zetesis
- **Head-to-head artifacts:** `ops/benchmarks/artifacts/adr-010-2026-07-30/{arex,odr}/` (six trial JSONs; committed at `e882b2a`)
- **Manual blind rating:** ODR 3.0/18 (16.7%) vs. AREX 0.0/18 (0%) on F1-F6 canonical facts. Winner locked on **completion reliability under the Colossus envelope**; substrate answer-quality tuning is Stage 6.3's job.

## Colossus thermal envelope (**hard constraint until remediation**)
Two RTX 5090 display-blank thermal events above 85 °C this session, both during sustained vLLM bfloat16 attention with an extended KV cache (once at 32k context, once at 65k). **Do not run bfloat16 inference above the safe envelope on Colossus until thermal remediation is done and re-verified.**

- **Safe operating envelope for vLLM on Colossus:** `--enforce-eager --gpu-memory-utilization 0.75 --max-model-len 32768`
- **Thermal remediation work (separate future track, NOT blocking Stage 6.3):** undervolt / fan-curve tune / thermal-pad refresh; verify sustained ≥ 30 min at 65k bfloat16 attention < 82 °C before considering the AREX-Turbo revisit gate re-openable.
- **Stage 6.3 tuning runs Ollama-only** — `qwen2.5:32b-instruct-q4_K_M` at ~28 GB VRAM peak, well inside the observed thermal envelope. No vLLM inference required at 6.3 unless a specific comparison demands it.

## Completed this session
- Post-reboot health check (GPU 33 °C idle / 829 MiB · SearXNG up · Ollama alive · repo at `9ca4b54`)
- Committed ODR + AREX 32k trial artifacts as `e882b2a` (seven files, 648 insertions)
- Bumped vLLM to 65k context, ran AREX-Turbo re-run cohort — all three failed (2× visit-tool 404s + 1× connection error alongside RTX 5090 display-blank thermal event; trials not committed to repo)
- Manual blind rating of all six trials against F1-F6 (see `/tmp/adr010/rating.md`)
- Fanned ADR-010 LOCKED across ADR file · adrs/README.md · Kosmos-Build-Spec-v25.md §17/§23/§24 · Kosmos-Build-Sequence-v25.md §6.2 · PORTING_LEDGER.md §Zetesis · BUILD_LOG.md · SESSION_HANDOFF.md
- Committed + pushed + tagged `stage-6-2-complete`

## Remaining before current Definition of Done
- Stage 6.2 DoD is **met** (this session). No open work at 6.2.

## Open questions / awaiting user answer
- **Stage 6.3 substrate-tuning approach.** ODR at 16.7% on F1-F6 is well below shipping quality. Three main dials to consider before wire-up:
  1. Prompt anchoring against the F1-F6 rubric pattern (cheapest, quickest, no VRAM impact)
  2. Source-diversity floor + retrieval-gate tightening in the MCP substrate
  3. Model swap to a stronger open-weight (e.g., `qwen2.5:72b-instruct-q4_K_M`, or a coder/reasoning variant) — requires VRAM re-planning against the thermal envelope
- User decision needed: which dial(s) drive Stage 6.3, and in what order.

## Exact next action
```bash
cd ~/dev/kosmos
git pull --ff-only origin main
git log --oneline -5   # confirm stage-6-2-complete tag is on latest
```
Then confirm Stage 6.3 substrate-tuning plan (which dial first) before starting `adapters/zetesis/inner_loop/` scaffolding.
