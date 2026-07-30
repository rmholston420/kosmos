# ADR-052 — Stage 6.1 · Zetesis plugin skeleton + Stage-5 deferral

**Status:** Ratified v25
**Lock-in phase:** Stage 6.1 (Phase 6 — Research + ADR-010 Resolution)
**Supersedes:** —
**Amends:** ADR-015 (Oikos-Ahead-of-Zetesis Build Sequencing)

## Context

Stage 6.1 in `Kosmos-Build-Sequence-v25.md` is the first Phase-6
milestone. Its Definition of Done reads:

> Plugin loads.

Two upstream constraints converged at the moment 4.6 landed
(2026-07-30):

- **User elected to defer Stage 5** (Oikos, APEX-in-plugin, and
  associated Phase-5 subsystems) until later, jumping directly from
  Stage 4.6 (Gnosis-retrieval exit gate) into Stage 6.1 (Zetesis
  skeleton). This departs from ADR-015 ("Oikos-Ahead-of-Zetesis
  Build Sequencing," Ratified v24) and requires an amendment.
- **Build-Sequence §6.1's stated port list (LLMPort, MemoryPort,
  VectorPort, DataPort) omits SearchPort** — the 11th formal port
  (ADR-021 Ratified v25, Stage 1.1 landed). SearchPort is Zetesis's
  primary means of gathering fresh web evidence; its absence from
  §6.1 is a stale-sequence omission, not a deliberate exclusion.
  Similarly, `zetesis-stub` is called out at spec §191 +
  Build-Sequence §1.6 as **the** driver of Tektos Phase-10 model-swap-
  under-load priority-queue arbitration — meaning ResourcePort is
  implicitly required, not optional, at Stage 6.1 landing.

At Stage 4.6 landing (commit `5ce3917`, tag `stage-4-6-complete`):

- No `plugins/zetesis/` exists — clean greenfield.
- All 11 formal ports (SearchPort/LLMPort/EventBusPort/SecretsPort/
  ObservabilityPort/VectorPort/MemoryPort/DataPort/ResourcePort/
  NotificationPort/FrontendContractPort) have working adapters and
  landed Protocols under `ports/*.py`.
- Existing plugins (Praxis at Stage 2.1, Phrouros at Stage 2.3,
  Tektos at Stage 3.1+) establish the dataclass-plugin-with-async-
  start-stop pattern.
- ADR-010 (AREX vs LangChain Open Deep Research head-to-head) is
  **OPEN — head-to-head eval pre-Phase-6.2**. Any Zetesis code at
  6.1 that pre-commits to an inner-loop vendor would pre-empt that
  decision.

Six lock-in questions surfaced during scope-restatement; the user
locked answers as Q1=A · Q2=A · Q3=A · Q4=confirmed · Q5=C · Q6=A,
then extended with Q7=B-plus after the SearchPort omission was
flagged. This ADR captures all seven locks.

## Decision

### Q1 — Sequencing amendment shape

**A** — Amend ADR-015 with a status-amendment block preserving the
original Oikos-before-Zetesis rationale, then author this ADR-052
locking the concrete Stage 6.1 skeleton. Do not supersede ADR-015;
Stage 5 is deferred, not cancelled.

Rejected: authoring a new ADR to reverse ADR-015 (over-heavy for a
user-elected sequencing shift; violates the amend-not-overwrite
discipline in `kosmos-adr-authoring`).

### Q2 — Panel / route surface at Stage 6.1

**A** — `build_zetesis_descriptor()` returns a `PluginDescriptor`
with **zero panels, zero routes, empty design tokens**. The kernel
discovers Zetesis via `FrontendContractPort.register_plugin` but
nothing renders yet. Panels + routes land at Stage 6.3/6.4 when real
research output exists to display.

Rejected: adding a `PanelSlot.RESEARCH_FEED` slot at 6.1 (requires
`ports/frontend_contract.py` amendment + a separate ADR — scope
creep against DoD literal "Plugin loads"). Rejected: reusing an
existing slot (no natural fit; would misrepresent Zetesis as
approvals/governance/trace producer).

### Q3 — ADR-010 posture at Stage 6.1

**A** — The skeleton is **inner-loop-agnostic**. `LLMPort`,
`SearchPort`, `MemoryPort`, `VectorPort`, `DataPort`, `EventBusPort`,
`ResourcePort`, `NotificationPort`, `ObservabilityPort`, and
`SecretsPort` are held as constructor dependencies but **called
zero times** at 6.1. No research-pipeline scaffolding, no query
decomposition seam, no `ResearchInnerLoop` Protocol. The
AREX-vs-Open-Deep-Research head-to-head runs pre-Phase-6.2 per
ADR-010 § "Lock-in phase"; 6.1 must not pre-empt it.

Rejected: scaffolding an abstract `ResearchInnerLoop` Protocol seam
(risks pre-empting ADR-010's decision surface even if the seam is
"minimal"). Enforcement: `test_start_touches_no_business_port`
constructs the plugin with `_UntouchablePort` sentinels that raise
`AssertionError` on any attribute access; `start()` completing
without raising proves zero business-port calls at Stage 6.1.

### Q4 — MemoryPort write contract constants

**Confirmed** — locked at 6.1 so downstream Stage-6 tests + Phrouros
grounding checks can pin exact strings, even though the first write
lands at Stage 6.3:

- `ZETESIS_MEMORY_PROVENANCE = "zetesis_research"`
- `ZETESIS_MEMORY_PREDICATE = "zetesis.research.completed"`
- `ZETESIS_MEMORY_DEFAULT_CONFIDENCE = 0.75`

The default confidence mirrors Tektos ADR-036's pre-Reflexion
default; Zetesis's Phase-6.3 inner loop will replace it with a
task-tuned score once ADR-010 resolves. `0.75 ∈ (0, 1]` — passes
`ports.memory.validate_zero_trust_write` (ADR-008).

### Q5 — Zetesis stub fate

**C** — The real `ZetesisPlugin` **is** the `zetesis-stub` that
spec §191 + Build-Sequence §1.6 require for Tektos Phase-10
model-swap-under-load. There is no separate stub package. Spec §191
explicitly says: *"When the real plugins are built (Phase 6), they
must pass the identical fixture-stub contract test before
promotion."* — this ADR interprets that as "the real plugin at
Stage 6.1 is what Tektos's Phase-10 rig binds to; no interim stub
exists."

Rejected: **A** (go back and build a separate `plugins/zetesis_stub/`
package — creates code the spec says will be deleted at Phase 6).
Rejected: **B** (KNOWN_ISSUES.md deferral — leaves the spec-literal
obligation unresolved for an entire phase).

Practical consequence: `ResourcePort` becomes a required (non-None)
port slot at 6.1 landing because the fixture-stub contract requires
the stub to *request a background model load on a fixed schedule to
exercise priority-queue arbitration.* At Stage 6.1 the request is
not fired yet, but the port must be wired.

### Q6 — ADR shape

**A** — Single composite ADR-052 covers Q1–Q7. The questions are
load-bearing on each other (Q5=C forces ResourcePort into Q7=B-plus;
Q3=A forbids business-port calls that Q7's expanded port list would
otherwise invite). Splitting into per-question ADRs would fragment
the lock-in trail.

### Q7 — Port surface at Stage 6.1

**B-plus** — 10 required (non-None) + 1 optional slot.

**Required:**

1. `FrontendContractPort` — descriptor registration.
2. `LLMPort` — inner-loop query decomposition / summarization /
   citation grounding (first call at Stage 6.3).
3. `MemoryPort` — `zetesis.research.completed` writes + prior-research
   retrieval (first call at Stage 6.3).
4. `VectorPort` — semantic retrieval over prior research + external
   corpora (first call at Stage 6.3).
5. `DataPort` — JSON-LD import/export for research questions +
   reports (first call at Stage 6.3).
6. `SearchPort` — web-search substrate (**Q7 correction to §6.1
   omission**; primary means of gathering fresh evidence).
7. `EventBusPort` — publishes `zetesis.research.completed` for
   Synedrion strategic-signal consumption (**Q7 addition**; spec
   §35 System-4 requires it).
8. `ResourcePort` — priority-queue arbitration per spec §172
   (**Q7 addition**; required by Q5=C stub-role obligation via
   spec §191).
9. `NotificationPort` — algedonic path for grounding-failure /
   source-diversity-gate violations (**Q7 addition**; spec §46
   two-layer anti-hallucination). Required so no research path
   silently swallows a signal.
10. `ObservabilityPort` — trace + metrics for every inner-loop call
    (**Q7 addition**). Required so no Phase-6.3+ inference escapes
    observation.

**Optional:**

11. `SecretsPort` — external-service credentials (academic APIs,
    alternate SearchPort backends). Defaults to `None` at 6.1;
    wired when Zetesis first consumes a non-local SearXNG backend
    or paywalled data source.

Rejected: **B** (as above but with `ResourcePort` + `EventBusPort`
optional — weakens the Q5=C stub-role commitment and invites
plugins that silently swallow events, breaking ADR-007's events-only
cross-plugin coupling model). Rejected: keeping the original §6.1
four-port list verbatim (leaves the SearchPort omission unresolved
and forces a Q7 amendment at Stage 6.3, when the port surface is
harder to change without touching real inner-loop code).

## Rationale

- **Minimal DoD honored literally.** §6.1 says "Plugin loads." The
  skeleton loads, registers with FrontendContractPort, and does
  nothing else. Every choice above defends that literal.
- **ADR-010 pristine.** Zero business-port calls at 6.1 means the
  head-to-head eval remains a clean apples-to-apples comparison at
  Phase 6.2. No sunk-cost bias toward whichever inner loop the 6.1
  skeleton would have "started to sketch."
- **Stub-role obligation discharged.** Q5=C + Q7=B-plus together
  mean the Phase-1 debt for `zetesis-stub` closes at 6.1 landing:
  the real plugin holds ResourcePort and can drive the Tektos
  Phase-10 rig without any interim shim.
- **Spec/sequence gap closed.** Q7 upgrading §6.1's port list from
  4 → 10 required + 1 optional resolves the pre-existing omission
  of SearchPort + the implicit ResourcePort requirement from
  §172/§191. Build-Sequence §6.1 is updated in the same fanout.
- **Zero-trust preserved.** Every write constant sits in `(0, 1]`
  and every provenance/predicate string is fixed at 6.1, so
  Phrouros grounding checks (Phase 4 scope) and downstream Stage-6
  tests can pin exact values before any actual write lands.
- **Amend-not-overwrite discipline.** ADR-015 stays; a status-
  amendment block records the deferral rationale ("user elected to
  jump to Stage 6.1 after Stage 4.6 landed"). Stage 5 remains valid
  future work; ADR-015 will drive its build order when the user
  returns.

## Consequences

- **New files:**
  - `plugins/zetesis/__init__.py` — public re-exports.
  - `plugins/zetesis/plugin.py` — `ZetesisPlugin` dataclass +
    `build_zetesis_descriptor()` + locked constants.
  - `plugins/zetesis/tests/__init__.py`.
  - `plugins/zetesis/tests/test_zetesis_plugin.py` — 29 fast
    contract tests, including the ADR-007 AST guard scanning
    `plugins/zetesis/**/*.py` for `plugins.praxis` /
    `plugins.phrouros` / `plugins.tektos` imports.

- **ADR-015 amended** with a status-amendment block dated
  2026-07-30 noting the Stage-5 deferral. Original decision text
  preserved; status line updated to
  `Ratified (v24) · Amended 2026-07-30 (Stage-5 deferred by user)`.

- **`Kosmos-Build-Spec-v25.md` §17** — ADR-052 row appended after
  ADR-051, before §17.1.

- **`Kosmos-Build-Sequence-v25.md` §6.1** rewritten as a LANDED
  block: DoD stays "Plugin loads"; port list expanded from 4 to
  10 required + 1 optional per Q7=B-plus, with ADR-052 cited.
  Tag `stage-6-1-complete` recorded.

- **`docs/adrs/README.md`** — ADR-052 index row inserted before
  the OPEN section.

- **`PORTING_LEDGER.md`** — no change. No new upstream component
  vendored (the plugin skeleton is purpose-written; no OSS port).

- **Test surface:** `plugins/zetesis/tests/test_zetesis_plugin.py`
  = 29 fast tests. Whole-repo fast tier moves from 957 / 19 at
  Stage 4.6 to **986 / 19** at Stage 6.1 landing (delta +29,
  matches new file exactly).

- **ADR-007 respected.** AST scan of `plugins/zetesis/**/*.py`
  finds zero imports of `plugins.praxis`, `plugins.phrouros`, or
  `plugins.tektos`. Zetesis reaches every other plugin only via
  the event bus (once EventBusPort is exercised at Stage 6.3+).

- **ADR-008 preserved.** Every Zetesis write path (Stage 6.3+)
  will carry `ZETESIS_MEMORY_PROVENANCE` +
  `ZETESIS_MEMORY_DEFAULT_CONFIDENCE ∈ (0, 1]` — zero-trust
  invariants pinned at 6.1 before any write lands.

- **ADR-010 preserved.** Zetesis at 6.1 makes zero `LLMPort`
  calls. The Phase-6.2 head-to-head eval remains fully open.

- **ADR-015 amended but not superseded.** Stage-5 (Oikos + APEX-
  in-plugin + Nomisma-adjacent Phase-5 work) is deferred, not
  cancelled. When the user returns to Stage 5, ADR-015's
  sequencing rationale re-activates as guidance for the order of
  Phase-5 substages.

- **ADR-021 preserved.** SearchPort promotion to a required
  Zetesis constructor slot at 6.1 (Q7=B-plus) reinforces
  ADR-021's "web search is first-class" claim.

- **ADR-029 preserved.** ResourcePort's fixed priority order
  (`Phrouros anomaly > Tektos active > Synedrion/Zetesis
  background`) is Zetesis's arbitration substrate; Q7=B-plus
  wires the port slot so Stage 6.3's first LLM inference call
  will pass through the priority queue by construction.

- **DoD anchor.** `pytest plugins/zetesis/` — 29 fast tests
  green. Whole-repo fast tier: `pytest` — 986 / 19 (+29 vs.
  Stage 4.6 close).

- **Tag `stage-6-1-complete`** to be applied on the fanout
  commit.

- **Stop-condition status:** met — plugin loads, descriptor
  registers, all 10 required port slots are held, all locked
  constants pin exactly, ADR-007 AST guard clean, no business
  port called at 6.1.

## Lock-in phase

Stage 6.1 · Phase 6 (Research + ADR-010 Resolution) · Weeks 9–10.

## References

- `Kosmos-Build-Spec-v25.md` §4.1 (port surface), §17 (ADR
  summary), §35/§38 (System-4/System-1 role), §46 (anti-
  hallucination), §95 (SearchPort surface), §172 (priority queue),
  §191 (fixture-stub contract), §555 (Phase-1 fixture-stub build).
- `Kosmos-Build-Sequence-v25.md` §1.6 (`zetesis-stub` Phase-1
  build), §6.1 (Zetesis skeleton, now rewritten as LANDED).
- `docs/adrs/ADR-015-oikos-before-zetesis.md` — amended in the
  same commit with the 2026-07-30 status-amendment block.
- `docs/adrs/ADR-010-arex-vs-langchain-open-deep-research.md` —
  preserved OPEN; Zetesis at 6.1 makes no inner-loop commitment.
- `docs/adrs/ADR-021-searchport-as-11th-port.md` — cited by Q7.
- `docs/adrs/ADR-029-resourceport-full-surface.md` — cited by Q7
  + Q5=C stub-role obligation.
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` — source
  of the `0.75` pre-Reflexion default confidence mirrored by Q4.
- `docs/adrs/ADR-051-stage-4-6-exit-gate-gnosis-surrogate.md` —
  immediate predecessor; same six-question shape extended to
  seven here.
