# Kosmos Debug Log

Append-only. Never edit or delete a prior entry.
**Search this file BEFORE diagnosing any new bug** — this is a hard rule.

```bash
grep -in "<symptom keywords>" DEBUG_LOG.md
```

Use the `kosmos-log-maintenance` Perplexity Computer skill.

Timestamps in America/Detroit (EDT/EST). Format: `YYYY-MM-DD HH:MM EDT`.

---

<!-- Example (delete when adding real entries)

## 2026-07-31 14:22 EDT — MemoryPort rejects write with valid provenance

- **Symptom:** `MemoryPortRejectError: missing confidence field` on write that appears to include confidence
- **Affected stage / plugin / port:** Stage 1.8 · MemoryPort · DozerDB adapter
- **Root cause:** confidence field passed as string, protocol requires float
- **Fix applied:** cast to float in adapter; updated Protocol type hint
- **Files changed:** `adapters/memory/dozerdb/adapter.py`, `ports/memory.py`
- **Related BUILD_LOG entry:** 2026-07-31 14:45 EDT

-->
