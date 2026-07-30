# ADR: Gnosis-Humanities Scope Assignment — Gnoma Feature Absorption

## Status
Proposed (requires Tier-2 ADR ratification per Kosmos v20 ADR practice)

## Context
Gnoma's build spec contains several fully-designed capabilities with no current home in Kosmos's plugin roadmap. Kosmos v20 already reserves "Gnosis-humanities" as a distinct domain plugin in Rollout Plan Phase 6, built only after the substrate is stable. This ADR assigns Gnoma's five orphaned feature clusters to Gnosis-humanities rather than to core Gnosis, keeping core Gnosis minimal (provenance, MemoryPort, DozerDB graph, canonical export) per the v20 Build Philosophy's "generalize on demand" principle.

## Decision
Gnoma's OCR, translation, pose-comparison, paper-discovery, and spatio-temporal capabilities are assigned to **Gnosis-humanities**, consuming core Gnosis's MemoryPort/VectorPort/DataPort contracts rather than duplicating storage.

## Feature Assignment

| Gnoma Capability | Gnosis-Humanities Module | Kosmos Port Dependencies |
|---|---|---|
| Tibetan OCR (buda-base/tibetan-ocr-app) | `ocr_tibetan/` | MemoryPort (text.extracted → episodic), EventBusPort |
| Sanskrit OCR (ihdia/sanskrit-ocr, pe-ocr-sanskrit) | `ocr_sanskrit/` | MemoryPort, EventBusPort |
| Chinese OCR (Kraken-based CHAT_models) | `ocr_chinese/` | MemoryPort, EventBusPort |
| Translation (MITRA) | `translation/` | LLMPort, EventBusPort (consumes text.extracted, emits text.translated) |
| OCR-triptych UI (image/transcription/translation sync view) | `ui/ocr-triptych/` | FrontendContractPort |
| Pose comparison (MediaPipe Pose + joint-angle cosine similarity) | `pose_comparison/` | VectorPort (embedding storage), MemoryPort (posture as :Thing node) |
| Pose-compare UI (skeleton overlay + heatmap) | `ui/pose-compare-view/` | FrontendContractPort |
| Paper discovery (llm-rss + OpenAlex/Semantic Scholar/arXiv) | `paper_discovery/` | EventBusPort (emits document.uploaded), scheduled via kernel routines engine |
| Spatio-temporal query engine | `spatio_temporal/` | MemoryPort (queries Place/TimeSpan on core Gnosis's CIDOC CRM graph — no schema migration needed) |
| Map view (OpenHistoricalMap) | `ui/map-view/` | FrontendContractPort |
| Timeline view (vis-timeline) | `ui/timeline/` | FrontendContractPort |
| Three-way cross-highlighting (graph↔timeline↔map) | `ui/` (shared state) | FrontendContractPort |

## Explicitly Excluded from This Assignment
The following Gnoma capabilities remain with **core Gnosis** (not Gnosis-humanities), since they are general-purpose rather than humanities-specific, consistent with what Kosmos v20 already names as deferred core-Gnosis work:

- LightRAG knowledge graph + RAG
- Auto-growing wiki (axiom_wiki)
- Entity resolution/deduplication (0.95/0.85 threshold blocking)
- Source-quality scoring (OpenAlex + Credibility-style heuristics)
- Distillation/summarization (map-reduce, structx, PaperQA2)
- 5W1H event-extraction pipeline (Actor/Place/TimeSpan/Event/Thing mapping) — this is the CIDOC CRM population mechanism itself and must live in core Gnosis since every plugin's events flow through it, not just humanities data

## Rationale
1. **Domain-plugin sizing discipline**: Kosmos caps every plugin at "a scope one builder can own end-to-end." Bundling Tibetan/Sanskrit/Chinese OCR, translation, pose comparison, paper discovery, and spatio-temporal UI into core Gnosis would violate that discipline; Gnosis-humanities absorbs the domain-specific load instead.
2. **Events-only coupling (ADR-007)**: Gnosis-humanities never imports Gnosis's package directly — it calls MemoryPort/VectorPort/EventBusPort exactly as Tektos does, preserving the ports-and-adapters mandate.
3. **Dependency ordering already supports this**: Rollout Plan Phase 6 places domain plugins including Gnosis-humanities only after core substrate (Gnosis, Praxis, Zetesis) is proven, so Gnosis-humanities can safely depend on core Gnosis's CIDOC CRM graph without re-deriving it.
4. **No schema migration required**: Because core Gnosis's CIDOC CRM contracts (Actor/Place/TimeSpan/Event/Thing) are already 5W1H-native from Phase 1, Gnosis-humanities's spatio-temporal and pose-comparison features (each a :Thing subtype) can query the existing graph directly.

## Build-Order Placement
Per Rollout Plan Phase 6, Gnosis-humanities is sequenced after Praxis, Zetesis, Koinonia, Synedrion, and Phrouros, alongside Poros/Nomisma/Hygieia, since "domain plugins should come only after the substrate is stable." No change to that sequencing is proposed here — this ADR only fixes *what* Gnosis-humanities builds when its turn arrives, closing the gap where Gnoma's features had no assigned owner.

## Definition of Done
- Gnosis-humanities `manifest.toml` declares dependencies on MemoryPort, VectorPort, EventBusPort, LLMPort, FrontendContractPort — no plugin-local kernel substitutes, matching the Tektos precedent.
- All three OCR engines, translation, pose comparison, paper discovery, and spatio-temporal query/UI modules are named explicitly in the Gnosis-humanities scope entry of PORT_CONTRACTS.md.
- A fixture Tibetan colophon OCR run, a fixture pose-comparison pair, and a fixture paper-discovery cycle each write through MemoryPort with correct provenance and PII classification tags, verified against Agent Memory Guard.
- Rollout Plan Phase 6 entry for Gnosis-humanities is amended to reference this ADR as its scope definition.
