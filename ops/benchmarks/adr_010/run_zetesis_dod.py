"""Stage 6.3 (proper) DoD runner — call ZetesisPlugin.research() on Colossus.

**Not for Perplexity sandbox execution.** Requires Colossus with:

- Ollama serving ``qwen2.5:32b-instruct-q4_K_M`` at 127.0.0.1:11434
- SearXNG on 127.0.0.1:8888 (``docker compose up -d searxng``)
- MCP search server on 127.0.0.1:8000 (``python -m plugins.zetesis.research.mcp_search_server --transport streamable-http``)

This is the sub-slice 4 DoD trial: bind four production adapters
(``OllamaAdapter``, ``SearxngAdapter``, ``OtelStackObservabilityAdapter``,
``ValkeyEventBusAdapter``) into a real ``ZetesisPlugin``, drive one
research call through the ``research()`` surface with the exact
Stage 6.3.9 shim set, and emit a ``TrialMetrics`` artifact for the
same rater discipline used in ADR-054 / ADR-055.

Rating gate: answer_correctness >= 4.83 / 6 (0.5 tolerance below the
5.33 Stage 6.3.9 baseline; ADR-056 §D6). Latency is informational;
adapter-binding overhead is expected but not gated. GPU envelope
(pre-flight cooldown, thermal watchdog, 435W power cap) is enforced
verbatim from runner.py so a Zetesis-side run is subject to the same
Colossus safety boundaries the baseline was.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path

from ops.benchmarks.adr_010.metrics import TrialMetrics
from ops.benchmarks.adr_010.policy import GPUMonitor, wait_for_cooldown
from ops.benchmarks.adr_010.runner import (
    _collect_fact_anchor_urls,
    load_question,
)
from plugins.zetesis.adapters.real import build_stage_6_3_9_zetesis_plugin
from plugins.zetesis.plugin import ZetesisResearchConfig
from plugins.zetesis.research.rubric_critique import build_rubric_lines_from_facts

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ARTIFACT_ROOT = (
    _REPO_ROOT / "ops" / "benchmarks" / "artifacts" / "adr-010-2026-07-30"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stage 6.3 (proper) sub-slice 4 DoD runner: drive one ADR-010 "
            "trial through ZetesisPlugin.research()."
        )
    )
    # ── Endpoints ────────────────────────────────────────────────────────
    parser.add_argument(
        "--ollama-base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
    )
    parser.add_argument(
        "--ollama-model",
        default=os.environ.get("OLLAMA_MODEL", "qwen2.5:32b-instruct-q4_K_M"),
    )
    parser.add_argument(
        "--searxng-url",
        default=os.environ.get("SEARXNG_URL", "http://127.0.0.1:8888"),
    )
    parser.add_argument(
        "--mcp-url",
        default=os.environ.get("MCP_URL", "http://127.0.0.1:8000"),
    )
    parser.add_argument(
        "--ollama-keep-alive",
        default=os.environ.get("ADR010_OLLAMA_KEEP_ALIVE", "60s"),
    )
    # ── Thermal envelope (mirrors runner.py post-88C-incident defaults) ──
    parser.add_argument(
        "--cooldown-target-c",
        type=float,
        default=float(os.environ.get("ADR010_COOLDOWN_TARGET_C", "60")),
    )
    parser.add_argument(
        "--cooldown-min-seconds",
        type=float,
        default=float(os.environ.get("ADR010_COOLDOWN_MIN_SECONDS", "1")),
    )
    parser.add_argument(
        "--cooldown-max-seconds",
        type=float,
        default=float(os.environ.get("ADR010_COOLDOWN_MAX_SECONDS", "300")),
    )
    parser.add_argument("--no-cooldown", action="store_true")
    parser.add_argument(
        "--thermal-abort-c",
        type=float,
        default=float(os.environ.get("ADR010_THERMAL_ABORT_C", "85")),
    )
    parser.add_argument(
        "--power-cap-watts",
        type=int,
        default=int(os.environ.get("ADR010_POWER_CAP_WATTS", "435")),
    )
    parser.add_argument("--no-power-cap", action="store_true")
    # ── Shim toggles (default: all on, matching Stage 6.3.9 baseline) ────
    parser.add_argument("--no-fact-check", action="store_true")
    parser.add_argument("--no-license-grounding", action="store_true")
    parser.add_argument("--no-feature-grounding", action="store_true")
    parser.add_argument("--no-enterprise-license-grounding", action="store_true")
    parser.add_argument("--no-rubric-critique", action="store_true")
    parser.add_argument("--no-cove", action="store_true")
    parser.add_argument("--no-claim-support-gate", action="store_true")
    parser.add_argument("--no-structural-finalize", action="store_true")
    return parser.parse_args()


def apply_power_cap(watts: int) -> None:
    """Apply nvidia-smi -pl <watts>. Log-and-continue on failure."""
    try:
        subprocess.run(
            ["sudo", "-n", "nvidia-smi", "-pl", str(watts)],
            check=True,
            capture_output=True,
        )
        logger.info("power cap set: %d W", watts)
    except Exception as exc:  # noqa: BLE001 — log and continue
        logger.warning("nvidia-smi power cap failed: %s", exc)


def pre_flight_cooldown(args: argparse.Namespace) -> None:
    if args.no_cooldown:
        return
    logger.info(
        "pre-flight cooldown (target=%.1fC, min=%.0fs, max=%.0fs)",
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
        "pre-flight cooldown done: waited %.1fs, temp=%.1fC",
        waited,
        final_temp,
    )


def artifact_path(trial_id: str) -> Path:
    d = _ARTIFACT_ROOT / "zetesis"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{trial_id}.json"


def emit(metrics: TrialMetrics) -> Path:
    path = artifact_path(metrics.trial_id)
    with path.open("w") as f:
        json.dump(metrics.to_dict(), f, indent=2, ensure_ascii=False)
    logger.info("wrote %s", path)
    return path


async def run_one_trial(args: argparse.Namespace) -> TrialMetrics:
    fixture = load_question()
    question_id = str(fixture.get("id") or fixture.get("question_id") or "adr_010")
    question = fixture["question"]
    fact_anchor_urls = _collect_fact_anchor_urls(fixture)
    # ADR-054 shim-data parity: rubric-critique fires only when
    # rubric_lines is non-empty (see runner.py `not args.no_rubric_critique
    # and bool(rubric_lines)`). ADR-054's 5.33 baseline built these from
    # the fixture's canonical_facts; the DoD trial must do the same or
    # the rubric-critique shim silently no-ops and F4/F5/F6 rationale-
    # preservation regresses (which is exactly what trial_01_42e695
    # exhibited).
    canonical_facts = (fixture.get("ground_truth") or {}).get(
        "canonical_facts", []
    ) or []
    rubric_lines = build_rubric_lines_from_facts(canonical_facts)

    trial_id = f"trial_01_{uuid.uuid4().hex[:6]}"
    logger.info(
        "Zetesis DoD trial %s (question_id=%s)", trial_id, question_id
    )

    # ── env vars ODR's OpenAI client honors (verbatim from runner.py) ────
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "ollama")
    os.environ["OPENAI_BASE_URL"] = args.ollama_base_url
    os.environ["OLLAMA_KEEP_ALIVE"] = args.ollama_keep_alive

    plugin = build_stage_6_3_9_zetesis_plugin(
        ollama_base_url=args.ollama_base_url,
        ollama_model=args.ollama_model,
        searxng_url=args.searxng_url,
    )
    await plugin.start()

    monitor = GPUMonitor(thermal_abort_at_c=args.thermal_abort_c)
    monitor.start()
    try:
        # Build the plugin's research config with the exact Stage 6.3.9
        # shim set so this DoD trial is apples-to-apples with the ADR-054
        # baseline (5.33 / 6). Note: ``thermal_event`` is NOT forwarded —
        # the sub-slice 3 ``research()`` surface deliberately does not
        # expose it (thermal safety is an operator-level concern, not a
        # per-call knob). The ``GPUMonitor`` still enforces the thermal
        # abort by killing the subprocess-level Ollama request if temp
        # crosses ``--thermal-abort-c``.
        cfg = ZetesisResearchConfig(
            ollama_base_url=args.ollama_base_url,
            ollama_model=args.ollama_model,
            mcp_server_url=args.mcp_url,
            question_id=question_id,
            trial_id=trial_id,
            fact_anchor_urls=tuple(fact_anchor_urls) if fact_anchor_urls else None,
            rubric_lines=tuple(rubric_lines) if rubric_lines else None,
            enable_fact_check=not args.no_fact_check,
            enable_license_grounding=not args.no_license_grounding,
            enable_feature_grounding=not args.no_feature_grounding,
            enable_enterprise_license_grounding=(
                not args.no_enterprise_license_grounding
            ),
            enable_rubric_critique=not args.no_rubric_critique,
            enable_cove=not args.no_cove,
            enable_claim_support_gate=not args.no_claim_support_gate,
            enable_structural_finalize=not args.no_structural_finalize,
        )
        report = await plugin.research(question, config=cfg)
    finally:
        monitor.stop()

    metrics = TrialMetrics(
        contender="zetesis",
        trial_id=trial_id,
        question_id=question_id,
        source_diversity=report.source_diversity,
        latency_seconds=report.latency_seconds,
        gpu_utilization_peak_pct=monitor.peak_utilization_pct,
        vram_peak_gb=monitor.peak_vram_gb,
        final_answer=report.answer or "",
        final_evidences=list(report.evidences),
        final_confidence="",
        error=report.error,
        # ResearchReport.trajectory_events is an int count; TrialMetrics
        # keeps a full trajectory list. We record the count under a single
        # summary entry so the JSON artifact stays useful to the blind
        # rater without dragging the full inner-loop trajectory through
        # the plugin's public API surface.
        trajectory=[
            {
                "zetesis_research_summary": {
                    "trajectory_events_count": report.trajectory_events,
                    "memory_event_id": report.memory_event_id,
                    "trial_id": report.trial_id,
                    "question_id": report.question_id,
                }
            }
        ],
    )
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
    return metrics


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )
    args = parse_args()
    if not args.no_power_cap:
        apply_power_cap(args.power_cap_watts)
    pre_flight_cooldown(args)
    metrics = asyncio.run(run_one_trial(args))
    path = emit(metrics)
    print(
        f"\n=== Zetesis DoD trial complete ===\n"
        f"trial_id={metrics.trial_id}\n"
        f"artifact={path}\n"
        f"latency_seconds={metrics.latency_seconds:.2f}\n"
        f"source_diversity={metrics.source_diversity}\n"
        f"gpu_peak_pct={metrics.gpu_utilization_peak_pct:.1f}\n"
        f"vram_peak_gb={metrics.vram_peak_gb:.2f}\n"
        f"error={metrics.error!r}\n"
        f"\nNext: rate final_answer against the fixture's canonical facts\n"
        f"(same rubric as ADR-054/055), write the rating to:\n"
        f"  ops/benchmarks/adr_010/artifacts/adr-010-2026-07-30/zetesis/\n"
        f"  RATING_STAGE_6_3_PROPER.md\n"
        f"Gate: rating >= 4.83 / 6.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
