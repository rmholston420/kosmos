"""Contract tests for Stage 6.3.1 prompt anchoring.

Fast tier — no LLM, no network. Verifies the ODR-substrate prompt anchoring
module's structural contract:

  1. ``KOSMOS_MCP_PROMPT`` describes the two tools and enforces the five
     tool-usage discipline clauses.
  2. ``build_anchored_user_turn`` preserves the raw question verbatim and
     prepends the Positions-A-E structural scaffold.
  3. The scaffold is answer-agnostic: no F1-F6 canonical strings, no vendor
     names, no license identifiers, and no fixture-specific artifact names
     leak into the prompt module.
  4. Injection sites in ``harness/odr.py`` route through the anchoring
     functions (not the pre-Stage-6.3.1 inline placeholder prompt).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from plugins.zetesis.research import odr as odr_module
from plugins.zetesis.research.prompts import (
    KOSMOS_MCP_PROMPT,
    build_anchored_user_turn,
)

# ADR-056 sub-slice 1: prompts / odr modules live at
# ``plugins/zetesis/research/`` (this file's parent dir). The fixture stays
# under ``ops/benchmarks/adr_010/fixtures/`` since it is fixture-side data.
_RESEARCH_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = Path(__file__).resolve().parents[4]
_FIXTURE = (
    _REPO_ROOT
    / "ops"
    / "benchmarks"
    / "adr_010"
    / "fixtures"
    / "adr_010_question.json"
)


def _norm(text: str) -> str:
    """Collapse whitespace so line-wrapped phrases match single-line tests."""
    return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------------------------
# 1. KOSMOS_MCP_PROMPT — tool docs + five discipline clauses present
# ---------------------------------------------------------------------------

def test_mcp_prompt_declares_both_tools() -> None:
    assert "search(query, top_k=10)" in KOSMOS_MCP_PROMPT
    assert "visit(url, goal)" in KOSMOS_MCP_PROMPT


def test_mcp_prompt_requires_visited_urls_for_citations() -> None:
    # Rule 1: citations must be visited, not just search-result snippets.
    assert "actually visited" in KOSMOS_MCP_PROMPT
    assert "NOT a citation" in KOSMOS_MCP_PROMPT


def test_mcp_prompt_requires_authoritative_first_party_source() -> None:
    # Rule 2: license/packaging claims must cite first-party sources.
    norm = _norm(KOSMOS_MCP_PROMPT)
    assert "authoritative first-party source" in norm
    for hint in ("LICENSE file", "canonical repository"):
        assert hint in norm


def test_mcp_prompt_encodes_distinct_domain_floor() -> None:
    # Rule 3: three distinct registrable domains required.
    norm = _norm(KOSMOS_MCP_PROMPT)
    assert "THREE" in norm
    assert "registrable domain" in norm


def test_mcp_prompt_has_refusal_guard() -> None:
    # Rule 4: refusal-guard forbids self-contradiction.
    norm = _norm(KOSMOS_MCP_PROMPT)
    assert "unverified from public sources" in norm
    for forbidden in ("hedge", "contradict"):
        assert forbidden in norm


def test_mcp_prompt_locks_fork_vs_plugin_terminology() -> None:
    # Rule 5: fork vs. plugin conflation guard (F1-shape defense).
    norm = _norm(KOSMOS_MCP_PROMPT)
    for term in ('"fork"', '"plugin"'):
        assert term in norm


# ---------------------------------------------------------------------------
# 2. build_anchored_user_turn — preserves raw question + prepends scaffold
# ---------------------------------------------------------------------------

def test_anchored_turn_preserves_raw_question_verbatim() -> None:
    raw = "What are the three most architecturally significant differences?"
    wrapped = build_anchored_user_turn(raw)
    assert wrapped.endswith(raw)


def test_anchored_turn_prepends_scaffold_before_question() -> None:
    raw = "Compare artifact X and artifact Y with citations."
    wrapped = build_anchored_user_turn(raw)
    assert wrapped.index("ANSWER-SHAPE CONTRACT") < wrapped.index(raw)


def test_anchored_turn_declares_all_five_positions_in_order() -> None:
    wrapped = build_anchored_user_turn("dummy question")
    positions = ["Position A", "Position B", "Position C", "Position D", "Position E"]
    indices = [wrapped.index(p) for p in positions]
    assert indices == sorted(indices), "Positions A-E must appear in order"
    # Positions cover the five load-bearing anchors.
    for anchor in ("Packaging model", "License posture", "Source availability", "Feature deltas", "Explicit non-features"):
        assert anchor in wrapped


def test_anchored_turn_requires_reasoning_discipline_section() -> None:
    wrapped = build_anchored_user_turn("dummy question")
    assert "REASONING DISCIPLINE" in wrapped
    # Order arrow may be line-wrapped; check normalized form.
    assert "A \u2192 B \u2192 C \u2192 D \u2192 E" in _norm(wrapped)


def test_anchored_turn_strips_incoming_whitespace() -> None:
    raw = "  padded question  \n"
    wrapped = build_anchored_user_turn(raw)
    assert wrapped.endswith("padded question")
    assert not wrapped.endswith("  ")


# ---------------------------------------------------------------------------
# 3. Answer-agnosticism — no fixture-specific strings leak into the prompts
# ---------------------------------------------------------------------------

_FORBIDDEN_VENDOR_NAMES = ("Neo4j", "DozerDB", "ONgDB", "AGPLv3", "GPLv3", "AGPL-3.0", "multi-database")


def test_mcp_prompt_is_answer_agnostic() -> None:
    for forbidden in _FORBIDDEN_VENDOR_NAMES:
        assert forbidden not in KOSMOS_MCP_PROMPT, (
            f"Answer-agnostic guard: KOSMOS_MCP_PROMPT leaked {forbidden!r}. "
            f"Fixture-specific strings belong only in fixtures/, never in "
            f"harness/prompts.py."
        )


def test_scaffold_is_answer_agnostic() -> None:
    wrapped = build_anchored_user_turn("dummy")
    scaffold_only = wrapped.replace("dummy", "")
    for forbidden in _FORBIDDEN_VENDOR_NAMES:
        assert forbidden not in scaffold_only, (
            f"Answer-agnostic guard: scaffold leaked {forbidden!r}."
        )


def test_prompts_module_never_names_canonical_facts() -> None:
    # Load canonical fact statements from the fixture and confirm none of
    # their identifying phrases appear in the prompt module source.
    prompts_source = (_RESEARCH_DIR / "prompts.py").read_text(encoding="utf-8")
    norm_source = _norm(prompts_source)
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    for fact in fixture["ground_truth"]["canonical_facts"]:
        stmt = fact["statement"]
        # Slide a 40-char window; any window match = leak. Shorter
        # substrings might collide on generic vocabulary like "and its".
        for i in range(0, max(1, len(stmt) - 40), 20):
            window = stmt[i : i + 40]
            norm_window = _norm(window).strip()
            assert norm_window not in norm_source, (
                f"Canonical-fact leak: fact {fact['fact_id']} window "
                f"{norm_window!r} appears in prompts.py"
            )


# ---------------------------------------------------------------------------
# 4. Injection sites in odr.py route through the anchoring functions
# ---------------------------------------------------------------------------

def test_odr_config_injects_kosmos_mcp_prompt() -> None:
    config = odr_module.build_odr_config(
        ollama_base_url="http://127.0.0.1:11434/v1",
        ollama_model="qwen2.5:32b-instruct-q4_K_M",
        mcp_server_url="http://127.0.0.1:8000",
    )
    assert config["configurable"]["mcp_prompt"] is KOSMOS_MCP_PROMPT


def test_odr_config_supplies_api_key_on_every_model_slot() -> None:
    # Regression guard for `OpenAIError: Missing credentials` at
    # Zetesis research start. The OpenAI SDK enforces a non-empty
    # ``api_key`` at client construction time even when ``base_url``
    # targets Ollama's openai-compat endpoint. Every ODR model slot
    # must carry a sentinel key so ``init_chat_model`` does not raise
    # when the operator has no ``OPENAI_API_KEY`` env var (the common
    # local-first case on Colossus).
    config = odr_module.build_odr_config(
        ollama_base_url="http://127.0.0.1:11434/v1",
        ollama_model="qwen2.5:32b-instruct-q4_K_M",
        mcp_server_url="http://127.0.0.1:8000",
    )
    configurable = config["configurable"]
    for slot in (
        "research_model_config",
        "summarization_model_config",
        "final_report_model_config",
        "compression_model_config",
    ):
        assert slot in configurable, f"missing slot {slot!r}"
        assert (
            configurable[slot].get("api_key")
        ), f"{slot!r} missing non-empty api_key"


def test_odr_module_seeds_openai_api_key_env_var() -> None:
    # ODR's ``get_api_key_for_model`` in
    # ``vendor/adr_010/open_deep_research/src/open_deep_research/utils.py``
    # reads ``OPENAI_API_KEY`` from ``os.getenv`` (not from any
    # ``configurable.*.api_key`` slot) for every ``openai:`` prefixed
    # model tag. The odr module must seed a sentinel at import time so
    # the OpenAI SDK does not raise ``OpenAIError: Missing credentials``
    # on Colossus (local-first, no OPENAI_API_KEY exported).
    import os as _os
    assert _os.environ.get("OPENAI_API_KEY"), (
        "OPENAI_API_KEY not seeded by plugins.zetesis.research.odr; "
        "AsyncOpenAI would raise at client construction on Colossus"
    )


def test_odr_module_imports_anchoring_functions() -> None:
    # Guard against a future refactor that reintroduces the pre-6.3.1 inline
    # placeholder prompt in odr.py.
    odr_source = (_RESEARCH_DIR / "odr.py").read_text(encoding="utf-8")
    assert "KOSMOS_MCP_PROMPT" in odr_source
    assert "build_anchored_user_turn" in odr_source
    # The placeholder that shipped in Stage 6.2 must be gone.
    assert "Use them to research thoroughly." not in odr_source
