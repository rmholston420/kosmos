# ADR-038 — Aider Repomap Pattern-Vendor for Tektos

**Status:** Ratified v25
**Lock-in phase:** Stage 3.3
**Supersedes:** —

## Context

Stage 3.3 needs a repository map that Tektos can use to give the coding
agent stable, PageRank-weighted context about a large codebase (10k+
files) without blowing the model's context window. Aider ships a
production-hardened repomap (`aider/repomap.py`, Apache-2.0) that
already solves:

- multi-language def/ref tag extraction via tree-sitter + `.scm` queries
- PageRank over the def→ref graph with identifier heuristics
- tree-context rendering with a token budget (binary-searched)

The upstream module is tightly coupled to aider's IO/prompt scaffolding,
Django-style singletons, and shell-facing CLI. Directly vendoring
`repomap.py` would drag in aider internals that violate ADR-007
(events-only cross-plugin coupling) and would be brittle against future
upstream refactors.

Six locked decisions had to be made before implementation:

- **Q1** — vendor the *pattern* or the *file*?
- **Q2** — expose repomap through a new `RepoMapPort` or keep it
  Tektos-internal?
- **Q3** — MemoryPort write shape (per-file, per-run, both)?
- **Q4** — freshness → confidence formula?
- **Q5** — DoD test strategy?
- **Q6** — single composite ADR or one ADR per module?

## Decision

- **Q1 = A · PATTERN-VENDORED.** Reimplement the upstream algorithm
  in-tree at `plugins/tektos/repomap/` (policy · tags · rank · render ·
  indexer). Only the six upstream `.scm` tree-sitter query files (one per
  language) are vendored verbatim under
  `plugins/tektos/repomap/queries/` with attribution.
- **Q2 = A (revised) · Tektos-internal.** No new port. Repomap lives at
  `plugins/tektos/repomap/` and is called by Tektos coding-agent flows
  directly. Deferring `RepoMapPort` until a second plugin needs repomap;
  premature port surfaces have historically thrashed (see ADR-023).
- **Q3 = C · Both per-file and per-run.** Every indexed file emits one
  `tektos.repomap.indexed` MemoryPort write (subject=`<repo-relative
  path>`, confidence=freshness score). Every `index()` call emits
  exactly one `tektos.repomap.snapshot` write with mean confidence,
  total files, rendered map, and cache version.
- **Q4 = B · Linear decay.**
  `confidence = max(REPOMAP_MIN_CONFIDENCE, 1.0 - min(1.0,
  age_days / 30.0))` with `REPOMAP_MIN_CONFIDENCE = 0.01` (ADR-008
  requires confidence > 0). Locked in
  `plugins/tektos/repomap/policy.py::compute_freshness_confidence`.
- **Q5 = C · Fast synthetic + env-gated large + env-gated real.** The
  stage1-gate always runs a 500-file synthetic corpus that asserts the
  full DoD contract (per-file writes, snapshot, MemoryPort queryable).
  The literal 10k-file DoD test is env-gated behind
  `KOSMOS_STAGE_33_LARGE_CORPUS=1` and runs on Colossus; a CPython real-
  corpus integration test is env-gated behind
  `KOSMOS_STAGE_33_REAL_CORPUS=1`.
- **Q6 = A · Single composite ADR-038.** All six Q-decisions ratified in
  this one ADR to keep the Stage 3.3 fan-out atomic.

## Rationale

**Q1 pattern-vendor over file-vendor.** Aider's `repomap.py` (867 lines)
is tightly coupled to aider IO, prompt scaffolding, and its own token
counter. Copying the file wholesale would (a) drag in ADR-007-violating
imports, (b) make future aider bug-fix uptakes painful (line-level
diff-and-pray), and (c) put Kosmos on the hook for the entire aider
license surface even for code it doesn't call. Reimplementing the
algorithm in-tree — with only the `.scm` queries vendored verbatim —
gives us a narrow, auditable dependency (the queries) while letting us
keep the port-layer and MemoryPort discipline clean.

**Q2 no new port yet.** The spec did not require `RepoMapPort` at Stage
3.3; only Tektos consumes repomap today. ADR-023 established the
"envelope-first" pattern where new port surfaces are ratified only after
a second consumer exists. Keeping repomap Tektos-internal defers that
lock-in.

**Q3 both write shapes.** Per-file writes make repomap results
queryable at the granularity the coding-agent needs (e.g. "when was
`plugins/foo.py` last mapped?"). The per-run snapshot gives Phrouros
and other observers a single row to trend map growth without joining
thousands of per-file rows.

**Q4 linear decay.** Simpler than the exponential half-life we
considered; matches operators' intuition ("30 days old = stale"). The
`0.01` floor is the minimum non-zero confidence ADR-008 accepts, so
old-but-still-present files remain queryable rather than being dropped.

**Q5 tiered tests.** The full 10k DoD literal is real but expensive in
the sandbox (>10 minutes wall clock; wastes credits). The 500-file
smoke variant asserts the same contract in <5s and keeps
`make stage1-gate` fast; the 10k literal is provable locally on Colossus
via `KOSMOS_STAGE_33_LARGE_CORPUS=1` and would run in any real CI too.
Precedent: `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1` for Stage 3.2's real MCP
integration test.

**Q6 single composite.** These six decisions are load-bearing on each
other (Q3 depends on Q1's write-side ownership; Q4 depends on Q3's
write shape; Q5 depends on Q3's write count). Splitting them into
separate ADRs would obscure the interdependence and multiply update
fan-out.

## Alternatives considered

**Q1 — file-vendor.** Copy `aider/repomap.py` verbatim under
`plugins/tektos/repomap.py` with only import-path rewrites. Rejected:
drags aider's `Model`, `IgnorantTemporaryDirectory`, and
`InputOutput` singletons into Tektos, violates ADR-007, and makes
upstream bug-fix uptake a manual line-diff exercise.

**Q1 — write from scratch.** Ignore aider entirely. Rejected: aider's
PageRank + identifier heuristics + `.scm` query set are the actual
value; reimplementing from tree-sitter primitives alone would take
weeks and yield inferior ranking.

**Q2 — new `RepoMapPort`.** Add a port with `index()`, `query()`, and
adapter registration. Rejected as premature until a second consumer
exists; ADR-023 pattern says port surfaces get ratified after a second
call site.

**Q3 — per-file writes only.** Rejected: forces observers to aggregate
across thousands of rows to trend map growth.

**Q3 — per-run snapshot only.** Rejected: loses per-file freshness
queryability — the coding-agent's most common query pattern.

**Q4 — exponential half-life** `2 ** (-age_days / half_life)`.
Rejected: operators find "30 days = stale" intuitively linear;
half-life fits noisier signals (e.g. login staleness), not source-code
freshness.

**Q5 — always run 10k literal.** Rejected: burns sandbox credits with
no functional gain (500-file smoke exercises the same contract).

**Q5 — replace synthetic with only real-corpus.** Rejected: real-corpus
tests depend on network + upstream repo stability; can't be part of
`make stage1-gate`.

**Q6 — one ADR per Q-decision.** Rejected: six ADRs with cross-refs
obscure the load-bearing interdependence; a composite is cleaner.

## Consequences

**Files touched (this ADR fan-out):**

- `plugins/tektos/repomap/__init__.py` (new — public re-exports)
- `plugins/tektos/repomap/policy.py` (new — 7 locked constants +
  `compute_freshness_confidence`)
- `plugins/tektos/repomap/tags.py` (new — tree-sitter extraction +
  diskcache)
- `plugins/tektos/repomap/rank.py` (new — NetworkX PageRank + ident
  heuristics)
- `plugins/tektos/repomap/render.py` (new — tree-context render +
  token-budget binary search)
- `plugins/tektos/repomap/indexer.py` (new — `index()` facade,
  MemoryPort writes)
- `plugins/tektos/repomap/queries/{python,javascript,typescript,rust,go,bash}-tags.scm`
  (new — verbatim from aider `5dc9490bb35f`)
- `plugins/tektos/repomap/queries/ATTRIBUTION.md` (new — SPDX +
  provenance)
- `plugins/tektos/tests/test_repomap.py` (new — 31 tests: locked
  constants, freshness formula, tag extraction, rank, render, indexer,
  smoke 500-file corpus, env-gated 10k DoD, env-gated real CPython)
- `pyproject.toml` — 7 deps added under the Stage 3.3 marker:
  `tree-sitter>=0.24`, `tree-sitter-language-pack>=1.13`,
  `networkx>=3.4`, `scipy>=1.14`, `grep-ast>=0.9`, `pygments>=2.18`,
  `diskcache>=5.6`
- `docs/PORTING_LEDGER.md` — aider entry upgraded from PLANNED to
  PATTERN-VENDORED; 7 new dep entries added
- `docs/Kosmos-Build-Spec-v25.md` — §17 ADR-038 row; §18 3.3 DoD points
  to `tests/test_repomap.py::test_repomap_smoke_...` and env-gated 10k
- `docs/Kosmos-Build-Sequence-v25.md` — §3.3 rewritten as LANDED
- `docs/adrs/README.md` — ADR-038 row appended
- `BUILD_LOG.md` — 2 timestamped entries (code ship + tests + docs)
- `SESSION_HANDOFF.md` — overwritten (Stage 3.3 LANDED · Stage 3.4 next)

**Enforcement:**

- ADR-007: no plugin imports another plugin — repomap is pure Tektos-
  internal, no cross-plugin imports.
- ADR-008: every MemoryPort write carries provenance = `aider-repomap`
  and confidence in (0, 1]; enforced at write time by
  `ports.memory.validate_zero_trust_write`.
- Colossus envelope (128GB RAM / 32GB VRAM): repomap is CPU-only + disk-
  cached; no GPU use, RAM footprint bounded by tree-sitter cache and
  NetworkX graph. The 10k literal fits Colossus easily.

## Lock-in phase

Stage 3.3 · Tektos coding-agent context module. Locked constants live
in `plugins/tektos/repomap/policy.py` and cannot be changed without a
superseding ADR.

## References

- Upstream: [Aider `repomap.py` @ `5dc9490bb35f`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f/aider/repomap.py)
  · Apache-2.0
- `plugins/tektos/repomap/queries/ATTRIBUTION.md` (SPDX + provenance)
- `docs/PORTING_LEDGER.md` — aider entry
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (DozerDB MemoryPort · zero-trust writes)
- ADR-023 (envelope-first port introduction)
- ADR-036 (Tektos OpenHands SDK vendoring — sibling Stage 3.1 pattern)
- ADR-037 (Tektos MCP transport — sibling Stage 3.2 pattern)
