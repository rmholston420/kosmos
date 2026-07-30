# Kosmos Session Handoff — 2026-07-30 05:14 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 3.12 · Stage-3 exit gate (next up)
- **Plugin / kernel component:** Tektos (end-to-end refactor DoD)
- **Port(s) in progress:** none (Stage 3.12 has no new port — it's an integration DoD proving Tektos can refactor a real Kosmos file end-to-end through the Stage 3.1–3.11 pipeline)

## Completed this session (Stage 3.11 · Tektos UI HTMX dashboard · ADR-045)
- ADR-045 authored fresh at `Ratified v25 · Stage 3.11` (Q1=C · Q1a=A · Q1b=B · Q1c=A · Q1d=A · Q1e=A · Q1f=A · Q1g=A · Q2=A · Q3=A · Q4=A · Q5=A · Q6=A · Q7=B · Q8=C · Q9=A · Q10=A · Q_res_1=B · Q_res_2=B · Promotion=A)
- ADR-041 STATUS AMENDMENT: ui_parity_status IN_PROGRESS → COMPLIANT with ADR-045 pointer
- New port `ports/approval.py` promoted from intra-Praxis `ChangeApprovalProtocol`: `ChangeApprovalTier` + `ApprovalStatus` + `ApprovalRecord` (field `approval_id`) + `ApprovalGatewayPort` + `ApprovalResolverPort` (three verbs including `list_pending(*, proposing_domain=None)` port-level filter). `plugins/praxis/apex/models.py` re-exports for backward compat.
- New adapter `adapters/approval_resolver/praxis/adapter.py` — `PraxisApprovalResolverAdapter` wraps `KernelChangeApprovalAdapter`; 5 contract tests pass
- Tektos UI subsystem shipped at `plugins/tektos/ui/{__init__,policy,models,executor,templates,server}.py` + vendored `htmx.min.js` (50917 B, sha256 `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`, upstream `bigskysoftware/htmx@b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f`, license `0BSD`)
- `plugins/tektos/plugin.py` gains one `Route(path="/tektos", label="Tektos", icon="📐", lazy_module="tektos/pages/DashboardPage")` in `build_tektos_descriptor()` — flips parity to COMPLIANT
- `scripts/tektos_ui.py` (uvicorn runner) + `Makefile` `ui-serve` target
- `pyproject.toml` gains `[project.optional-dependencies] ui = ["fastapi>=0.115", "uvicorn>=0.32", "httpx>=0.27"]` + `plugins.tektos.ui` + `adapters.approval_resolver` + `adapters.approval_resolver.praxis` to setuptools packages + `[tool.setuptools.package-data] "plugins.tektos.ui" = ["htmx.min.js"]`
- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-045 row), `docs/adrs/README.md` (ADR-045 row), `docs/PORTING_LEDGER.md` (htmx + fastapi + uvicorn VENDORED rows), `docs/Kosmos-Build-Sequence-v25.md` (§3.11 LANDED block)
- 815 total green + 8 env-gated skips (was 791 + 7 at Stage 3.10 close). `make stage1-gate` PASS.
- DoD literal anchor `test_plan_approve_execute_diff_flow_visible_in_kernel_dashboard_build_sequence_3_11_dod` PASS

## Remaining before current Definition of Done (Stage 3.12)
- Choose one non-trivial refactor on a real Kosmos file that the Stage 3.1–3.11 Tektos pipeline can execute end-to-end
- Drive Tektos: agent (3.1) → MCP tool call (3.2) → repomap (3.3) → OpenSpec plan (3.6) → plan renderer + APEX HUMAN_REVIEW gate (3.7) → Pier eval verdict (3.8) → docling ingest if applicable (3.10) → UI Approve/Execute/Diff (3.11)
- DoD: refactor commit passes `ruff` + `bandit` + `pytest`
- Fan-out: BUILD_LOG entry, SESSION_HANDOFF overwrite → Stage 4.1, PORTING_LEDGER updates only if new components are vendored

## Open questions / awaiting user answer
- **User must run Q-lock for Stage 3.12** — which real Kosmos file to refactor, whether the refactor is scoped to a single spec or spans multiple, whether to run through the real Pier tier (`KOSMOS_STAGE_38_REAL_PIER=1`) or the fake shim, and whether to launch the interactive UI tier (`KOSMOS_STAGE_311_INTERACTIVE=1`) for approval or use TestClient-only

## Exact next action
- Start Stage 3.12 by presenting Q-lock questions (mirror the Stage 3.11 lock-question format). Read `docs/Kosmos-Build-Spec-v25.md` §3.12 + `docs/Kosmos-Build-Sequence-v25.md` §3.12 verbatim first, then draft ambiguity list from real-Kosmos-file selection, refactor scope, Pier tier choice, and UI tier choice.
