# Kosmos Known Issues

Running open list of unresolved bugs and blockers. Editable — but when resolved, move the entry into `DEBUG_LOG.md` as a closed diagnosis (with fix) and delete from here.

Use the `kosmos-log-maintenance` Perplexity Computer skill.

---

<!-- Example (delete when adding real entries)

### 2026-07-31 — llama-swap warm-swap intermittently exceeds 2s SLO

- **Blocks:** Stage 1.7 lock-in gate for ADR-009
- **Symptom:** ~1 in 20 swaps take 2.4–3.1s; expected < 2s
- **Attempted fixes:** raised llama-swap process priority (no effect); pinned to CPU cores 0–3 (partial improvement)
- **Next investigation:** check VRAM fragmentation between swaps; measure PCIe bandwidth headroom
- **Related DEBUG_LOG search terms:** "warm-swap", "llama-swap", "SLO"

-->
