# Kosmos

Single-user local-first Life Management System, targeted at **Colossus**
(AMD Ryzen 9 7900X · 128 GB RAM · RTX 5090 32 GB VRAM · Kubuntu 26.04 LTS).

## Repo layout (Stage 0.1)

```
kosmos/
├── README.md                    # this file
├── .gitignore
├── .perplexity/                 # Perplexity Computer skills + prompts
│   ├── skills/
│   │   ├── kosmos-port-workflow/SKILL.md
│   │   ├── kosmos-adr-authoring/SKILL.md
│   │   ├── kosmos-log-maintenance/SKILL.md
│   │   └── kosmos-spec-diff/SKILL.md
│   └── prompts/
│       ├── kosmos-build-system-prompt.md
│       └── kosmos-debug-system-prompt.md
│
├── BUILD_LOG.md                 # append-only — every completed step
├── DEBUG_LOG.md                 # append-only — search FIRST before diagnosing
├── KNOWN_ISSUES.md              # running open list
├── SESSION_HANDOFF.md           # overwrite at end of every session; READ at start of next
│
├── docs/                        # all spec + decision content lives here
│   ├── Kosmos-Build-Spec-v25.md          # master spec (stand-alone; supersedes v19–v24)
│   ├── Kosmos-Build-Sequence-v25.md      # executable stage → plugin → port → DoD order
│   ├── PORTING_LEDGER.md                 # every OSS port logged BEFORE first commit that uses it
│   ├── Kosmos-ADRs-Bundle.md             # all 22 ADRs in one file
│   ├── Kosmos-Perplexity-Skills-Bundle.md# 4 skills + 2 prompts in one file
│   └── adrs/                             # individual ADR files (ADR-001 … ADR-020)
│
├── templates/                   # starter copies of the four log files
│
├── kernel/                      # System 5 (identity) + System 2/3 (coordination)
├── plugins/                     # System 1 units (Tektos, Gnosis, Oikos, Zetesis, …)
├── ports/                       # formal Protocol interfaces (LLMPort, MemoryPort, …)
├── adapters/                    # concrete implementations of ports (vendored OSS wrapped here)
├── governance/                  # Praxis + Phrouros
└── ops/                         # deploy, benchmarks, DR runbooks
```

## Start-of-session ritual (HARD)

```bash
cat SESSION_HANDOFF.md
cat KNOWN_ISSUES.md
less docs/Kosmos-Build-Sequence-v25.md   # find your current stage/step
```

## The four non-negotiable disciplines

1. **Vendor before hand-build.** Log every port in `docs/PORTING_LEDGER.md` before first use.
2. **No plugin imports another plugin.** Cross-plugin coupling via event bus / formal ports only (ADR-007).
3. **Zero-trust memory writes.** No `MemoryPort.write` without `provenance` + `confidence`.
4. **Maintain the four logs.** BUILD_LOG (append), DEBUG_LOG (search first, then append),
   KNOWN_ISSUES (edit), SESSION_HANDOFF (overwrite each session end).

## Perplexity Computer skills

Load the appropriate skill before every relevant action:

- `kosmos-port-workflow` — before writing any component
- `kosmos-adr-authoring` — before making an architectural decision
- `kosmos-log-maintenance` — after every completed step + at session end
- `kosmos-spec-diff` — before editing any spec / sequence / ADR

## Current status

Stage 0.1 monorepo skeleton — docs and Perplexity skills in place; kernel/plugin/port
directories seeded as empty scaffolds. Next: Stage 0.2 (copy log templates to root
— already done at bootstrap) and Stage 0.3 (install skills into Perplexity user library),
then Stage 1.1 (donor adapter consolidation).

**Only OPEN ADR:** [ADR-010](docs/adrs/ADR-010-zetesis-inner-loop-eval.md) —
AREX vs. LangChain Open Deep Research head-to-head immediately before Phase 6.2.
All other ADRs are Ratified or Ratified v25.
