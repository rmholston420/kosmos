# Kosmos Session Handoff — 2026-07-30 14:22 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 6.3.4b · Zetesis inner-loop ODR substrate (harness hotfix inside Stage 6.3.4 lock-in band)
- **Plugin / kernel component:** ADR-010 head-to-head eval — ODR harness (`ops/benchmarks/adr_010/`)
- **Port(s) in progress:** none formal; operational tuning inside ADR-010 LOCKED band.

## Completed this session

- Stage 6.3.4 shims 4/5/6/7/8 landed, ran clean on Colossus (peak 74 °C, all 3 trials wrote artifacts).
- Stage 6.3.4b harness hotfix:
  - **URL extractor** widened to exclude `[` and `]` from URL body — kills the `github.com/neo4j/neo4j[3]` footnote-marker bug the Stage 6.3.4 log surfaced.
  - **Cooldown min-seconds default 15 → 10** (Stage 6.3.4 peak 74 °C, 11 °C below 85 °C watchdog, 14 °C below 88 °C driver-crash line).
- `ops/benchmarks/adr_010/tests/` = **131 passed** locally (was 128: +3 regression tests).

## Remaining before current Definition of Done

- **On Colossus**, after `git pull`:
  1. `.venv/bin/python -m pytest ops/benchmarks/adr_010/tests/` — expect **131 green**
  2. `.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr`
     - Cooldowns should be 10 s.
     - No `[3` / `[7` / `[N` fragments in verifier URLs.
- **Blind rate** the three artifacts against `fixture.ground_truth.canonical_facts`:
  - `ops/benchmarks/artifacts/adr-010-2026-07-30/odr/trial_01_*.json`
  - `.../trial_02_*.json`
  - `.../trial_03_*.json`
- **Stage 6.3.4 Definition of Done:** mean rated correctness ≥ 5/6 across 3 trials AND `final_unverified_urls` empty on every trial AND no `[unsupported]` markers survive to final report for any of the 6 canonical facts.
- If missed:
  1. First escalation: `--n-consistency 3` (shim 5 opt-in, ~3× runtime).
  2. Second escalation: Stage 6.3.5 quantization/model uplift ADR.

## Open questions / awaiting user answer

- **Neo4j CE-vs-EE dual-licensing.** Shim 4 records one license family per repo. Neo4j itself is dual-licensed (CE = GPLv3, EE = commercial). If the rating still misses F1/F2 after 6.3.4b, this needs a shim 4 upgrade (per-repo `license_families: [gpl-3.0, commercial]`) or a fixture-level dual-licensing directive.

## Exact next action

On Colossus:

```bash
cd ~/dev/kosmos && git pull \
  && .venv/bin/python -m pytest ops/benchmarks/adr_010/tests/ \
  && .venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
```
