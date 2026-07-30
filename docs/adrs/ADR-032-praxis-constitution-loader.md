# ADR-032 — Praxis Constitution Loader (Ed25519 JWS over JCS)

**Status:** Ratified v25
**Lock-in phase:** Stage 2.1 · Praxis plugin · constitution boot-verification subsystem
**Supersedes:** —

## Context

Stage 2.1 (Build-Sequence §2.1) requires a Praxis subsystem that loads the
kernel constitution and refuses to boot if the on-disk constitution artifact
does not match its Ed25519 signature. The spec (§278) specifies:

> Constitution system — signed/versioned YAML+Markdown tree (`signing.py`,
> `verifier.py`, `amend_service.py`, CLI, `pubkey.pem`, `schema.json`,
> ratified `v0001.yaml/.json/.sig` triplet), already fully implemented in
> Rigpa-LMS; ported using Ed25519 asymmetric signing; amendment CLI/UI
> deferred until Synedrion exists to drive amendments.

Two orthogonal decisions must be locked at Stage 2.1:

**Scope question (Q1):** Rigpa's donor includes seven files — `signing.py`,
`verifier.py`, `amend_service.py`, `service.py`, `cli.py`, `models.py`,
`schemas.py` — plus the genesis artifact triplet. Spec §278 defers amendment
CLI/UI to Synedrion (Phase 6.3). What subset ships at Stage 2.1?

- **Option A (verifier + loader only, spec-tight):** Port `signing.py`
  primitives inline into a single `verifier.py`. Ship boot-time
  `ConstitutionLoader`. No standalone `signing.py`. Minimum bytes.
- **Option B (verifier + loader + signing helper, chosen):** Port
  `signing.py` as a standalone module (pure crypto primitives, zero I/O),
  ship `verifier.py` on top of it, ship boot-time `ConstitutionLoader`.
  Defers `amend_service.py`, `service.py`, `cli.py`, `models.py`, `schemas.py`
  to Synedrion (Phase 6.3).
- **Option C (full Rigpa parity):** Port all seven files including amend
  service and CLI. **Explicitly rejected by spec §278.**

**UI parity question (Q2):** Praxis is Kosmos's first plugin. Spec §17.1
(UI Parity Rule, ADR-014) requires every plugin to register a
`FrontendContractPort` component before Tier-2 promotion, with only Tektos
Phase 2 grandfathered. The Next.js shell doesn't land until Stage 3.5. What
does Praxis register at Stage 2.1?

- **Option A (register PluginDescriptor now, kernel-side only, chosen):**
  Register `PluginDescriptor(name="praxis", panels=(governance-panel,),
  routes=(), state_namespace="praxis")` with `ui_parity_status=IN_PROGRESS`.
  Stage 3.5 Next.js shell picks it up and resolves to COMPLIANT.
- **Option B (defer to Stage 3.5):** Requires an ADR amending §17.1 to
  grandfather kernel-plugins built before Stage 3.5. Delays Stage 2 and
  makes §17.1 more permissive. **Rejected.**

## Decision

**Q1 = B.** Port Rigpa's `signing.py` (122 lines of pure Ed25519+JCS
primitives, zero I/O) as a standalone module `plugins/praxis/constitution/signing.py`.
Layer `verifier.py` on top. Ship boot-time `ConstitutionLoader` that reads the
`vNNNN.{yaml,json,sig}` triplet from `governance/constitution/versions/`,
verifies the signature via `verifier.py`, cross-checks that the JSON copy is
the JCS canonicalization of the YAML payload, and raises
`ConstitutionTamperError` on any mismatch — a raised error at
`ConstitutionLoader.__init__` boot path is the Stage 2.1 DoD's "boot refused"
signal.

**Explicitly deferred to Synedrion (Phase 6.3):** `amend_service.py`
(amendment workflow), `service.py` (version diff/list HTTP surface),
`cli.py` (`rigpa-constitution` CLI), `models.py` (SQLAlchemy schema),
`schemas.py` (Pydantic serialization), `router.py` (FastAPI HTTP), the
amendment REST endpoints, the `constitution_amendments` DB table.

**Q2 = A.** Praxis registers a `PluginDescriptor` via the
`FrontendContractPort` at plugin init. Descriptor:

- `name = "praxis"`
- `version = "0.1.0"`
- `kernel_compat = "0.1.x"`
- `state_namespace = "praxis"`
- `routes = ()` — no HTTP routes at Stage 2.1
- `panels = (Panel(slot=PanelSlot.RIGHT_SIDEBAR, name="praxis.governance",
  priority=100, lazy_module="praxis/governance-panel"),)` — declarative
  stub only; Stage 3.5 Next.js shell resolves the lazy_module reference
- `design_tokens = ()` — Praxis uses kernel-inherited tokens
- `ui_parity_status = UiParityStatus.IN_PROGRESS` — Stage 3.5 shell promotes
  to `COMPLIANT` when the panel component renders

Grandfathering scope stays exactly as ADR-014 defines it: **only** Tektos
Phase 2. Praxis honors §17.1 via kernel-side registration.

## Rationale

**Q1=B:**

- `signing.py` in Rigpa is deliberately a leaf module — no imports from
  other Rigpa domains, no I/O orchestration beyond `Path.read_bytes()` in
  the key loaders. Porting it now costs ~120 lines and eliminates a future
  "port signing.py before amend_service.py" step when Synedrion lands.
- The DoD ("Tampered constitution → boot refused") requires only three
  primitives: canonicalize, verify, load_public_key. All three are in
  `signing.py`. Verifier.py is a 26-line facade that couples them to the
  co-located `pubkey.pem`.
- `amend_service.py` requires a database (SQLAlchemy `ConstitutionAmendment`
  table with `challenge_id`, `expires_at`, state machine), a signing
  workflow, and — crucially — a **user interface for humans to ratify
  amendments**. Spec §278 explicitly ties the CLI/UI landing to Synedrion.
- `service.py` (list/diff/get_current) is a nice-to-have HTTP surface. Not
  needed for boot verification. Deferrable.

**Q1 alternatives rejected:**

- **Option A** (inline signing into verifier.py): saves ~30 lines but
  couples crypto primitives to the co-located `pubkey.pem` path. When
  amend_service lands at Synedrion, we'd have to extract signing.py
  anyway — a re-port. Not worth the temporary savings.
- **Option C** (full parity): violates spec §278; requires DB + FastAPI +
  amendment state machine + UI. Would inflate Stage 2.1 from ~1 day to
  ~1 week and pull forward Synedrion work.

**Q2=A:**

- ADR-014 §17.1 was written with exactly this case in mind — the enum
  `UiParityStatus.IN_PROGRESS` exists precisely because plugins land
  backend-first and the UI resolves later. IN_PROGRESS is a promotion path,
  not a grandfathering exception.
- Registering the descriptor now surfaces the panel in
  `get_panel_manifest()` immediately, so the Stage 3.5 Next.js shell will
  discover Praxis without any registration-code changes at 3.5.
- No ADR amendment needed. Keeps §17.1 clean: exactly one grandfathered
  exception (Tektos Phase 2), forever.

**Q2 alternatives rejected:**

- **Option B**: amending §17.1 to grandfather kernel-plugins-before-3.5
  weakens the discipline. Every future kernel plugin (Phrouros §2.3, likely
  candidates at §2.2) would inherit the exception. The rule loses meaning.
  IN_PROGRESS handles this case natively.

## Consequences

**Files added:**

- `plugins/praxis/__init__.py` — package marker
- `plugins/praxis/plugin.py` — PraxisPlugin bootstrap: load constitution,
  verify signature, register with FrontendContractPort
- `plugins/praxis/constitution/__init__.py` — subpackage marker
- `plugins/praxis/constitution/signing.py` — Ed25519 sign/verify + JCS
  canonicalize + PEM key loaders (ported from Rigpa)
- `plugins/praxis/constitution/verifier.py` — ConstitutionVerifier facade
  bound to `governance/constitution/pubkey.pem` by default
- `plugins/praxis/constitution/loader.py` — ConstitutionLoader (boot-time
  read-verify orchestrator + ConstitutionTamperError)
- `plugins/praxis/constitution/errors.py` — ConstitutionTamperError,
  ConstitutionNotFoundError, ConstitutionMalformedError
- `plugins/praxis/tests/__init__.py`
- `plugins/praxis/tests/test_constitution_loader.py` — contract tests
  including the §2.1 DoD test `test_tampered_constitution_refuses_boot_build_sequence_2_1_dod`
- `governance/__init__.py` — package marker
- `governance/constitution/__init__.py`
- `governance/constitution/pubkey.pem` — genesis Ed25519 public key
- `governance/constitution/versions/v0001.yaml` — genesis constitution
  (YAML source of truth)
- `governance/constitution/versions/v0001.json` — JCS canonicalization of
  v0001.yaml
- `governance/constitution/versions/v0001.sig` — Ed25519 detached signature
  over v0001.json (base64url ASCII)
- `scripts/gen_constitution_genesis.py` — one-shot key+genesis generator
  (regeneratable; committed for reproducibility)

**Files touched:**

- `docs/Kosmos-Build-Spec-v25.md` — §17 ADR summary table gets ADR-032 row
- `docs/Kosmos-Build-Sequence-v25.md` — §2.1 gets a landing note
- `docs/adrs/README.md` — ADR-032 row appended
- `PORTING_LEDGER.md` — Praxis Constitution port entries: Rigpa
  `signing.py`/`verifier.py` PATTERN-VENDORED, `service.py`/`amend_service.py`/`cli.py`/`models.py`/`schemas.py`
  PATTERN-VENDORED-reference-only-deferred-to-Synedrion, stdlib `pathlib`/`json`/`hashlib`
  VENDORED-reused-stdlib
- `pyproject.toml` — register `plugins.praxis` and `governance.constitution`
  packages; no new runtime deps (`PyYAML>=6.0`, `rfc8785>=0.1.4`,
  `cryptography>=49` already declared)
- `BUILD_LOG.md` — 2 append-only entries at Stage 2.1 landing

**Downstream ADRs:** Synedrion amendment workflow will supersede portions
of this ADR by adding the deferred amend_service.py, cli.py, service.py,
models.py, schemas.py. Any Synedrion ADR must reference ADR-032 as its
foundation. This ADR is not superseded by that landing — the
verifier+loader primitives lock at Stage 2.1 and remain the boot-time
enforcement contract.

**Cross-plugin coupling (ADR-007):** Praxis does not import any other
plugin. The constitution loader emits no cross-plugin events at Stage 2.1;
future amend_service.py will publish `praxis.constitution.amended` events
via `EventBusPort` when Synedrion lands.

**Zero-trust MemoryPort (ADR-008):** the constitution loader does not write
to MemoryPort. If a future subsystem exposes the ratified constitution to
MemoryPort (e.g. for cross-plugin visibility), that write will supply
`provenance="praxis.constitution.v{N}"` and `confidence=1.0`.

## Lock-in phase

Stage 2.1 · Praxis plugin · constitution boot-verification subsystem.

## References

- Spec §278 (Constitution system statement)
- Spec §17.1 (UI Parity Rule)
- ADR-014 (UI Parity Rule ratified)
- ADR-006, ADR-006a (Ed25519 JWS over JCS — Rigpa's original decisions,
  referenced but not superseded)
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (zero-trust MemoryPort writes)
- ADR-031 (FrontendContractPort — Praxis's registration target)
- Build-Sequence §2.1 (DoD: tampered constitution → boot refused)
- Rigpa donor: `backend/src/rigpa/domains/governance/constitution/{signing.py,verifier.py,service.py,amend_service.py,cli.py,models.py,schemas.py,pubkey.pem,versions/v0001.{yaml,json,sig}}`
- RFC 8785 (JCS — JSON Canonicalization Scheme)
- RFC 8032 (Ed25519)
