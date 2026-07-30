# ADR-050 — Stage 4.5 · SuttaCentral Bilara humanities corpus as MemoryPort adapter corpus (CC0)

**Status:** Ratified v25
**Lock-in phase:** Stage 4.5 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.5 in `Kosmos-Build-Sequence-v25.md` calls for landing the Humanities
canonical-text substrate ahead of Gnosis Phase 3 — the second content
corpus after Stage 4.4's Superpowers Personal-KB landing (ADR-049), and
the first canonical-text corpus. Two prior ADRs constrain how:

- **ADR-002** and **ADR-016** locate the Humanities substrate inside the
  merged **Gnosis** plugin (Humanities cluster) at Phase 3. ADR-016
  explicitly names *canonical Buddhist text corpora* as an intended
  Humanities substrate under Gnosis.
- **ADR-047** (Stage 4.2 hybrid tier) established the fast-tier
  `humanities_cidoc_sample` — a five-fact, hand-authored CIDOC-CRM
  probe used as an invariants smoke corpus. That corpus stays; it
  guards CIDOC-CRM edge semantics against future refactors even after
  a real-content corpus lands.

Stage 4.5's Definition of Done ("Humanities canonical-text KB port
landed under Gnosis Humanities substrate; typed CIDOC-CRM retrieval +
provenance verified against fixtures") requires deciding six things
in the same shape as ADR-049:

- **Q1 — Upstream source:** which canonical-text corpus lands? License?
- **Q2 — Refresh cadence:** how are re-ingests governed?
- **Q3 — Adapter now vs. plugin later:** relocation policy.
- **Q4 — Retrieval surface:** temporal only? Vector? Typed CIDOC-CRM
  edges?
- **Q5 — Ingest granularity:** one record per publication? Per file?
  Per segment?
- **Q6 — Substrate scope:** what content lands vs. stays out?

Every question flagged for explicit ADR choice by Kosmos custom
instructions. User delegated Q6 to "make the optimal choice", which
also forced a pivot on Q1 (see below); the remaining five were
locked from the same session (2026-07-30). This ADR records the
resulting decisions and the alternatives that were rejected.

State on **2026-07-30**:
- Two canonical candidates were surveyed:
  - **84000** — Kangyur / Tengyur (Tibetan → English) — CC-BY-NC-4.0
    on the translated text. Rich TEI-XML, mature translator apparatus.
  - **SuttaCentral Bilara** — Pali → English (and other) parallel
    translations under `github.com/suttacentral/bilara-data`. CC0
    public-domain dedication on the translations, Mahasangiti Pali
    root in the public domain.
- Upstream Bilara HEAD @ `3c93d1cea80fdebcefb777c8724c35bd971f360a`
  on the `published` branch — segment-keyed JSON files under
  `translation/<lang>/<translator>/**` mirrored by
  `root/<lang>/<edition>/**`.
- Stage 4.4 corpora infrastructure ships:
  `synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export`,
  `superpowers` under `adapters/memory/dozerdb/corpora/`, exercised
  by `test_corpora_contract.py` in fast + env-gated live tiers.
- DozerDB adapter baseline is 142 passed / 8 skipped (Stage 4.4
  completion, ADR-049).
- Colossus disk headroom: 300 GB free on the primary drive at Stage
  4.5 kickoff — enough for a 920 MB upstream Bilara clone, but tight
  enough that the ingest CLI is designed to fetch blob-by-blob via
  `gh api` and never require a local clone.

## Decision

Land the SuttaCentral Bilara canonical-text corpus as a **fifth Stage
4.2-shaped adapter corpus**, `humanities-bilara`, colocated with the
existing four under `adapters/memory/dozerdb/corpora/humanities_bilara/`,
ingesting **full-body segment-keyed JSON per file** at a **pinned
upstream commit SHA**, with a workspace-local re-ingest CLI at
`scripts/ingest_humanities.py`. The Stage 4.2 hand-authored
`humanities_cidoc_sample` corpus stays as a fast-tier invariants probe.

The six locked answers:

**Q1 — Upstream source: SuttaCentral Bilara, CC0.** The 84000 corpus
was surveyed and rejected. Its translated text is licensed
CC-BY-NC-4.0 (non-commercial), which introduces a downstream
propagation restriction on any Kosmos artifact that co-mingles
canonical text with commercial-adjacent tooling; Bilara's CC0
dedication eliminates that restriction entirely. Bilara is also
structurally superior for CIDOC-CRM edge extraction: the
directory-level mirror between `translation/<lang>/<translator>/…` and
`root/<lang>/<edition>/…` is literally CIDOC-CRM `P73_has_translation`,
requiring no textual heuristics. Rejected: (a) 84000 alone — NC
license posture; (b) both 84000 and Bilara at Stage 4.5 — doubles the
provenance surface before a single canonical corpus is
battle-tested; 84000 can land in a later stage under its own ADR
after Gnosis exposes the multi-corpus surface.

**Q2 — Refresh cadence:** Pinned SHA + re-ingest CLI. No cron, no
network fetch at import, no auto-update. Regenerating the fixture is
an explicit human action: `scripts/ingest_humanities.py --sha <SHA>
[--via gh|checkout]`. Rejected: (a) tracking Bilara `published`
branch — pulls uncontrolled content into MemoryPort and violates
Kosmos's local-first posture; (b) one-shot commit with no CLI —
makes future updates a manual copy-paste chore and loses provenance.

**Q3 — Adapter now, Gnosis later:** Corpus lives under
`adapters/memory/dozerdb/corpora/humanities_bilara/` at Stage 4.5.
When Gnosis lands at Phase 3, the corpus module + fixture + ingest
CLI relocate to `plugins/gnosis/humanities/canonical_kb/`. The public
loader shape (`load_corpus`, `CORPUS` singleton, env override
`KOSMOS_HUMANITIES_BILARA_PATH`) is deliberately stable across the
move, matching Stage 4.4's Superpowers relocation contract.
Rejected: (a) build the Gnosis plugin skeleton now — creates a
phantom plugin that only Gnosis will populate later; (b) never move
it — leaves substrate content in an adapter package, violating
ADR-016.

**Q4 — Retrieval surface:** Temporal + typed-CIDOC-CRM-link. Every
fact carries the same pinned `as_of` (upstream commit-authored date)
so time-slice queries collapse to before/at cutoff. Mirror
relationships between Pali root files and their English translations
parse into typed `CorpusEdge` records with `kind="P73_is_translation_of"`.
Translator attribution parses into `CorpusEdge` records with
`kind="P94_was_created_by"` pointing at synthesized CIDOC-CRM
`E21_Person` actor records (one per referenced translator, sourced
from Bilara's `_author.json`). **VectorPort surface is NOT opened.**
Rejected: (a) temporal-only — loses the CIDOC-CRM topology Bilara's
directory structure explicitly encodes; (b) temporal + vector —
hauls in an embedding stack before Phase 3 and forks the retrieval
path; (c) untyped `references` kind (as Stage 4.4 uses for
Markdown-link edges) — throws away the CIDOC-CRM property URIs
that make the Humanities substrate interoperable with external
knowledge-graph tooling.

**Q5 — Ingest granularity:** Per-file (per translation JSON + per
mirrored root JSON) plus per-referenced-translator actor records.
One MemoryPort record per `translation/<lang>/<translator>/**/*.json`
at the pinned SHA, one per mirrored `root/<lang>/<edition>/**/*.json`,
one per referenced translator from `_author.json`. Rejected:
(a) per-publication roll-up — collapses the file-level granularity
Bilara publishes at (a single publication like `scpub86 = Cariyapitaka`
contains 35 files); (b) per-segment splitting — each Bilara file is
already segment-keyed; splitting into ~140 × ~30-segment records
would multiply the fixture size 30× without changing what CIDOC-CRM
edges can be typed against; (c) omitting actor records — leaves
`P94_was_created_by` edges pointing at strings, not resolvable graph
nodes, and fails the Corpus construction-time resolvability
invariant.

**Q6 — Substrate scope:** Full-body segment-keyed JSON. Each fact's
`attributes` carries `body` (segment text concatenated in insertion
order), `segment_count`, `source_commit`, `license` (`CC0-1.0` for
translations, `public-domain` for Mahasangiti Pali root),
`upstream_url`, translator/publication metadata, and the typed
`references` list. Stage 4.5 slice is Bhikkhu Sujato's English
translations of three Khuddaka Nikaya publications (scpub7
Dhammapada, scpub19 Khuddakapatha, scpub86 Cariyapitaka) mirrored
by their Mahasangiti Pali root — 70 translation files + 70 root
files + 1 translator actor = 141 records, 140 CIDOC-CRM edges,
~392 KB fixture. Rejected: pointer-only records (URL + hash, no body)
— turns the substrate into a network-fetch dependency and defeats
local-first operation.

## Rationale

The six answers compose into a single principle: **the Humanities
canonical-text substrate is a CIDOC-CRM-typed data landing, not a
code vendor**. Bilara content enters Kosmos as inert JSON inside a
fixture, mediated by the same MemoryPort contract every other corpus
honors — zero-trust provenance, bounded confidence, timezone-aware
`as_of`, ADR-007 (no plugin-to-plugin imports; corpora live under
`adapters/`, not `plugins/`).

The Q1 pivot from 84000 to Bilara is load-bearing: CC0 removes an
entire class of downstream propagation questions, and Bilara's
directory-mirror structure means the CIDOC-CRM edges we want
(`P73_has_translation`, `P94_was_created_by`) fall out of the
filesystem layout without any textual inference. That makes the
edge machinery unit-testable against a bijective invariant
(every translation has exactly one root at the same `bilara_uid`),
which is asserted in the Stage 4.5 contract tests.

Locating the corpus under the DozerDB adapter at Stage 4.5 keeps the
Stage 4.2 contract tests as the enforcement layer. `ALL_CORPORA`
gains one entry; the parametrized invariant tests and env-gated live
tier extend to it automatically. When Gnosis lands at Phase 3, the
move is a directory relocation, not a re-implementation. The Stage
4.2 `humanities_cidoc_sample` corpus stays alongside — it is a
5-fact hand-authored invariants probe that guards CIDOC-CRM edge
semantics even when the real-content corpus is disabled or
overridden via `KOSMOS_HUMANITIES_BILARA_PATH`.

Typed CIDOC-CRM edges (`P73_is_translation_of`, `P94_was_created_by`)
are the retrieval feature Bilara's authorship style requires:
canonical texts are addressed by mirrored parallels between root and
translation, and by translator attribution. Materializing those into
`CorpusEdge` with CIDOC-CRM property URIs (rather than a generic
`"references"` kind) keeps Gnosis's future graph-shaped queries
against Humanities substrate grounded in a standard vocabulary
external tooling already understands.

## Consequences

**New files (adapter package):**
- `adapters/memory/dozerdb/corpora/humanities_bilara/__init__.py` —
  public re-exports (`CORPUS`, `SOURCE_COMMIT`,
  `UPSTREAM_LICENSE_TRANSLATION`, `UPSTREAM_LICENSE_ROOT`,
  `UPSTREAM_URL`, `load_corpus`, `load_facts_and_edges`).
- `adapters/memory/dozerdb/corpora/humanities_bilara/humanities_bilara.py`
  — JSONL loader + env override + typed-edge materialization +
  temporal query helpers, mirroring `superpowers.py` with additions
  for the actor / root / translation subject-namespace validation.
- `adapters/memory/dozerdb/corpora/humanities_bilara/fixtures/humanities_bilara.jsonl`
  — 141 records at SHA `3c93d1cea80fdebcefb777c8724c35bd971f360a`,
  140 typed CIDOC-CRM edges (70 × `P73_is_translation_of` + 70 ×
  `P94_was_created_by`), ~392 KB.

**Extended files:**
- `adapters/memory/dozerdb/corpora/__init__.py` — exports
  `HUMANITIES_BILARA_CORPUS` and `load_humanities_bilara_corpus`, and
  adds `HUMANITIES_BILARA_CORPUS` to `ALL_CORPORA` (grows to five).
- `adapters/memory/dozerdb/corpora/test_corpora_contract.py` — 7 new
  fast tests (cardinality by subject namespace, provenance triple +
  CIDOC-CRM class labels, typed-edge kind census + resolvability,
  root/translation bijection at `bilara_uid`, env override path,
  missing-attribute + unknown-namespace rejection, fixture commit
  check).

**Workspace tooling (not committed to plugin space):**
- `scripts/ingest_humanities.py` — CLI to regenerate the fixture from
  any pinned SHA, via `gh api` (default, blob-by-blob) or a local
  checkout under `--via checkout --source <path>`. Not invoked at
  runtime by any adapter or plugin; not a package.

**Test-suite outcome:** DozerDB adapter suite moves from 142 passed /
8 skipped to **155 passed / 9 skipped**; the +13 passes come from 7
new Stage 4.5 tests plus parametrized invariants that already sweep
over `ALL_CORPORA`; the +1 skip is the new Stage 4.5 corpus wiring
into the env-gated `test_live_tier_ingests_corpus_end_to_end`
parametrization.

**ADR-049 relationship:** ADR-049 unchanged. Its Superpowers
Personal-KB decisions govern methodology skill ingest; ADR-050
governs canonical-text ingest. §17 of the spec carries both rows.

**ADR-047 relationship:** ADR-047's `humanities_cidoc_sample` fast
tier corpus stays. It is not superseded — its 5-fact hand-authored
invariants probe is intentionally decoupled from any real upstream
content and remains the guard against CIDOC-CRM edge regressions
when Bilara is disabled or overridden.

**Downstream ADRs to update:** none. ADR-002 and ADR-016 already
specify the Gnosis endpoint; ADR-050 confirms the Stage 4.5 landing
site and the deferred relocation.

**PORTING_LEDGER:** new entry under **Content corpora → Humanities**
classifying `suttacentral/bilara-data` as a **content ingest**, not a
vendored code dependency. SHA + license + fixture path recorded.

**Gnosis Phase 3 move-plan:** relocation is a rename of
`adapters/memory/dozerdb/corpora/humanities_bilara/` →
`plugins/gnosis/humanities/canonical_kb/`, plus an import-path bump
in `adapters/memory/dozerdb/corpora/__init__.py` (which removes
`HUMANITIES_BILARA_CORPUS` from `ALL_CORPORA` and lets Gnosis
register it via the plugin bus). The fixture format and env
override name stay identical.

## Lock-in phase

Stage 4.5 (Kosmos-Build-Sequence-v25 §4.5) locks this in. Any later
change to any of Q1–Q6 requires an amending ADR.

## References

- `Kosmos-Build-Sequence-v25.md` §4.5 (Humanities corpus port under Gnosis)
- `Kosmos-Build-Spec-v25.md` §17 (ADR summary table)
- `docs/adrs/ADR-002-gnosis-humanities-scope.md`
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-016-knowsys-gnosis-merge.md`
- `docs/adrs/ADR-047-stage-4-2-corpora-hybrid-tier.md`
- `docs/adrs/ADR-049-stage-4-4-superpowers-kb-adapter-corpus.md`
- `PORTING_LEDGER.md` (Content corpora → Humanities section)
- Upstream: `github.com/suttacentral/bilara-data` @
  `3c93d1cea80fdebcefb777c8724c35bd971f360a` (translations CC0-1.0,
  Mahasangiti Pali root public domain)
