#!/usr/bin/env python3
"""Stage-1 exit gate (Build-Sequence §1.15 DoD).

Enforces the four §1.15 criteria in order:

    1. All eleven ports have a module in ``ports/`` and a working
       adapter package under ``adapters/`` with a ``test_contract.py``.
    2. All ADR statuses are ``Ratified``/``Locked``/``Ratified v25``/``Superseded``.
       (ADR-010 landed LOCKED on 2026-07-30 after the Stage 6.2 head-to-head;
       no ADR-010 OPEN exception is honored anymore.)
    3. ``BUILD_LOG.md`` has an entry per Stage-1 sub-stage (1.1–1.14).
    4. The full port contract suite runs green.

Exit code 0 on pass, 1 on any failure.

Run directly (``python scripts/stage1_gate.py``) or via
``make stage1-gate``.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# The eleven Stage-1 ports (spec §4.1). §1.13 slot absorbed by §1.11.
PORTS: dict[str, str] = {
    "search": "1.1",
    "llm": "1.2",
    "secrets": "1.5",
    "event_bus": "1.4",
    "observability": "1.6",
    "vector": "1.7",
    "memory": "1.8",
    "data": "1.10",
    "resource": "1.11",
    "notification": "1.12",
    "frontend_contract": "1.14",
}

# ADR-010 landed LOCKED on 2026-07-30 (Stage 6.2 head-to-head resolved).
# No ADR is permitted OPEN at Stage-1 exit anymore (spec §17).
OPEN_ADR = None

RATIFIED_MARKERS = (
    "Ratified v25",
    "Ratified",
    "Locked",
    "LOCKED",
    # A superseded ADR is a legitimate terminal state — its authoritative
    # successor is what carries the current decision. The audit trail is
    # preserved in the amended file.
    "Superseded",
)

# Build-Sequence sub-stages that must have BUILD_LOG timestamps.
SUBSTAGES = [
    "1.1",
    "1.2",
    "1.3",
    "1.4",
    "1.5",
    "1.6",
    "1.7",
    "1.8",
    "1.10",
    "1.11",
    "1.12",
    "1.14",
]

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
# Criterion 1 — eleven ports + adapters + contract tests
# ---------------------------------------------------------------------------


def check_ports(report: GateReport) -> None:
    report.section(f"1. Eleven ports have working adapters ({len(PORTS)} expected)")
    for port, stage in PORTS.items():
        port_module = ROOT / "ports" / f"{port}.py"
        adapter_pkg = ROOT / "adapters" / port
        if not port_module.exists():
            report.fail(f"port module missing: ports/{port}.py (Stage {stage})")
            continue
        report.ok(f"ports/{port}.py (Stage {stage})")

        if not adapter_pkg.is_dir():
            report.fail(f"adapter package missing: adapters/{port}/")
            continue

        contract_tests = list(adapter_pkg.rglob("test_contract.py"))
        if not contract_tests:
            report.fail(f"no test_contract.py under adapters/{port}/")
            continue
        report.ok(
            f"adapters/{port}/ ({len(contract_tests)} contract-test file(s))"
        )


# ---------------------------------------------------------------------------
# Criterion 2 — ADR status audit
# ---------------------------------------------------------------------------


ADR_README_ROW_RE = re.compile(
    r"^\|\s*ADR-(\d{3})\s*\|\s*`?([^|`]+?)`?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$",
    re.MULTILINE,
)


def check_adrs(report: GateReport) -> None:
    """Audit adrs/README.md summary table — the load-bearing status source."""
    report.section("2. ADR statuses — all Ratified/Locked/Superseded (no ADRs OPEN post-2026-07-30)")
    adr_dir = ROOT / "docs" / "adrs"
    if not adr_dir.is_dir():
        report.fail("docs/adrs/ directory missing")
        return
    readme_path = adr_dir / "README.md"
    if not readme_path.exists():
        report.fail("docs/adrs/README.md missing")
        return

    readme = readme_path.read_text(encoding="utf-8")
    rows = ADR_README_ROW_RE.findall(readme)
    if not rows:
        report.fail("adrs/README.md status table did not match expected shape")
        return

    checked = 0
    seen: set[str] = set()
    for adr_num, filename, _title, status_raw, _phase in rows:
        adr_id = f"ADR-{adr_num}"
        if adr_id in seen:
            continue  # dedupe if a row appears twice
        seen.add(adr_id)

        # Confirm the referenced ADR file exists.
        if not (adr_dir / filename.strip()).exists():
            report.fail(f"{adr_id}: README references missing file {filename!r}")
            continue

        status = status_raw.strip().replace("**", "")
        checked += 1

        if OPEN_ADR is not None and adr_id == OPEN_ADR:
            if "OPEN" not in status.upper():
                report.fail(f"{adr_id}: expected OPEN, got {status!r}")
            else:
                report.ok(f"{adr_id}: OPEN (deferred pre-Phase-6.2, expected)")
            continue

        if not any(marker in status for marker in RATIFIED_MARKERS):
            report.fail(f"{adr_id}: expected Ratified/Locked, got {status!r}")
        else:
            report.ok(f"{adr_id}: {status}")

    report.ok(f"{checked} ADR(s) audited via docs/adrs/README.md")


# ---------------------------------------------------------------------------
# Criterion 3 — BUILD_LOG has entry per sub-stage
# ---------------------------------------------------------------------------


BUILD_LOG_ENTRY_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2} E[DS]T) — Stage (\d+\.\d+)",
    re.MULTILINE,
)


def check_build_log(report: GateReport) -> None:
    report.section("3. BUILD_LOG.md — timestamped entry per Stage-1 sub-stage")
    path = ROOT / "BUILD_LOG.md"
    if not path.exists():
        report.fail("BUILD_LOG.md missing at repo root")
        return
    text = path.read_text(encoding="utf-8")
    entries = BUILD_LOG_ENTRY_RE.findall(text)
    stages_seen: dict[str, str] = {}
    for ts, stage in entries:
        stages_seen.setdefault(stage, ts)

    for sub in SUBSTAGES:
        if sub not in stages_seen:
            report.fail(f"no BUILD_LOG entry for Stage {sub}")
        else:
            report.ok(f"Stage {sub} — {stages_seen[sub]}")


# ---------------------------------------------------------------------------
# Criterion 4 — pytest suite green
# ---------------------------------------------------------------------------


def check_pytest(report: GateReport) -> None:
    report.section("4. Full port contract suite green")
    python = ROOT / ".venv" / "bin" / "python"
    if not python.exists():
        report.fail(f"venv python not found at {python}")
        return
    proc = subprocess.run(
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
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    report = GateReport()
    print("Kosmos Stage-1 exit gate — Build-Sequence §1.15 DoD")
    print("=" * 60)
    check_ports(report)
    check_adrs(report)
    check_build_log(report)
    check_pytest(report)
    print(report.render())
    print("\n" + "=" * 60)
    if report.passed:
        print("STAGE 1 EXIT GATE: PASS")
        return 0
    print(f"STAGE 1 EXIT GATE: FAIL ({len(report.failures)} failure(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())
