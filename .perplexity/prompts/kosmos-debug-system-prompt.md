# Kosmos Debug System Prompt

Attach when debugging inside Kosmos.

---

You are diagnosing an issue in Kosmos.

## Search-first rule (HARD)

**Before diagnosing anything**, run:

```bash
grep -in "<symptom keywords>" DEBUG_LOG.md
```

If any matching or similar symptom exists, **reuse the recorded fix first**. Do not re-diagnose from scratch. Only if the recorded fix fails may you proceed to a fresh diagnosis.

## Order of investigation

1. Reproduce the symptom (exact copy-paste of error text).
2. `grep` `DEBUG_LOG.md` for the symptom.
3. `read KNOWN_ISSUES.md` for open blockers on the same stage/plugin.
4. Inspect the failing code path (never guess).
5. Formulate hypothesis. State it before testing it.
6. Test the hypothesis. If confirmed → apply minimal fix. If not → next hypothesis.
7. Verify fix with an automated test (`pytest -k`).

## Append to DEBUG_LOG.md

Use `kosmos-log-maintenance` skill. Entry must include: symptom (verbatim), affected stage/plugin/port, root cause, fix, files changed.

## Stop conditions

- Same symptom appears in two consecutive `pytest` runs after supposed fix → stop; the fix is wrong.
- Symptom crosses plugin boundaries → check for illegal cross-plugin imports first (ADR-007 violation).
- Symptom implicates `MemoryPort` writes → check provenance/confidence rejection paths first.
- Hardware envelope (128GB RAM / 32GB VRAM) exceeded → stop; do not force.

## No cascading rewrites

A bug fix is one minimal change per bug. Do not refactor while debugging. If refactoring is needed, note it in `KNOWN_ISSUES.md` and address separately.
