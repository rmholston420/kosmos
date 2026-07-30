# Kosmos v25 Bundle

**Everything needed to build Kosmos, ready to execute Stage 1 immediately.**

## What's in this bundle

| Path | Purpose |
|---|---|
| `Kosmos-Build-Spec-v25.md` | Definitive unified master spec. Supersedes v19–v24 and all addenda. Stand-alone. |
| `Kosmos-Build-Sequence-v25.md` | Executable stage → plugin → port → DoD order. Follow top-to-bottom. |
| `PORTING_LEDGER.md` | Every OSS component to vendor. Log to this file **before** first commit that uses it. |
| `adrs/` | 22 ADR files (numbered ADR-001…ADR-020, plus DozerDB variant of 008 and DeepSWE variant of 007). Only ADR-010 is OPEN. |
| `adrs/README.md` | ADR index. |
| `perplexity/skills/` | Four Perplexity Computer skills that automate spec/log/ADR/port discipline. |
| `perplexity/prompts/` | Two reusable system prompts (build, debug). |
| `templates/` | `BUILD_LOG.md`, `DEBUG_LOG.md`, `KNOWN_ISSUES.md`, `SESSION_HANDOFF.md` starter files. |
| `archive/` | Every source file this bundle was compiled from (v22, v23, v24, addenda, agentic scans, ADRs, etc.). Provenance only — do not reference from live docs. |

## Stage 1 quickstart

```bash
# 1. Unpack this bundle at the repo location of your choice
unzip kosmos-v25.zip -d ~/dev/
cd ~/dev/kosmos-v25/

# 2. Copy templates to the future Kosmos repo root
mkdir -p ~/dev/kosmos/
cp templates/*.md ~/dev/kosmos/
cp Kosmos-Build-Spec-v25.md Kosmos-Build-Sequence-v25.md PORTING_LEDGER.md ~/dev/kosmos/docs/ 2>/dev/null || mkdir -p ~/dev/kosmos/docs && cp Kosmos-Build-Spec-v25.md Kosmos-Build-Sequence-v25.md PORTING_LEDGER.md ~/dev/kosmos/docs/
cp -r adrs ~/dev/kosmos/docs/
cp -r perplexity/skills ~/dev/kosmos/.perplexity/ 2>/dev/null || mkdir -p ~/dev/kosmos/.perplexity && cp -r perplexity/skills ~/dev/kosmos/.perplexity/

# 3. Follow Kosmos-Build-Sequence-v25.md from Stage 0.1
```

## Perplexity Computer skills — install

Each skill under `perplexity/skills/kosmos-*` is a stand-alone directory containing a `SKILL.md` file. Install via the Perplexity Computer skill library — the `save_custom_skill` tool accepts either the directory zipped or the `SKILL.md` directly.

Once installed:

- `kosmos-port-workflow` — load before writing any component
- `kosmos-adr-authoring` — load before making an architectural decision
- `kosmos-log-maintenance` — load after every completed step and at end of session
- `kosmos-spec-diff` — load before editing the spec, sequence, ledger, or any ADR

## Resolved decisions in v25 (vs. v24)

| ADR | Decision |
|---|---|
| ADR-004 | Bernstein Janitor spike-test **approved** — adopt iff Tektos Phase 4 fixture wins |
| ADR-008-DozerDB | **DozerDB fork** adopted as MemoryPort graph store |
| ADR-009 | **llama-swap primary** + router-mode fallback (contingent on Stage 1.7 SLO benchmark) |
| ADR-011 | **a2a-sdk** as Koinonia standalone transport (not on Moltbook) |
| ADR-012 | Consolidate `ollama.py` / `searxng.py` duplicates in Stage 1.1 |
| ADR-013 | Memory-bridge redundancy comparison during Stage 1 pre-Phase-2 |

## The only remaining OPEN decision

**ADR-010** — AREX vs. LangChain Open Deep Research for the Zetesis inner loop. Head-to-head evaluation runs immediately before Phase 6.2. Winner locked at that point; loser recorded as `REJECTED` in PORTING_LEDGER.

## Non-negotiables (verbatim from project custom instructions)

- Target Colossus first. Single-user, local-first. No cloud control planes, no multi-user assumptions, no GitHub-native CI unless explicitly asked.
- Be terse. Bullets, exact commands. No filler.
- Never ask the user to manually edit files. Give exact bash commands / scripts.
- Never guess. Inspect donor code before porting.
- Vendor before hand-build. Log every port in `PORTING_LEDGER.md`.
- No plugin imports another plugin — event bus / formal ports only (ADR-007).
- Zero-trust memory writes: `provenance` + `confidence` mandatory.
- Maintain `BUILD_LOG.md`, `DEBUG_LOG.md`, `KNOWN_ISSUES.md`, `SESSION_HANDOFF.md`.

## Bundle version

**Kosmos-v25** · compiled 2026-07-29 (America/Detroit).
