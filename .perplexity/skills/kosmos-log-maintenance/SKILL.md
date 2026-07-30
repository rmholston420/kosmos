---
name: kosmos-log-maintenance
description: 'Load before writing to any of the four Kosmos operational logs — BUILD_LOG.md (append-only), DEBUG_LOG.md (append-only, search FIRST before diagnosing), KNOWN_ISSUES.md, and SESSION_HANDOFF.md (overwrite each session end). Enforces the timestamp format YYYY-MM-DD HH:MM EDT, append-only discipline, and the search-DEBUG_LOG-first rule from Kosmos custom instructions. Load automatically after any completed build step, decision, bug fix, or at end of session.'
---

# Kosmos Log Maintenance

Kosmos has four operational log files at the monorepo root. This skill enforces the discipline for all four.

## The four logs

| File | Discipline | When to update |
|---|---|---|
| `BUILD_LOG.md` | **Append-only** | After every completed slice / decision / port |
| `DEBUG_LOG.md` | **Append-only** — **search before diagnosing** | On any non-trivial bug diagnosis + fix |
| `KNOWN_ISSUES.md` | Editable (open list) | On unresolved bug that blocks progress |
| `SESSION_HANDOFF.md` | **Overwrite each session end** | At the end of every work session |

## BUILD_LOG.md — append-only

Every entry has this shape:

```markdown
## <YYYY-MM-DD HH:MM EDT> — <one-line summary>

- **Stage / plugin / port:** <e.g. Stage 1.8 · MemoryPort · DozerDB adapter>
- **What changed:** <what was built or modified>
- **Files touched:** <bullet list of paths>
- **Ports / adapters affected:** <list>
- **PORTING_LEDGER / ADR updated:** <ADR-### or —>
- **Stop-condition status:** <met | in-progress | blocked (reason)>
```

Rules:
- Timestamp must be `America/Detroit` (user's timezone), format `YYYY-MM-DD HH:MM EDT` (or `EST` in winter).
- **Never edit or delete a prior entry.** Only append at the end.
- If a step is aborted, log the abort with reason as its own entry.

## DEBUG_LOG.md — search first, then append

### Search-first rule

Before diagnosing **any** new bug:

```bash
grep -in "<symptom keywords>" DEBUG_LOG.md
```

If a matching or similar symptom exists, reuse the recorded fix instead of re-diagnosing. This is a **hard rule** from Kosmos custom instructions.

### Entry format

```markdown
## <YYYY-MM-DD HH:MM EDT> — <symptom summary>

- **Symptom:** <exact error text / behavior observed, copy-pasted>
- **Affected stage / plugin / port:** <e.g. Stage 3 · Tektos · LLMPort>
- **Root cause:** <what was actually wrong>
- **Fix applied:** <what was changed>
- **Files changed:** <bullet list>
- **Related BUILD_LOG entry:** <timestamp or —>
```

Rules:
- Never edit or delete a prior entry.
- If a fix is later superseded by a better one, append a new entry with `**Supersedes:** <YYYY-MM-DD HH:MM EDT>` in place of `Related BUILD_LOG entry`.

## KNOWN_ISSUES.md — running open list

Editable. Each open issue is a subsection with:

```markdown
### <YYYY-MM-DD> — <issue title>

- **Blocks:** <stage/phase/plugin or "no blockers">
- **Symptom:** <what's wrong>
- **Attempted fixes:** <bullets>
- **Next investigation:** <what to try>
- **Related DEBUG_LOG search terms:** <so future you can find related fixes>
```

When resolved:
- Move the entry into `DEBUG_LOG.md` as a closed diagnosis (with fix).
- Delete from `KNOWN_ISSUES.md`.

## SESSION_HANDOFF.md — overwrite each session end

At the **end** of every session, overwrite this file entirely. Its purpose is to reflect **current state only**, not history.

```markdown
# Kosmos Session Handoff — <YYYY-MM-DD HH:MM EDT>

## Current build-sequencing position
- **Stage / phase:** <e.g. Stage 1.8>
- **Plugin / kernel component:** <e.g. MemoryPort / DozerDB adapter>
- **Port(s) in progress:** <list>

## Completed this session
- <bullet list of BUILD_LOG entries appended this session>

## Remaining before current Definition of Done
- <bullet list of remaining tasks in this DoD>

## Open questions / awaiting user answer
- <or "none">

## Exact next action
- <one command or one clearly stated task>
```

At the **start** of a new session, `read SESSION_HANDOFF.md` before doing anything else.

## Cross-cutting rules

- All timestamps in America/Detroit.
- Never batch appends across multiple completed steps into one entry — one entry per step.
- If a file does not exist yet, create it from the template in `templates/` on first write.

## Stop conditions

- If a BUILD_LOG or DEBUG_LOG entry would need to modify a prior entry → stop; the discipline is append-only.
- If SESSION_HANDOFF.md was not read at session start → stop and read it before doing any work.
- If a DEBUG_LOG search hit exists and the recorded fix has not been tried → stop and try that fix first.

## References

- Project custom instructions (verbatim: "Keep a running build log", "Keep a running debug log", "Maintain SESSION_HANDOFF.md")
- `templates/BUILD_LOG.md`, `templates/DEBUG_LOG.md`, `templates/KNOWN_ISSUES.md`, `templates/SESSION_HANDOFF.md`
