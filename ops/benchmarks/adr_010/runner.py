"""ADR-010 head-to-head eval runner.

Colossus-side entry point. See ../adr_010/README.md for run sequence.

Emits ops/benchmarks/artifacts/adr-010-2026-07-30/{contender}/trial_{n}.json
per trial with the 6 locked metrics. Post-run rating (answer_correctness) is
applied by the blind rater, not this runner.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from .harness.arex import run_arex_trial
from .harness.odr import run_odr_trial
from .harness.rubric_critique import build_rubric_lines_from_facts
from .harness.self_consistency import (
    compose_consensus_report,
    summarize_vote,
    tally_claims,
)
from .metrics import TrialMetrics
from .policy import GPUMonitor, wait_for_cooldown

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_PATH = _REPO_ROOT / "ops" / "benchmarks" / "adr_010" / "fixtures" / "adr_010_question.json"
_ARTIFACT_ROOT = _REPO_ROOT / "ops" / "benchmarks" / "artifacts" / "adr-010-2026-07-30"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ADR-010 head-to-head eval runner")
    parser.add_argument(
        "--contender",
        choices=("arex", "odr"),
        required=True,
    )
    parser.add_argument("--trials", type=int, default=3, help="trials per contender")
    parser.add_argument(
        "--searxng-url",
        default=os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888"),
    )
    parser.add_argument(
        "--arex-base-url",
        default=os.environ.get("AREX_BASE_URL", "http://127.0.0.1:8001/v1"),
    )
    parser.add_argument(
        "--arex-model",
        default=os.environ.get("AREX_MODEL", "AREX-Turbo"),
    )
    parser.add_argument(
        "--ollama-base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
    )
    parser.add_argument(
        "--ollama-model",
        default=os.environ.get("OLLAMA_MODEL", "qwen2.5:32b-instruct-q4_K_M"),
    )
    parser.add_argument(
        "--mcp-url",
        default=os.environ.get("MCP_URL", "http://127.0.0.1:8000"),
    )
    # ---- Thermal envelope ----
    #
    # Colossus is a single-user workstation with an RTX 5090 (Blackwell,
    # SM_120). Sustained 32B-parameter Ollama load pushes junction temp
    # above 85 C within a single ~2 min trial. Kosmos runs benchmarks at
    # BACKGROUND priority (see policy.GPUMonitor / ADR-029 ResourcePort);
    # the operator-visible boundary is thermal, not compute. These flags
    # let us serialize trials with a cooldown window and (optionally)
    # block on a temperature threshold before starting the next trial.
    parser.add_argument(
        "--cooldown-target-c",
        type=float,
        default=float(os.environ.get("ADR010_COOLDOWN_TARGET_C", "60")),
        help=(
            "target GPU temperature (C) before starting the next trial. "
            "Lowered from 70->60 after Colossus 88C driver-crash incident "
            "(2026-07-30). Applied both as pre-flight before every trial "
            "AND between trials. Held at 60C in Stage 6.3.3 (only the "
            "minimum wait was shortened)."
        ),
    )
    parser.add_argument(
        "--cooldown-min-seconds",
        type=float,
        default=float(os.environ.get("ADR010_COOLDOWN_MIN_SECONDS", "15")),
        help=(
            "minimum cooldown seconds, applied both pre-flight and between "
            "trials. Progression: 30 -> 60 (post-88C incident) -> 45 -> 30 "
            "-> 15 (Stage 6.3.4: Stage 6.3.3 3-trial run with 30s waits "
            "peaked at 73C and trial-start temps were 36/37/42C \u2014 12C "
            "below the 85C watchdog and 21C below the 88C driver-crash line. "
            "Target C held at 60.)"
        ),
    )
    parser.add_argument(
        "--cooldown-max-seconds",
        type=float,
        default=float(os.environ.get("ADR010_COOLDOWN_MAX_SECONDS", "300")),
        help="cooldown hard cap; proceed even if still above target",
    )
    parser.add_argument(
        "--no-cooldown",
        action="store_true",
        help="disable both pre-flight and inter-trial cooldown (dangerous)",
    )
    parser.add_argument(
        "--thermal-abort-c",
        type=float,
        default=float(os.environ.get("ADR010_THERMAL_ABORT_C", "85")),
        help=(
            "hard-abort in-flight trial when GPU >= this many degrees C. "
            "Set to 85 after RTX 5090 driver crash at 88C on 2026-07-30. "
            "Colossus runs the display on the same GPU as compute, so a "
            "driver crash takes down the desktop."
        ),
    )
    parser.add_argument(
        "--power-cap-watts",
        type=int,
        default=int(os.environ.get("ADR010_POWER_CAP_WATTS", "400")),
        help=(
            "apply nvidia-smi -pl <watts> at startup to reduce sustained "
            "board-power draw. RTX 5090 stock TDP is 575W; 400W is the "
            "post-incident conservative default. Requires sudo; if not "
            "available, the runner logs and continues (does NOT fail)."
        ),
    )
    parser.add_argument(
        "--no-power-cap",
        action="store_true",
        help="skip nvidia-smi -pl entirely (accepts full thermal risk)",
    )
    parser.add_argument(
        "--no-fact-check",
        action="store_true",
        help=(
            "disable Stage 6.3.3 URL-verification shim (shim 3). Not "
            "recommended — the shim exists specifically because the 32B "
            "model was observed fabricating repo URLs and license IDs."
        ),
    )
    # ---- Stage 6.3.4 additive shims ----
    parser.add_argument(
        "--no-license-grounding",
        action="store_true",
        help="disable shim 4 (fetches LICENSE files for cited GitHub repos)",
    )
    parser.add_argument(
        "--no-rubric-critique",
        action="store_true",
        help=(
            "disable shim 6 (asks the model to score its own report against "
            "the fixture rubric and rewrite failures). Rubric extracted from "
            "fixture ground_truth.canonical_facts."
        ),
    )
    parser.add_argument(
        "--no-cove",
        action="store_true",
        help=(
            "disable shim 7 (chain-of-verification: per-claim verification "
            "sub-questions + rewrite). Up to 6 extra ainvoke rounds per trial."
        ),
    )
    parser.add_argument(
        "--no-claim-support-gate",
        action="store_true",
        help=(
            "disable shim 8 (marks license/identity claims whose subject "
            "doesn't appear in retrieval observations as [unsupported])"
        ),
    )
    parser.add_argument(
        "--n-consistency",
        type=int,
        default=int(os.environ.get("ADR010_N_CONSISTENCY", "1")),
        help=(
            "shim 5: number of independent ODR runs per trial to vote across. "
            "Default 1 (off). Set >= 2 to enable self-consistency voting; "
            "the trial's final_answer becomes the consensus report and each "
            "per-run report is preserved in trajectory. Cost scales linearly."
        ),
    )
    parser.add_argument(
        "--ollama-keep-alive",
        default=os.environ.get("ADR010_OLLAMA_KEEP_ALIVE", "60s"),
        help=(
            "OLLAMA_KEEP_ALIVE value exported before invoking ODR. Default "
            "60s so the 32B model releases VRAM during the 60s+ between-"
            "trial cooldown window and reloads warmly on the next trial."
        ),
    )
    return parser.parse_args()


def load_question() -> dict:
    with _FIXTURE_PATH.open() as f:
        return json.load(f)


def artifact_path(contender: str, trial_id: str) -> Path:
    d = _ARTIFACT_ROOT / contender
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{trial_id}.json"


def emit(metrics: TrialMetrics) -> Path:
    path = artifact_path(metrics.contender, metrics.trial_id)
    with path.open("w") as f:
        json.dump(metrics.to_dict(), f, indent=2, ensure_ascii=False)
    logger.info("wrote %s", path)
    return path


def _collect_fact_anchor_urls(fixture: dict) -> list[str]:
    """Extract fact-anchor URLs from the fixture's ground_truth.

    Stage 6.3.3 medium-strength anchor policy: the harness pulls a
    curated allowlist of authoritative URLs from the fixture rather
    than hardcoding them, so the anchor list stays fixture-owned and
    the harness is generic. Dedupe while preserving order.
    """
    gt = fixture.get("ground_truth", {}) or {}
    facts = gt.get("canonical_facts", []) or []
    seen: set[str] = set()
    urls: list[str] = []
    for f in facts:
        for u in f.get("supporting_urls", []) or []:
            if isinstance(u, str) and u not in seen:
                seen.add(u)
                urls.append(u)
    return urls


def _combine_self_consistency(
    trial_id: str,
    contender: str,
    question_id: str,
    per_run: list[TrialMetrics],
) -> TrialMetrics:
    """Shim 5: fold N per-run TrialMetrics into a single trial artifact.

    - For N=1 (default), returns the single run unchanged aside from
      relabeling its ``trial_id``.
    - For N>=2, tallies claim-level agreement across each run's
      ``final_answer`` via :mod:`self_consistency`, replaces the trial's
      ``final_answer`` with the consensus report, and preserves every
      per-run trajectory plus the vote summary under
      ``trajectory[-1]["self_consistency"]``.
    - ``source_diversity`` becomes the max across runs; ``latency_seconds``
      the sum; ``gpu_utilization_peak_pct`` and ``vram_peak_gb`` the max.
    - If any run recorded an ``error``, that error is preserved on the
      combined artifact so the blind rater can spot it.
    """
    if not per_run:
        return TrialMetrics(
            contender=contender,
            trial_id=trial_id,
            question_id=question_id,
            error="self_consistency: zero completed runs",
        )
    if len(per_run) == 1:
        m = per_run[0]
        m.trial_id = trial_id
        return m

    reports = [m.final_answer or "" for m in per_run]
    tally = tally_claims(reports)
    consensus = compose_consensus_report(tally)
    vote = summarize_vote(tally, per_run_final_answers=reports)

    combined = TrialMetrics(
        contender=contender,
        trial_id=trial_id,
        question_id=question_id,
        source_diversity=max(m.source_diversity for m in per_run),
        latency_seconds=sum(m.latency_seconds for m in per_run),
        gpu_utilization_peak_pct=max(
            m.gpu_utilization_peak_pct for m in per_run
        ),
        vram_peak_gb=max(m.vram_peak_gb for m in per_run),
        final_answer=consensus,
        final_evidences=list(per_run[0].final_evidences),
        final_confidence=per_run[0].final_confidence,
        error=next((m.error for m in per_run if m.error), None),
    )
    for m in per_run:
        combined.trajectory.append(
            {
                "self_consistency_sub_run": {
                    "trial_id": m.trial_id,
                    "latency_seconds": m.latency_seconds,
                    "source_diversity": m.source_diversity,
                    "final_answer": m.final_answer,
                    "final_evidences": m.final_evidences,
                    "final_confidence": m.final_confidence,
                    "error": m.error,
                    "trajectory": m.trajectory,
                }
            }
        )
    combined.trajectory.append({"self_consistency": vote})
    return combined


async def run_odr(
    args: argparse.Namespace,
    question_id: str,
    question: str,
    fact_anchor_urls: list[str] | None = None,
    rubric_lines: list[str] | None = None,
) -> None:
    # ODR wires configurable_fields=("model","max_tokens","api_key") in
    # deep_researcher.py, so our research_model_config.base_url is dropped.
    # Point the OpenAI client at Ollama via env vars instead.
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "ollama")
    os.environ["OPENAI_BASE_URL"] = args.ollama_base_url
    # Ollama VRAM release policy — see runner --ollama-keep-alive help.
    os.environ["OLLAMA_KEEP_ALIVE"] = args.ollama_keep_alive
    for i in range(args.trials):
        # Pre-flight cooldown BEFORE every trial (including the first).
        # Post-incident (2026-07-30 88C driver crash) discipline: never
        # start a trial with the GPU already above cooldown_target_c.
        _pre_flight_cooldown(args, i)

        trial_id = f"trial_{i + 1:02d}_{uuid.uuid4().hex[:6]}"
        monitor = GPUMonitor(thermal_abort_at_c=args.thermal_abort_c)
        monitor.start()
        n_runs = max(1, int(args.n_consistency))
        per_run_metrics: list[TrialMetrics] = []
        try:
            for run_ix in range(n_runs):
                sub_id = (
                    trial_id
                    if n_runs == 1
                    else f"{trial_id}_r{run_ix + 1:02d}"
                )
                m = await run_odr_trial(
                    question=question,
                    question_id=question_id,
                    trial_id=sub_id,
                    ollama_base_url=args.ollama_base_url,
                    ollama_model=args.ollama_model,
                    mcp_server_url=args.mcp_url,
                    thermal_event=monitor.thermal_event,
                    fact_anchor_urls=fact_anchor_urls,
                    enable_fact_check=not args.no_fact_check,
                    enable_license_grounding=not args.no_license_grounding,
                    enable_rubric_critique=(
                        not args.no_rubric_critique and bool(rubric_lines)
                    ),
                    rubric_lines=rubric_lines,
                    enable_cove=not args.no_cove,
                    enable_claim_support_gate=not args.no_claim_support_gate,
                )
                per_run_metrics.append(m)
                if monitor.thermal_exceeded():
                    break
            metrics = _combine_self_consistency(
                trial_id=trial_id,
                contender="odr",
                question_id=question_id,
                per_run=per_run_metrics,
            )
        finally:
            monitor.stop()
        metrics.gpu_utilization_peak_pct = monitor.peak_utilization_pct
        metrics.vram_peak_gb = monitor.peak_vram_gb
        # If the watchdog fired, annotate the artifact with the exact
        # threshold breach for the blind rater.
        if monitor.thermal_exceeded():
            metrics.trajectory.append(
                {
                    "thermal_watchdog": {
                        "aborted": True,
                        "reason": monitor.abort_reason,
                        "abort_temp_c": monitor.abort_temperature_c,
                        "threshold_c": args.thermal_abort_c,
                    }
                }
            )
            logger.warning(
                "trial %d aborted by thermal watchdog: %s",
                i + 1,
                monitor.abort_reason,
            )
        emit(metrics)
        _cooldown_between_trials(args, i, monitor.peak_temperature_c)


def run_arex(args: argparse.Namespace, question_id: str, question: str) -> None:
    for i in range(args.trials):
        _pre_flight_cooldown(args, i)
        trial_id = f"trial_{i + 1:02d}_{uuid.uuid4().hex[:6]}"
        monitor = GPUMonitor(thermal_abort_at_c=args.thermal_abort_c)
        monitor.start()
        try:
            metrics = run_arex_trial(
                question=question,
                question_id=question_id,
                trial_id=trial_id,
                base_url=args.arex_base_url,
                model=args.arex_model,
                searxng_url=args.searxng_url,
            )
        finally:
            monitor.stop()
        metrics.gpu_utilization_peak_pct = monitor.peak_utilization_pct
        metrics.vram_peak_gb = monitor.peak_vram_gb
        emit(metrics)
        _cooldown_between_trials(args, i, monitor.peak_temperature_c)


def _pre_flight_cooldown(args: argparse.Namespace, trial_index: int) -> None:
    """Wait for GPU to reach cooldown_target_c BEFORE starting a trial.

    Added after the 2026-07-30 88C incident. Between-trial cooldown alone
    doesn't help the first trial or trials that inherit heat from other
    workloads; pre-flight closes that gap.
    """
    if args.no_cooldown:
        return
    logger.info(
        "pre-flight cooldown for trial %d (target=%.1fC, min=%.0fs, max=%.0fs)",
        trial_index + 1,
        args.cooldown_target_c,
        args.cooldown_min_seconds,
        args.cooldown_max_seconds,
    )
    waited, final_temp = wait_for_cooldown(
        target_c=args.cooldown_target_c,
        min_seconds=args.cooldown_min_seconds,
        max_seconds=args.cooldown_max_seconds,
        logger=logger,
    )
    logger.info(
        "pre-flight cooldown done: waited %.1fs, temp=%.1fC", waited, final_temp
    )


def _cooldown_between_trials(
    args: argparse.Namespace, trial_index: int, trial_peak_temp_c: float
) -> None:
    """Sleep between trials to keep the GPU inside the thermal envelope.

    Runs after every trial except the final one. Honors --no-cooldown.
    Uses ``wait_for_cooldown`` from policy.py so behavior stays symmetric
    with the metrics side of the ResourcePort.
    """
    if args.no_cooldown:
        return
    if trial_index + 1 >= args.trials:
        return
    logger.info(
        "trial %d peak temp=%.1fC; entering cooldown (target=%.1fC, min=%.0fs, max=%.0fs)",
        trial_index + 1,
        trial_peak_temp_c,
        args.cooldown_target_c,
        args.cooldown_min_seconds,
        args.cooldown_max_seconds,
    )
    waited, final_temp = wait_for_cooldown(
        target_c=args.cooldown_target_c,
        min_seconds=args.cooldown_min_seconds,
        max_seconds=args.cooldown_max_seconds,
        logger=logger,
    )
    logger.info(
        "cooldown complete: waited %.1fs, final temp=%.1fC", waited, final_temp
    )


def _apply_power_cap(args: argparse.Namespace) -> None:
    """Apply nvidia-smi -pl <watts> at startup. Never fail the run on this.

    Post-2026-07-30-incident hardening. On Colossus the RTX 5090 stock TDP
    is 575W; capping to 400W drops sustained wattage ~30% at the cost of
    ~20-30% slower token generation. Requires sudo. If sudo is not
    available or nvidia-smi is missing, logs and continues — do not
    hard-fail the benchmark on a defense-in-depth measure.
    """
    if args.no_power_cap:
        logger.warning("--no-power-cap: skipping nvidia-smi -pl; full thermal risk accepted")
        return
    nvsmi = shutil.which("nvidia-smi")
    if nvsmi is None:
        logger.warning("nvidia-smi not on PATH; skipping power cap")
        return
    sudo = shutil.which("sudo")
    if sudo is None:
        logger.warning("sudo not on PATH; skipping power cap (nvidia-smi -pl requires root)")
        return
    cmd = [sudo, "-n", nvsmi, "-pl", str(args.power_cap_watts)]
    logger.info("applying power cap: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10.0
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("power cap command failed to execute: %s", exc)
        return
    if result.returncode != 0:
        logger.warning(
            "power cap returned rc=%d; stderr=%s",
            result.returncode,
            result.stderr.strip(),
        )
        return
    logger.info("power cap applied: %s", result.stdout.strip() or f"{args.power_cap_watts}W")


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = parse_args()
    _apply_power_cap(args)
    fixture = load_question()
    question_id = fixture["question_id"]
    question = fixture["question"]
    logger.info(
        "ADR-010 run: contender=%s trials=%d thermal_abort=%sC cooldown_target=%sC",
        args.contender,
        args.trials,
        args.thermal_abort_c,
        args.cooldown_target_c,
    )
    logger.info("question_id=%s", question_id)

    fact_anchor_urls = _collect_fact_anchor_urls(fixture)
    if fact_anchor_urls:
        logger.info(
            "fact-anchor advisory active: %d URL(s) injected into prompt",
            len(fact_anchor_urls),
        )

    canonical_facts = (fixture.get("ground_truth") or {}).get(
        "canonical_facts", []
    ) or []
    rubric_lines = build_rubric_lines_from_facts(canonical_facts)
    logger.info(
        "Stage 6.3.4 shims: license_grounding=%s rubric_critique=%s cove=%s "
        "claim_support_gate=%s n_consistency=%d rubric_points=%d",
        not args.no_license_grounding,
        not args.no_rubric_critique and bool(rubric_lines),
        not args.no_cove,
        not args.no_claim_support_gate,
        args.n_consistency,
        len(rubric_lines),
    )

    if args.contender == "arex":
        run_arex(args, question_id, question)
    else:
        asyncio.run(
            run_odr(
                args, question_id, question, fact_anchor_urls, rubric_lines
            )
        )
    logger.info("done. artifacts at %s/%s/", _ARTIFACT_ROOT, args.contender)
    return 0


if __name__ == "__main__":
    sys.exit(main())
