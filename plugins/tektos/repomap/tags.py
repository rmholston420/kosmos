"""Tree-sitter tag extraction — pattern-vendor of aider's tag scanner.

Extracts ``(definition, reference)`` tags from source files using
tree-sitter queries. Query files (``queries/<lang>-tags.scm``) are
verbatim from upstream aider (Apache-2.0); everything else in this
module is a reimplementation of aider's ``get_tags``/``get_tags_raw``
against the same Tree-sitter surface.

Caching:

* On-disk cache lives at ``<repo_root>/.kosmos.repomap.cache.v<N>/``
  where ``<N>`` is :data:`plugins.tektos.repomap.policy.REPOMAP_CACHE_VERSION`.
* Cache key is the absolute filename; cache value carries ``mtime``
  and a tuple of :class:`Tag` records.
* If ``diskcache`` raises :class:`sqlite3.DatabaseError` mid-run, we
  fall back to an in-memory dict for the remainder of the call, so a
  corrupt cache never breaks indexing.

Pygments fallback:

If a language's ``.scm`` query produces defs but no refs (e.g. some
C/C++ tag files), we backfill refs from Pygments ``Token.Name`` tokens
— identical to upstream aider's behavior. Line number is ``-1`` for
Pygments-derived refs since Pygments does not surface line info per
token.
"""

from __future__ import annotations

import os
import sqlite3
import warnings
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from diskcache import Cache

# Suppress the FutureWarning aider suppresses too (tree_sitter <-> tsl bridge).
warnings.simplefilter("ignore", category=FutureWarning)

from grep_ast.tsl import USING_TSL_PACK, get_language, get_parser  # noqa: E402
from grep_ast import filename_to_lang  # noqa: E402
from pygments.lexers import guess_lexer_for_filename  # noqa: E402
from pygments.token import Token  # noqa: E402
from tree_sitter import Query  # noqa: E402

from .policy import REPOMAP_CACHE_VERSION

__all__ = [
    "Tag",
    "TAGS_CACHE_DIRNAME",
    "SUPPORTED_LANGUAGES",
    "extract_tags",
    "iter_source_files",
]


TAGS_CACHE_DIRNAME: str = f".kosmos.repomap.cache.v{REPOMAP_CACHE_VERSION}"
"""On-disk tags cache directory name, placed under the repo root."""

_SQLITE_ERRORS: tuple[type[BaseException], ...] = (
    sqlite3.OperationalError,
    sqlite3.DatabaseError,
    OSError,
)

_QUERIES_DIR: Path = Path(__file__).parent / "queries"


def _supported_languages_from_queries() -> frozenset[str]:
    """Discover languages by scanning ``queries/*-tags.scm``."""
    if not _QUERIES_DIR.is_dir():
        return frozenset()
    langs = set()
    for p in _QUERIES_DIR.glob("*-tags.scm"):
        stem = p.name.removesuffix("-tags.scm")
        if stem:
            langs.add(stem)
    return frozenset(langs)


SUPPORTED_LANGUAGES: frozenset[str] = _supported_languages_from_queries()
"""Set of tree-sitter language names for which we ship tag queries.

Currently: ``python``, ``javascript``, ``typescript``, ``rust``, ``go``,
``bash``. Add more by dropping additional ``<lang>-tags.scm`` files into
:file:`queries/` (verbatim from upstream aider) and updating
:file:`queries/ATTRIBUTION.md`.
"""


@dataclass(frozen=True, slots=True)
class Tag:
    """A single definition or reference tag.

    Attributes:
        rel_fname: Path relative to the indexed repo root.
        fname: Absolute path on disk.
        name: Identifier name (function/class/variable/etc.).
        kind: ``"def"`` or ``"ref"``.
        line: 0-indexed source line, or ``-1`` for Pygments-derived refs.
    """

    rel_fname: str
    fname: str
    name: str
    kind: str
    line: int


def iter_source_files(
    repo_root: str | os.PathLike[str],
    *,
    languages: Iterable[str] | None = None,
) -> Iterator[str]:
    """Yield absolute paths of files under ``repo_root`` we can tag.

    Only files whose :func:`grep_ast.filename_to_lang` returns a
    language in :data:`SUPPORTED_LANGUAGES` (or the caller-supplied
    ``languages`` allowlist) are yielded. Symlinks are not followed.
    Hidden directories (``.git``, ``.venv``, ``__pycache__``, etc.) are
    skipped by name.

    Args:
        repo_root: Path to the repo root.
        languages: Optional restrictor. Defaults to
            :data:`SUPPORTED_LANGUAGES`.
    """
    allow = frozenset(languages) if languages else SUPPORTED_LANGUAGES
    root = Path(repo_root).resolve()
    skip_dirs = {".git", ".venv", "__pycache__", "node_modules", ".mypy_cache",
                 ".pytest_cache", ".ruff_cache", "dist", "build",
                 TAGS_CACHE_DIRNAME}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            abs_path = os.path.join(dirpath, fname)
            lang = filename_to_lang(abs_path)
            if lang and lang in allow:
                yield abs_path


def _load_cache(cache_dir: Path) -> Cache | dict[str, Any]:
    """Open the diskcache, falling back to an in-memory dict on error."""
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        return Cache(str(cache_dir))
    except _SQLITE_ERRORS:
        return {}


def _tag_from_capture(
    *, fname: str, rel_fname: str, name: str, kind: str, line: int
) -> Tag:
    return Tag(rel_fname=rel_fname, fname=fname, name=name, kind=kind, line=line)


def _run_query(query: Query, root_node: Any) -> dict[str, list[Any]]:
    """Run a tree-sitter Query and return ``{tag: [node, ...]}``.

    Handles the tree-sitter 0.23 → 0.24 API split (aider's own
    ``_run_captures`` compatibility shim, reimplemented).
    """
    if hasattr(query, "captures"):
        # Old API (tree-sitter <= 0.23).
        return query.captures(root_node)
    from tree_sitter import QueryCursor  # noqa: WPS433 — deferred import

    cursor = QueryCursor(query)
    return cursor.captures(root_node)


def _tags_from_source(
    *, fname: str, rel_fname: str, lang: str, code: str, query_scm: str
) -> list[Tag]:
    """Extract tags from a single file's source text.

    Runs the tree-sitter query, translates captures to :class:`Tag`
    records, and — if the query produced defs but no refs — backfills
    refs from Pygments (upstream aider's fallback).
    """
    language = get_language(lang)
    parser = get_parser(lang)
    tree = parser.parse(bytes(code, "utf-8"))
    captures = _run_query(Query(language, query_scm), tree.root_node)

    tags: list[Tag] = []
    saw_kinds: set[str] = set()
    for tag_name, nodes in captures.items():
        if tag_name.startswith("name.definition."):
            kind = "def"
        elif tag_name.startswith("name.reference."):
            kind = "ref"
        else:
            continue
        saw_kinds.add(kind)
        for node in nodes:
            tags.append(
                _tag_from_capture(
                    fname=fname,
                    rel_fname=rel_fname,
                    name=node.text.decode("utf-8", errors="replace"),
                    kind=kind,
                    line=node.start_point[0],
                )
            )

    # Pygments fallback for defs-only languages.
    if "def" in saw_kinds and "ref" not in saw_kinds:
        try:
            lexer = guess_lexer_for_filename(fname, code)
            for tok_type, tok_val in lexer.get_tokens(code):
                if tok_type in Token.Name:
                    tags.append(
                        _tag_from_capture(
                            fname=fname,
                            rel_fname=rel_fname,
                            name=tok_val,
                            kind="ref",
                            line=-1,
                        )
                    )
        except Exception:  # noqa: BLE001 — Pygments is best-effort
            pass

    return tags


def extract_tags(
    fname: str,
    *,
    repo_root: str | os.PathLike[str],
    cache: Cache | dict[str, Any] | None = None,
) -> list[Tag]:
    """Extract tags from ``fname``, using an on-disk cache keyed by mtime.

    Args:
        fname: Absolute path to the source file.
        repo_root: Absolute path to the repo root (used to compute
            ``rel_fname`` and to place the cache directory).
        cache: Optional pre-opened cache. If omitted, a diskcache is
            opened at ``<repo_root>/<TAGS_CACHE_DIRNAME>/`` and closed
            after this call. Caller-supplied caches are *not* closed
            here.

    Returns:
        List of :class:`Tag`. Empty if the language is unsupported,
        the file is unreadable, or tree-sitter produced no captures.

    Raises:
        FileNotFoundError: if ``fname`` does not exist.
    """
    root = Path(repo_root).resolve()
    abs_path = os.path.abspath(fname)
    try:
        mtime = os.path.getmtime(abs_path)
    except OSError as exc:
        raise FileNotFoundError(abs_path) from exc

    rel_fname = os.path.relpath(abs_path, root)
    lang = filename_to_lang(abs_path)
    if not lang or lang not in SUPPORTED_LANGUAGES:
        return []

    query_path = _QUERIES_DIR / f"{lang}-tags.scm"
    if not query_path.is_file():
        return []
    query_scm = query_path.read_text(encoding="utf-8")

    close_after = cache is None
    if cache is None:
        cache = _load_cache(root / TAGS_CACHE_DIRNAME)

    try:
        try:
            cached = cache.get(abs_path) if hasattr(cache, "get") else cache.get(abs_path)
        except _SQLITE_ERRORS:
            cached = None
        if cached is not None and cached.get("mtime") == mtime:
            return list(cached["data"])

        try:
            code = Path(abs_path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []

        tags = _tags_from_source(
            fname=abs_path,
            rel_fname=rel_fname,
            lang=lang,
            code=code,
            query_scm=query_scm,
        )
        try:
            cache[abs_path] = {"mtime": mtime, "data": tuple(tags)}
        except _SQLITE_ERRORS:
            pass
        return tags
    finally:
        if close_after and hasattr(cache, "close"):
            try:
                cache.close()
            except Exception:  # noqa: BLE001
                pass


assert USING_TSL_PACK, (
    "Kosmos Stage 3.3 assumes tree-sitter-language-pack is installed "
    "(REPOMAP_CACHE_VERSION=4 lock-in in ADR-038)."
)
