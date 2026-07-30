# ADR-053 — Stage 6.3.8 · ADR-010 ODR structural-finalize shim (schema-constrained JSON + deterministic markdown render)

**Status:** Ratified v25
**Lock-in phase:** Stage 6.3 (Phase 6 — Research + ADR-010 resolution)
**Supersedes:** —
**Amends:** —

## Context

The ADR-010 head-to-head harness at `ops/benchmarks/adr_010/` compares
Open Deep Research (ODR) against AREX-Turbo on a fixed rubric-based
question, blind-rated F1–F6.  Between Stage 6.3.4 and Stage 6.3.7 we
iteratively added shims that clean the writer's free-form markdown
output post-hoc:

- shim 3 URL-verification + strip
- shim 6 rubric self-critique (coverage check)
- shim 7 chain-of-verification (CoVe)
- shim 8 claim-support gate
- 6.3.6b finalize-time strip
- 6.3.7 empty-citation-wrapper regex sweeps + `[unverified]` sweep

Blind rating regressed from **4.17/6** (6.3.6b baseline) to **2.94/6**
(6.3.7 mean of 3 trials, 2026-07-30) — three distinct failure modes
survived every added sweep and one new mode appeared:

1. **Feature-delta fabrication** — the writer added plausible-sounding
   but rubric-orphan claims (security-hardened Docker containers,
   telemetry/phone-home behavior, spatial indexing).  The rubric-
   critique shim (shim 6) checks *coverage* of F1–F6 but not
   *overreach* beyond F1–F6.  A prompt-layer deny-list of specific
   forbidden features would only cover known fabrications; the class
   is open-set.
2. **Empty citation wrappers** — after URL strip, the surrounding
   markdown wrapper survives (`*(Source: )*`, `[N] Neo4j Repository:`
   with no URL, `[label]()`).  Regex sweeps caught known variants but
   the writer kept inventing novel wrapper syntax between stages.
3. **Bracketed scratch markers** — writer emitted
   `[unsupported: no citation in observations]`, `[needs citation]`,
   `[unverified: source unreachable]`, `[not covered]` as inline
   self-critique annotations.  Each new marker variant required a new
   regex sweep.

A deep-research pass (see `research_6_3_7b.md`, arXiv sources
ALCE/RARR/FActScore/CoVe/CoNLI/LLMQuoter/I-CALM plus Anthropic's own
hallucination guide, Ollama structured-outputs docs, Instructor
library, Reducto schema-design principles) converged on a single
conclusion:

> The empty-wrapper and scratch-marker classes are not bugs of
> insufficient regex coverage.  They are structural consequences of
> letting the model emit wrapper syntax and scratch-note text as
> free-form tokens in the same channel as the report body.  The
> literature-favored fix is schema-constrained JSON output rendered
> to markdown deterministically in code.

## Decision

**Add a new final shim (shim 9) that emits the report as a
JSON-schema-constrained object via Ollama's native `response_format=
json_schema` parameter and renders markdown deterministically in
Python from the validated object.**

Concretely:

- New module: `ops/benchmarks/adr_010/harness/structural_finalize.py`.
- Exports: `FINAL_REPORT_JSON_SCHEMA`, `Claim`, `Citation`,
  `ValidatedReport`, `StructuralFinalizeError`,
  `build_structural_finalize_prompt`, `call_ollama_schema_constrained`,
  `parse_and_validate`, `render_markdown`, `structural_finalize`.
- Schema (strict, `additionalProperties: false` throughout):
  `{title: str, claims: [{text: str, rubric_ref: F1|F2|F3|F4|F5|F6|null,
  citations: [{label: str, url: str}]}]}`.
- Allow-list gate: after parse, any claim with `rubric_ref=None AND
  empty citations` (or all citations failed URL-shape validation) is
  dropped, not annotated.
- Renderer: pure Python, deterministic.  Wrapper syntax is a template
  applied only when a URL passes shape validation, so
  `*(Source: )*` cannot appear.  There is no text channel that carries
  scratch markers.
- Fallback: on JSON parse error, all-dropped, or network error, keep
  the pre-shim-9 `current_report` and record a `schema_error` /
  `call_error` outcome in `shim_events`.
- New CLI flag: `--no-structural-finalize` (default off = shim
  enabled).
- New `run_odr_trial` kwarg: `enable_structural_finalize=True`.

Shim ordering: **placed after shim 8** and before the finalize URL-
verify block.  Reason: shim 8 marks unsupported claims, and shim 9
emits only rubric-anchored or citation-anchored claims — a shim-8
`[unsupported]` mark on a claim with no citation and no rubric_ref
will naturally translate to a drop under the shim-9 allow-list gate.
The URL-verify block after shim 9 remains a safety net (catches
malformed URLs the schema doesn't reject) but is now covering an
increasingly-empty failure surface.

## Rationale

Alternatives considered:

- **Ship 6.3.7b (drop-in regex sweeps + prompt-layer anti-fabrication
  deny-list).**  Rejected: research explicitly finds enumerated
  deny-lists are structurally weaker than allow-lists under
  autoregressive decoding ("pink elephant" / negation-priming effect),
  and the empty-wrapper / marker classes are open-set (a new wrapper
  variant would defeat the sweep in the next run).  We had already
  observed this failure pattern regress 4.17 → 2.94.
- **Fine-tune Qwen2.5-32B for stricter grounding (Self-RAG /
  reflection-token style).**  Rejected: requires training
  infrastructure and a labeled dataset we don't have; violates the
  project's local-first no-cloud constraint at practical scale; and
  the same effect is available at inference time via grammar-
  constrained decoding.
- **Add a separate LLM-as-judge post-hoc filter (CoNLI-style).**
  Considered future work.  For 6.3.8 the schema-constrained finalize
  handles the observed failure modes at lower cost (one extra
  Ollama call, deterministic render, no second model).  Vectara's
  FaithBench shows generic LLM-judge filters are ~50% accurate on
  hard cases, so we prefer the closed-set structural constraint
  first and reserve judge-filter for cases where schema alone
  proves insufficient.
- **Refactor all shims (grounding, CoVe, rubric-critique) to
  structured JSON at once.**  Rejected as too large for a "get
  Colossus green again" iteration.  Finalize-only has the smallest
  blast radius: the three failure modes all manifest in the final
  report body, not upstream shim intermediates.

Why this specific technique per source:

- **Ollama structured outputs**
  ([docs.ollama.com/api](https://github.com/ollama/ollama/blob/main/docs/api.md)):
  first-class support for `format=<json-schema>` on both the native
  and OpenAI-compatible endpoints, no new dependency.
- **Instructor library**
  ([github.com/567-labs/instructor](https://github.com/567-labs/instructor)):
  Pydantic-validated citation URL field — empty / malformed URLs
  fail validation at parse time rather than passing through as
  wrapper artifacts.
- **Reducto grounded-extraction principles**
  ([llms.reducto.ai/json-schema-extraction-with-citations](https://llms.reducto.ai/json-schema-extraction-with-citations)):
  "visible-only" extraction — omit absent data entirely rather than
  emitting a labeled-but-empty field.  Directly maps onto the
  empty-`[N] Label:` sources-block bug: no citation object → no
  rendered line, not an empty labelled entry.
- **RARR** ([arXiv:2210.08726](https://arxiv.org/abs/2210.08726)):
  post-hoc rewrite pattern that deletes unsupported spans while
  preserving supported ones.  Our shim executes the deletion step
  in deterministic Python (drop claims failing the allow-list) after
  the LLM produces structured claims.
- **Anthropic anti-hallucination guide**
  ([docs.anthropic.com/…/reduce-hallucinations](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)):
  allow-list framing ("use ONLY these facts") + abstention permission
  ("if you cannot cite it, omit it") over deny-lists.  Both are
  encoded in `build_structural_finalize_prompt`.
- **LLMQuoter** ([arXiv:2501.05554](https://arxiv.org/html/2501.05554v1)):
  quote-first grounding disproportionately helps smaller / quantized
  models — directly relevant to Kosmos's q4_K_M-quantized 32B
  writer.  The prompt hands the model the notes verbatim so it can
  copy citation URLs rather than invent them.

## Consequences

- **New file** `ops/benchmarks/adr_010/harness/structural_finalize.py`
  (~470 lines: schema, dataclasses, Ollama call, parser, renderer,
  prompt builder).
- **New file** `ops/benchmarks/adr_010/tests/test_structural_finalize.py`
  (19 tests: schema validation, allow-list gate, URL-shape validation,
  render determinism, wrapper impossibility, marker impossibility,
  fabrication mitigation, prompt-content semantics).
- **Modified** `ops/benchmarks/adr_010/harness/odr.py`:
  new import, new `enable_structural_finalize` kwarg on
  `run_odr_trial`, new shim 9 block between shim 8 and the finalize
  URL-verify block.
- **Modified** `ops/benchmarks/adr_010/runner.py`: new
  `--no-structural-finalize` CLI flag, wire through to
  `run_odr_trial`, banner bumped to "Stage 6.3.8".
- **Test count:** 1180 → 1199 passed (+19), 19 skipped (unchanged).
- **PORTING_LEDGER change:** none.  `structural_finalize.py` is
  purpose-written; no OSS vendored.  The design is informed by the
  cited literature but code is original.
- **Ports affected:** none.  This is entirely inside the ADR-010 ODR
  contender wrapper.  No plugin-space code changes, no kernel-space
  code changes.  ADR-007 (events-only cross-plugin coupling)
  respected trivially — the shim doesn't touch any plugin.
- **Zero-trust MemoryPort:** not applicable; no MemoryPort write.
- **Rollout:** default-on.  A single opt-out flag
  (`--no-structural-finalize`) is retained for A/B comparison
  against 6.3.7 in the artifact record.
- **Colossus verification:** run 3-trial 6.3.8 with the standing
  command, blind-rate F1–F6, compare mean vs. 4.17 baseline (target
  ≥5/6, floor: beat baseline).

## Lock-in phase

Stage 6.3.8 (ADR-010 Phase-6.3 resolution stream).  Lock-in
condition: 6.3.8 Colossus 3-trial blind mean ≥ 4.17 baseline.

## References

- Kosmos-Build-Spec-v25.md §17 (ADR summary), §21 (rollout / ADR-010
  head-to-head)
- `research_6_3_7b.md` at repo root — the deep-research pass that
  drove this decision
- DEBUG_LOG.md 2026-07-30 (6.3.7 regression notes)
- Prior stage ADRs on the same head-to-head: ADR-010 (parent),
  ADR-052 (Stage 6.1 skeleton — establishes Phase-6 scaffolding)
