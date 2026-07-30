# Kosmos Session Handoff — 2026-07-29 21:37 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 1.5 complete → next is Stage 1.6 (VectorPort vs ResourcePort vs ObservabilityPort)
- **Plugin / kernel component:** Kernel · `ports/` + `adapters/`
- **Ports formalized:** SearchPort (Stage 1.1), LLMPort (Stage 1.2), EventBusPort (Stage 1.4), SecretsPort (Stage 1.5)
- **LLMPort adapters:** Ollama (Stage 1.1), llama-swap (Stage 1.3)
- **SearchPort adapters:** SearXNG (Stage 1.1)
- **EventBusPort adapters:** Valkey/Redis Streams (Stage 1.4)
- **SecretsPort adapters:** age-file (Stage 1.5, primary per ADR-024)

## Completed this session

- v25 bundle → public repo `rmholston420/kosmos` (`main`)
- Stage 0.1 monorepo skeleton
- 4 Perplexity Computer skills installed to user library
- **Stage 1.1** — Ollama + SearXNG consolidated; **ADR-021** Ratified v25
- **Stage 1.2** — LLMPort Protocol formalized; **ADR-022** Ratified v25 (surface expansion 3→10)
- **Stage 1.3** — llama-swap vendored as second LLMPort adapter; swappability proven
- **Stage 1.4** — EventBusPort + EventEnvelope + Valkey adapter; **ADR-023** Ratified v25 (envelope-first MVP, `ack` deferred)
- **Stage 1.5** — SecretsPort + SecretValue + age-file adapter; **ADR-024** Ratified v25 (age-file primary, Vault + `lease` deferred)
- **77/77 contract tests pass** (Ollama 12 + llama-swap 15 + SearXNG 8 + EventBus 19 + Secrets 23)
- Spec §4.1 amended four times (SearchPort added, LLMPort surface, EventBusPort surface, SecretsPort surface); Eleven ports total, four formalized
- PORTING_LEDGER: 8 VENDORED entries (Ollama, llama-swap, SearXNG, redis-py, Rigpa envelope pattern, pyrage, PyYAML, Rigpa age-secrets loader pattern)
- BUILD_LOG: 10 timestamped entries
- ADR-007 (events-only cross-plugin coupling) executable since Stage 1.4
- Local-first constraint held: no Vault, no cloud control planes; age-encrypted file backend matches donor Rigpa pattern

## Remaining before current Definition of Done (Stage 1.5)

- Push Stage 1.5 changes to `main` (pending — this session's final commit)
- Verify on Colossus (`git pull && pytest adapters/ ports/`)

## Open questions / awaiting user answer

- None for Stages 1.1 / 1.2 / 1.3 / 1.4 / 1.5
- **Stage 1.6 direction TBD.** Remaining unformalized ports from spec §4.1:
  - **VectorPort** (Qdrant) — needed before MemoryPort work in Stage 5+; can use `AgeFileSecretsAdapter` for any Qdrant API keys
  - **ResourcePort** (APEX priority-queue) — GPU scheduling; relevant once Tektos exists in Stage 2
  - **ObservabilityPort** (Langfuse + OpenTelemetry) — traces/scores/cost logging for every port call
  - **NotificationPort** — cross-plugin alerts
  - **DataPort** — JSON(-LD) canonical export
  - Recommendation: **ObservabilityPort next** — every port call already logged in ADR history should also be traceable at runtime; cheap to add now, expensive to retrofit; unblocks cost accounting for LLMPort work at Stage 2

## Exact next action

On Colossus:
```bash
cd ~/dev/kosmos
git pull origin main
source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate)
pip install -e '.[dev]' PyYAML
pytest adapters/ ports/ -v
```

Expect: `77 passed`. If green, confirm Stage 1.6 direction (ObservabilityPort recommended).
