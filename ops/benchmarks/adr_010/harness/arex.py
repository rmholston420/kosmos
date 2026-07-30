"""AREX-Turbo contender: XML tool-call loop over vendored inference/ bundle.

Upstream ships:
- vendor/adr_010/arex_inference/prompts.py   — BROWSECOMP_SYSTEM_PROMPT, USER prompt, tool schemas
- vendor/adr_010/arex_inference/inference.py — single-turn OpenAI-compat call w/ locked params

Upstream does NOT ship a tool executor loop. We author it here:
- Parse the XML <tool_call> emitted by AREX-Turbo
- Dispatch to {search, google_scholar, visit, update_context, finish}
- Append <tool_response> to the message trajectory
- Repeat until `finish` fires or step limit hit

XML format (from prompts.py; direct excerpt of upstream spec):

    <tool_call>
    <function=name>
    <parameter=arg1>value1</parameter>
    <parameter=arg2>value2</parameter>
    </function>
    </tool_call>

Locked inference params (from vendored inference.py):
  temperature=1.0, top_p=0.95, top_k=20, presence_penalty=1.5, max_tokens=8192
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

from ..metrics import TrialMetrics
from .search_backend import (
    SearXNGClient,
    format_search_results,
    format_visit_response,
    retry_call,
    unique_domain_count,
)

# Ensure vendored AREX inference bundle is importable.
_ROOT = Path(__file__).resolve().parents[4]
_VENDORED = _ROOT / "vendor" / "adr_010" / "arex_inference"
if str(_VENDORED) not in sys.path:
    sys.path.insert(0, str(_VENDORED))

logger = logging.getLogger(__name__)

_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*<function=(?P<name>[^>]+)>(?P<body>.*?)</function>\s*</tool_call>",
    re.DOTALL,
)
_PARAM_RE = re.compile(
    r"<parameter=(?P<name>[^>]+)>(?P<value>.*?)</parameter>",
    re.DOTALL,
)


class AREXParseError(Exception):
    """Model emitted a malformed <tool_call> block."""


def parse_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    """Extract (function_name, params) from a model response.

    Returns None if no <tool_call> block is present (model emitted plain text,
    which is a protocol violation per the AREX system prompt but we handle it
    gracefully).
    """
    m = _TOOL_CALL_RE.search(text)
    if not m:
        return None
    name = m.group("name").strip()
    body = m.group("body")
    params: dict[str, Any] = {}
    for pm in _PARAM_RE.finditer(body):
        raw = pm.group("value").strip()
        # AREX system prompt says: "For structured parameters such as `query`
        # and `evidences`, the parameter content MUST be valid JSON"
        try:
            params[pm.group("name").strip()] = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            params[pm.group("name").strip()] = raw
    return name, params


def _tool_response(body: str) -> str:
    return f"<tool_response>\n{body}\n</tool_response>"


def run_arex_trial(
    *,
    question: str,
    question_id: str,
    trial_id: str,
    base_url: str,
    api_key: str = "EMPTY",
    model: str = "AREX-Turbo",
    searxng_url: str,
    max_steps: int = 40,
    max_tokens: int = 8192,
) -> TrialMetrics:
    """Run a single AREX BrowseComp trial against a vLLM-served AREX-Turbo."""
    try:
        from openai import OpenAI  # type: ignore[import-not-found]
        from prompts import build_messages  # vendored inference/prompts.py
    except ImportError as exc:  # pragma: no cover — runtime dependency
        raise RuntimeError(
            "AREX runtime deps missing: pip install openai; ensure vendor/adr_010/arex_inference/ is present"
        ) from exc

    metrics = TrialMetrics(
        contender="arex", trial_id=trial_id, question_id=question_id
    )
    client = OpenAI(base_url=base_url.rstrip("/") + "/", api_key=api_key, timeout=600.0)
    searxng = SearXNGClient(base_url=searxng_url)

    messages: list[dict[str, Any]] = build_messages(question)
    cited_urls: list[str] = []
    start = time.monotonic()
    try:
        for step in range(max_steps):
            resp = client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=1.0,
                top_p=0.95,
                presence_penalty=1.5,
                extra_body={"top_k": 20},
            )
            assistant_text = resp.choices[0].message.content or ""
            messages.append({"role": "assistant", "content": assistant_text})
            metrics.trajectory.append({"step": step, "assistant": assistant_text})

            parsed = parse_tool_call(assistant_text)
            if parsed is None:
                metrics.error = f"step {step}: no <tool_call> emitted"
                break
            name, params = parsed

            if name == "finish":
                metrics.final_answer = str(params.get("answer", ""))
                evs = params.get("evidences", [])
                if isinstance(evs, list):
                    metrics.final_evidences = [
                        e for e in evs if isinstance(e, dict)
                    ]
                    cited_urls.extend(
                        str(e.get("url", "")) for e in metrics.final_evidences
                    )
                metrics.final_confidence = str(params.get("confidence", ""))
                break

            tool_body = _dispatch_tool(name, params, searxng, cited_urls)
            tool_msg = _tool_response(tool_body)
            messages.append({"role": "user", "content": tool_msg})
            metrics.trajectory.append(
                {"step": step, "tool": name, "params": params, "response": tool_body}
            )
        else:
            metrics.error = f"step budget exhausted after {max_steps} steps"
    except Exception as exc:  # noqa: BLE001 — record any runtime failure into metrics
        metrics.error = f"{type(exc).__name__}: {exc}"
    finally:
        metrics.latency_seconds = time.monotonic() - start
        metrics.source_diversity = unique_domain_count(cited_urls)
        searxng.close()

    return metrics


def _dispatch_tool(
    name: str,
    params: dict[str, Any],
    searxng: SearXNGClient,
    cited_urls: list[str],
) -> str:
    """Execute one AREX tool call and return the tool_response body."""
    if name == "search":
        queries = params.get("query") or []
        if isinstance(queries, str):
            queries = [queries]
        chunks: list[str] = []
        for q in queries:
            results = retry_call(searxng.search, str(q))
            chunks.append(format_search_results(str(q), results))
        return "\n\n".join(chunks) if chunks else "(no queries)"

    if name == "google_scholar":
        queries = params.get("query") or []
        if isinstance(queries, str):
            queries = [queries]
        chunks = []
        for q in queries:
            results = retry_call(searxng.search, str(q), categories="science")
            chunks.append(format_search_results(str(q), results))
        return "\n\n".join(chunks) if chunks else "(no queries)"

    if name == "visit":
        urls = params.get("url") or []
        if isinstance(urls, str):
            urls = [urls]
        goal = str(params.get("goal", ""))
        chunks = []
        for u in urls:
            content = retry_call(searxng.visit, str(u))
            chunks.append(format_visit_response(str(u), goal, content))
            cited_urls.append(str(u))
        return "\n\n---\n\n".join(chunks) if chunks else "(no urls)"

    if name == "update_context":
        # The context compression is the model's job; we just ack.
        return "context updated"

    return f"ERROR: unknown tool `{name}`"


__all__ = ["parse_tool_call", "run_arex_trial", "AREXParseError"]
