"""Public repomap indexing facade + :class:`ports.memory.MemoryPort` wiring.

Stage 3.3 · ADR-038. Ties together:

* :mod:`plugins.tektos.repomap.tags` — tree-sitter tag extraction.
* :mod:`plugins.tektos.repomap.rank` — NetworkX PageRank over refs.
* :mod:`plugins.tektos.repomap.render` — token-budgeted tree rendering.
* :mod:`plugins.tektos.repomap.policy` — locked constants + freshness.

Writes to MemoryPort (both per-run):

1. **Per-file** with predicate :data:`REPOMAP_INDEXED_PREDICATE`:
   - ``subject`` = ``rel_fname``
   - ``predicate`` = ``"tektos.repomap.indexed"``
   - ``object`` = ``f"rank={total_rank:.6f}"``
   - ``provenance`` = ``"aider-repomap"``
   - ``confidence`` = :func:`compute_freshness_confidence`
   - ``attributes`` = ``{def_count, ref_count, rank, mtime_epoch, mtime_iso, language, top_idents}``

2. **Per-run snapshot** with predicate :data:`REPOMAP_SNAPSHOT_PREDICATE`:
   - ``subject`` = repo root abs path
   - ``predicate`` = ``"tektos.repomap.snapshot"``
   - ``object`` = ``f"files={total_files} idents={total_idents} tokens={rendered_tokens}"``
   - ``provenance`` = ``"aider-repomap"``
   - ``confidence`` = mean per-file freshness (clamped to
     :data:`REPOMAP_MIN_CONFIDENCE` floor)
   - ``attributes`` = ``{total_files, total_idents, top_files, rendered_map, cache_version, index_started_epoch, index_completed_epoch}``

All writes go through :meth:`ports.memory.MemoryPort.write_event`; the
port's zero-trust guard is authoritative — we never bypass it.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from diskcache import Cache
from grep_ast import filename_to_lang

from ports.memory import MemoryPort

from .policy import (
    REPOMAP_DEFAULT_MAP_TOKENS,
    REPOMAP_INDEXED_PREDICATE,
    REPOMAP_MIN_CONFIDENCE,
    REPOMAP_PROVENANCE,
    REPOMAP_SNAPSHOT_PREDICATE,
    REPOMAP_CACHE_VERSION,
    compute_freshness_confidence,
)
from .rank import RankedTag, rank_files, rank_tags
from .render import default_token_counter, render_repomap
from .tags import TAGS_CACHE_DIRNAME, Tag, extract_tags, iter_source_files

__all__ = ["RepoMapResult", "index"]


@dataclass(frozen=True, slots=True)
class RepoMapResult:
    """Return value of :func:`index`.

    Attributes:
        repo_root: Absolute path of the indexed repo.
        files_indexed: Number of files that produced at least one tag.
        idents_ranked: Number of ``(file, ident)`` pairs the ranker
            produced.
        rendered_map: The final budget-fitted text repomap.
        rendered_tokens: Token count of :attr:`rendered_map` per the
            supplied ``token_counter``.
        top_files: List of ``(rel_fname, aggregated_rank)`` sorted desc.
        per_file_event_ids: :class:`MemoryPort` event IDs for the
            per-file writes, keyed by ``rel_fname``.
        snapshot_event_id: :class:`MemoryPort` event ID of the run
            snapshot.
        elapsed_seconds: Wall-clock duration of :func:`index`.
    """

    repo_root: str
    files_indexed: int
    idents_ranked: int
    rendered_map: str
    rendered_tokens: int
    top_files: tuple[tuple[str, float], ...]
    per_file_event_ids: dict[str, str]
    snapshot_event_id: str
    elapsed_seconds: float


def _summarize_file_tags(tags: Iterable[Tag]) -> tuple[int, int]:
    """Return ``(def_count, ref_count)`` for a file's tags."""
    defs = refs = 0
    for t in tags:
        if t.kind == "def":
            defs += 1
        elif t.kind == "ref":
            refs += 1
    return defs, refs


async def index(
    repo_root: str | os.PathLike[str],
    *,
    memory: MemoryPort,
    max_map_tokens: int = REPOMAP_DEFAULT_MAP_TOKENS,
    languages: Iterable[str] | None = None,
    token_counter: Callable[[str], int] = default_token_counter,
    chat_fnames: Iterable[str] = (),
    mentioned_idents: Iterable[str] = (),
    now_epoch: float | None = None,
    top_k_files: int = 32,
    top_k_idents_per_file: int = 8,
) -> RepoMapResult:
    """Index ``repo_root``, write to MemoryPort, return the result.

    Args:
        repo_root: Path to the repo to index.
        memory: A :class:`ports.memory.MemoryPort` implementation.
        max_map_tokens: Budget for the rendered repomap.
        languages: Optional language allowlist (default: all supported).
        token_counter: Optional token counter (default: whitespace-split
            fallback).
        chat_fnames: Optional focused-file bias for the ranker.
        mentioned_idents: Optional identifier bias for the ranker.
        now_epoch: Reference "now" for freshness. Defaults to
            :func:`time.time`. Pass explicitly in tests for determinism.
        top_k_files: How many files to include in the snapshot's
            ``top_files`` attribute.
        top_k_idents_per_file: How many top idents to summarize per
            per-file attribute payload.

    Returns:
        :class:`RepoMapResult`.
    """
    started = time.time()
    if now_epoch is None:
        now_epoch = started
    root = Path(repo_root).resolve()
    root_str = str(root)

    # 1. Walk + extract tags.
    tags_by_file: dict[str, list[Tag]] = {}
    abs_by_rel: dict[str, str] = {}
    lang_by_rel: dict[str, str] = {}
    cache = Cache(str(root / TAGS_CACHE_DIRNAME))
    try:
        for abs_path in iter_source_files(root, languages=languages):
            rel = os.path.relpath(abs_path, root_str)
            tags = extract_tags(abs_path, repo_root=root_str, cache=cache)
            if not tags:
                continue
            tags_by_file[rel] = tags
            abs_by_rel[rel] = abs_path
            lang_by_rel[rel] = filename_to_lang(abs_path) or "unknown"
    finally:
        try:
            cache.close()
        except Exception:  # noqa: BLE001
            pass

    # 2. Rank.
    ranked = rank_tags(
        tags_by_file,
        chat_fnames=chat_fnames,
        mentioned_idents=mentioned_idents,
    )

    # 3. Render.
    rendered = render_repomap(
        ranked,
        repo_root=root_str,
        max_tokens=max_map_tokens,
        token_counter=token_counter,
    )
    rendered_tokens = token_counter(rendered) if rendered else 0

    # 4. Per-file aggregates for MemoryPort attributes.
    per_file_file_rank = dict(rank_files(ranked))
    per_file_top_idents: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for rt in ranked:
        if len(per_file_top_idents[rt.rel_fname]) < top_k_idents_per_file:
            per_file_top_idents[rt.rel_fname].append((rt.ident, rt.rank))

    # 5. Per-file MemoryPort writes.
    per_file_event_ids: dict[str, str] = {}
    confidences: list[float] = []
    for rel_fname, tags in tags_by_file.items():
        abs_path = abs_by_rel[rel_fname]
        try:
            mtime = os.path.getmtime(abs_path)
        except OSError:
            mtime = now_epoch  # treat unstat'able files as "now"
        conf = compute_freshness_confidence(
            file_mtime_epoch=mtime, now_epoch=now_epoch
        )
        confidences.append(conf)
        def_count, ref_count = _summarize_file_tags(tags)
        total_rank = per_file_file_rank.get(rel_fname, 0.0)
        top_idents = per_file_top_idents.get(rel_fname, [])
        eid = await memory.write_event(
            subject=rel_fname,
            predicate=REPOMAP_INDEXED_PREDICATE,
            object=f"rank={total_rank:.6f}",
            provenance=REPOMAP_PROVENANCE,
            confidence=conf,
            attributes={
                "def_count": def_count,
                "ref_count": ref_count,
                "rank": total_rank,
                "mtime_epoch": mtime,
                "language": lang_by_rel.get(rel_fname, "unknown"),
                "top_idents": [{"ident": i, "rank": r} for i, r in top_idents],
                "cache_version": REPOMAP_CACHE_VERSION,
            },
        )
        per_file_event_ids[rel_fname] = str(eid.id)

    # 6. Snapshot write.
    mean_conf = (
        sum(confidences) / len(confidences) if confidences else REPOMAP_MIN_CONFIDENCE
    )
    mean_conf = max(REPOMAP_MIN_CONFIDENCE, min(1.0, mean_conf))
    top_files_sorted = sorted(
        per_file_file_rank.items(), key=lambda kv: (-kv[1], kv[0])
    )[:top_k_files]
    completed = time.time()
    snapshot_eid = await memory.write_event(
        subject=root_str,
        predicate=REPOMAP_SNAPSHOT_PREDICATE,
        object=(
            f"files={len(tags_by_file)} idents={len(ranked)} "
            f"tokens={rendered_tokens}"
        ),
        provenance=REPOMAP_PROVENANCE,
        confidence=mean_conf,
        attributes={
            "total_files": len(tags_by_file),
            "total_idents": len(ranked),
            "rendered_tokens": rendered_tokens,
            "top_files": [
                {"rel_fname": f, "rank": r} for f, r in top_files_sorted
            ],
            "rendered_map": rendered,
            "cache_version": REPOMAP_CACHE_VERSION,
            "index_started_epoch": started,
            "index_completed_epoch": completed,
        },
    )

    return RepoMapResult(
        repo_root=root_str,
        files_indexed=len(tags_by_file),
        idents_ranked=len(ranked),
        rendered_map=rendered,
        rendered_tokens=rendered_tokens,
        top_files=tuple(top_files_sorted),
        per_file_event_ids=per_file_event_ids,
        snapshot_event_id=str(snapshot_eid.id),
        elapsed_seconds=completed - started,
    )
