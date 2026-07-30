# ADR: Pier as a Tektos Eval-on-Deploy Vendor Candidate

> **STATUS AMENDMENT (2026-07-30):** Superseded by [ADR-042](./ADR-042-tektos-pier-eval-harness.md). The Kosmos v20.2 framing in this ADR (`SandboxProvider`, capability-broker-mediated isolation, Tier-2 promotion pipeline, `PORT_CONTRACTS.md` logging, Phase 10 fixture scenarios) does not survive under Kosmos v25's ports-plus-plugins architecture. ADR-042 replaces it with a Tektos-internal Pier eval subsystem that: (a) vendors `datacurve-pier==0.3.0` from PyPI as a dev-only optional dependency, (b) invokes Pier as a subprocess through its `pier run` CLI — no in-process import, (c) locks a single MemoryPort event predicate `tektos.eval.trial_completed` with locked provenance and bounded confidence per ADR-008, (d) treats verdicts as advisory only (ADR-042 Q7=B) so plan cards remain user-approved, and (e) introduces no new port surface per ADR-023. Retained here for the audit trail; not authoritative.

## Status
Superseded by ADR-042 (2026-07-30). Original: Proposed (Kosmos v20.2 Section 9 continuous eval-on-deploy gate).

## Context
Kosmos v20.2 Addendum Section 9 introduced a continuous eval-on-deploy gate requiring every plugin build — not only initial Tier-2 promotion — to trigger an automated eval-suite run alongside existing SBOM/SCA, contract, and chaos tests. That gate was defined without naming a concrete eval harness. Pier (`datacurve-ai/pier`) is a Harbor-compatible framework for evaluating coding agents in sandboxed environments: it reads Harbor's task format and runs trials against it, giving Tektos a standards-compatible way to define and execute fixture eval scenarios rather than building bespoke eval tooling from scratch.

## Decision
Adopt Pier as the eval-execution harness satisfying Kosmos v20.2 Section 9's continuous eval-on-deploy requirement for Tektos, running Tektos-specific fixture tasks authored in Harbor's task format. Do not adopt Pier's own sandboxing/orchestration layer as a replacement for Tektos's existing `SandboxProvider`/capability-broker-mediated isolation (Tektos Phase 2) — Pier's sandbox execution is used only for the isolated act of running an eval trial, not for Tektos's production task execution path.

## Rationale
1. **Directly closes a named gap**: v20.2 Section 9's Definition of Done requires "a fixture plugin rebuild triggers the eval suite automatically as part of CI," but named no harness. Pier's Harbor-format compatibility means eval fixtures can be authored once and potentially reused against other Harbor-compatible benchmarks (e.g., any future SWE-bench-style suite Kosmos adopts), avoiding a bespoke, Tektos-only eval format.
2. **Scope discipline**: Pier is adopted narrowly as an eval-trial runner, not as a sandbox or orchestration replacement, consistent with Tektos's "no plugin-local kernel" principle — the eval trials it runs are isolated CI-time checks, not part of Tektos's runtime capability-broker-gated execution path, so there is no overlap with Kosmos's existing sandbox governance.
3. **Vendor-before-build**: Building a bespoke eval-trial runner when a standards-compatible one already exists would violate Kosmos's own vendor-before-build principle without a documented reason to prefer custom code.

## Integration Plan
- Pier is vendored as a CI-time dependency only, invoked by the kernel-wide Tier-2 promotion pipeline (and the new continuous eval-on-deploy gate) — not embedded inside Tektos's runtime `plugins/tektos/` module tree.
- Tektos's own fixture scenarios (Phase 10's four required end-to-end scenarios: spec-drop build path, prompt-to-spec build path, cross-plugin memory visibility, model-swap under load) are additionally expressed as Harbor-format tasks where practical, so Pier can execute them as part of the standing eval-on-deploy gate rather than only at Phase 10 hardening.
- Eval-suite results from Pier runs are logged in `PORT_CONTRACTS.md` per plugin per build, per v20.2 Section 9's existing requirement — no new governance artifact needed.

## Build-Order Placement
Applies from the point the continuous eval-on-deploy gate is first enforced (kernel-wide, per v20.2 Section 9), and specifically exercises Tektos's fixture scenarios from Phase 4 onward (once meaningful plugin behavior exists to evaluate). No change to Rollout Plan phase sequencing.

## Definition of Done
- Pier is logged in `PORTING_LEDGER.md` with source URL, commit hash, SPDX license identifier, and a note confirming it is CI-time-only, not a runtime dependency.
- At least one Tektos fixture scenario is expressed in Harbor task format and successfully executed via Pier in CI.
- A deliberately regressed fixture (failing eval) correctly blocks deploy, satisfying v20.2 Section 9's Definition of Done.
- Confirm Pier's own sandboxing does not require or introduce any capability-broker bypass; if it does, isolate Pier's CI execution environment from any path that could reach production secrets or the kernel audit log.
