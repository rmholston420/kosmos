# Paste-in Session Seed — Tektos 3.12→3.14

Copy everything between the fences below into the first message of the new session.

---

```
Context: Kosmos LMS on Colossus (single-user local-first, RTX 5090, Kubuntu). Continuing from a prior session that just closed Stage 1.6 Phase 3 (memory subsystem). Now pivoting to Tektos.

Repo: ~/dev/kosmos on Colossus. Branch: stage-1-6-p3-code (PR #34 open). Latest commit: e416d57. All Stage 1.6 Phase 3 tiers green on Colossus.

Before you do anything, read these files in order:
1. SESSION_HANDOFF_TEKTOS.md
2. docs/seeds/tektos-3.12.md
3. Kosmos-Build-Spec-v25.md (specifically §3.12+)
4. SESSION_HANDOFF.md
5. BUILD_LOG.md (tail, for recent context)
6. DEBUG_LOG.md (only if a symptom recurs)

Locked scope (do not deviate):
- Stage 3.12: POST /api/tektos/intentions + <IntentionForm /> on /tektos
- Stage 3.13: RealExecutor(llm=LLMPort, memory=MemoryPort, repo_root=Path) replacing NopExecutor
- Stage 3.14: POST /api/tektos/apply/{approval_id} + Apply button on /tektos/detail

Every backend slice ships its frontend GUI in the SAME commit. One stage = one commit. Push after each stage's DoD is verified on Colossus.

Constraints (from user, verbatim from project instructions):
- Colossus-only. Ollama for LLM. Never OpenAI, Anthropic, or any cloud fallback — not even for testing.
- Single-user local-first. No multi-user assumptions. No CI dependency.
- Minimize verbosity. Short answers, bullets, exact commands. Never ask me to manually edit files — always give exact shell commands / insertion scripts.
- Never guess. Always inspect relevant files before modifying anything, including Rigpa-LMS / Forge-OH / PlexClaw donor code before porting from it.
- Zero-trust memory writes: no write to MemoryPort without provenance + confidence.
- No plugin imports another plugin's package directly (ADR-007). Cross-plugin coupling via event bus or formal ports only.
- Append-only BUILD_LOG.md and DEBUG_LOG.md with `YYYY-MM-DD HH:MM EDT` timestamps. Overwrite SESSION_HANDOFF.md before ending the session.
- We are credit-constrained. Efficient tool calls. Load the seed once; do not re-explore the tree.

Stop condition (single sentence, the entire session's DoD):
I open /tektos in the browser, type a coding intention, watch a plan render, click Approve, click Execute, see a REAL diff of actual repo files, click Apply, and the files change on disk.

Verify pattern on Colossus after each stage:
    cd ~/dev/kosmos
    git pull
    sudo systemctl restart kosmos-kernel
    sleep 3
    pytest plugins/tektos/tests/ -q
    (cd ui && npm run build && npx playwright test <spec-for-this-stage>)
    KOSMOS_STAGE_312_INTERACTIVE=1 pytest tests/integration/test_tektos_312_live.py -q  # 3.13+ only

Immediate first action: read the six files above, then propose a decomposed plan for Stage 3.12 (intentions endpoint + IntentionForm). Ask ONE clarifying question if anything in the seed is ambiguous; otherwise start on 3.12 with exact bash commands I can paste directly.

Do not touch:
- Memory subsystem code (Phase 3 is done, stable).
- New ADRs (3.12–3.14 land under existing ADR-045 + ADR-046).
- Kernel version (D7 will land naturally with 3.14).
- Anything beyond 3.14 apply.

Ready.
```

---

## Where the seed lives

- `docs/seeds/tektos-3.12.md` — full seed (270 lines, versioned in repo)
- `SESSION_HANDOFF_TEKTOS.md` — transient pointer (60 lines)
- `SESSION_HANDOFF.md` — pause-state snapshot from prior session
- `BUILD_LOG.md` tail — pause-point entry `2026-08-01 15:20 EDT`

## Why this shape

The paste-in preamble does three things a fresh session can't otherwise infer:
1. Anchors the branch + commit hash so `git pull` lands exactly where the prior session stopped.
2. Reproduces the verbatim project-instruction constraints in the session preamble so the new agent does not need to derive them from memory or a partial context window.
3. Locks the scope to 3.12→3.13→3.14 with no room for interpretive expansion, and defines a single verifiable stop condition.
