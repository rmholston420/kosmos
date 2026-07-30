#!/usr/bin/env python3
"""scripts/deepswe_fetch.py — hydrate the DeepSWE corpus into ``.eval-cache/``.

Manifest-only vendoring per ADR-007-DeepSWE STATUS AMENDMENT 2026-07-30:
this script pulls the DeepSWE task directories for the pinned subset
from the upstream commit into a local cache directory that the real
Pier tier reads from. The cache is git-ignored; the manifest is the
authoritative record.

Usage:

    .venv/bin/python scripts/deepswe_fetch.py \\
        --cache-dir .eval-cache/deepswe

Idempotent: re-runs are no-ops when every subset task already exists
under ``<cache-dir>/<upstream_commit>/tasks/<task_id>/``.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.tektos.eval.corpora.deepswe import (  # noqa: E402
    DEEPSWE_UPSTREAM_COMMIT,
    DEEPSWE_UPSTREAM_REPO,
    load_deepswe_manifest,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="deepswe_fetch",
        description="Hydrate the DeepSWE corpus subset into a local cache.",
    )
    ap.add_argument(
        "--cache-dir",
        default=".eval-cache/deepswe",
        help="Cache root (default: .eval-cache/deepswe).",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Re-clone even when the pinned commit is already present.",
    )
    return ap.parse_args(argv)


def _git(args: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(["git", *args], check=True, cwd=cwd)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    corpus = load_deepswe_manifest()

    cache_root = Path(args.cache_dir).resolve()
    commit_dir = cache_root / DEEPSWE_UPSTREAM_COMMIT
    tasks_dir = commit_dir / "tasks"

    if tasks_dir.is_dir() and not args.force:
        missing = [
            entry.task_id
            for entry in corpus.subset
            if not (tasks_dir / entry.task_id / "task.toml").is_file()
        ]
        if not missing:
            print(f"deepswe_fetch: cache hit at {commit_dir}", file=sys.stderr)
            return 0
        print(
            f"deepswe_fetch: cache incomplete — refetching (missing: {missing})",
            file=sys.stderr,
        )
        shutil.rmtree(commit_dir)

    commit_dir.parent.mkdir(parents=True, exist_ok=True)
    if commit_dir.exists() and args.force:
        shutil.rmtree(commit_dir)

    print(
        f"deepswe_fetch: cloning {DEEPSWE_UPSTREAM_REPO} @ {DEEPSWE_UPSTREAM_COMMIT}",
        file=sys.stderr,
    )
    _git(["clone", "--filter=blob:none", "--no-checkout", DEEPSWE_UPSTREAM_REPO, str(commit_dir)])
    _git(["-C", str(commit_dir), "checkout", DEEPSWE_UPSTREAM_COMMIT])

    # Verify every subset task is present.
    missing = [
        entry.task_id
        for entry in corpus.subset
        if not (tasks_dir / entry.task_id / "task.toml").is_file()
    ]
    if missing:
        print(
            f"deepswe_fetch: FATAL — pinned commit is missing subset tasks: {missing}",
            file=sys.stderr,
        )
        return 1
    print(f"deepswe_fetch: hydrated {len(corpus.subset)} tasks in {commit_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
