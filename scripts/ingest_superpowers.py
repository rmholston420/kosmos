"""Superpowers KB ingest CLI (Stage 4.4 · ADR-049).

Regenerates
`adapters/memory/dozerdb/corpora/superpowers/fixtures/superpowers.jsonl`
from a pinned upstream commit SHA of `github.com/obra/superpowers`.

Not vendored code — this is workspace-local tooling. Superpowers's
Markdown content lands as data in the fixture; no upstream code is
imported at runtime.

Usage:
    # From a Colossus checkout of the upstream repo (fastest, no auth):
    python scripts/ingest_superpowers.py \\
        --source /path/to/superpowers-checkout \\
        --sha 44c9b2d6e889982ac18c27d05a19fefe335194e1

    # Or from GitHub via gh:
    python scripts/ingest_superpowers.py \\
        --sha 44c9b2d6e889982ac18c27d05a19fefe335194e1 \\
        --via gh

Each fixture record is one `.md` file under upstream `skills/`, emitted
as a `CorpusFact`-shaped JSON row:

    - event_id     — stable slug: `superpowers.<skill>.<basename-without-md>`
                     (e.g. `superpowers.test-driven-development.SKILL`)
    - subject      — `superpowers/<skill>` (the containing skill directory)
    - predicate    — `superpowers.skill.imported`
    - object       — path-relative-to-`skills/` (e.g.
                     `test-driven-development/SKILL.md`)
    - as_of        — commit-authored date (UTC)
    - provenance   — `superpowers@<SHA>:<path>`
    - confidence   — 1.0 (source-verified, MIT-licensed)
    - attributes   — { body, source_commit, license, upstream_url,
                       references (typed cross-refs to sibling files) }

The cross-reference edges (Q4 answer) are parsed from inline Markdown
links `[text](path)` in each body that resolve to another
`skills/*/*.md` file at the pinned SHA. Edges are stored inside the
record's attributes so no schema migration is needed. Corpus
construction expands them into `CorpusEdge`s at load time.

ADR-007 respected — this CLI never imports anything under `plugins/`.
ADR-008 respected — no Superpowers code enters `vendor/` or `adapters/`
package code; only Markdown content lands as fixture data.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "adapters"
    / "memory"
    / "dozerdb"
    / "corpora"
    / "superpowers"
    / "fixtures"
    / "superpowers.jsonl"
)

UPSTREAM_REPO = "obra/superpowers"
UPSTREAM_LICENSE = "MIT"
UPSTREAM_URL = "https://github.com/obra/superpowers"

# Match inline Markdown links: [text](target). Ignore reference-style,
# images, and code-fenced content (best-effort; full CommonMark parse
# is out of scope for a fixture builder).
_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")


@dataclass(frozen=True, slots=True)
class SkillFile:
    """One upstream .md file at the pinned SHA."""

    path: str  # relative to upstream repo root, e.g. `skills/foo/SKILL.md`
    skill: str  # `foo` (containing skill directory under skills/)
    basename: str  # `SKILL.md`
    body: str  # decoded UTF-8 file contents


def _slugify_basename(name: str) -> str:
    """Strip `.md` and normalize slashes for the event_id tail."""
    stem = name[:-3] if name.endswith(".md") else name
    return stem.replace("/", "-")


def _event_id(skill: str, subpath: str) -> str:
    """Stable id — matches provenance path for grep-ability."""
    return f"superpowers.{skill}.{_slugify_basename(subpath)}"


def _parse_references(body: str, current: SkillFile, all_paths: set[str]) -> list[dict]:
    """Extract inline links that resolve to another file at the same SHA.

    Returns a list of edge dicts:
        { "kind": "references",
          "target_path": "<skills/other/SKILL.md>",
          "target_event_id": "superpowers.other.SKILL",
          "anchor_text": "<link text>" }

    Only edges whose target resolves inside the fixture set are kept
    (otherwise they can't be verified at test time).
    """
    edges: list[dict] = []
    current_dir = Path(current.path).parent  # e.g. skills/foo
    seen: set[tuple[str, str]] = set()  # dedupe (target_path, anchor)
    for m in _LINK_RE.finditer(body):
        anchor, target = m.group(1).strip(), m.group(2).strip()
        # Strip URL fragments and query
        target = target.split("#", 1)[0].split("?", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        # Resolve target relative to current file's directory, without
        # touching the filesystem (we're operating on repo-relative paths).
        parts: list[str] = []
        for seg in (current_dir / target).parts:
            if seg == "..":
                if parts:
                    parts.pop()
            elif seg in (".", ""):
                continue
            else:
                parts.append(seg)
        rel = "/".join(parts)
        if not rel.startswith("skills/"):
            # Some Superpowers skills reference sibling repos or files
            # outside skills/; those aren't in our fixture set.
            continue
        if not rel.endswith(".md"):
            continue
        if rel == current.path:
            continue
        if rel not in all_paths:
            continue  # target isn't in the ingested set
        key = (rel, anchor)
        if key in seen:
            continue
        seen.add(key)
        # Recompute the target skill and basename
        target_parts = rel.split("/")
        # skills/<skill>/[optional subdirs...]/basename
        target_skill = target_parts[1]
        target_subpath = "/".join(target_parts[2:])
        edges.append({
            "kind": "references",
            "target_path": rel,
            "target_event_id": _event_id(target_skill, target_subpath),
            "anchor_text": anchor,
        })
    return edges


def _load_from_gh(sha: str) -> tuple[list[SkillFile], str]:
    """Load all skills/*.md files at the pinned SHA using `gh api`.

    Returns (files, commit_iso_date).
    """
    tree_raw = subprocess.check_output(
        ["gh", "api", f"repos/{UPSTREAM_REPO}/git/trees/{sha}?recursive=1"],
        text=True,
    )
    tree = json.loads(tree_raw)["tree"]
    paths = sorted(
        e["path"]
        for e in tree
        if e["path"].startswith("skills/") and e["path"].endswith(".md")
    )
    commit_raw = subprocess.check_output(
        ["gh", "api", f"repos/{UPSTREAM_REPO}/git/commits/{sha}"],
        text=True,
    )
    commit = json.loads(commit_raw)
    commit_iso = commit["author"]["date"]

    files: list[SkillFile] = []
    for p in paths:
        blob_raw = subprocess.check_output(
            ["gh", "api", f"repos/{UPSTREAM_REPO}/contents/{p}?ref={sha}"],
            text=True,
        )
        blob = json.loads(blob_raw)
        body = base64.b64decode(blob["content"]).decode("utf-8")
        parts = p.split("/")
        skill = parts[1]
        basename = "/".join(parts[2:])
        files.append(SkillFile(path=p, skill=skill, basename=basename, body=body))
    return files, commit_iso


def _load_from_checkout(source: Path, sha: str) -> tuple[list[SkillFile], str]:
    """Load all skills/*.md from a local upstream checkout at the pinned SHA."""
    # Verify SHA is present in the checkout
    subprocess.check_call(
        ["git", "-C", str(source), "cat-file", "-e", f"{sha}^{{commit}}"],
    )
    commit_iso = subprocess.check_output(
        ["git", "-C", str(source), "show", "-s", "--format=%aI", sha],
        text=True,
    ).strip()
    tree_out = subprocess.check_output(
        ["git", "-C", str(source), "ls-tree", "-r", "--name-only", sha, "skills/"],
        text=True,
    )
    paths = sorted(p for p in tree_out.splitlines() if p.endswith(".md"))
    files: list[SkillFile] = []
    for p in paths:
        body = subprocess.check_output(
            ["git", "-C", str(source), "show", f"{sha}:{p}"], text=True,
        )
        parts = p.split("/")
        skill = parts[1]
        basename = "/".join(parts[2:])
        files.append(SkillFile(path=p, skill=skill, basename=basename, body=body))
    return files, commit_iso


def _build_records(files: Iterable[SkillFile], sha: str, commit_iso: str) -> list[dict]:
    """Turn every file into a CorpusFact-shaped JSON row."""
    all_paths = {f.path for f in files}
    records: list[dict] = []
    for f in files:
        refs = _parse_references(f.body, f, all_paths)
        row = {
            "event_id": _event_id(f.skill, f.basename),
            "subject": f"superpowers/{f.skill}",
            "predicate": "superpowers.skill.imported",
            "object": f"{f.skill}/{f.basename}",
            "as_of": commit_iso,
            "provenance": f"superpowers@{sha}:{f.path}",
            "confidence": 1.0,
            "attributes": {
                "body": f.body,
                "source_commit": sha,
                "source_path": f.path,
                "license": UPSTREAM_LICENSE,
                "upstream_url": f"{UPSTREAM_URL}/blob/{sha}/{f.path}",
                "references": refs,
            },
        }
        records.append(row)
    return records


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingest Superpowers skills into Kosmos MemoryPort fixture.")
    p.add_argument("--sha", required=True, help="Pinned upstream commit SHA.")
    p.add_argument(
        "--via",
        choices=("gh", "checkout"),
        default="gh",
        help="How to fetch files: `gh api` (default, needs network + gh auth) or local checkout via --source.",
    )
    p.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Local upstream checkout path when --via=checkout.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=FIXTURE_PATH,
        help=f"Output JSONL path (default: {FIXTURE_PATH}).",
    )
    args = p.parse_args(argv)

    if args.via == "checkout":
        if args.source is None:
            p.error("--via=checkout requires --source /path/to/upstream")
        files, commit_iso = _load_from_checkout(args.source, args.sha)
    else:
        files, commit_iso = _load_from_gh(args.sha)

    if not files:
        print(f"error: no skills/*.md files found at {args.sha}", file=sys.stderr)
        return 2

    records = _build_records(files, args.sha, commit_iso)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fh:
        for row in records:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    edge_count = sum(len(r["attributes"]["references"]) for r in records)
    print(
        f"wrote {len(records)} records ({edge_count} typed cross-reference edges) "
        f"to {args.output} @ {args.sha[:12]}"
    )
    # Silence lint for unused import in narrow paths.
    _ = datetime, timezone
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
