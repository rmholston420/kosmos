# Kosmos Session Handoff — 2026-07-29 21:34 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 1.4 complete → next is Stage 1.5 (per sequence — VectorPort/Qdrant OR SecretsPort/Vault, whichever the sequence puts next)
- **Plugin / kernel component:** Kernel · `ports/` + `adapters/`
- **Ports formalized:** LLMPort (Stage 1.2), SearchPort (Stage 1.1), EventBusPort (Stage 1.4)
- **LLMPort adapters:** Ollama (Stage 1.1), llama-swap (Stage 1.3) — both isinstance-check against LLMPort
- **SearchPort adapters:** SearXNG (Stage 1.1)
- **EventBusPort adapters:** Valkey/Redis Streams (Stage 1.4)

## Completed this session

- v25 bundle → public repo `rmholston420/kosmos` (`main`)
- Stage 0.1 monorepo skeleton
- 4 Perplexity Computer skills installed to user library
- **Stage 1.1** — Ollama (3→1) + SearXNG (2→1) consolidated
- **ADR-021** Ratified v25 — SearchPort as 11th port
- **Stage 1.2** — `ports/llm.py` LLMPort Protocol formalized
- **ADR-022** Ratified v25 — LLMPort surface expansion (3→10 methods, spec §4.1 amended)
- **Stage 1.3** — llama-swap vendored as second LLMPort adapter; swappability proven
- **Stage 1.4** — `ports/event_bus.py` + `ports/event_envelope.py` formalized; Valkey adapter with in-memory fake
- **ADR-023** Ratified v25 — EventBusPort envelope-first MVP (spec §4.1 amended); consumer-group `ack` deferred to future ADR-024 (MUST land before Stage 2 Tektos out-of-process consumers)
- **54/54 contract tests pass** (Ollama 12 + llama-swap 15 + SearXNG 8 + EventBus 19)
- Spec §4.1 amended twice (LLMPort surface, EventBusPort surface); Ten→Eleven ports
- PORTING_LEDGER: 5 VENDORED entries (Ollama, llama-swap, SearXNG, redis-py, Rigpa envelope pattern)
- BUILD_LOG: 8 timestamped entries
- ADR-007 (events-only cross-plugin coupling) is executable for the first time

## Remaining before current Definition of Done (Stage 1.4)

- Push Stage 1.4 changes to `main` (pending — this session's final commit)
- Verify on Colossus (`git pull && pytest adapters/ ports/`)

## Open questions / awaiting user answer

- None for Stages 1.1 / 1.2 / 1.3 / 1.4
- **Stage 1.5 direction TBD:** which port next?
  - **SecretsPort** (Vault/hvac) — small; unblocks any adapter needing a secret
  - **VectorPort** (Qdrant) — needed before memory subsystem work in Stage 5+
  - **ResourcePort** (APEX priority-queue) — needed before Colossus GPU scheduling (relevant once Tektos exists)
  - Recommendation: **SecretsPort** — smallest and unblocks the others; also unblocks any future connector needing credentials

## Exact next action

On Colossus:
```bash
cd ~/dev/kosmos
git pull origin main
source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate)
pip install -e '.[dev]'
pytest adapters/ ports/ -v
```

Expect: `54 passed`. If green, confirm Stage 1.5 direction (SecretsPort recommended).
