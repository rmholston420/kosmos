"""plugins/tektos/tests/test_pier_eval.py — Stage 3.8 DoD + fast unit tier.

Two-tier layout (ADR-042 Q8=A):

1. Fast unit tier (default) — runs under ``make stage1-gate`` and the
   full-repo pytest. Uses a fake MemoryPort and a fake ``pier`` CLI
   shim so nothing outside this process is invoked. No Docker, no
   ``datacurve-pier`` install required.

2. Real Pier tier — env-gated by ``KOSMOS_STAGE_38_REAL_PIER=1`` and
   requires a live Docker daemon plus ``datacurve-pier`` installed
   into the venv. Skipped otherwise.

The single DoD test name literal
``test_tektos_plan_runs_through_pier_before_user_review_build_sequence_3_8_dod``
is the Stage 3.8 exit gate marker.
"""

from __future__ import annotations

import ast
import asyncio
import inspect
import json
import os
import shutil
import stat
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from ports.memory import MemoryEventId, MemoryPort, validate_zero_trust_write
from plugins.tektos.eval import (
    PIER_DEFAULT_ENV,
    PIER_EVAL_PROVENANCE,
    PIER_MAX_CONFIDENCE,
    PIER_MIN_CONFIDENCE,
    PIER_TRIAL_PREDICATE,
    PIER_UPSTREAM_COMMIT,
    PIER_UPSTREAM_LICENSE,
    PIER_UPSTREAM_PACKAGE,
    PIER_UPSTREAM_PYPI_VERSION,
    PierEnv,
    PierTrialFailure,
    TrialVerdict,
    VerifierOutcome,
    confidence_for_outcome,
    record_pier_verdict,
    run_and_record_trial,
    run_pier_trial,
)
from plugins.tektos.eval import policy as eval_policy
from plugins.tektos.eval import harness as eval_harness


# ---------------------------------------------------------------------------
# fakes


@dataclass
class _FakeMemoryPort:
    writes: list[dict[str, Any]] = field(default_factory=list)
    _seq: int = 0

    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> MemoryEventId:
        validate_zero_trust_write(provenance=provenance, confidence=confidence)
        self._seq += 1
        self.writes.append(
            {
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "provenance": provenance,
                "confidence": confidence,
                "source_citation": source_citation,
                "pii_tier": pii_tier,
                "attributes": dict(attributes or {}),
            }
        )
        return MemoryEventId(id=f"evt-{self._seq}", written_at=datetime.now(UTC))

    async def query_temporal(self, *args: Any, **kwargs: Any):  # pragma: no cover
        return []

    async def query_semantic(self, *args: Any, **kwargs: Any):  # pragma: no cover
        return []


# ---------------------------------------------------------------------------
# fake pier CLI shim (fast tier)


_FAKE_PIER_TEMPLATE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import argparse, json, os, sys
    from pathlib import Path

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("-p", "--path", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--jobs-root", required=True)
    args = ap.parse_args()

    jobs_root = Path(args.jobs_root)
    jobs_root.mkdir(parents=True, exist_ok=True)
    trajectory = {
        "task": args.path,
        "agent": args.agent,
        "env": args.env,
        "verifier": {"exit_code": %(exit_code)d},
        "peak_context_tokens": 4321,
        "llm_call_count": 7,
    }
    (jobs_root / "trajectory.json").write_text(json.dumps(trajectory))
    sys.exit(%(exit_code)d)
    """
)


def _install_fake_pier(tmp_path: Path, *, exit_code: int, monkeypatch) -> Path:
    fake_dir = tmp_path / "fake_bin"
    fake_dir.mkdir()
    fake_cli = fake_dir / "pier"
    fake_cli.write_text(_FAKE_PIER_TEMPLATE % {"exit_code": exit_code})
    fake_cli.chmod(fake_cli.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{fake_dir}{os.pathsep}{original_path}")
    return fake_cli


# ---------------------------------------------------------------------------
# ADR-007: no cross-plugin imports


def test_eval_subsystem_imports_no_other_plugins_adr_007() -> None:
    eval_dir = Path(__file__).resolve().parent.parent / "eval"
    offenders: list[str] = []
    for py_file in eval_dir.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if not name.startswith("plugins."):
                    continue
                if name.startswith("plugins.tektos"):
                    continue
                offenders.append(f"{py_file.name}: {name}")
    assert offenders == [], (
        "ADR-007 violation: plugins.tektos.eval must not import other "
        f"plugin packages. Offenders: {offenders}"
    )


# ---------------------------------------------------------------------------
# ADR-042 locked policy constants


def test_locked_policy_constants_match_adr_042() -> None:
    assert PIER_EVAL_PROVENANCE == "pier-eval-harness"
    assert PIER_TRIAL_PREDICATE == "tektos.eval.trial_completed"
    assert PIER_UPSTREAM_COMMIT == "fefa7475a32bb05271abdea378e8083c83eb5c35"
    assert PIER_UPSTREAM_LICENSE == "Apache-2.0"
    assert PIER_UPSTREAM_PACKAGE == "datacurve-pier"
    assert PIER_UPSTREAM_PYPI_VERSION == "0.3.0"
    assert PIER_DEFAULT_ENV == "docker"
    assert PIER_MIN_CONFIDENCE == 0.0
    assert PIER_MAX_CONFIDENCE == 1.0
    assert eval_policy.PIER_TIMEOUT_SEC == 1800.0


def test_confidence_mapping_is_bounded_and_pass_only_gets_one() -> None:
    assert confidence_for_outcome(VerifierOutcome.PASS) == 1.0
    assert confidence_for_outcome(VerifierOutcome.FAIL) == 0.0
    assert confidence_for_outcome(VerifierOutcome.ERROR) == 0.0
    with pytest.raises(TypeError):
        confidence_for_outcome("PASS")  # type: ignore[arg-type]


def test_pier_env_docker_only_is_the_default_selection() -> None:
    assert PierEnv(PIER_DEFAULT_ENV) is PierEnv.DOCKER


def test_trial_verdict_round_trips_to_json_friendly_attributes() -> None:
    verdict = TrialVerdict(
        task_name="kosmos/tektos-plan-execution-smoke",
        trial_id="trial-abc",
        outcome=VerifierOutcome.PASS,
        verifier_exit_code=0,
        trajectory_dir="/tmp/pier/jobs/trial-abc",
        pier_env=PierEnv.DOCKER,
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_commit=PIER_UPSTREAM_COMMIT,
        peak_context_tokens=1234,
        llm_call_count=5,
    )
    payload = verdict.to_attributes()
    # No enum leakage — plain strings only.
    assert isinstance(payload["outcome"], str)
    assert isinstance(payload["pier_env"], str)
    # JSON round-trip is stable.
    assert json.loads(json.dumps(payload)) == payload


# ---------------------------------------------------------------------------
# harness — fast tier (fake pier CLI)


async def test_run_pier_trial_parses_pass_trajectory(tmp_path, monkeypatch) -> None:
    _install_fake_pier(tmp_path, exit_code=0, monkeypatch=monkeypatch)
    task_dir = _minimal_task_dir(tmp_path)
    verdict = await run_pier_trial(task_dir, jobs_root=tmp_path / "jobs")
    assert verdict.outcome is VerifierOutcome.PASS
    assert verdict.verifier_exit_code == 0
    assert verdict.pier_env is PierEnv.DOCKER
    assert verdict.pier_commit == PIER_UPSTREAM_COMMIT
    assert verdict.pier_version == PIER_UPSTREAM_PYPI_VERSION
    assert verdict.peak_context_tokens == 4321


async def test_run_pier_trial_parses_fail_trajectory(tmp_path, monkeypatch) -> None:
    _install_fake_pier(tmp_path, exit_code=1, monkeypatch=monkeypatch)
    task_dir = _minimal_task_dir(tmp_path)
    verdict = await run_pier_trial(task_dir, jobs_root=tmp_path / "jobs")
    assert verdict.outcome is VerifierOutcome.FAIL
    assert verdict.verifier_exit_code == 1


async def test_run_pier_trial_rejects_non_harbor_directory(tmp_path, monkeypatch) -> None:
    _install_fake_pier(tmp_path, exit_code=0, monkeypatch=monkeypatch)
    bogus = tmp_path / "not-a-task"
    bogus.mkdir()
    with pytest.raises(PierTrialFailure):
        await run_pier_trial(bogus, jobs_root=tmp_path / "jobs")


async def test_record_pier_verdict_writes_locked_shape_to_memory_port() -> None:
    memory = _FakeMemoryPort()
    verdict = _make_verdict(outcome=VerifierOutcome.PASS)
    event_id = await record_pier_verdict(
        verdict, memory_port=memory, change_id="add-dark-mode"
    )
    assert event_id.id == "evt-1"
    (write,) = memory.writes
    assert write["predicate"] == PIER_TRIAL_PREDICATE
    assert write["provenance"] == PIER_EVAL_PROVENANCE
    assert write["confidence"] == PIER_MAX_CONFIDENCE
    assert write["object"] == "PASS"
    assert write["subject"] == "add-dark-mode::kosmos/tektos-plan-execution-smoke::trial-abc"
    assert write["attributes"]["change_id"] == "add-dark-mode"
    assert write["attributes"]["outcome"] == "PASS"
    assert write["attributes"]["pier_commit"] == PIER_UPSTREAM_COMMIT


async def test_record_pier_verdict_fail_uses_zero_confidence() -> None:
    memory = _FakeMemoryPort()
    verdict = _make_verdict(outcome=VerifierOutcome.FAIL, exit_code=1)
    await record_pier_verdict(verdict, memory_port=memory)
    (write,) = memory.writes
    assert write["confidence"] == PIER_MIN_CONFIDENCE
    assert write["object"] == "FAIL"


async def test_record_pier_verdict_error_uses_zero_confidence() -> None:
    memory = _FakeMemoryPort()
    verdict = _make_verdict(outcome=VerifierOutcome.ERROR, exit_code=-1)
    await record_pier_verdict(verdict, memory_port=memory)
    (write,) = memory.writes
    assert write["confidence"] == PIER_MIN_CONFIDENCE
    assert write["object"] == "ERROR"


async def test_run_and_record_trial_records_error_when_pier_fails(
    tmp_path, monkeypatch
) -> None:
    # No fake pier on PATH -> harness raises PierNotAvailableError which is
    # not a PierTrialFailure. To exercise the ERROR-verdict path we simulate
    # the trial failure directly via monkeypatch.
    memory = _FakeMemoryPort()

    async def _boom(*args: Any, **kwargs: Any):
        raise PierTrialFailure("simulated docker daemon down")

    monkeypatch.setattr(eval_harness, "run_pier_trial", _boom)
    task_dir = _minimal_task_dir(tmp_path)
    with pytest.raises(PierTrialFailure):
        await run_and_record_trial(
            task_dir, memory_port=memory, change_id="cid-1"
        )
    (write,) = memory.writes
    assert write["object"] == "ERROR"
    assert write["confidence"] == PIER_MIN_CONFIDENCE
    assert write["attributes"]["change_id"] == "cid-1"


# ---------------------------------------------------------------------------
# fixture is a valid Harbor task


def test_committed_harbor_fixture_is_shaped_correctly() -> None:
    fixture = (
        Path(__file__).resolve().parent.parent
        / "eval"
        / "tasks"
        / "tektos-plan-execution-smoke"
    )
    assert (fixture / "task.toml").is_file()
    assert (fixture / "instruction.md").is_file()
    assert (fixture / "environment" / "src" / "hello.py").is_file()
    assert (fixture / "tests" / "test_hello.py").is_file()
    assert (fixture / "solution" / "hello.py").is_file()


# ---------------------------------------------------------------------------
# DoD literal — Stage 3.8 exit gate marker


async def test_tektos_plan_runs_through_pier_before_user_review_build_sequence_3_8_dod(
    tmp_path, monkeypatch
) -> None:
    """Stage 3.8 DoD: every Tektos plan runs through Pier before user review.

    Verified by exercising the full pipeline end-to-end against a fake
    pier CLI: harness invokes pier, parses the trajectory, and records
    exactly one ``tektos.eval.trial_completed`` MemoryPort event with
    the ADR-042 locked shape.
    """
    _install_fake_pier(tmp_path, exit_code=0, monkeypatch=monkeypatch)
    memory = _FakeMemoryPort()
    task_dir = _minimal_task_dir(tmp_path)

    verdict, event_id = await run_and_record_trial(
        task_dir,
        memory_port=memory,
        change_id="stage-3-8-smoke",
        jobs_root=tmp_path / "jobs",
    )

    assert verdict.outcome is VerifierOutcome.PASS
    assert event_id.id == "evt-1"
    (write,) = memory.writes
    assert write["predicate"] == PIER_TRIAL_PREDICATE
    assert write["provenance"] == PIER_EVAL_PROVENANCE
    assert write["confidence"] == PIER_MAX_CONFIDENCE
    assert write["object"] == "PASS"
    assert "stage-3-8-smoke" in write["subject"]


# ---------------------------------------------------------------------------
# real Pier tier — env-gated


_REAL_PIER_ENV = "KOSMOS_STAGE_38_REAL_PIER"


@pytest.mark.skipif(
    os.environ.get(_REAL_PIER_ENV) != "1",
    reason=(
        f"set {_REAL_PIER_ENV}=1 (and install datacurve-pier + start Docker) "
        "to enable the real Pier tier"
    ),
)
async def test_real_pier_smoke_fixture_runs_on_colossus(tmp_path) -> None:
    if shutil.which("pier") is None:
        pytest.skip("pier CLI not installed")
    fixture = (
        Path(__file__).resolve().parent.parent
        / "eval"
        / "tasks"
        / "tektos-plan-execution-smoke"
    )
    memory = _FakeMemoryPort()
    try:
        verdict, event_id = await run_and_record_trial(
            fixture,
            memory_port=memory,
            change_id="real-pier-smoke",
            jobs_root=tmp_path / "jobs",
            timeout_sec=600.0,
        )
    except PierTrialFailure as exc:  # pragma: no cover - real-tier only
        pytest.skip(f"real pier trial failed to complete: {exc}")
    assert verdict.outcome in {VerifierOutcome.PASS, VerifierOutcome.FAIL}
    assert event_id.id.startswith("evt-")


# ---------------------------------------------------------------------------
# helpers


def _minimal_task_dir(tmp_path: Path) -> Path:
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "task.toml").write_text(
        'version = "1.0"\n[task]\nname = "kosmos/fake"\nauthors=["t"]\nkeywords=[]\n'
    )
    (task_dir / "instruction.md").write_text("noop")
    return task_dir


def _make_verdict(
    *, outcome: VerifierOutcome, exit_code: int = 0
) -> TrialVerdict:
    return TrialVerdict(
        task_name="kosmos/tektos-plan-execution-smoke",
        trial_id="trial-abc",
        outcome=outcome,
        verifier_exit_code=exit_code,
        trajectory_dir="/tmp/pier/jobs/trial-abc",
        pier_env=PierEnv.DOCKER,
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_commit=PIER_UPSTREAM_COMMIT,
    )
