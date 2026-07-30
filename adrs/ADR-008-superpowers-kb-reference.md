# ADR: Superpowers as a Tektos Knowledge-Base Methodology Reference

## Status
Proposed (requires Tier-2 ADR ratification)

## Context
Tektos v1 Phase 4 (Knowledge Base, KB Authoring, Self-Improvement, Multi-Agent Safety) plans a hybrid rule-table-plus-vector KB seeded from `astral-sh/ruff` and `PyCQA/bandit`, with structured-form/bulk-import authoring and a 180-day reconfirmation cycle. Superpowers (`obra/superpowers`, MIT, ~244K GitHub stars as of July 2026, one of the fastest-growing open-source repositories of 2026) is a composable-skills methodology framework for coding agents, encoding a 7-phase development discipline (brainstorming → planning → TDD → subagent-driven execution → two-stage code review → systematic debugging → branch completion) as ~14-20 individually-loadable Markdown skill files, now the top plugin on Anthropic's official Claude Code marketplace and supported across Claude Code, Cursor, Copilot CLI, Gemini CLI, and OpenCode.

## Decision
Do not vendor Superpowers's skill files directly into Tektos's KB. Adopt its underlying methodology pattern — an enforced brainstorm→plan→TDD→execute→review→verify→complete phase sequence, expressed as individually-loadable skill units — as the structural template for Tektos's own KB-authored engineering-discipline rules, replacing ad hoc rule entries with an equivalent phase-gated skill sequence native to Tektos's existing propose→validate→gate pipeline.

## Rationale
1. **Scale of adoption is a strong signal of a real gap being solved**: reaching ~244K stars in under nine months, faster than nearly any other 2026 open-source developer tool, indicates Superpowers's core insight — coding agents left unconstrained skip testing and verification — is a widely-felt problem, not a niche preference. Tektos's own self-improvement pipeline (Reflexion strategy, Voyager-pattern skill library) already targets a similar outcome but without Superpowers's specific enforced-sequencing mechanism.
2. **Direct architectural compatibility**: Superpowers's skill-loading model (individually-activatable Markdown units, triggered contextually) is structurally identical to the three-tier progressive-disclosure pattern already adopted for Tektos's KB per the earlier Kosmos v20.2/graph-engineering research (metadata always-loaded, body loaded on trigger). Adopting Superpowers's methodology content as skill entries in that same format is additive, not a new subsystem.
3. **Does not conflict with governance**: Superpowers's "no code before tests, no completion without evidence" enforcement maps onto Tektos's existing governance ladder tiers (e.g., a fixture failing systematic-debugging 3-strike rule could escalate to HUMAN_REVIEW) rather than requiring a parallel enforcement mechanism.
4. **Not vendored as executable code**: Superpowers ships as Markdown skill definitions plus lightweight orchestration logic for Claude Code specifically. Directly importing its skill files would tie Tektos's KB content to Superpowers's own update cadence and marketplace distribution; instead, the *methodology* (phase sequence, TDD enforcement, two-stage review, systematic debugging protocol) is authored natively as Tektos KB entries, referencing Superpowers as a design source in provenance metadata.

## Scope of Adoption
- Tektos KB gains a new rule category: engineering-discipline skills (brainstorming, TDD enforcement, systematic debugging, two-stage code review), authored in Tektos's own three-tier progressive-disclosure format, with `source_citation` pointing to Superpowers's public methodology as design provenance (not a code dependency).
- Superpowers's "3-strike systematic debugging" rule (three failed fix attempts trigger architectural reconsideration rather than continued patching) is adopted as a concrete Tektos self-improvement trigger, feeding into the existing Reflexion-strategy pipeline.
- Superpowers's two-stage code review (spec-compliance pass, then code-quality pass, run by separate reviewer instances to avoid bias) is adopted as the structure for Tektos's own multi-agent code-review step where applicable.

## Build-Order Placement
Applies at Tektos Phase 4 (Knowledge Base, KB Authoring, Self-Improvement). No change to Rollout Plan sequencing.

## Definition of Done
- Tektos KB includes engineering-discipline skill entries for TDD enforcement, systematic debugging (3-strike rule), and two-stage code review, each citing Superpowers as design provenance.
- A fixture task demonstrates the 3-strike systematic-debugging trigger correctly escalating to a self-improvement/HUMAN_REVIEW path rather than continued unguided patching.
- No Superpowers code or Markdown files are directly vendored into Tektos's `vendor/` directory; `PORTING_LEDGER.md` is not modified since no code is ported, only a design-provenance citation is recorded in KB rule metadata.
