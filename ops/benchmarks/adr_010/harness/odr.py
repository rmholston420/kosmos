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

import asyncio
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from ..metrics import TrialMetrics
from . import claim_support, cove, license_grounding, rubric_critique
from .prompts import (
    KOSMOS_MCP_PROMPT,
    build_anchored_user_turn,
    build_fact_check_correction_directive,
)
from .search_backend import unique_domain_count
from .url_verify import annotate_unverified, extract_urls, verify_urls


class ThermalAbort(RuntimeError):
    """Raised when the GPU thermal watchdog fires during an ainvoke call.

    Not a vendor bug — an operator-visible physical-envelope breach. The
    trial artifact records this distinctly from ``vendor_error`` so the
    blind rater can filter thermal-aborted trials out of the sample.
    """

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
    thermal_event: Any | None = None,
    thermal_poll_seconds: float = 1.0,
    fact_anchor_urls: list[str] | None = None,
    enable_fact_check: bool = True,
    enable_license_grounding: bool = True,
    enable_rubric_critique: bool = True,
    rubric_lines: list[str] | None = None,
    enable_cove: bool = True,
    enable_claim_support_gate: bool = True,
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
    # thread_id is assigned per-attempt inside _invoke_once() below so
    # each retry gets a fresh LangGraph checkpoint namespace.

    # Stage 6.3.1 prompt anchoring: wrap the raw fixture question in the
    # answer-agnostic structural scaffold (Positions A-E). See
    # harness/prompts.py for the full contract.
    anchored_question = build_anchored_user_turn(
        question, fact_anchor_urls=fact_anchor_urls
    )

    cited_urls: list[str] = []
    start = time.monotonic()

    # Stage 6.3.2 · MCP retrieval gate (runtime enforcement).
    #
    # Two shims wrap ODR's ainvoke, both here in the harness (vendor tree
    # stays pristine per Stage 6.2 substrate lock + ADR-007 porting rules):
    #
    # 1. Vendor-bug retry. ODR upstream d337ae3 assumes hosted-model schema
    #    conformance (deep_researcher.py:275 does `tool_call["args"]
    #    ["reflection"]` with no fallback). Small local models freelance
    #    tool argument keys. On any exception during ainvoke, retry once
    #    with a fresh thread_id and identical config.
    #
    # 2. Retrieval gate. Empty `raw_notes` on the returned state means the
    #    supervisor emitted a final report without any researcher subgraph
    #    ever running an MCP tool (parametric-memory answer). This is the
    #    Stage 6.3.1 failure mode empirically observed on n=2 valid trials.
    #    On zero-`raw_notes` completion, re-invoke once with an escalated
    #    directive appended to the user turn. Bounded to one retry per
    #    trial to keep the sample budget stable.
    #
    # Both retries stay inside the same trial artifact; only the final
    # attempt's outputs land in `metrics`. Retry counts and reasons are
    # recorded in `metrics.trajectory` so the blind rater and any future
    # analysis can see them.
    async def _invoke_once(user_content: str) -> dict:
        cfg = dict(config)
        cfg["configurable"] = dict(config["configurable"])
        cfg["configurable"]["thread_id"] = str(uuid.uuid4())

        # Stage 6.3.2 thermal watchdog. When ``thermal_event`` is set by
        # GPUMonitor upon crossing the abort threshold, race the ainvoke
        # against a poller task; on breach, cancel ainvoke and raise
        # ThermalAbort. Colossus runs the display on the same RTX 5090 as
        # Ollama, so a driver crash takes down the desktop — hence the
        # hard cancel rather than a soft slowdown.
        invoke_coro = deep_researcher.ainvoke(
            {"messages": [{"role": "user", "content": user_content}]},
            config=cfg,
        )
        if thermal_event is None:
            return await invoke_coro

        invoke_task = asyncio.create_task(invoke_coro)

        async def _watchdog() -> None:
            while not invoke_task.done():
                if thermal_event.is_set():
                    return
                await asyncio.sleep(thermal_poll_seconds)

        watchdog_task = asyncio.create_task(_watchdog())
        done, _pending = await asyncio.wait(
            {invoke_task, watchdog_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if invoke_task in done:
            watchdog_task.cancel()
            try:
                await watchdog_task
            except BaseException:  # noqa: BLE001
                pass
            return invoke_task.result()

        # Thermal breach. Cancel ainvoke; give it up to 5s to unwind.
        invoke_task.cancel()
        try:
            await asyncio.wait_for(invoke_task, timeout=5.0)
        except BaseException:  # noqa: BLE001
            pass
        raise ThermalAbort(
            "GPU thermal watchdog fired during ainvoke; task cancelled."
        )

    result: dict | None = None
    last_exc: Exception | None = None
    attempts: list[dict] = []

    # ---- Shim 1: vendor-bug retry (max 2 attempts) ----
    # A ThermalAbort is NEVER retried — the physical envelope is what it
    # is, and re-attempting will just re-breach. Vendor bugs are retried
    # once. This is the difference between a schema-drift bug (retriable)
    # and a real-world constraint (not).
    thermal_aborted = False
    for attempt in range(2):
        try:
            result = await _invoke_once(anchored_question)
            attempts.append({"attempt": attempt + 1, "outcome": "ok"})
            last_exc = None
            break
        except ThermalAbort as exc:
            last_exc = exc
            thermal_aborted = True
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "outcome": "thermal_abort",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            break  # no retry: physical envelope, not schema drift
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "outcome": "vendor_error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    # ---- Shim 2: retrieval gate (only if shim 1 landed a result) ----
    # Skip the gate on thermal abort — no point re-running under a breach.
    if result is not None and not thermal_aborted:
        raw_notes = result.get("raw_notes", []) or []
        if not raw_notes:
            escalated = (
                anchored_question
                + "\n\n### RETRIEVAL GATE (mandatory)\n"
                "Your previous attempt on this question emitted a final report "
                "without invoking any MCP search tool. That is a discipline "
                "failure. Do NOT answer from memory. You MUST call the MCP "
                "search tool at least three times, on distinct queries, "
                "before emitting any final report. Every claim in your final "
                "report must cite a URL that appeared in an MCP search result "
                "during THIS run. If a claim cannot be so cited, drop the "
                "claim rather than fabricating a source."
            )
            attempts.append(
                {
                    "attempt": len(attempts) + 1,
                    "outcome": "retrieval_gate_retry",
                    "reason": "raw_notes empty on first successful invocation",
                }
            )
            try:
                retry_result = await _invoke_once(escalated)
                result = retry_result
                attempts[-1]["outcome"] = "retrieval_gate_retry_ok"
            except Exception as exc:  # noqa: BLE001
                # Keep the pre-gate result; record the gate failure.
                attempts[-1]["outcome"] = "retrieval_gate_retry_failed"
                attempts[-1]["error"] = f"{type(exc).__name__}: {exc}"

    # ---- Shim 3: fact-check (URL verification, one retry) ----
    # Post-Stage 6.3.2 (blind rating 1.33/6): the retrieval gate is
    # firing but the model still fabricates URLs and swaps SPDX
    # identifiers. This shim verifies every URL cited in the final
    # report against the live network. If any URL fails to resolve
    # (DNS, HTTP 4xx/5xx, timeout, connect error), we re-invoke once
    # with a correction directive listing the failed URLs.
    #
    # Retry rules:
    #   - Runs only if shim-2 produced a result (final_report present)
    #     and enable_fact_check is True.
    #   - Skipped after ThermalAbort (no re-invoke under thermal breach).
    #   - Bounded to one retry per trial. If retry ALSO cites failing
    #     URLs, those URLs are annotated `[unverified]` in the final
    #     artifact and no further retry is issued.
    #   - The retry's own output is verified in turn and its unverified
    #     URLs are annotated the same way.

    fact_check_events: list[dict] = []
    if (
        enable_fact_check
        and result is not None
        and not thermal_aborted
    ):
        prelim_report = str(result.get("final_report", ""))
        prelim_urls = extract_urls(prelim_report)
        if prelim_urls:
            try:
                verifications = await verify_urls(prelim_urls)
            except Exception as exc:  # noqa: BLE001
                # Verifier itself failed — log, skip shim entirely.
                fact_check_events.append(
                    {
                        "pass": "initial",
                        "outcome": "verifier_error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                verifications = {}
            unverified_first = [
                u for u, r in verifications.items() if not r.ok
            ]
            fact_check_events.append(
                {
                    "pass": "initial",
                    "urls_checked": len(verifications),
                    "urls_unverified": len(unverified_first),
                    "unverified": unverified_first,
                    "kinds": {
                        u: r.kind
                        for u, r in verifications.items()
                        if not r.ok
                    },
                }
            )
            if unverified_first:
                # One retry with correction directive.
                correction_turn = (
                    anchored_question
                    + "\n\n"
                    + build_fact_check_correction_directive(unverified_first)
                )
                attempts.append(
                    {
                        "attempt": len(attempts) + 1,
                        "outcome": "fact_check_retry",
                        "reason": (
                            f"{len(unverified_first)} of {len(verifications)} "
                            "cited URLs failed live verification"
                        ),
                    }
                )
                try:
                    retry_result = await _invoke_once(correction_turn)
                except ThermalAbort as exc:
                    attempts[-1]["outcome"] = "fact_check_retry_thermal_abort"
                    attempts[-1]["error"] = f"{type(exc).__name__}: {exc}"
                    # Keep the pre-fact-check result; annotate its
                    # unverified URLs in the final block below.
                except Exception as exc:  # noqa: BLE001
                    attempts[-1]["outcome"] = "fact_check_retry_failed"
                    attempts[-1]["error"] = f"{type(exc).__name__}: {exc}"
                else:
                    attempts[-1]["outcome"] = "fact_check_retry_ok"
                    result = retry_result
                    # Re-verify the retry's URLs so persistent failures
                    # still get annotated.
                    retry_report = str(result.get("final_report", ""))
                    retry_urls = extract_urls(retry_report)
                    if retry_urls:
                        try:
                            retry_verifs = await verify_urls(retry_urls)
                        except Exception as exc:  # noqa: BLE001
                            fact_check_events.append(
                                {
                                    "pass": "retry",
                                    "outcome": "verifier_error",
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                            )
                            retry_verifs = {}
                        unverified_after = [
                            u for u, r in retry_verifs.items() if not r.ok
                        ]
                        fact_check_events.append(
                            {
                                "pass": "retry",
                                "urls_checked": len(retry_verifs),
                                "urls_unverified": len(unverified_after),
                                "unverified": unverified_after,
                                "kinds": {
                                    u: r.kind
                                    for u, r in retry_verifs.items()
                                    if not r.ok
                                },
                            }
                        )

    # ---- Shims 4/6/7/8 (Stage 6.3.4): additive post-fact-check passes ----
    # These shims only run once shim-3 has produced (or preserved) a
    # result, and are skipped after thermal abort. They mutate the
    # in-memory `final_report_override`; the finalize block below reads
    # from it if set. Each shim records its outcome in the trajectory
    # regardless of whether it actually changed the text.
    final_report_override: str | None = None
    shim_events: list[dict] = []

    if result is not None and not thermal_aborted:
        current_report = str(result.get("final_report", ""))
        current_notes = result.get("raw_notes") or []
        current_notes_text = "\n".join(
            str(n) for n in current_notes if n is not None
        )

        # ---- Shim 4: LICENSE-file grounding ----
        if enable_license_grounding and current_report:
            try:
                cited_urls_now = extract_urls(current_report)
                license_facts = await license_grounding.ground_licenses(
                    cited_urls_now
                )
                directive = license_grounding.build_license_correction_directive(
                    license_facts
                )
                shim_events.append(
                    {
                        "shim": "license_grounding",
                        "facts": [
                            {
                                "owner": f.owner,
                                "repo": f.repo,
                                "ok": f.ok,
                                "license_family": f.license_family,
                                "source_url": f.source_url,
                            }
                            for f in license_facts
                        ],
                        "directive_emitted": bool(directive),
                    }
                )
                if directive:
                    correction_turn = anchored_question + "\n\n" + directive
                    try:
                        retry_result = await _invoke_once(correction_turn)
                    except ThermalAbort as exc:
                        shim_events[-1]["retry_outcome"] = "thermal_abort"
                        shim_events[-1]["error"] = f"{type(exc).__name__}: {exc}"
                        thermal_aborted = True
                    except Exception as exc:  # noqa: BLE001
                        shim_events[-1]["retry_outcome"] = "retry_failed"
                        shim_events[-1]["error"] = f"{type(exc).__name__}: {exc}"
                    else:
                        shim_events[-1]["retry_outcome"] = "retry_ok"
                        result = retry_result
                        current_report = str(result.get("final_report", ""))
                        current_notes = result.get("raw_notes") or []
                        current_notes_text = "\n".join(
                            str(n) for n in current_notes if n is not None
                        )
            except Exception as exc:  # noqa: BLE001
                shim_events.append(
                    {
                        "shim": "license_grounding",
                        "outcome": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

        # ---- Shim 6: rubric self-critique ----
        if (
            enable_rubric_critique
            and rubric_lines
            and current_report
            and not thermal_aborted
        ):
            critique_turn = rubric_critique.build_rubric_critique_turn(
                current_report, rubric_lines
            )
            try:
                critique_result = await _invoke_once(critique_turn)
            except ThermalAbort as exc:
                shim_events.append(
                    {
                        "shim": "rubric_critique",
                        "outcome": "thermal_abort",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                thermal_aborted = True
            except Exception as exc:  # noqa: BLE001
                shim_events.append(
                    {
                        "shim": "rubric_critique",
                        "outcome": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            else:
                critique_text = str(critique_result.get("final_report", ""))
                rewritten = rubric_critique.extract_rewritten_report(
                    critique_text
                )
                if rewritten:
                    current_report = rewritten
                    shim_events.append(
                        {
                            "shim": "rubric_critique",
                            "outcome": "rewrite_ok",
                            "rubric_points": len(rubric_lines),
                        }
                    )
                else:
                    shim_events.append(
                        {
                            "shim": "rubric_critique",
                            "outcome": "no_fenced_output",
                        }
                    )

        # ---- Shim 7: chain-of-verification ----
        if enable_cove and current_report and not thermal_aborted:
            claims = cove.extract_claims(current_report, max_claims=6)
            if len(claims) >= 2:
                # Answer each sub-question via a single ainvoke.
                verified: list[tuple[cove.CoveClaim, str]] = []
                cove_answers: list[dict] = []
                for claim in claims:
                    subq = cove.build_sub_question(claim)
                    try:
                        subq_result = await _invoke_once(subq)
                    except ThermalAbort as exc:
                        shim_events.append(
                            {
                                "shim": "cove",
                                "outcome": "thermal_abort",
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        thermal_aborted = True
                        break
                    except Exception as exc:  # noqa: BLE001
                        cove_answers.append(
                            {
                                "claim": claim.source_sentence,
                                "outcome": "error",
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        verified.append((claim, ""))
                        continue
                    answer = str(subq_result.get("final_report", ""))
                    verified.append((claim, answer))
                    cove_answers.append(
                        {
                            "claim": claim.source_sentence,
                            "outcome": "answered",
                            "answer_length": len(answer),
                        }
                    )
                if not thermal_aborted and verified:
                    rewrite_turn = cove.build_cove_rewrite_turn(
                        current_report, verified
                    )
                    try:
                        rewrite_result = await _invoke_once(rewrite_turn)
                    except ThermalAbort as exc:
                        shim_events.append(
                            {
                                "shim": "cove",
                                "outcome": "thermal_abort_rewrite",
                                "error": f"{type(exc).__name__}: {exc}",
                                "answers": cove_answers,
                            }
                        )
                        thermal_aborted = True
                    except Exception as exc:  # noqa: BLE001
                        shim_events.append(
                            {
                                "shim": "cove",
                                "outcome": "rewrite_error",
                                "error": f"{type(exc).__name__}: {exc}",
                                "answers": cove_answers,
                            }
                        )
                    else:
                        rewrite_text = str(
                            rewrite_result.get("final_report", "")
                        )
                        rewritten = cove.extract_rewritten_report(rewrite_text)
                        if rewritten:
                            current_report = rewritten
                            shim_events.append(
                                {
                                    "shim": "cove",
                                    "outcome": "rewrite_ok",
                                    "claims_verified": len(verified),
                                    "answers": cove_answers,
                                }
                            )
                        else:
                            shim_events.append(
                                {
                                    "shim": "cove",
                                    "outcome": "no_fenced_output",
                                    "claims_verified": len(verified),
                                    "answers": cove_answers,
                                }
                            )
            else:
                shim_events.append(
                    {
                        "shim": "cove",
                        "outcome": "insufficient_claims",
                        "claims_found": len(claims),
                    }
                )

        # ---- Shim 8: claim-support gate (pure post-processing) ----
        if enable_claim_support_gate and current_report:
            notes_urls = extract_urls(current_notes_text)
            unsupported = claim_support.find_unsupported_claims(
                current_report, notes_urls, current_notes_text
            )
            if unsupported:
                current_report = claim_support.apply_unsupported_marks(
                    current_report, unsupported
                )
            shim_events.append(
                {
                    "shim": "claim_support",
                    "unsupported_count": len(unsupported),
                    "unsupported": [
                        {
                            "kind": u.claim.kind,
                            "subject": u.claim.subject,
                            "object": u.claim.object,
                        }
                        for u in unsupported
                    ],
                }
            )

        final_report_override = current_report

    # ---- Finalize metrics ----
    try:
        if result is None:
            # Both shim-1 attempts raised. Surface the last exception.
            assert last_exc is not None
            raise last_exc

        if final_report_override is not None:
            final_report = final_report_override
        else:
            final_report = str(result.get("final_report", ""))

        # Annotate persistent unverified URLs in the FINAL report body
        # so the blind rater sees them inline. Recomputes verification
        # on the FINAL text (post-retry if retry ran), rather than
        # trusting the retry pass's cached results, because the retry
        # may have introduced new URLs the retry-pass verify missed.
        annotation_urls: list[str] = []
        if enable_fact_check and final_report:
            final_urls = extract_urls(final_report)
            if final_urls:
                try:
                    final_verifs = await verify_urls(final_urls)
                except Exception:  # noqa: BLE001
                    final_verifs = {}
                final_report, annotation_urls = annotate_unverified(
                    final_report, final_verifs
                )

        metrics.final_answer = final_report
        metrics.final_confidence = ""  # ODR does not emit a confidence score

        cited_urls = extract_urls(final_report)
        # Strip the `[unverified]` marker from the evidence URL list — the
        # marker sits between the URL and the tag, so the raw URL is
        # already the token that regex captured.
        metrics.final_evidences = [
            {"evidence": "(auto-extracted from ODR report body)", "url": u}
            for u in cited_urls
            if not u.startswith("[unverified]")
        ]
        notes = result.get("notes")
        if notes is not None:
            metrics.trajectory.append({"notes": notes})
        raw_notes = result.get("raw_notes") or []
        metrics.trajectory.append({"raw_notes_count": len(raw_notes)})
        if fact_check_events:
            metrics.trajectory.append({"fact_check": fact_check_events})
        if shim_events:
            metrics.trajectory.append({"shim_events": shim_events})
        if annotation_urls:
            metrics.trajectory.append(
                {"final_unverified_urls": annotation_urls}
            )
    except Exception as exc:  # noqa: BLE001
        metrics.error = f"{type(exc).__name__}: {exc}"
    finally:
        metrics.trajectory.append({"attempts": attempts})
        metrics.latency_seconds = time.monotonic() - start
        metrics.source_diversity = unique_domain_count(cited_urls)

    return metrics


__all__ = ["ThermalAbort", "build_odr_config", "run_odr_trial"]
