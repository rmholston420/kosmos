"""Open Deep Research contender: LangGraph-driven ODR + qwen2.5:32b via Ollama.

Search fairness: ODR's SearchAPI is set to NONE and it consumes SearXNG-backed
search + visit through the MCP server in harness/mcp_search_server.py. This
gives ODR the same tool contract as AREX, so ADR-010 measures loop quality,
not search quality.

Model: qwen2.5:32b-instruct-q4_K_M served by Ollama at 127.0.0.1:11434,
addressed via LangChain's OpenAI-compatible provider (langchain-openai +
base_url override).

Not runnable in the Perplexity sandbox — requires Ollama + running ODR
LangGraph + MCP server. Contract tests (test_odr_config.py) verify config
assembly only.
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from ..metrics import TrialMetrics
from .prompts import KOSMOS_MCP_PROMPT, build_anchored_user_turn
from .search_backend import unique_domain_count

_ROOT = Path(__file__).resolve().parents[4]
_ODR_SRC = _ROOT / "vendor" / "adr_010" / "open_deep_research" / "src"
if str(_ODR_SRC) not in sys.path:
    sys.path.insert(0, str(_ODR_SRC))

logger = logging.getLogger(__name__)


def build_odr_config(
    *,
    ollama_base_url: str = "http://127.0.0.1:11434/v1",
    ollama_model: str = "qwen2.5:32b-instruct-q4_K_M",
    mcp_server_url: str = "http://127.0.0.1:8000",
) -> dict[str, Any]:
    """Assemble the RunnableConfig ODR needs.

    All three ODR model slots (research, summarization, final-report) point at
    the same Ollama-served qwen2.5:32b so the comparison measures one LLM.

    ODR's current deep_researcher wires `configurable_fields=("model",
    "max_tokens", "api_key")` and calls `init_chat_model` without a
    `model_provider` keyword. LangChain's `init_chat_model` therefore has to
    infer the provider from the model string. We force provider=openai by
    prefixing the model tag with `openai:` — LangChain splits on the first
    colon, so the tag `openai:qwen2.5:32b-instruct-q4_K_M` parses as
    (provider=openai, model=qwen2.5:32b-instruct-q4_K_M) and the model name
    is forwarded verbatim to the OpenAI-compatible endpoint (Ollama).
    """
    prefixed_model = f"openai:{ollama_model}"
    return {
        "configurable": {
            # Search: disabled — MCP-supplied tools substitute.
            "search_api": "none",
            # MCP: SearXNG-backed search + visit tools we host in mcp_search_server.
            "mcp_config": {
                "url": mcp_server_url,
                "tools": ["search", "visit"],
                "auth_required": False,
            },
            # Stage 6.3.1 prompt anchoring: tool-usage discipline injected
            # via ODR's officially-supported mcp_prompt hook. See
            # harness/prompts.py for the full contract.
            "mcp_prompt": KOSMOS_MCP_PROMPT,
            # Model slots — all pointed at Ollama via openai-compat.
            "research_model": prefixed_model,
            "research_model_config": {
                "base_url": ollama_base_url,
                "temperature": 0.7,
            },
            "summarization_model": prefixed_model,
            "summarization_model_config": {
                "base_url": ollama_base_url,
                "temperature": 0.3,
            },
            "final_report_model": prefixed_model,
            "final_report_model_config": {
                "base_url": ollama_base_url,
                "temperature": 0.3,
            },
            "compression_model": prefixed_model,
            "compression_model_config": {
                "base_url": ollama_base_url,
                "temperature": 0.3,
            },
            # Environment knobs commonly needed for local models.
            "allow_clarification": False,
            "max_researcher_iterations": 12,
            "max_concurrent_research_units": 1,
        }
    }


async def run_odr_trial(
    *,
    question: str,
    question_id: str,
    trial_id: str,
    ollama_base_url: str = "http://127.0.0.1:11434/v1",
    ollama_model: str = "qwen2.5:32b-instruct-q4_K_M",
    mcp_server_url: str = "http://127.0.0.1:8000",
) -> TrialMetrics:
    """Run a single ODR trial. Async because ODR is LangGraph async."""
    try:
        from open_deep_research.deep_researcher import (  # type: ignore[import-not-found]
            deep_researcher,
        )
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "ODR runtime deps missing. Install ODR deps: "
            "pip install -e vendor/adr_010/open_deep_research"
        ) from exc

    metrics = TrialMetrics(
        contender="odr", trial_id=trial_id, question_id=question_id
    )
    config = build_odr_config(
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        mcp_server_url=mcp_server_url,
    )
    config["configurable"]["thread_id"] = str(uuid.uuid4())

    # Stage 6.3.1 prompt anchoring: wrap the raw fixture question in the
    # answer-agnostic structural scaffold (Positions A-E). See
    # harness/prompts.py for the full contract.
    anchored_question = build_anchored_user_turn(question)

    cited_urls: list[str] = []
    start = time.monotonic()
    try:
        result = await deep_researcher.ainvoke(
            {"messages": [{"role": "user", "content": anchored_question}]},
            config=config,
        )
        # ODR returns a compiled report in `final_report`; extract cited URLs
        # from the raw notes on `notes` state.
        final_report = str(result.get("final_report", ""))
        metrics.final_answer = final_report
        metrics.final_confidence = ""  # ODR does not emit a confidence score
        # Best-effort URL extraction from the report body.
        import re

        cited_urls = re.findall(r"https?://[^\s\)]+", final_report)
        metrics.final_evidences = [
            {"evidence": "(auto-extracted from ODR report body)", "url": u}
            for u in cited_urls
        ]
        # Retain notes trajectory if surfaced.
        notes = result.get("notes")
        if notes is not None:
            metrics.trajectory.append({"notes": notes})
    except Exception as exc:  # noqa: BLE001
        metrics.error = f"{type(exc).__name__}: {exc}"
    finally:
        metrics.latency_seconds = time.monotonic() - start
        metrics.source_diversity = unique_domain_count(cited_urls)

    return metrics


__all__ = ["build_odr_config", "run_odr_trial"]
