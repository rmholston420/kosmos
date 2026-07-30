# Kosmos ops compose files

Docker Compose files for local development backing services on Colossus.
Single-user, local-first — do not lift these into a cloud control plane
without redoing the auth/secrets story.

## memory.yml — DozerDB (MemoryPort backing service)

Bring up:

```bash
docker compose -f ops/compose/memory.yml up -d
```

Wait for health:

```bash
docker compose -f ops/compose/memory.yml ps
# Look for kosmos-dozerdb ... (healthy)
```

Bolt endpoint: `bolt://localhost:7687`
HTTP browser: `http://localhost:7474`
User: `neo4j`
Password: `kosmos-dev-password` (dev default; change before any
non-single-user deployment)

### Environment variables

The env-gated contract tests + the Gnosis corpus runner honor:

| Variable | Default | Meaning |
| --- | --- | --- |
| `KOSMOS_STAGE_42_LIVE` | *(unset)* | Set to `1` to enable live-tier tests + target this compose service |
| `MEMORY_BOLT_URI` | `bolt://localhost:7687` | DozerDB Bolt endpoint |
| `MEMORY_BOLT_USER` | `neo4j` | Bolt user |
| `MEMORY_BOLT_PASSWORD` | `kosmos-dev-password` | Bolt password |
| `OLLAMA_URL` | `http://localhost:11434/v1` | Ollama OpenAI-compatible endpoint |
| `OLLAMA_LLM_MODEL` | `qwen3-coder` | Model Graphiti uses for entity extraction |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model Graphiti uses for embeddings |

### First-time embedder pull

`nomic-embed-text` must exist locally before the live tier runs, else the
first `record_event` will pause for the model pull:

```bash
ollama pull nomic-embed-text
```

### Teardown

```bash
docker compose -f ops/compose/memory.yml down          # stop + remove containers
docker compose -f ops/compose/memory.yml down --volumes # also wipe data volumes
```
