---
name: kosmos-spec-diff
description: Load before editing Kosmos-Build-Spec-v25.md, Kosmos-Build-Sequence-v25.md, PORTING_LEDGER.md, or any ADR under adrs/. Enforces the newer-wins conflict rule, prevents silent duplication of decisions across specs, and ensures every spec edit is paired with an ADR (if load-bearing) and a BUILD_LOG entry. Use whenever the user asks to update the spec, revise a section, resolve an ambiguity, or version-bump anything under docs/.
---

# Kosmos Spec Diff

## When to use

Load this skill before any edit to:

- `Kosmos-Build-Spec-v25.md`
- `Kosmos-Build-Sequence-v25.md`
- `PORTING_LEDGER.md`
- Any file under `adrs/`

Also load when the user proposes a new spec version (v26, etc.).

## The newer-wins rule

Where prior specs conflict, **newer wins** (v25 > v24 > v23 …). Kosmos v25 is the current authoritative baseline. Older docs live in `archive/` and are **not referenced** from live code, sequence, or ADRs.

If a user request appears to revive an older spec's position, verify against v25 first. If the older position is now preferred, the correct action is to **amend v25**, not to reference the older spec.

## Edit workflow

### 1. Identify the surface

Is the edit:
- **Structural** (adds/removes a section, changes stage/phase order, changes port list) → requires ADR.
- **Content** (fills in TBDs, tightens wording, corrects a factual error) → no ADR, but BUILD_LOG entry.
- **Cosmetic** (typo fix, formatting) → BUILD_LOG entry only.

### 2. Structural edits require an ADR first

Author the ADR via `kosmos-adr-authoring` skill **before** editing the spec. The spec edit then references the ADR ID.

### 3. Prevent silent duplication

- If a decision is stated in **§17 (ADR summary)** of the spec, it must also live in the individual ADR file under `adrs/`. Both must agree.
- If a decision is stated in **§21 (Rollout Plan)** of the spec, the corresponding step in `Kosmos-Build-Sequence-v25.md` must agree.
- If a port is listed in a spec section, `PORTING_LEDGER.md` must have a corresponding entry.

After every edit, cross-check these agreements.

### 4. Edit procedure

Use the `edit` tool with unique `old_string` values. Never rewrite a whole file when a targeted diff suffices.

```
edit(
  file_path="/path/to/Kosmos-Build-Spec-v25.md",
  edits=[{"old_string": "<exact anchor>", "new_string": "<updated>"}]
)
```

For large restructures, generate the new content in a temp file, diff against the original, then commit an atomic replacement — but only after ADR approval.

### 5. Update related files atomically

Every structural edit fans out. Common fan-out set:

- `Kosmos-Build-Spec-v25.md` (main body + §17 table)
- `adrs/ADR-###-*.md` (new or amended)
- `adrs/README.md` (index row updated)
- `Kosmos-Build-Sequence-v25.md` (if lock-in phase or DoD changes)
- `PORTING_LEDGER.md` (if a port is added/removed/superseded)
- `BUILD_LOG.md` (append entry)

Do **not** commit a partial fan-out. Either commit the full set or none.

### 6. Version discipline

- Never bump the spec version number inside a spec edit unless the user explicitly requests it.
- A version bump (v25 → v26) triggers full archive of the old spec into `archive/` and a fresh ADR (`ADR-###-spec-v26-cut.md`) recording the rationale.

## Stop conditions

- Edit would create disagreement between spec §17 and an ADR file → stop; align both first.
- Edit revives an archived spec's position without amending v25 → stop; propose v25 amendment.
- Edit adds a port not in `PORTING_LEDGER.md` → stop; add ledger entry first.
- Edit removes a Definition of Done from an in-progress stage → stop; requires ADR + user approval.

## References

- `Kosmos-Build-Spec-v25.md` (baseline resolution rule at top)
- `adrs/README.md`
- `kosmos-adr-authoring` skill
- `kosmos-log-maintenance` skill
