# ADR-077 — Stage 3.13 / 3.14 / 3.15: Tektos intention scaffolder, sandboxed executor, and diff surface

**Status:** Ratified v25
**Lock-in phase:** Stage 3 · Post-3.12 continuation
**Supersedes:** —

## Context

Stage 3.12 exited with ADR-046: `TektosAgent` calls `propose_plan()` +
`propose_execution()` behind APEX gates, `render_and_gate_plan_card`
projects a `Plan` into a `PlanCard`, and `Phrouros-post-execute` closes
the loop. Two facts pushed the discipline forward but not yet to a
usable single-user local loop:

1. **`v25` `Kosmos-Build-Spec` has no §3.13 / §3.14 / §3.15.** Phase 3
   exits at §3.12. There is no spec-blessed continuation slot for
   post-3.12 Tektos work. The `Kosmos-Build-Sequence-v25.md` cross-cutting
   duties still apply, but no DoD text exists to gate a shipment.

2. **`v25` deferred `SandboxProvider` / `WorktreeProvider`** to Phase 4
   via ADR-039. The sandbox substrate the user needs before Tektos can
   plan-then-execute against a real diff does not exist today. The
   post-3.12 Tektos surface therefore fans into three separable slices,
   each with its own DoD and stop condition:

   - **3.13** — intention → scaffolded OpenSpec change dir → plan →
     gated `PlanCard`. **Nothing executes.** Zero contact with the
     working tree. Deterministic, no LLM.
   - **3.14** — `git worktree` sandbox provider + LLM-driven task
     execution against the sandbox + `git apply` two-identity
     auto-commit + real diff render behind the `HUMAN_REVIEW` gate.
   - **3.15** — end-to-end wiring (approve on `/tektos/detail` →
     apply diff to the working tree; reject → discard worktree;
     Phrouros-post-execute lands the closing anomaly-check event
     the same way §3.12 does).

The user has explicitly locked "optimal on all" for the Q1–Q6
architecture questions raised in-session: numbered stages 3.13/3.14/3.15
(**Q1(b)**), `git worktree` sandbox for 3.14 (**Q2(a)**), deterministic
scaffolder for 3.13 (**Q3(a)**), `git apply` two-identity auto-commit
for 3.14 (**Q4(b)**), Stage 3.13 landed **this session** as intention
endpoint + scaffolder + `produce_plan` + `render_and_gate_plan_card`
(**Q5(b)**), SESSION_HANDOFF overwritten fresh at session end (**Q6**).

## Decision

### D1. Stage numbering

Adopt `3.13`, `3.14`, and `3.15` as continuation slots inside Phase 3
of `Kosmos-Build-Spec-v25.md`. Each stage keeps the same one-person-module
scope discipline as `3.1`–`3.12`. When `v26` of the spec lands, these
numbers stay; ADR-077 is the authority until then.

### D2. Stage 3.13 DoD — intention scaffolder

- New Python module `plugins/tektos/intention/` with:
  - `policy.py` — locked constants:
    - `INTENTION_ROOT_ENV = "KOSMOS_TEKTOS_INTENTION_ROOT"`
    - `INTENTION_PROVENANCE = "tektos_intention_scaffolder"`
    - `INTENTION_SCAFFOLD_PREDICATE = "tektos.intention.scaffolded"`
    - `INTENTION_WRITE_CONFIDENCE = 1.0`
    - `MIN_INTENTION_LENGTH = 8`, `MAX_INTENTION_LENGTH = 512`
  - `scaffolder.py` — `scaffold_intention(intention, *, root=None, now=None)`
    writes a **new** OpenSpec change directory containing `proposal.md`
    and `tasks.md`. Refuses to overwrite. Never writes inside the Kosmos
    working tree — root defaults to `$XDG_STATE_HOME/kosmos/tektos/intentions`
    (with `~/.local/state` fallback). `intention_to_change_id()` slugifies
    via NFKD → lowercase ASCII → collapsed hyphens, rejecting empty
    slugs (whitespace-only, all-hyphen, unicode-only after NFKD).
- New kernel endpoint `POST /api/tektos/intention` that:
  1. requires `KernelRegistry.memory` + `.approval` (503 if missing);
  2. calls `scaffold_intention(body.intention)`;
  3. calls `produce_plan(scaffold.change_dir, memory)` (Stage 3.6);
  4. calls `render_and_gate_plan_card(plan, panel_id=TEKTOS_PLAN_APPROVAL_PANEL_ID,
     approval=approval, memory=memory)` (Stage 3.7, `HUMAN_REVIEW` tier,
     provenance `tektos_plan_renderer`);
  5. returns `{change_id, change_dir, intention, scaffolded_at, plan_card}`.
- New Next.js `<IntentionForm/>` client component mounted on `/tektos`.
  Length-gated submit, character counter, error surface reads FastAPI
  `detail`, on success links to `/tektos/detail?id=<approval_id>`.
- Approvals continue through the existing
  `/api/approvals/{id}/{approve,reject}` routes — no new approval surface.
- Zero-trust: every `MemoryPort` write goes through `render_and_gate_plan_card`
  (its own `record_intention` provenance path). The scaffolder itself
  writes only to disk, never to memory.
- ADR-007: `plugins/tektos/intention/` imports **no** other plugin
  package. Contract test asserts this via AST.
- **Stop condition:** user pulls `stage-3-13-tektos-intention`, opens
  `/tektos`, types an intention, sees a gated `PlanCard` on
  `/tektos/detail?id=<approval_id>`. **No code execution.**

### D2a. Stage 3.13.1 DoD — plan detail read surface (follow-up)

Minimal read surface for a scaffolded plan, landed on the same branch
after D2. **No new execution surface.**

- New kernel endpoint `GET /api/tektos/plan/{approval_id}` returning
  `{approval, change_id, change_dir, files: {proposal_md, tasks_md}}`.
  - 503 if approval resolver unavailable.
  - 404 if APEX has no such approval, or the record's `proposing_domain`
    is not `"tektos"`.
  - `files` entries are `null` when the file is missing / unreadable /
    over 128 KiB — endpoint never raises on filesystem edge cases.
  - Path-traversal guard: resolved `change_dir` must live under
    `resolve_intention_root()`.
- Updated `/tektos/detail?id=<approval_id>` page renders the record,
  the `PlanCard`-shaped `delta`, `proposal.md`, and `tasks.md`.
  Approve / Reject route through the existing
  `/api/approvals/{id}/{approve,reject}` surface (`kernelClient.resolveApproval`).
  Execute + Show Diff buttons remain visible but disabled, labeled
  “Stage 3.14”.

### D2b. Deployment — systemd drop-in (kosmos-kernel)

The scaffolder's default resolution is
`$XDG_STATE_HOME/kosmos/tektos/intentions` (or
`~/.local/state/kosmos/tektos/intentions`). The Colossus
`kosmos-kernel` unit runs with `ProtectHome=read-only`, which makes
both defaults unwritable at runtime. The repo ships a drop-in at

    deploy/systemd/kosmos-kernel.service.d/10-tektos-intention-root.conf

that overrides `KOSMOS_TEKTOS_INTENTION_ROOT` to
`/var/lib/kosmos/tektos/intentions` and asks systemd to auto-create
that directory via `StateDirectory=kosmos/tektos/intentions` +
`StateDirectoryMode=0750`. `StateDirectory` is added to
`ReadWritePaths` automatically under `ProtectSystem=strict`.

Deploy on Colossus:

    sudo mkdir -p /etc/systemd/system/kosmos-kernel.service.d
    sudo cp deploy/systemd/kosmos-kernel.service.d/10-tektos-intention-root.conf \
      /etc/systemd/system/kosmos-kernel.service.d/
    sudo systemctl daemon-reload && sudo systemctl restart kosmos-kernel

### D3. Stage 3.14 DoD — sandbox executor (deferred, do not build)

- New port `SandboxProvider` (kernel/ports) with `git worktree`-backed
  adapter under `adapters/sandbox/gitworktree/`. Worktrees created under
  `$XDG_STATE_HOME/kosmos/tektos/sandboxes/<change_id>/`, base ref
  `HEAD`, branch name `tektos/<change_id>`. Cleaned up on approval
  resolution.
- New `tektos_agent` execution loop that, for each task in the
  approved plan, runs one LLM turn (Ollama on Colossus) against the
  sandbox worktree. Two-identity commit pattern: LLM-authored commits
  land as `Tektos <tektos@kosmos.local>`, user-authored resolutions
  (approve/reject) land as `rmholston420 <lawapa.naljor@gmail.com>`.
- New endpoints:
  - `POST /api/tektos/plan/{approval_id}/execute` — runs the loop.
  - `GET  /api/tektos/plan/{approval_id}/diff` — returns unified diff
    from the sandbox worktree.
- `getPlanDetail`, `approveTektosPlan`, `executeTektosPlan`,
  `getTektosDiff` in `ui/lib/kernel-client.ts` stop 404-ing at this
  stage.
- Colossus resource envelope (128 GB RAM / 32 GB VRAM) enforced by
  refusing to launch execution if free VRAM < model requirement.

### D4. Stage 3.15 DoD — end-to-end wiring (deferred, do not build)

- On approve: kernel calls the sandbox provider to `git apply` the
  worktree diff onto the working tree with the user identity, tags
  `tektos-<change_id>-approved-<ts>`, emits `tektos.plan.applied`
  through the event bus, runs Phrouros-post-execute the same way
  Stage 3.12 does.
- On reject: kernel discards the sandbox worktree, emits
  `tektos.plan.rejected`, no working-tree contact.

### D5. Anti-goals (all three stages)

- **No cloud fallback.** Ollama-only. No OpenAI / Anthropic / any
  network LLM. Colossus-local.
- **No PORTING_LEDGER additions in Stage 3.13.** Nothing is vendored.
  Stage 3.14 will vendor nothing either — `git` is a system binary,
  not a Python package.
- **No new memory-subsystem surface.** All memory writes route through
  existing `render_and_gate_plan_card` machinery.
- **No cross-plugin imports.** Even inside the same phase.
- **No multi-user assumptions.** Single-user, single Colossus.

## Consequences

- Stage 3.13 unblocks the visible "type an intention → see a gated
  plan" loop without touching the working tree. This is safe to iterate
  on before the sandbox substrate exists.
- Stages 3.14 and 3.15 remain sequenced: sandbox first, wiring second.
  Attempting the wiring without the sandbox would either leak execution
  onto the working tree or require a temporary sandbox that would then
  be thrown away.
- The four Tektos plan-surface routes in `ui/lib/kernel-client.ts`
  (`getPlanDetail`, `approveTektosPlan`, `executeTektosPlan`,
  `getTektosDiff`) keep their 404 status until Stage 3.14. The comment
  block above them is updated to name ADR-077 and the exact stage that
  lifts each 404.
- Existing `/api/approvals/*` machinery is reused as-is. Stage 3.13
  therefore adds zero new approval endpoints.

## Related work

- ADR-039 — SandboxProvider / WorktreeProvider deferral.
- ADR-046 — Stage 3.12 exit gate.
- ADR-063 — Tektos turn endpoint.
- ADR-067 — Kernel route surface (Tektos plan routes deferred to a
  dedicated ADR — this one).
- ADR-076 — Stage 1.6 Phase 3 memory surfaces (unrelated but current).

## References

- `plugins/tektos/intention/` (this ADR, D2)
- `kernel/app.py::tektos_intention` (this ADR, D2)
- `ui/components/IntentionForm.tsx` (this ADR, D2)
- `ui/tests/28-tektos-intention.spec.ts` (this ADR, D2)
- `plugins/tektos/tests/test_intention_scaffolder.py` (this ADR, D2)
