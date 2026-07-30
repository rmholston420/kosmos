"""Contract tests for AREX <tool_call> XML parser.

Validates the exact format documented in the AREX BROWSECOMP_SYSTEM_PROMPT
(vendored at vendor/adr_010/arex_inference/prompts.py). Any deviation
signals an upstream protocol drift that would break the harness.
"""

from __future__ import annotations

from ops.benchmarks.adr_010.harness.arex import parse_tool_call


def test_parses_search_with_json_query_array():
    text = """<think>
    plan phase
    </think>
    <tool_call>
    <function=search>
    <parameter=query>["neo4j community license", "dozerdb plugin architecture"]</parameter>
    </function>
    </tool_call>"""
    parsed = parse_tool_call(text)
    assert parsed is not None
    name, params = parsed
    assert name == "search"
    assert params["query"] == ["neo4j community license", "dozerdb plugin architecture"]


def test_parses_visit_with_string_and_scalar_params():
    text = """<tool_call>
    <function=visit>
    <parameter=url>https://dozerdb.org/</parameter>
    <parameter=goal>identify plugin license</parameter>
    </function>
    </tool_call>"""
    parsed = parse_tool_call(text)
    assert parsed is not None
    name, params = parsed
    assert name == "visit"
    assert params["url"] == "https://dozerdb.org/"
    assert params["goal"] == "identify plugin license"


def test_parses_finish_with_nested_evidences_json():
    text = """<tool_call>
    <function=finish>
    <parameter=answer>DozerDB is a plugin, not a fork.</parameter>
    <parameter=evidences>[
      {"evidence": "GPLv3 plugin", "url": "https://dozerdb.org/"},
      {"evidence": "Bootstrapping approach", "url": "https://github.com/orgs/DozerDB/discussions/1"}
    ]</parameter>
    <parameter=confidence>85%</parameter>
    </function>
    </tool_call>"""
    parsed = parse_tool_call(text)
    assert parsed is not None
    name, params = parsed
    assert name == "finish"
    assert isinstance(params["evidences"], list)
    assert len(params["evidences"]) == 2
    assert params["evidences"][0]["url"] == "https://dozerdb.org/"
    assert params["confidence"] == "85%"


def test_returns_none_when_no_tool_call_present():
    text = "I'll just answer directly: DozerDB extends Neo4j Community."
    assert parse_tool_call(text) is None


def test_handles_multiline_parameter_body():
    text = """<tool_call>
    <function=update_context>
    <parameter=context>Line 1 fact.
Line 2 with [Verified in: https://example.com/x](https://example.com/x).
Line 3 next step.</parameter>
    </function>
    </tool_call>"""
    parsed = parse_tool_call(text)
    assert parsed is not None
    name, params = parsed
    assert name == "update_context"
    assert "Line 1" in params["context"]
    assert "Line 3" in params["context"]
