"""PageRank over the identifier reference graph.

Pattern-vendor of upstream aider's ``RepoMap.get_ranked_tags`` (Apache-2.0,
commit ``5dc9490bb35f``). Reimplemented from the algorithm surface — no
upstream source copied.

Algorithm:

1. Build a :class:`networkx.MultiDiGraph` whose nodes are relative file
   paths.
2. For each identifier that has both a definition and a reference,
   add edges from every referencing file to every defining file. Edge
   weight is scaled by:
   * ``x10`` if the identifier was explicitly mentioned by the caller.
   * ``x10`` if the identifier is snake_case/kebab-case/CamelCase and
     ``len(ident) >= 8`` (heuristic for "distinctive" symbols).
   * ``x0.1`` if the identifier starts with ``_`` (private-by-convention).
   * ``x0.1`` if the identifier is defined in more than 5 files (probably
     a generic name).
   * ``x50`` if the referencer is one of the caller's ``chat_fnames``
     (files under active focus).
   * Final weight is scaled by ``sqrt(num_refs)`` so high-frequency
     mentions don't dominate.
3. Add small self-edges for defs that never appear as refs (upstream
   tree-sitter 0.23.2 Ruby quirk workaround; harmless elsewhere).
4. Run :func:`networkx.pagerank` with a personalization vector biased
   toward ``chat_fnames`` and files mentioned by the caller.
5. Distribute each source node's rank across its out-edges to compute
   per-``(file, ident)`` scores, then sort and return
   :class:`RankedTag` records.

Ties are broken by ``(rank_desc, (fname, ident))`` — deterministic.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

import networkx as nx

from .tags import Tag

__all__ = ["RankedTag", "rank_tags"]


@dataclass(frozen=True, slots=True)
class RankedTag:
    """A file/identifier pair with its PageRank-derived score."""

    rel_fname: str
    ident: str
    rank: float
    def_tags: tuple[Tag, ...]


def _classify_ident(ident: str) -> tuple[bool, bool, bool]:
    """Return ``(is_snake, is_kebab, is_camel)`` heuristics."""
    is_snake = ("_" in ident) and any(c.isalpha() for c in ident)
    is_kebab = ("-" in ident) and any(c.isalpha() for c in ident)
    is_camel = any(c.isupper() for c in ident) and any(c.islower() for c in ident)
    return is_snake, is_kebab, is_camel


def rank_tags(
    tags_by_file: Mapping[str, Iterable[Tag]],
    *,
    chat_fnames: Iterable[str] = (),
    mentioned_idents: Iterable[str] = (),
) -> list[RankedTag]:
    """Compute per-``(file, ident)`` ranks over the tag corpus.

    Args:
        tags_by_file: Mapping of ``rel_fname`` to an iterable of
            :class:`Tag` records (both defs and refs).
        chat_fnames: Optional set of relative filenames the caller is
            actively focused on. Their edges get a x50 weight boost and
            they receive personalization mass.
        mentioned_idents: Optional set of identifier names mentioned
            explicitly by the caller. Edges targeting these idents get
            a x10 weight boost.

    Returns:
        List of :class:`RankedTag`, sorted by ``rank`` descending. Files
        that produced no ranked idents are omitted; callers that want
        an "all files" view should merge in the raw file list.
    """
    chat_set = frozenset(chat_fnames)
    mentioned_set = frozenset(mentioned_idents)

    defines: dict[str, set[str]] = defaultdict(set)
    references: dict[str, list[str]] = defaultdict(list)
    definitions: dict[tuple[str, str], set[Tag]] = defaultdict(set)

    all_files: set[str] = set()
    for rel_fname, tags in tags_by_file.items():
        all_files.add(rel_fname)
        for tag in tags:
            if tag.kind == "def":
                defines[tag.name].add(rel_fname)
                definitions[(rel_fname, tag.name)].add(tag)
            elif tag.kind == "ref":
                references[tag.name].append(rel_fname)

    # If no refs at all, fall back to defs-as-refs so PageRank has edges.
    if not references:
        references = {k: list(v) for k, v in defines.items()}

    idents = set(defines.keys()) & set(references.keys())

    graph: nx.MultiDiGraph = nx.MultiDiGraph()
    for fname in all_files:
        graph.add_node(fname)

    # Self-edges for orphaned defs (upstream quirk workaround).
    for ident, definers in defines.items():
        if ident in references:
            continue
        for definer in definers:
            graph.add_edge(definer, definer, weight=0.1, ident=ident)

    for ident in idents:
        definers = defines[ident]
        mul = 1.0
        is_snake, is_kebab, is_camel = _classify_ident(ident)
        if ident in mentioned_set:
            mul *= 10.0
        if (is_snake or is_kebab or is_camel) and len(ident) >= 8:
            mul *= 10.0
        if ident.startswith("_"):
            mul *= 0.1
        if len(defines[ident]) > 5:
            mul *= 0.1

        for referencer, num_refs in Counter(references[ident]).items():
            use_mul = mul
            if referencer in chat_set:
                use_mul *= 50.0
            # sqrt-dampen high-frequency mentions.
            damped = math.sqrt(num_refs)
            for definer in definers:
                graph.add_edge(
                    referencer, definer, weight=use_mul * damped, ident=ident
                )

    # Personalization: mass on chat files, else uniform.
    n = max(1, len(all_files))
    per_file = 100.0 / n
    personalization: dict[str, float] = {}
    for f in all_files:
        if f in chat_set:
            personalization[f] = per_file

    try:
        if personalization:
            ranked = nx.pagerank(
                graph,
                weight="weight",
                personalization=personalization,
                dangling=personalization,
            )
        else:
            ranked = nx.pagerank(graph, weight="weight")
    except ZeroDivisionError:
        try:
            ranked = nx.pagerank(graph, weight="weight")
        except ZeroDivisionError:
            return []

    # Distribute per-node rank across out-edges to get per-(file, ident) scores.
    ranked_definitions: dict[tuple[str, str], float] = defaultdict(float)
    for src in graph.nodes:
        src_rank = ranked.get(src, 0.0)
        out_edges = list(graph.out_edges(src, data=True))
        total_weight = sum(data["weight"] for _s, _d, data in out_edges)
        if total_weight <= 0:
            continue
        for _s, dst, data in out_edges:
            share = src_rank * data["weight"] / total_weight
            ranked_definitions[(dst, data["ident"])] += share

    # Sort deterministically: rank desc, then (fname, ident) asc.
    sorted_items = sorted(
        ranked_definitions.items(), key=lambda item: (-item[1], item[0])
    )

    results: list[RankedTag] = []
    for (fname, ident), rank in sorted_items:
        if fname in chat_set:
            continue
        def_tags = tuple(sorted(definitions.get((fname, ident), set()),
                                key=lambda t: (t.line, t.name)))
        results.append(RankedTag(rel_fname=fname, ident=ident, rank=rank,
                                 def_tags=def_tags))

    return results


def rank_files(ranked: Iterable[RankedTag]) -> list[tuple[str, float]]:
    """Aggregate per-``(file, ident)`` ranks into per-file totals.

    Returns list of ``(rel_fname, total_rank)`` sorted by rank desc.
    Useful for the per-file :class:`ports.memory.MemoryPort` writes.
    """
    totals: dict[str, float] = defaultdict(float)
    for rt in ranked:
        totals[rt.rel_fname] += rt.rank
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


# Re-export in the module __all__ for callers that want file totals.
__all__.append("rank_files")
