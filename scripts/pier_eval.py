#!/usr/bin/env python3
"""scripts/pier_eval.py — Pier eval-harness CLI wrapper (Stage 3.8, ADR-042).

Runs one Harbor task through Pier and records the trial verdict in the
Kosmos MemoryPort (or a stdout-only mode for smoke checks). This is the
kernel-side companion to :mod:`plugins.tektos.eval.harness`.

Usage:

    .venv/bin/python scripts/pier_eval.py \\
        --task plugins/tektos/eval/tasks/tektos-plan-execution-smoke \\
        --agent nop --env docker --stdout

    .venv/bin/python scripts/pier_eval.py \\
        --task path/to/task --agent claude-code --env docker \\
        --change-id add-dark-mode  # writes into MemoryPort

The default mode (``--stdout``) never touches MemoryPort — it prints
the verdict JSON on stdout so ``make eval-gate`` can smoke-check the
wiring without a live MemoryPort adapter.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from plugins.tektos.eval import (  # noqa: E402
    PIER_DEFAULT_ENV,
    PierEnv,
    PierNotAvailableError,
    PierTrialFailure,
    run_and_record_trial,
    run_pier_trial,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="pier_eval",
        description="Run a Harbor task through Pier and record the verdict.",
    )
    ap.add_argument(
        "--task",
        required=True,
        help="Path to a Harbor task directory (containing task.toml).",
    )
    ap.add_argument("--agent", default="nop", help="Pier agent name.")
    ap.add_argument(
        "--env",
        default=PIER_DEFAULT_ENV,
        choices=[env.value for env in PierEnv],
        help="Pier execution environment.",
    )
    ap.add_argument(
        "--stdout",
        action="store_true",
        default=True,
        help=(
            "Print verdict JSON on stdout. Default at Stage 3.8 — the "
            "MemoryPort adapter is wired via plugins, not this CLI."
        ),
    )
    ap.add_argument(
        "--change-id",
        default=None,
        help="Optional OpenSpec change_id to cross-reference in the verdict.",
    )
    ap.add_argument(
        "--jobs-root",
        default=None,
        help="Directory Pier writes trial artifacts to (default: tempdir).",
    )
    ap.add_argument(
        "--trial-id",
        default=None,
        help="Optional caller-provided trial id (default: uuid4-derived).",
    )
    return ap.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    pier_env = PierEnv(args.env)
    _ = args.change_id  # accepted for forward compat; the CLI does not
    # write into MemoryPort at Stage 3.8 (see :mod:`plugins.tektos.eval`
    # `run_and_record_trial` for the in-process integration path).
    try:
        verdict = await run_pier_trial(
            args.task,
            agent=args.agent,
            pier_env=pier_env,
            jobs_root=args.jobs_root,
            trial_id=args.trial_id,
        )
    except PierNotAvailableError as exc:
        print(f"pier_eval: {exc}", file=sys.stderr)
        return 2
    except PierTrialFailure as exc:
        payload: dict[str, Any] = {"error": str(exc), "outcome": "ERROR"}
        print(json.dumps(payload, indent=2))
        return 1
    print(json.dumps(verdict.to_attributes(), indent=2))
    return 0 if verdict.outcome.value == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    return asyncio.run(_run(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
