# ADR-049 — Stage 4.4 · Superpowers KB as MemoryPort adapter corpus (full-body, MIT)

**Status:** Ratified v25
**Lock-in phase:** Stage 4.4 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.4 in `Kosmos-Build-Sequence-v25.md` calls for landing the Superpowers
Personal-KB substrate ahead of Gnosis Phase 3. Two prior ADRs constrain how:

- **ADR-008** treats `obra/superpowers` as a **methodology reference** for
  the Tektos skill-library UX and explicitly says *do not vendor Superpowers
  code or Markdown files directly* into a plugin package.
- **ADR-002** and **ADR-016** locate the Personal-KB substrate inside the
  merged **Gnosis** plugin (Humanities cluster) at Phase 3, with
  ADR-016 line 22 saying: *"Personal-KB substrate (Superpowers, per
  ADR-008) lives inside Gnosis."*

Those two statements are not in conflict but need reconciling:
- ADR-008's "no direct vendoring" refers to the Tektos UX — a plugin cannot
  `import` or transclude Superpowers files as if they were its own skill code.
- The Personal-KB substrate is a different use of the same upstream repo:
  Superpowers's Markdown methodology becomes **temporal facts inside the
  MemoryPort**, not plugin code and not runtime imports.

Stage 4.4's Definition of Done ("Superpowers KB port landed under Gnosis
Personal-KB substrate; typed retrieval + provenance verified against
fixtures") requires deciding six things:

- **Q1 — Location at Stage 4.4:** Gnosis plugin does not exist yet
  (Phase 3). Where does the corpus live in the meantime?
- **Q2 — Refresh cadence:** how are new upstream skills picked up?
- **Q3 — Adapter now vs. plugin later:** relocation policy.
- **Q4 — Retrieval surface:** temporal only? Vector? Typed links?
- **Q5 — Ingest granularity:** one record per skill? Per file? Per section?
- **Q6 — Substrate scope:** what MIT content lands vs. stays out?

Every question flagged for explicit ADR choice by Kosmos custom instructions.
User delegated all six to "make the optimal choice" (see session transcript
2026-07-30). This ADR records the resulting decisions and the alternatives
that were rejected.

State on **2026-07-30**:
- Upstream `obra/superpowers` HEAD @ `44c9b2d6e889982ac18c27d05a19fefe335194e1`
  — 38 Markdown files under `skills/` across 14 skill directories, MIT.
- Stage 4.2 corpora infrastructure ships:
  `synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export` under
  `adapters/memory/dozerdb/corpora/`, exercised by
  `test_corpora_contract.py` in fast + env-gated live tiers.
- Stage 4.3 (ADR-048) bumped `agent-memory-guard==0.3.0` and made
  `Policy.tiered()` the default, unblocking pre-Phase-3 landings.
- DozerDB adapter baseline is 130 passed / 7 skipped.

## Decision

Land Superpowers as a **fourth Stage 4.2-shaped adapter corpus**,
`superpowers`, colocated with the three existing corpora under
`adapters/memory/dozerdb/corpora/superpowers/`, ingesting **full-body
Markdown per file** at a **pinned upstream commit SHA**, with a
workspace-local re-ingest CLI at `scripts/ingest_superpowers.py`.

The six locked answers:

**Q1 — Location:** Adapter corpus, colocated with `rigpa-export`.
Rejected: (a) creating a `plugins/gnosis/` package early — violates
plugin-scope discipline before Phase 3 lands; (b) a top-level
`kbs/superpowers/` module — bypasses the Stage 4.2 corpora contract
tests that already exercise ingest, provenance, and zero-trust
invariants for every entry in `ALL_CORPORA`.

**Q2 — Refresh cadence:** Pinned SHA + re-ingest CLI. No cron, no
network fetch at import, no auto-update. Regenerating the fixture is an
explicit human action: `scripts/ingest_superpowers.py --sha <SHA>`.
Rejected: (a) scheduled re-check against upstream `main` — pulls
uncontrolled content into MemoryPort and violates Kosmos's local-first
posture; (b) one-shot commit with no CLI — makes future updates a
manual copy-paste chore and loses provenance.

**Q3 — Adapter now, Gnosis later:** Corpus lives under
`adapters/memory/dozerdb/corpora/superpowers/` at Stage 4.4. When
Gnosis lands at Phase 3, the corpus module + fixture + ingest CLI
relocate to `plugins/gnosis/humanities/personal_kb/`. The public
loader shape (`load_corpus`, `CORPUS` singleton, env override
`KOSMOS_SUPERPOWERS_PATH`) is deliberately stable across the move.
Rejected: (a) build the plugin skeleton now — creates a phantom plugin
that only Gnosis will populate later, and forces `ALL_CORPORA` to
straddle two package trees; (b) never move it — leaves substrate
content in an adapter package, violating ADR-016.

**Q4 — Retrieval surface:** Temporal + typed-link. Every fact carries the
same pinned `as_of` (upstream commit-authored date) so time-slice
queries collapse to before/at cutoff. Inter-skill cross-references
(inline Markdown `[text](path)` links between sibling files) parse
into typed `CorpusEdge` records with `kind="references"`, materialized
at load time. **VectorPort surface is NOT opened.** Rejected:
(a) temporal-only — loses the topology Superpowers explicitly encodes
across its skill files; (b) temporal + vector — hauls in an embedding
stack before Phase 3 and creates a second retrieval path that Gnosis
would then have to reconcile.

**Q5 — Ingest granularity:** Per-file. One MemoryPort record per
`skills/*/*.md` at the pinned SHA. Rejected: (a) per-skill roll-up —
loses the internal structure Superpowers deliberately splits across
`SKILL.md` + companion `.md` siblings (e.g. `test-driven-development/
writing-good-tests.md` is a distinct authored artifact); (b) per-section
splitting — introduces a Markdown parser + section-ID heuristics that
would drift out of sync with upstream section changes.

**Q6 — Substrate scope:** Full-body Markdown. Each fact's `attributes`
carries `body`, `source_commit`, `license="MIT"`, `upstream_url`, and
the typed `references` list. MIT permits redistribution with license
notice; provenance is captured per record. Rejected: pointer-only
records (URL + hash, no body) — turns the substrate into a
network-fetch dependency and defeats local-first operation.

## Rationale

The six answers above compose into a single principle: **the Personal-KB
substrate is a data landing, not a code vendor**. Superpowers content
enters Kosmos as inert Markdown inside a fixture, mediated by the same
MemoryPort contract every other corpus honors — zero-trust provenance,
bounded confidence, timezone-aware `as_of`, ADR-007 (no plugin-to-plugin
imports; corpora live under `adapters/`, not `plugins/`).

Locating the corpus under the DozerDB adapter at Stage 4.4 keeps the
Stage 4.2 contract tests as the enforcement layer. `ALL_CORPORA` gains
one entry; the parametrized invariant tests and env-gated live tier
extend to it automatically. When Gnosis lands at Phase 3, the move is
a directory relocation, not a re-implementation.

Typed cross-reference edges are the retrieval feature Superpowers's own
authorship style requires: files link to sibling skills as first-class
citations. Materializing those into `CorpusEdge` (rather than leaving
them as raw Markdown link text buried in `attributes.body`) keeps
Gnosis's future graph-shaped queries against Personal-KB substrate
grounded in Superpowers's declared topology instead of an inferred one.

## Consequences

**New files (adapter package):**
- `adapters/memory/dozerdb/corpora/superpowers/__init__.py` — public
  re-exports (`CORPUS`, `SOURCE_COMMIT`, `UPSTREAM_LICENSE`,
  `UPSTREAM_URL`, `load_corpus`, `load_facts_and_edges`).
- `adapters/memory/dozerdb/corpora/superpowers/superpowers.py` —
  JSONL loader + env override + typed-edge materialization + temporal
  query helpers, mirroring `rigpa_export.py`.
- `adapters/memory/dozerdb/corpora/superpowers/fixtures/superpowers.jsonl`
  — 38 records at SHA `44c9b2d6e889982ac18c27d05a19fefe335194e1`, 9
  typed cross-reference edges, ~310 KB.

**Extended files:**
- `adapters/memory/dozerdb/corpora/models.py` — new `CorpusEdge`
  dataclass; `Corpus` gains an optional `edges: tuple[CorpusEdge, ...]`
  field (defaults to `()`, backward-compatible with Stage 4.2 corpora)
  with construction-time invariants enforcing src/dst resolvability.
- `adapters/memory/dozerdb/corpora/__init__.py` — exports
  `SUPERPOWERS_CORPUS`, `CorpusEdge`, `load_superpowers_corpus`, and
  adds `SUPERPOWERS_CORPUS` to `ALL_CORPORA`.
- `adapters/memory/dozerdb/corpora/test_corpora_contract.py` — 7 new
  fast tests (cardinality, provenance triple, typed edges, env override
  path, missing-attribute rejection, fixture commit); ADR-007 AST scan
  now recurses (`rglob("*.py")`) so the new subpackage is covered.

**Workspace tooling (not committed to plugin space):**
- `scripts/ingest_superpowers.py` — CLI to regenerate the fixture from
  any pinned SHA, via `gh api` (default) or a local checkout. Not
  invoked at runtime by any adapter or plugin; not a package.

**Test-suite outcome:** DozerDB adapter suite moves from 130 passed / 7
skipped to **142 passed / 8 skipped**; the +1 skip is the new
Stage 4.4 corpus wiring into the env-gated
`test_live_tier_ingests_corpus_end_to_end` parametrization.

**ADR-008 relationship:** ADR-008 unchanged. Its "do not vendor" rule
still governs the Tektos skill-library UX; ADR-049 governs the
Personal-KB substrate use of the same upstream repo. §17 of the spec
carries both rows for clarity.

**Downstream ADRs to update:** none. ADR-002 and ADR-016 already
specify the Gnosis endpoint; ADR-049 confirms the Stage 4.4 landing
site and the deferred relocation.

**PORTING_LEDGER:** new entry under **Content corpora** classifying
`obra/superpowers` as a **content ingest**, not a vendored code
dependency. SHA + license + fixture path recorded.

**Gnosis Phase 3 move-plan:** relocation is a rename of
`adapters/memory/dozerdb/corpora/superpowers/` →
`plugins/gnosis/humanities/personal_kb/`, plus an import-path bump in
`adapters/memory/dozerdb/corpora/__init__.py` (which removes
`SUPERPOWERS_CORPUS` from `ALL_CORPORA` and lets Gnosis register it
via the plugin bus). The fixture format and env override name stay
identical.

## Lock-in phase

Stage 4.4 (Kosmos-Build-Sequence-v25 §4.4) locks this in. Any later
change to any of Q1–Q6 requires an amending ADR.

## References

- `Kosmos-Build-Sequence-v25.md` §4.4 (Superpowers KB port under Gnosis)
- `Kosmos-Build-Spec-v25.md` §17 (ADR summary table)
- `docs/adrs/ADR-002-gnosis-humanities-scope.md`
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-008-superpowers-kb-reference.md`
- `docs/adrs/ADR-016-knowsys-gnosis-merge.md`
- `docs/adrs/ADR-047-stage-4-2-corpora-hybrid-tier.md`
- `docs/adrs/ADR-048-stage-4-3-amg-v03-adoption.md`
- `PORTING_LEDGER.md` (Content corpora section)
- Upstream: `github.com/obra/superpowers` @
  `44c9b2d6e889982ac18c27d05a19fefe335194e1` (MIT)
