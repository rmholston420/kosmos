# ADR: DeepSWE as a Tektos Eval-Corpus Candidate

> **STATUS AMENDMENT (2026-07-30):** Ratified as part of the v25 ADR set and landed at Build-Sequence §3.9. The Stage 3.9 landing pins the subset to **5 tasks** (3 Python + 2 TypeScript) drawn from the upstream commit `e016041a6ccf8da29906afc9a3f5a8df940a1f78` and vendored **manifest-only** — the corpus is hydrated on-demand into a git-ignored `.eval-cache/deepswe/` and the pinned `plugins/tektos/eval/corpora/deepswe/manifest.toml` is the authoritative record. Definition-of-Done clauses 1 and 2 are satisfied by this stage; **clause 3 (context-rot cross-check) is DEFERRED** until the dedicated context-rot regression suite lands as a Kosmos-native artifact (v20.2 §3 is a pre-v25 reference and v25 has not yet cut a replacement suite). Unblock condition: land the context-rot regression suite as a separate stage, then append a follow-up STATUS AMENDMENT here recording the cross-check numbers.

## Status
Ratified v25 · Landed at Stage 3.9 (manifest-only, 5-task subset; clause 3 deferred)

## Context
The Pier eval-harness ADR adopts Pier as Tektos's CI-time eval-execution engine satisfying Kosmos v20.2 Section 9's continuous eval-on-deploy gate, but does not name a task corpus. DeepSWE (`datacurve-ai/deep-swe`, released May 2026) is a long-horizon coding-agent benchmark: 113 original tasks across 91 active open-source repositories (TypeScript, Go, Python, JavaScript, Rust), using the same Harbor task format Pier consumes, with program-based verifiers and reference solutions held out from the agent. Its stated design goal is specifically to avoid the memorization problem of SWE-Bench-style public-issue corpora — DeepSWE's official leaderboard runs used Pier running mini-swe-agent on Modal, with documented average solutions spanning 668 lines across 7 files (5.5x larger than typical SWE-Bench problems).

## Decision
Adopt a filtered subset of DeepSWE's task corpus as one input to Tektos's fixture eval-suite (run via Pier per the companion ADR), specifically for long-horizon, multi-file task scenarios that exercise Tektos's worktree orchestration and context-budget management under realistic load. Do not adopt DeepSWE as the sole or primary eval corpus — it measures general coding-agent capability, not Kosmos-specific integration correctness (governance ladder, MemoryPort writes, cross-plugin fixture scenarios), which remain covered by Tektos's own Phase 10 fixture scenarios.

## Rationale
1. **Directly usable with the already-adopted harness**: DeepSWE tasks are natively Harbor-format, requiring no format-translation work beyond what the Pier ADR already establishes.
2. **Fills a specific gap Tektos's own fixtures don't cover**: Tektos's Phase 10 required fixture scenarios (spec-drop build path, prompt-to-spec build path, cross-plugin memory visibility, model-swap under load) test Kosmos-specific integration correctness, not general long-horizon coding capability under realistic multi-file complexity. DeepSWE's 668-line/7-file average solution size stresses exactly the kind of sustained context and worktree-management load that the earlier context-rot regression testing (v20.2 Section 3) is designed to catch — a real corpus is more informative than a synthetic fixture for this purpose.
3. **Documented leaderboard caveats are noted, not ignored**: independent replication of DeepSWE's headline pass@1 figures has not been found, and public benchmark data can decay once absorbed into training corpora. This is treated as a pressure test for Tektos's behavior under realistic load, not a validated ranking signal, consistent with the benchmark's own stated caveats.
4. **License and provenance**: DeepSWE tasks are drawn from active open-source repositories with documented task construction methodology (arXiv paper available); a subset selection is filtered for license compatibility per repository before inclusion, logged in `PORTING_LEDGER.md`.

## Scope of Adoption
- A filtered subset of DeepSWE tasks (language-matched to Kosmos's actual stack — Python, TypeScript primarily) is selected, not the full 113-task corpus, to keep CI runtime bounded.
- These tasks run through Pier as part of the continuous eval-on-deploy gate's long-horizon-scenario category, distinct from Tektos's own Kosmos-specific integration fixtures.
- Results feed the same `PORT_CONTRACTS.md` eval-tracking mechanism established by the Pier ADR — no separate governance artifact.

## Build-Order Placement
Applies once the Pier eval-harness integration (companion ADR) is live, exercising Tektos from Phase 4 onward once meaningful plugin behavior exists to evaluate against realistic multi-file tasks.

## Definition of Done
- A filtered, license-cleared DeepSWE task subset is logged in `PORTING_LEDGER.md` with source URL, commit hash, and per-task license notes.
- At least one DeepSWE task runs successfully through Pier against a fixture Tektos build, producing a pass/fail verifier result.
- Context-rot regression measurements (v20.2 Section 3) are cross-checked against DeepSWE task performance as an additional real-world data point, not a replacement for the dedicated synthetic regression test.
