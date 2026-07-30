"""Tree-context rendering + token-budgeted binary search.

Pattern-vendor of upstream aider's ``RepoMap.to_tree`` /
``RepoMap.render_tree`` / ``RepoMap.get_ranked_tags_map_uncached``
(Apache-2.0, commit ``5dc9490bb35f``). Reimplemented from the
algorithm surface — no upstream source copied.

Public surface:

* :func:`render_repomap` — render a list of :class:`RankedTag` into a
  budget-fitted text tree.

Notes:

* Rendering uses :class:`grep_ast.TreeContext` to build per-file
  definition views. TreeContext is the same rendering primitive aider
  uses; it is Apache-2.0 licensed and comes from the ``grep-ast`` pip
  package we already vendor.
* Token counting is done via a caller-supplied ``token_counter``
  callable; the default is a simple whitespace-split approximation so
  callers with no LLM tokenizer available still get a sensible budget.
  Tektos will typically pass ``LLMPort.count_tokens`` in.
* The binary search widens or narrows the ranked-tag slice until the
  rendered tree fits within ``max_tokens`` (within a 15% tolerance —
  identical to upstream).
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from grep_ast import TreeContext

from .rank import RankedTag

__all__ = ["render_repomap", "default_token_counter"]

_LINE_TRUNC = 100  # chars — matches upstream aider's line truncation.
_OK_ERR = 0.15  # 15% token-budget tolerance.


def default_token_counter(text: str) -> int:
    """Cheap fallback token count: whitespace-split word count.

    Underestimates LLM-tokenizer counts by ~25% on English prose, so
    callers using this will produce slightly smaller-than-budget maps.
    That's the safe direction. For accurate counts pass an
    :meth:`LLMPort.count_tokens`-style callable.
    """
    return len(text.split())


def _render_tree_context(*, abs_fname: str, rel_fname: str,
                        lines: Sequence[int], code: str) -> str:
    """Render one file's tree context showing ``lines`` as points of interest."""
    if not code.endswith("\n"):
        code += "\n"
    context = TreeContext(
        rel_fname,
        code,
        color=False,
        line_number=False,
        child_context=False,
        last_line=False,
        margin=0,
        mark_lois=False,
        loi_pad=0,
        show_top_of_file_parent_scope=False,
    )
    context.lines_of_interest = set()
    context.add_lines_of_interest([ln for ln in lines if ln >= 0])
    context.add_context()
    return context.format()


def _to_tree(
    ranked: Sequence[RankedTag],
    *,
    repo_root: str,
    code_cache: dict[str, str],
) -> str:
    """Join per-file tree contexts into one repomap string."""
    if not ranked:
        return ""

    # Group def_tags by rel_fname, keeping only the def_tags themselves
    # (renderable). Line-only tags (files with no defs surfaced) still
    # get their filename echoed with an empty body.
    tags_by_file: dict[str, list[int]] = {}
    abs_by_rel: dict[str, str] = {}
    order: list[str] = []

    for rt in ranked:
        if rt.rel_fname not in tags_by_file:
            tags_by_file[rt.rel_fname] = []
            order.append(rt.rel_fname)
        for tag in rt.def_tags:
            tags_by_file[rt.rel_fname].append(tag.line)
            abs_by_rel[rt.rel_fname] = tag.fname

    output_parts: list[str] = []
    for rel in order:
        lines = tags_by_file[rel]
        abs_path = abs_by_rel.get(rel, os.path.join(repo_root, rel))
        if not lines:
            output_parts.append(f"\n{rel}\n")
            continue

        if rel not in code_cache:
            try:
                code_cache[rel] = Path(abs_path).read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError:
                output_parts.append(f"\n{rel}\n")
                continue

        try:
            body = _render_tree_context(
                abs_fname=abs_path,
                rel_fname=rel,
                lines=sorted(set(lines)),
                code=code_cache[rel],
            )
        except Exception:  # noqa: BLE001 — TreeContext can be brittle on odd files
            output_parts.append(f"\n{rel}\n")
            continue

        output_parts.append(f"\n{rel}:\n{body}")

    joined = "".join(output_parts)
    # Truncate long lines to keep minified files sane (upstream behavior).
    truncated = "\n".join(line[:_LINE_TRUNC] for line in joined.splitlines())
    return truncated + "\n" if truncated else ""


def render_repomap(
    ranked: Sequence[RankedTag],
    *,
    repo_root: str | os.PathLike[str],
    max_tokens: int,
    token_counter: Callable[[str], int] = default_token_counter,
) -> str:
    """Render ``ranked`` into a budget-fitted repomap text tree.

    Binary-search on the number of ranked tags included until the
    rendered tree's token count fits within ``max_tokens`` (or within
    ±15%). Empty input, or a budget that can't fit even the top-1
    entry, returns ``""``.

    Args:
        ranked: :class:`RankedTag` records sorted by rank desc.
        repo_root: Repo root — used to resolve absolute paths when
            :class:`RankedTag.def_tags` is empty (files that made the
            ranking cut but have no locatable def lines).
        max_tokens: Budget ceiling.
        token_counter: Callable that returns the token count for a
            string. Defaults to :func:`default_token_counter`.

    Returns:
        The rendered repomap as a single string (may be empty).
    """
    if not ranked or max_tokens <= 0:
        return ""

    root = str(Path(repo_root).resolve())
    code_cache: dict[str, str] = {}
    n = len(ranked)
    lower, upper = 0, n
    # Start estimate: upstream uses max_tokens // 25 as a first guess.
    middle = min(max(1, max_tokens // 25), n)
    best_tree = ""
    best_tokens = 0

    while lower <= upper:
        tree = _to_tree(ranked[:middle], repo_root=root, code_cache=code_cache)
        tokens = token_counter(tree)

        pct_err = abs(tokens - max_tokens) / max_tokens
        if (tokens <= max_tokens and tokens > best_tokens) or pct_err < _OK_ERR:
            best_tree = tree
            best_tokens = tokens
            if pct_err < _OK_ERR:
                break

        if tokens < max_tokens:
            lower = middle + 1
        else:
            upper = middle - 1
        middle = (lower + upper) // 2
        if middle < 0:
            break

    return best_tree
