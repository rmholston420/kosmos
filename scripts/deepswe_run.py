#!/usr/bin/env python3
"""scripts/deepswe_run.py — run the DeepSWE subset through Pier (Stage 3.9).

Reads the manifest, resolves each pinned task under
``<cache-dir>/<upstream_commit>/tasks/``, runs each task through
:func:`plugins.tektos.eval.run_pier_trial`, aggregates the outcomes
into a :class:`CorpusRunSummary`, and prints the aggregate JSON on
stdout. Does NOT touch MemoryPort at Stage 3.9 kickoff — the
MemoryPort-backed integration path is exercised by the fast unit tier
using a fake port, and by ``make deepswe-gate`` on Colossus once a
live MemoryPort adapter is wired for the kernel runner.

Usage:

    .venv/bin/python scripts/deepswe_run.py \\
        --cache-dir .eval-cache/deepswe \\
        --agent nop --env docker
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.tektos.eval import (  # noqa: E402
    PIER_DEFAULT_ENV,
    PIER_UPSTREAM_PYPI_VERSION,
    PierEnv,
    PierNotAvailableError,
    PierTrialFailure,
    run_pier_trial,
)
from plugins.tektos.eval.corpora.deepswe import (  # noqa: E402
    DEEPSWE_UPSTREAM_COMMIT,
    build_corpus_run_summary,
    load_deepswe_manifest,
    utc_now_iso,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="deepswe_run",
        description="Run the DeepSWE subset through Pier and print the aggregate.",
    )
    ap.add_argument(
        "--cache-dir",
        default=".eval-cache/deepswe",
        help="Cache root written by scripts/deepswe_fetch.py.",
    )
    ap.add_argument("--agent", default="nop", help="Pier agent name.")
    ap.add_argument(
        "--env",
        default=PIER_DEFAULT_ENV,
        choices=[env.value for env in PierEnv],
        help="Pier execution environment.",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on number of tasks (useful for smoke checks).",
    )
    return ap.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    corpus = load_deepswe_manifest()
    cache_root = Path(args.cache_dir).resolve()
    commit_dir = cache_root / DEEPSWE_UPSTREAM_COMMIT
    tasks_dir = commit_dir / "tasks"
    if not tasks_dir.is_dir():
        print(
            f"deepswe_run: task cache missing at {tasks_dir}. "
            "Run scripts/deepswe_fetch.py first.",
            file=sys.stderr,
        )
        return 2

    pier_env = PierEnv(args.env)
    entries = list(corpus.subset)
    if args.limit is not None:
        entries = entries[: max(0, args.limit)]

    started_at = utc_now_iso()
    task_ids: list[str] = []
    outcomes: list[str] = []

    for entry in entries:
        task_path = tasks_dir / entry.task_id
        try:
            verdict = await run_pier_trial(
                task_path,
                agent=args.agent,
                pier_env=pier_env,
            )
            outcomes.append(verdict.outcome.value)
        except PierNotAvailableError as exc:
            print(f"deepswe_run: {exc}", file=sys.stderr)
            return 2
        except PierTrialFailure as exc:
            print(f"deepswe_run: {entry.task_id} ERROR: {exc}", file=sys.stderr)
            outcomes.append("ERROR")
        task_ids.append(entry.task_id)

    finished_at = utc_now_iso()
    summary = build_corpus_run_summary(
        subset_task_ids=tuple(task_ids),
        outcomes=tuple(outcomes),
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_env=pier_env.value,
        started_at=started_at,
        finished_at=finished_at,
    )
    print(json.dumps(summary.to_attributes(), indent=2))
    return 0 if summary.n_pass == summary.n_total else 1


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    return asyncio.run(_run(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
