#!/usr/bin/env python3
"""Stage-3 exit gate (Build-Sequence §3.12 DoD).

Enforces the §3.12 criteria:

    1. BUILD_LOG.md has a Stage 3.12 entry with a valid EDT/EST timestamp.
    2. ``ruff check`` on the refactor target passes.
    3. ``bandit -q -r`` on the refactor target passes.
    4. Full pytest suite runs green (Stage 3.12 DoD literal is inside it).
    5. The refactor commit (identified by its marker string in ``git log``)
       is present in the current branch history.

Exit code 0 on pass, 1 on any failure.

Run directly (``python scripts/stage3_gate.py``) or via ``make stage3-gate``.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Refactor target locked in ADR-046 (Q1=A).
REFACTOR_TARGET = "plugins/tektos/ui/templates.py"

# Marker string that must appear in the refactor commit message body
# (Q6=A · two-commit shape). ``scripts/stage3_gate.py`` scans ``git log``
# for this substring to identify the refactor commit.
REFACTOR_COMMIT_MARKER = "Stage 3.12 · Tektos refactor · extract-method"

# DoD literal test node id (Q10=A).
DOD_LITERAL_NODEID = (
    "plugins/tektos/tests/test_stage_3_12_exit_gate.py::"
    "test_tektos_refactors_real_kosmos_file_end_to_end_"
    "passes_ruff_bandit_pytest_build_sequence_3_12_dod"
)

BUILD_LOG_STAGE_312_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2} E[DS]T) — Stage 3\.12",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


class GateReport:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks: list[str] = []

    def ok(self, msg: str) -> None:
        self.checks.append(f"  ✔ {msg}")

    def fail(self, msg: str) -> None:
        self.failures.append(f"  ✘ {msg}")

    def section(self, title: str) -> None:
        self.checks.append(f"\n[{title}]")

    def render(self) -> str:
        out = "\n".join(self.checks)
        if self.failures:
            out += "\n\nFAILURES:\n" + "\n".join(self.failures)
        return out

    @property
    def passed(self) -> bool:
        return not self.failures


# ---------------------------------------------------------------------------
# Criterion 1 — BUILD_LOG has Stage 3.12 entry
# ---------------------------------------------------------------------------


def check_build_log(report: GateReport) -> None:
    report.section("1. BUILD_LOG.md — Stage 3.12 entry present")
    path = ROOT / "BUILD_LOG.md"
    if not path.exists():
        report.fail("BUILD_LOG.md missing at repo root")
        return
    text = path.read_text(encoding="utf-8")
    matches = BUILD_LOG_STAGE_312_RE.findall(text)
    if not matches:
        report.fail("no BUILD_LOG entry for Stage 3.12")
        return
    for ts in matches:
        report.ok(f"Stage 3.12 — {ts}")


# ---------------------------------------------------------------------------
# Criterion 2 — ruff check on the refactor target
# ---------------------------------------------------------------------------


def check_ruff(report: GateReport) -> None:
    report.section(f"2. ruff check {REFACTOR_TARGET}")
    ruff = ROOT / ".venv" / "bin" / "ruff"
    if not ruff.exists():
        report.fail(f"venv ruff not found at {ruff}")
        return
    proc = subprocess.run(  # noqa: S603
        [str(ruff), "check", REFACTOR_TARGET],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        report.fail(
            f"ruff failed (rc={proc.returncode}):\n{proc.stdout.strip()}\n"
            f"{proc.stderr.strip()}"
        )
    else:
        tail = proc.stdout.strip().splitlines()[-1:] or ["clean"]
        report.ok(f"ruff: {tail[-1]}")


# ---------------------------------------------------------------------------
# Criterion 3 — bandit on the refactor target
# ---------------------------------------------------------------------------


def check_bandit(report: GateReport) -> None:
    report.section(f"3. bandit -q -r {REFACTOR_TARGET}")
    bandit = ROOT / ".venv" / "bin" / "bandit"
    if not bandit.exists():
        report.fail(
            f"venv bandit not found at {bandit}; "
            "install via `.venv/bin/pip install -e '.[dev]'`"
        )
        return
    proc = subprocess.run(  # noqa: S603
        [
            str(bandit),
            "-q",
            "-c",
            "pyproject.toml",
            "-r",
            REFACTOR_TARGET,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        report.fail(
            f"bandit failed (rc={proc.returncode}):\n"
            f"{proc.stdout.strip()}\n{proc.stderr.strip()}"
        )
    else:
        report.ok(f"bandit: clean ({REFACTOR_TARGET})")


# ---------------------------------------------------------------------------
# Criterion 4 — full pytest suite green
# ---------------------------------------------------------------------------


def check_pytest(report: GateReport) -> None:
    report.section("4. Full pytest suite green (includes Stage 3.12 DoD literal)")
    python = ROOT / ".venv" / "bin" / "python"
    if not python.exists():
        report.fail(f"venv python not found at {python}")
        return
    proc = subprocess.run(  # noqa: S603
        [str(python), "-m", "pytest", "--tb=short", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    tail = proc.stdout.strip().splitlines()[-1:] or ["<no output>"]
    if proc.returncode != 0:
        report.fail(f"pytest failed (rc={proc.returncode}): {tail[-1]}")
    else:
        report.ok(f"pytest: {tail[-1]}")


# ---------------------------------------------------------------------------
# Criterion 5 — refactor commit present in git log
# ---------------------------------------------------------------------------


def check_refactor_commit(report: GateReport) -> None:
    report.section(
        f"5. Refactor commit present (marker: '{REFACTOR_COMMIT_MARKER}')"
    )
    git = ROOT / ".git"
    if not git.exists():
        report.fail(".git directory missing — not a git repository")
        return
    proc = subprocess.run(  # noqa: S603
        [
            "git",
            "log",
            "--oneline",
            "--grep",
            REFACTOR_COMMIT_MARKER,
            "-n",
            "5",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        report.fail(
            f"git log failed (rc={proc.returncode}): {proc.stderr.strip()}"
        )
        return
    hits = [line for line in proc.stdout.splitlines() if line.strip()]
    if not hits:
        report.fail(
            f"no commit found matching marker {REFACTOR_COMMIT_MARKER!r}"
        )
        return
    for line in hits:
        report.ok(f"commit: {line}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    report = GateReport()
    print("Kosmos Stage-3 exit gate — Build-Sequence §3.12 DoD")
    print("=" * 60)
    print(f"Refactor target : {REFACTOR_TARGET}")
    print(f"DoD literal     : {DOD_LITERAL_NODEID}")
    print(f"Commit marker   : {REFACTOR_COMMIT_MARKER}")
    check_build_log(report)
    check_ruff(report)
    check_bandit(report)
    check_pytest(report)
    check_refactor_commit(report)
    print(report.render())
    print("\n" + "=" * 60)
    if report.passed:
        print("STAGE 3 EXIT GATE: PASS")
        return 0
    print(f"STAGE 3 EXIT GATE: FAIL ({len(report.failures)} failure(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())
