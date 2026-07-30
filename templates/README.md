# Kosmos Templates

Copy these to the Kosmos monorepo root at Stage 0.2:

```bash
cp templates/{BUILD_LOG,DEBUG_LOG,KNOWN_ISSUES,SESSION_HANDOFF}.md ./
```

- `BUILD_LOG.md` — append-only build ledger
- `DEBUG_LOG.md` — append-only debug ledger (search first!)
- `KNOWN_ISSUES.md` — running open list
- `SESSION_HANDOFF.md` — overwrite at end of every session

All timestamps in America/Detroit (EDT/EST). Format: `YYYY-MM-DD HH:MM EDT`.

Discipline is enforced by the `kosmos-log-maintenance` Perplexity Computer skill.
