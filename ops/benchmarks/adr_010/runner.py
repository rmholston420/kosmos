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
import sys
import uuid
from pathlib import Path

from .harness.arex import run_arex_trial
from .harness.odr import run_odr_trial
from .metrics import TrialMetrics
from .policy import GPUMonitor

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
        default=os.environ.get("MCP_URL", "http://127.0.0.1:8765/sse"),
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


async def run_odr(args: argparse.Namespace, question_id: str, question: str) -> None:
    # ODR wires configurable_fields=("model","max_tokens","api_key") in
    # deep_researcher.py, so our research_model_config.base_url is dropped.
    # Point the OpenAI client at Ollama via env vars instead.
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "ollama")
    os.environ["OPENAI_BASE_URL"] = args.ollama_base_url
    for i in range(args.trials):
        trial_id = f"trial_{i + 1:02d}_{uuid.uuid4().hex[:6]}"
        monitor = GPUMonitor()
        monitor.start()
        try:
            metrics = await run_odr_trial(
                question=question,
                question_id=question_id,
                trial_id=trial_id,
                ollama_base_url=args.ollama_base_url,
                ollama_model=args.ollama_model,
                mcp_server_url=args.mcp_url,
            )
        finally:
            monitor.stop()
        metrics.gpu_utilization_peak_pct = monitor.peak_utilization_pct
        metrics.vram_peak_gb = monitor.peak_vram_gb
        emit(metrics)


def run_arex(args: argparse.Namespace, question_id: str, question: str) -> None:
    for i in range(args.trials):
        trial_id = f"trial_{i + 1:02d}_{uuid.uuid4().hex[:6]}"
        monitor = GPUMonitor()
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


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = parse_args()
    fixture = load_question()
    question_id = fixture["question_id"]
    question = fixture["question"]
    logger.info("ADR-010 run: contender=%s trials=%d", args.contender, args.trials)
    logger.info("question_id=%s", question_id)

    if args.contender == "arex":
        run_arex(args, question_id, question)
    else:
        asyncio.run(run_odr(args, question_id, question))
    logger.info("done. artifacts at %s/%s/", _ARTIFACT_ROOT, args.contender)
    return 0


if __name__ == "__main__":
    sys.exit(main())
