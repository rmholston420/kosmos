# ADR-044 — Tektos docling Document Ingestion (Stage 3.10)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.10
**Supersedes:** —

## Context

Build-Sequence §3.10 has a single-line DoD: **"PDF/DOCX/HTML → structured JSON-LD via DataPort."** Spec §18.5 names `docling-project/docling` as the local PDF/DOCX/PPTX/image → Markdown / structured-JSON pipeline. Spec §5.2 (Phase 5, bill/subscription tracking) is a later **use-site** for the same subsystem; Stage 3.10 is the **port-in** stage.

The `DataPort` (ADR-028) already declares the surface Kosmos needs — `export_canonical(record_type, payload, *, provenance, confidence, pii_tier, source_citation, attributes) -> CanonicalExportHandle`. The Stage 1.10 filesystem adapter enforces JCS canonicalization, hash-anchored envelopes, and the non-bypassable `validate_canonical_record` port-level guard. No plugin has consumed `DataPort` yet — Stage 3.10 is the first consumer.

docling upstream (`docling-project/docling`, MIT, PyPI `docling==2.116.0`, upstream HEAD `ba8251e9cda84bab44cebe3b884119d3f50cb12a` as of 2026-07-29) exposes a stable Python API: `DocumentConverter().convert(source).document` returns a Pydantic v2 `DoclingDocument` model with a lossless `export_to_dict()` JSON representation and multiple export formats (Markdown, HTML, JSON, DocTags). It pulls a large native dependency tree (PyTorch, torchvision, layout / OCR models) that is inappropriate for the Kosmos fast-test venv but appropriate for Colossus (128 GB RAM / RTX 5090).

### Locked-in decisions

- **Q1 = A — PATTERN-VENDOR.** No upstream source copied. `docling==2.116.0` (MIT) is added as an **optional** dev dependency under a new `[project.optional-dependencies] ingest` extra. The Tektos ingest subsystem imports docling **lazily**, mirroring how the Stage 3.8 Pier harness invokes `pier` via subprocess without an in-process import: the fast unit tier runs without the package installed. The subsystem re-implements the thin adapter layer (typed models, policy constants, harness) in Kosmos-native code; docling itself is invoked only via its documented `DocumentConverter().convert(...).document.export_to_dict()` surface.
- **Q2 = A — No new port; envelope-first per ADR-023.** Ingest is Tektos-internal. All persistence goes through the existing `DataPort.export_canonical` — no new verb, no new port. Matches ADR-038 / ADR-040 / ADR-041 / ADR-042 defer pattern. If a second consumer for "ingest-then-canonicalize" appears, a follow-up ADR can extract a formal port surface then.
- **Q3 = A — PII tier `INTERNAL` default; caller overrides.** Ingested documents are the user's local files (`docling` is a **local-execution** pipeline per its README) — not automatically `PUBLIC`. No PII detection at 3.10, so not automatically `SENSITIVE`. `INTERNAL` is the safe default; caller can pass `pii_tier=PIITier.SENSITIVE` or `PIITier.RESTRICTED` to route the envelope to the FS adapter's `restricted/` prefix (AES-256-at-rest per spec §147 lands with ops-deploy, not at 3.10).
- **Q4 = A — Confidence `1.0` on success; failure raises.** docling is a deterministic lossless converter — there is no per-document uncertainty signal to emit. Successful ingestion writes with `confidence=DOCLING_SUCCESS_CONFIDENCE=1.0`. Any failure (unsupported extension, docling raise, empty output) raises `DoclingIngestFailure` and writes **nothing** to `DataPort`. Mirrors Stage 3.8 Pier `PASS → 1.0` / `raise → nothing` pattern.
- **Q5 = A — Two-tier tests.** Fast unit tier (mandatory in `make stage1-gate`): a fake `DoclingConverter` shim + committed micro-fixtures (`.pdf` / `.docx` / `.html` under `plugins/tektos/tests/fixtures/docling/`) + the real filesystem `DataPort` writing to a `tmp_path`. Real docling tier: env-gated by `KOSMOS_STAGE_310_REAL_DOCLING=1`, skips unless `docling` importable — on Colossus this exercises the real converter against the same committed HTML fixture (deterministic, tiny; PDF/DOCX would require large runtime deps + model downloads at first use).
- **Q6 = A — Supported extensions at 3.10: `.pdf` `.docx` `.html` only.** Matches the DoD literal verbatim. docling supports many more formats (PPTX, XLSX, EPUB, images, audio, video), but Q6=A pins 3.10 scope to the three named in the DoD; extension whitelist locked in `policy.py` as `DOCLING_SUPPORTED_EXTENSIONS`. Widening this frozen set is a follow-up config change with no ADR needed.
- **Q7 = A — Kernel runner `scripts/docling_ingest.py`.** Mirrors Stage 3.8 `scripts/pier_eval.py` shape: `--path <file> --out-root <dir>`; loads config, invokes `run_docling_ingest(path, data_port=...)`, prints the returned `CanonicalExportHandle` fields as JSON on stdout. Wired to a new `Makefile ingest-doc` target using a committed sample fixture.
- **Q8 = A — New ADR-044 (this document).** Amends nothing. Adds one row to Spec §17 ADR table and to `docs/adrs/README.md` index.
- **Q9 = A — DoD literal anchor test.** `test_pdf_docx_html_ingest_produces_structured_jsonld_via_dataport_build_sequence_3_10_dod` wires three committed fixture inputs (one each of `.pdf` / `.docx` / `.html`) through the fake docling shim → real Stage-1.10 filesystem `DataPort` → asserts three canonical envelopes under `{root}/tektos.ingest.document/` with locked `record_type`, `provenance`, `pii_tier`, and shape-correct payload keys, and asserts `check_format_health()` reports zero degraded envelopes.

### Alternatives considered

- **Copy docling source into `plugins/tektos/ingest/vendor/`.** Rejected — large native dep tree, heavy licensing surface, no benefit vs. PyPI install; ADR-023 envelope-first + PyPI subprocess pattern is already the house style (ADR-038 / ADR-042).
- **Introduce a new `IngestPort` seam.** Rejected — no second consumer identified. ADR-023 envelope-first defer pattern applies; a future ADR can extract a formal port when Phase-5 bill-tracking or a second ingest domain lands.
- **PII tier `PUBLIC` default.** Rejected — ingested files are the user's local documents, which docling itself flags as a local-execution privacy feature.

## Decision

Ship the Tektos docling ingest subsystem at `plugins/tektos/ingest/{__init__,policy,models,harness}.py`. Add `docling==2.116.0` as a `[project.optional-dependencies] ingest` extra. Ingest goes through `DataPort.export_canonical` with `record_type="tektos.ingest.document"`, `provenance="tektos-docling-ingest"`, `confidence=1.0` on success, `pii_tier=PIITier.INTERNAL` default. Extension whitelist frozen to `{.pdf, .docx, .html}`. Kernel runner `scripts/docling_ingest.py` + `Makefile ingest-doc` target. Two-tier tests: fast fake-shim tier in `make stage1-gate`; env-gated real-docling tier via `KOSMOS_STAGE_310_REAL_DOCLING=1`.

## Locked constants

```python
DOCLING_INGEST_PROVENANCE = "tektos-docling-ingest"
DOCLING_INGEST_RECORD_TYPE = "tektos.ingest.document"
DOCLING_UPSTREAM_PACKAGE = "docling"
DOCLING_UPSTREAM_PYPI_VERSION = "2.116.0"
DOCLING_UPSTREAM_COMMIT = "ba8251e9cda84bab44cebe3b884119d3f50cb12a"
DOCLING_UPSTREAM_LICENSE = "MIT"
DOCLING_UPSTREAM_REPO = "https://github.com/docling-project/docling"
DOCLING_DEFAULT_PII_TIER = PIITier.INTERNAL
DOCLING_SUCCESS_CONFIDENCE = 1.0
DOCLING_MIN_CONFIDENCE = 0.0
DOCLING_MAX_CONFIDENCE = 1.0
DOCLING_SUPPORTED_EXTENSIONS = frozenset({".pdf", ".docx", ".html"})
```

## Rationale

- **Directly closes the DoD:** DoD literal names PDF/DOCX/HTML → structured JSON-LD via DataPort. docling produces the JSON, DataPort produces the JSON-LD envelope. No custom parser code needed.
- **Zero risk to fast-test path:** lazy import + PATTERN-VENDOR means `make stage1-gate` never touches docling's heavy native deps; only Colossus with the `[ingest]` extra installed exercises the real path.
- **Reuses ADR-028 policy shape:** the port-level guard (`validate_canonical_record`) already enforces `provenance` / `confidence` / `pii_tier` at the top of every write — Stage 3.10 inherits zero-trust discipline for free.
- **Envelope-first defer is the house pattern:** ADR-038 (repomap), ADR-040 (openspec), ADR-041 (plan renderer), ADR-042 (Pier), and now ADR-044 all defer new ports pending a second consumer. Consistent with ADR-023.
- **First `DataPort` consumer proves the port surface end-to-end** at a real use-site with real payloads, without ratifying anything new.

## Consequences

- `plugins/tektos/ingest/` becomes the canonical location for Tektos-domain document ingestion; Phase 5 bill/subscription tracking calls into it.
- `pyproject.toml` gains an `[project.optional-dependencies] ingest` extra with `docling==2.116.0`; the fast-test venv is unaffected.
- `docs/PORTING_LEDGER.md` docling row promoted `PLANNED` → `VENDORED (dev dep, Stage 3.10)`.
- Spec §18.5 docling row license corrected `Apache-2.0` → `MIT` (drift fix — actual upstream SPDX per GitHub API).
- Spec §17 gains one new row (`ADR-044 | Tektos docling Document Ingestion | Ratified v25 | Stage 3.10`).
- `docs/adrs/README.md` gains one new row.
- `Kosmos-Build-Sequence-v25.md` §3.10 rewritten as a LANDED block mirroring §3.8 / §3.9 shape.
- `Makefile` gains an `ingest-doc` target and `.PHONY` entry.
- ADR-007 respected: subsystem lives under `plugins.tektos.ingest`; AST guard test rejects any import of `plugins.<other>` from `plugins/tektos/ingest/`.
- ADR-008 respected: any `MemoryPort` writes at future use-sites (Phase 5) will carry provenance + confidence — 3.10 itself writes only through `DataPort`, whose port-level guard is equivalent.
- ADR-023 respected: envelope-first defer.
- ADR-028 respected: `DataPort` surface used unchanged. `check_format_health()` cross-verifies the newly-written envelopes as part of the DoD literal test.

## Lock-in phase

Stage 3.10.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §18.5 (Tektos donor row for docling), §5.2 (Phase 5 use-site), §136 (JSON-LD sole canonical format), §150 (PII tier classification)
- `docs/Kosmos-Build-Sequence-v25.md` §3.10 (this stage), §3.8 / §3.9 (pattern precedent)
- `docs/adrs/ADR-023-envelope-first-cross-plugin-coupling.md` (envelope-first defer)
- `docs/adrs/ADR-028-dataport-jsonld-canonical-export.md` (DataPort surface)
- `docs/adrs/ADR-042-tektos-pier-eval-harness.md` (PATTERN-VENDOR shape precedent)
- `docs/PORTING_LEDGER.md` docling row
- Upstream: `https://github.com/docling-project/docling` @ `ba8251e9cda84bab44cebe3b884119d3f50cb12a` (MIT)
