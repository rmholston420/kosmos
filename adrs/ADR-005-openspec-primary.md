# ADR: OpenSpec as Primary Spec-Driven Development Engine for Tektos Spec Studio

## Status
Proposed (requires Tier-2 ADR ratification)

## Context
Tektos v1's Spec Studio (Phase 3) currently designates GitHub Spec-Kit (`github/spec-kit`, MIT) as the primary spec-pipeline donor for Entry Point B (natural-language prompt → `/speckit.specify` → delta proposal → three-dimension verify gate), with OpenSpec (`Fission-AI/OpenSpec`, MIT) used narrowly as the delta-spec (ADDED/MODIFIED/REMOVED) data-model donor only. Since Tektos v1 was drafted, community adoption data shows OpenSpec growing 863% over six months versus Spec-Kit's roughly 18% over the same period, and OpenSpec has undergone a v1 rewrite producing a lighter, faster workflow that multiple production users (including internal use at Toggl, per community reporting) now prefer for day-to-day spec-driven development over Spec-Kit's heavier structured pipeline.

## Decision
Promote OpenSpec's full v1 workflow to the primary spec-driven development engine for Tektos's Spec Studio, retaining Spec-Kit only as a reference for the specific phase-gated `constitution→specify→clarify→plan→tasks` structure where Tektos's own governance ladder requires that level of explicit staging. OpenSpec's delta-spec data model, already adopted, remains unchanged as the underlying representation.

## Rationale
1. **Adoption trend is a meaningful signal, not the sole reason**: an 863% vs. 18% six-month growth differential, combined with documented production use, suggests OpenSpec's lighter workflow is winning on practical ergonomics — the same category of consideration Kosmos already applies via "repo reality wins" (ADR-007 guiding principle: when a ported component's actual working contract differs from the spec's assumption, follow the working code).
2. **No architectural conflict**: OpenSpec is already a vendored dependency (as the delta-spec data-model donor). Promoting it to primary engine is a scope expansion of an existing dependency, not a new vendor addition — lower integration risk than adding an unrelated new tool.
3. **Spec-Kit is not discarded**: Tektos's own governance ladder (HUMAN_REQUIRED gating, three-dimension verify gate) benefits from Spec-Kit's more explicit phase-gating for cases where Tektos needs stricter staging than OpenSpec's lighter default — e.g., production-deploy specs versus routine feature specs. Both entry points remain available; this ADR changes which is primary, not which is retained.

## Scope of Change
- **Entry Point A** (Docling-parsed uploaded spec → consistency check → living-spec table): unchanged — this entry point does not depend on Spec-Kit's `/speckit.specify` pipeline and is unaffected by this ADR.
- **Entry Point B** (natural-language prompt → structured spec): the default pipeline becomes OpenSpec's v1 workflow (proposal → delta-spec → validation) rather than Spec-Kit's `/speckit.specify` command. Spec-Kit's phase-gated pipeline remains available as an explicit alternative mode for specs that require its stricter staging (invoked deliberately, not the default).
- **Delta-spec model**: unchanged — OpenSpec's ADDED/MODIFIED/REMOVED representation was already the adopted data model; this ADR does not alter it.
- **Living-spec table**: unchanged — remains in Tektos's Postgres schema regardless of which entry-point pipeline produced the delta.

## Rationale for Not Discarding Spec-Kit Entirely
Kosmos's vendor-before-build principle requires re-verification, not permanent lock-in, of vendored choices — but discarding a working, license-compatible, already-integrated dependency without a specific failure mode is unwarranted caution in the other direction. Spec-Kit's explicit phase-gating remains valuable for exactly the class of spec Tektos's governance ladder treats most strictly (HUMAN_REQUIRED-tier changes), so it is retained as a named alternative mode rather than removed.

## Build-Order Placement
No change to Rollout Plan sequencing. This ADR applies at Tektos Phase 3 (Spec Studio) build time, before Entry Point B's default pipeline is implemented — cheaper to apply now than after Phase 3 ships with Spec-Kit as default.

## Definition of Done
- Tektos Phase 3's Entry Point B implementation defaults to OpenSpec's v1 proposal→delta-spec→validation workflow.
- A named alternative mode invokes Spec-Kit's phase-gated pipeline for specs explicitly flagged as requiring stricter staging (e.g., production-deploy-tier specs).
- A fixture natural-language prompt produces a valid delta-spec via OpenSpec's default path with zero unresolved CRITICAL issues, matching Tektos Phase 3's existing Definition of Done language.
- `PORTING_LEDGER.md`'s existing OpenSpec entry is updated to note the expanded scope (from data-model-only donor to primary pipeline engine); no new entry is required since OpenSpec was already vendored.
