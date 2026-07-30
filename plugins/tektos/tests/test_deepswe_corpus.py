"""plugins/tektos/tests/test_deepswe_corpus.py — Stage 3.9 DoD + fast unit tier.

Two-tier layout (ADR-007-DeepSWE STATUS AMENDMENT 2026-07-30, Q5=A):

1. Fast unit tier (default) — runs under ``make stage1-gate`` and the
   full-repo pytest. Uses a fake MemoryPort and a fake ``pier`` CLI
   shim so nothing outside this process is invoked. No Docker, no
   ``datacurve-pier`` install, no network I/O required.

2. Real DeepSWE tier — env-gated by ``KOSMOS_STAGE_39_REAL_DEEPSWE=1``.
   Requires a live Docker daemon, ``datacurve-pier`` installed into
   the venv, and network access on the first fetch to hydrate
   ``.eval-cache/deepswe/``. Skipped otherwise.

The single DoD test name literal
``test_deepswe_subset_benchmark_run_recorded_build_sequence_3_9_dod``
is the Stage 3.9 exit gate marker.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import stat
import subprocess
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
    PIER_UPSTREAM_PYPI_VERSION,
    PierEnv,
    run_pier_trial,
)
from plugins.tektos.eval.corpora.deepswe import (
    DEEPSWE_CORPUS_NAME,
    DEEPSWE_CORPUS_RUN_PREDICATE,
    DEEPSWE_EVAL_PROVENANCE,
    DEEPSWE_MAX_CONFIDENCE,
    DEEPSWE_MIN_CONFIDENCE,
    DEEPSWE_PERMISSIVE_LICENSES,
    DEEPSWE_SAMPLE_SEED,
    DEEPSWE_SUBSET_SIZE,
    DEEPSWE_UPSTREAM_COMMIT,
    DEEPSWE_UPSTREAM_LICENSE,
    DEEPSWE_UPSTREAM_REPO,
    CorpusRunSummary,
    DeepSweCorpus,
    DeepSweManifestError,
    DeepSweSubsetEntry,
    build_corpus_run_summary,
    corpus_run_confidence,
    load_deepswe_manifest,
    record_corpus_run,
    utc_now_iso,
)
from plugins.tektos.eval.corpora.deepswe import policy as deepswe_policy


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
    import argparse, json, sys
    from pathlib import Path

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("-p", "--path", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--jobs-root", required=True)
    args = ap.parse_args()

    task_name = Path(args.path).name

    # Exit-code map so a single fake pier can drive PASS + FAIL in one run.
    task_map = %(task_map)r
    exit_code = task_map.get(task_name, 0)

    jobs_root = Path(args.jobs_root)
    jobs_root.mkdir(parents=True, exist_ok=True)
    trajectory = {
        "task": args.path,
        "agent": args.agent,
        "env": args.env,
        "verifier": {"exit_code": exit_code},
        "peak_context_tokens": 4321,
        "llm_call_count": 7,
    }
    (jobs_root / "trajectory.json").write_text(json.dumps(trajectory))
    sys.exit(exit_code)
    """
)


def _install_fake_pier(
    tmp_path: Path,
    *,
    task_map: dict[str, int],
    monkeypatch,
) -> Path:
    fake_dir = tmp_path / "fake_bin"
    fake_dir.mkdir()
    fake_cli = fake_dir / "pier"
    fake_cli.write_text(_FAKE_PIER_TEMPLATE % {"task_map": task_map})
    fake_cli.chmod(fake_cli.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{fake_dir}{os.pathsep}{original_path}")
    return fake_cli


def _write_harbor_stub(root: Path, task_id: str) -> Path:
    """Write a minimal Harbor-shaped task dir (task.toml + instruction)."""
    task_root = root / task_id
    task_root.mkdir(parents=True, exist_ok=True)
    (task_root / "task.toml").write_text(
        textwrap.dedent(
            f"""\
            [task]
            name = "deepswe/{task_id}"
            [metadata]
            task_id = "{task_id}"
            language = "python"
            """
        )
    )
    (task_root / "instruction.md").write_text("stub instruction\n")
    return task_root


# ---------------------------------------------------------------------------
# ADR-007: no cross-plugin imports


def test_deepswe_corpus_imports_no_other_plugins_adr_007() -> None:
    corpus_dir = Path(__file__).resolve().parent.parent / "eval" / "corpora"
    offenders: list[str] = []
    for py_file in corpus_dir.rglob("*.py"):
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
        "ADR-007 violation: plugins.tektos.eval.corpora must not import "
        f"other plugin packages. Offenders: {offenders}"
    )


# ---------------------------------------------------------------------------
# Locked policy constants (ADR-007-DeepSWE STATUS AMENDMENT 2026-07-30)


def test_locked_policy_constants_match_adr_007_deepswe() -> None:
    assert DEEPSWE_CORPUS_NAME == "deepswe"
    assert DEEPSWE_EVAL_PROVENANCE == "deepswe-eval-corpus"
    assert DEEPSWE_CORPUS_RUN_PREDICATE == "tektos.eval.corpus_run_completed"
    assert DEEPSWE_UPSTREAM_COMMIT == "e016041a6ccf8da29906afc9a3f5a8df940a1f78"
    assert DEEPSWE_UPSTREAM_REPO == "https://github.com/datacurve-ai/deep-swe"
    assert DEEPSWE_UPSTREAM_LICENSE == "Apache-2.0"
    assert DEEPSWE_SUBSET_SIZE == 5
    assert DEEPSWE_SAMPLE_SEED == 0
    assert DEEPSWE_MIN_CONFIDENCE == 0.0
    assert DEEPSWE_MAX_CONFIDENCE == 1.0
    assert "MIT" in DEEPSWE_PERMISSIVE_LICENSES
    assert "Apache-2.0" in DEEPSWE_PERMISSIVE_LICENSES
    assert "GPL-3.0" not in DEEPSWE_PERMISSIVE_LICENSES
    assert "AGPL-3.0" not in DEEPSWE_PERMISSIVE_LICENSES


def test_corpus_run_confidence_bounds_and_edge_cases() -> None:
    assert corpus_run_confidence(0, 0) == 0.0
    assert corpus_run_confidence(0, 5) == 0.0
    assert corpus_run_confidence(3, 5) == pytest.approx(0.6)
    assert corpus_run_confidence(5, 5) == 1.0
    with pytest.raises(TypeError):
        corpus_run_confidence(1.0, 5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        corpus_run_confidence(-1, 5)
    with pytest.raises(ValueError):
        corpus_run_confidence(6, 5)


# ---------------------------------------------------------------------------
# Manifest loader (fast, no I/O outside the manifest file)


def test_committed_manifest_loads_five_tasks_three_python_two_typescript() -> None:
    corpus = load_deepswe_manifest()
    assert corpus.upstream_commit == DEEPSWE_UPSTREAM_COMMIT
    assert corpus.upstream_repo == DEEPSWE_UPSTREAM_REPO
    assert corpus.upstream_license == DEEPSWE_UPSTREAM_LICENSE
    assert corpus.subset_size == DEEPSWE_SUBSET_SIZE
    assert len(corpus.subset) == DEEPSWE_SUBSET_SIZE
    langs = corpus.language_mix()
    assert langs == {"python": 3, "typescript": 2}


def test_manifest_every_subset_entry_has_permissive_spdx() -> None:
    corpus = load_deepswe_manifest()
    for entry in corpus.subset:
        assert entry.spdx_license in DEEPSWE_PERMISSIVE_LICENSES, (
            f"subset entry {entry.task_id!r} has non-permissive SPDX "
            f"{entry.spdx_license!r}"
        )


def test_manifest_subset_task_ids_are_unique_and_sorted_deterministically() -> None:
    corpus = load_deepswe_manifest()
    ids = [entry.task_id for entry in corpus.subset]
    assert len(set(ids)) == len(ids)
    # Deterministic pick order (Python first sorted, then TypeScript sorted).
    py_ids = [e.task_id for e in corpus.subset if e.language == "python"]
    ts_ids = [e.task_id for e in corpus.subset if e.language == "typescript"]
    assert py_ids == sorted(py_ids)
    assert ts_ids == sorted(ts_ids)


def test_manifest_loader_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(DeepSweManifestError, match="not found"):
        load_deepswe_manifest(tmp_path / "nope.toml")


def test_manifest_loader_rejects_copyleft_spdx(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        textwrap.dedent(
            f"""\
            [corpus]
            name = "deepswe"
            description = "test"
            upstream_repo = "{DEEPSWE_UPSTREAM_REPO}"
            upstream_commit = "{DEEPSWE_UPSTREAM_COMMIT}"
            upstream_license = "Apache-2.0"
            corpus_total_tasks = 113
            sample_seed = 0
            subset_size = 5

            [[subset]]
            task_id = "gpl-poisoned-task"
            language = "python"
            upstream_repo = "https://github.com/example/gpl"
            upstream_owner = "example"
            upstream_repo_name = "gpl"
            base_commit = "abc123"
            spdx_license = "GPL-3.0"

            [[subset]]
            task_id = "ok-1"
            language = "python"
            upstream_repo = "https://github.com/example/ok"
            upstream_owner = "example"
            upstream_repo_name = "ok"
            base_commit = "abc123"
            spdx_license = "MIT"

            [[subset]]
            task_id = "ok-2"
            language = "python"
            upstream_repo = "https://github.com/example/ok2"
            upstream_owner = "example"
            upstream_repo_name = "ok2"
            base_commit = "abc123"
            spdx_license = "MIT"

            [[subset]]
            task_id = "ok-3"
            language = "typescript"
            upstream_repo = "https://github.com/example/ok3"
            upstream_owner = "example"
            upstream_repo_name = "ok3"
            base_commit = "abc123"
            spdx_license = "MIT"

            [[subset]]
            task_id = "ok-4"
            language = "typescript"
            upstream_repo = "https://github.com/example/ok4"
            upstream_owner = "example"
            upstream_repo_name = "ok4"
            base_commit = "abc123"
            spdx_license = "MIT"
            """
        )
    )
    with pytest.raises(DeepSweManifestError, match="permissive allowlist"):
        load_deepswe_manifest(manifest_path)


def test_manifest_loader_rejects_subset_size_mismatch(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        textwrap.dedent(
            f"""\
            [corpus]
            name = "deepswe"
            description = "test"
            upstream_repo = "{DEEPSWE_UPSTREAM_REPO}"
            upstream_commit = "{DEEPSWE_UPSTREAM_COMMIT}"
            upstream_license = "Apache-2.0"
            corpus_total_tasks = 113
            sample_seed = 0
            subset_size = 5

            [[subset]]
            task_id = "just-one"
            language = "python"
            upstream_repo = "https://github.com/example/x"
            upstream_owner = "example"
            upstream_repo_name = "x"
            base_commit = "abc"
            spdx_license = "MIT"
            """
        )
    )
    with pytest.raises(DeepSweManifestError, match="does not match"):
        load_deepswe_manifest(manifest_path)


def test_manifest_loader_rejects_upstream_commit_mismatch(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.toml"
    manifest_path.write_text(
        textwrap.dedent(
            """\
            [corpus]
            name = "deepswe"
            description = "test"
            upstream_repo = "https://github.com/datacurve-ai/deep-swe"
            upstream_commit = "0000000000000000000000000000000000000000"
            upstream_license = "Apache-2.0"
            corpus_total_tasks = 113
            sample_seed = 0
            subset_size = 1

            [[subset]]
            task_id = "x"
            language = "python"
            upstream_repo = "https://github.com/example/x"
            upstream_owner = "example"
            upstream_repo_name = "x"
            base_commit = "abc"
            spdx_license = "MIT"
            """
        )
    )
    with pytest.raises(DeepSweManifestError, match="upstream_commit mismatch"):
        load_deepswe_manifest(manifest_path)


# ---------------------------------------------------------------------------
# CorpusRunSummary invariants


def test_build_corpus_run_summary_counts_outcomes_correctly() -> None:
    summary = build_corpus_run_summary(
        subset_task_ids=("a", "b", "c", "d", "e"),
        outcomes=("PASS", "PASS", "FAIL", "ERROR", "PASS"),
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_env="docker",
        started_at="2026-07-30T07:50:00+00:00",
        finished_at="2026-07-30T07:55:00+00:00",
    )
    assert summary.n_total == 5
    assert summary.n_pass == 3
    assert summary.n_fail == 1
    assert summary.n_error == 1
    assert summary.corpus == "deepswe"
    assert summary.upstream_commit == DEEPSWE_UPSTREAM_COMMIT


def test_build_corpus_run_summary_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError, match="length"):
        build_corpus_run_summary(
            subset_task_ids=("a", "b"),
            outcomes=("PASS",),
            pier_version=PIER_UPSTREAM_PYPI_VERSION,
            pier_env="docker",
            started_at="2026-07-30T07:50:00+00:00",
            finished_at="2026-07-30T07:55:00+00:00",
        )


def test_build_corpus_run_summary_rejects_unknown_verdict_string() -> None:
    with pytest.raises(ValueError, match="unknown verdict"):
        build_corpus_run_summary(
            subset_task_ids=("a",),
            outcomes=("PARTIAL",),
            pier_version=PIER_UPSTREAM_PYPI_VERSION,
            pier_env="docker",
            started_at="2026-07-30T07:50:00+00:00",
            finished_at="2026-07-30T07:55:00+00:00",
        )


def test_summary_round_trips_to_json_friendly_attributes() -> None:
    summary = build_corpus_run_summary(
        subset_task_ids=("a", "b"),
        outcomes=("PASS", "FAIL"),
        trial_event_ids=("evt-1", "evt-2"),
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_env="docker",
        started_at="2026-07-30T07:50:00+00:00",
        finished_at="2026-07-30T07:55:00+00:00",
        run_id="run-fixed",
    )
    attrs = summary.to_attributes()
    payload = json.dumps(attrs)
    round = json.loads(payload)
    assert round["run_id"] == "run-fixed"
    assert round["n_pass"] == 1
    assert round["n_fail"] == 1
    assert round["subset_task_ids"] == ["a", "b"]
    assert round["trial_event_ids"] == ["evt-1", "evt-2"]


# ---------------------------------------------------------------------------
# record_corpus_run locked write shape


@pytest.mark.asyncio
async def test_record_corpus_run_writes_locked_shape_to_memory_port() -> None:
    port = _FakeMemoryPort()
    summary = build_corpus_run_summary(
        subset_task_ids=("t-1", "t-2", "t-3"),
        outcomes=("PASS", "FAIL", "PASS"),
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_env="docker",
        started_at="2026-07-30T07:50:00+00:00",
        finished_at="2026-07-30T07:55:00+00:00",
        run_id="run-locked",
    )
    event_id = await record_corpus_run(summary, memory_port=port)
    assert event_id.id.startswith("evt-")
    assert len(port.writes) == 1
    w = port.writes[0]
    assert w["predicate"] == DEEPSWE_CORPUS_RUN_PREDICATE
    assert w["provenance"] == DEEPSWE_EVAL_PROVENANCE
    assert w["subject"] == f"deepswe::{DEEPSWE_UPSTREAM_COMMIT}::0::run-locked"
    assert w["object"] == "2/3"
    assert w["confidence"] == pytest.approx(2 / 3)
    assert w["attributes"]["run_id"] == "run-locked"
    assert w["attributes"]["subset_task_ids"] == ["t-1", "t-2", "t-3"]


@pytest.mark.asyncio
async def test_record_corpus_run_all_pass_gets_max_confidence() -> None:
    port = _FakeMemoryPort()
    summary = build_corpus_run_summary(
        subset_task_ids=("t-1", "t-2"),
        outcomes=("PASS", "PASS"),
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_env="docker",
        started_at="2026-07-30T07:50:00+00:00",
        finished_at="2026-07-30T07:55:00+00:00",
    )
    await record_corpus_run(summary, memory_port=port)
    assert port.writes[0]["confidence"] == DEEPSWE_MAX_CONFIDENCE


@pytest.mark.asyncio
async def test_record_corpus_run_all_fail_gets_min_confidence() -> None:
    port = _FakeMemoryPort()
    summary = build_corpus_run_summary(
        subset_task_ids=("t-1",),
        outcomes=("FAIL",),
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_env="docker",
        started_at="2026-07-30T07:50:00+00:00",
        finished_at="2026-07-30T07:55:00+00:00",
    )
    await record_corpus_run(summary, memory_port=port)
    assert port.writes[0]["confidence"] == DEEPSWE_MIN_CONFIDENCE


# ---------------------------------------------------------------------------
# DoD literal: benchmark run recorded


@pytest.mark.asyncio
async def test_deepswe_subset_benchmark_run_recorded_build_sequence_3_9_dod(
    tmp_path, monkeypatch
) -> None:
    """Stage 3.9 DoD literal — 'Benchmark run recorded'.

    Wires the full pipeline: manifest → per-task Pier trial → aggregate
    CorpusRunSummary → single ``tektos.eval.corpus_run_completed``
    MemoryPort event. Uses a fake ``pier`` CLI shim that produces a
    mix of PASS + FAIL trajectories so the aggregate covers both
    outcome sides.
    """
    corpus = load_deepswe_manifest()
    assert corpus.subset_size == DEEPSWE_SUBSET_SIZE

    # Materialize a fake tasks tree that shadows the pinned subset.
    tasks_root = tmp_path / "tasks"
    for entry in corpus.subset:
        _write_harbor_stub(tasks_root, entry.task_id)

    # Fake pier: first three tasks PASS, last two FAIL (mirrors 3py/2ts
    # split but the outcome map is deliberate, not language-linked).
    task_ids = [entry.task_id for entry in corpus.subset]
    task_map = {tid: (0 if i < 3 else 1) for i, tid in enumerate(task_ids)}
    _install_fake_pier(tmp_path, task_map=task_map, monkeypatch=monkeypatch)

    started = utc_now_iso()
    trial_event_ids: list[str] = []
    port = _FakeMemoryPort()
    outcomes: list[str] = []

    for entry in corpus.subset:
        verdict = await run_pier_trial(
            tasks_root / entry.task_id,
            agent="nop",
            pier_env=PierEnv(PIER_DEFAULT_ENV),
            jobs_root=tmp_path / "_jobs" / entry.task_id,
        )
        outcomes.append(verdict.outcome.value)
    finished = utc_now_iso()

    summary = build_corpus_run_summary(
        subset_task_ids=tuple(task_ids),
        outcomes=tuple(outcomes),
        trial_event_ids=tuple(trial_event_ids),
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
        pier_env=PIER_DEFAULT_ENV,
        started_at=started,
        finished_at=finished,
        run_id="run-dod",
    )
    event_id = await record_corpus_run(summary, memory_port=port)

    # DoD: benchmark run is recorded — exactly one aggregate MemoryPort
    # event carrying locked shape.
    assert event_id.id.startswith("evt-")
    assert len(port.writes) == 1
    w = port.writes[0]
    assert w["predicate"] == DEEPSWE_CORPUS_RUN_PREDICATE
    assert w["provenance"] == DEEPSWE_EVAL_PROVENANCE
    assert w["subject"] == f"deepswe::{DEEPSWE_UPSTREAM_COMMIT}::0::run-dod"
    assert w["object"] == "3/5"
    assert w["confidence"] == pytest.approx(0.6)
    assert w["attributes"]["n_total"] == 5
    assert w["attributes"]["n_pass"] == 3
    assert w["attributes"]["n_fail"] == 2
    assert w["attributes"]["n_error"] == 0
    assert w["attributes"]["subset_task_ids"] == task_ids
    assert w["attributes"]["pier_env"] == "docker"
    assert w["attributes"]["upstream_commit"] == DEEPSWE_UPSTREAM_COMMIT


# ---------------------------------------------------------------------------
# Real Pier tier — env-gated


@pytest.mark.skipif(
    os.environ.get("KOSMOS_STAGE_39_REAL_DEEPSWE") != "1",
    reason=(
        "Real DeepSWE tier is opt-in only "
        "(set KOSMOS_STAGE_39_REAL_DEEPSWE=1). Requires Docker daemon, "
        "datacurve-pier installed, and network access to hydrate the corpus."
    ),
)
@pytest.mark.asyncio
async def test_real_deepswe_first_task_runs_through_pier_on_colossus(
    tmp_path,
) -> None:
    corpus = load_deepswe_manifest()
    if shutil.which("pier") is None:
        pytest.skip("pier CLI not installed; run `.venv/bin/pip install -e '.[eval]'`")
    if shutil.which("docker") is None:
        pytest.skip("docker CLI not on PATH")

    cache_root = tmp_path / "cache"
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[3] / "scripts" / "deepswe_fetch.py"),
            "--cache-dir",
            str(cache_root),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        pytest.skip(f"deepswe_fetch failed: {proc.stderr}")

    first = corpus.subset[0]
    task_path = cache_root / DEEPSWE_UPSTREAM_COMMIT / "tasks" / first.task_id
    assert task_path.is_dir(), f"Expected hydrated task at {task_path}"

    verdict = await run_pier_trial(
        task_path,
        agent="nop",
        pier_env=PierEnv(PIER_DEFAULT_ENV),
        jobs_root=tmp_path / "_jobs" / first.task_id,
    )
    assert verdict.outcome.value in {"PASS", "FAIL"}
