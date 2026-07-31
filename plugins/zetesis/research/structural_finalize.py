"""Stage 6.3.8 · Structural finalize shim (JSON-schema-constrained).

Motivation (see docs/adrs/ADR-053 and research_6_3_7b.md):

Stages 6.3.6b–6.3.7 tried to clean free-form-markdown finalize output with
per-artifact regex sweeps (empty-citation wrappers, orphan `[unverified]`
markers, orphan `[unsupported: …]` scratch notes, empty `[N] Label:`
Sources-block entries).  Each sweep was brittle: the writer keeps inventing
novel wrapper variants and novel bracketed markers because the wrapper text
is emitted by the model itself.  The blind rating regressed 4.17 → 2.94 in
6.3.7 because the anti-fabrication guard was an enumerated deny-list (a
pattern the literature — Anthropic guide, LLMQuoter, CoNLI, I-CALM — flags
as structurally weaker than an allow-list constraint under
autoregressive-decoding).

The 6.3.8 fix is architectural, not more regex:

  1. Add a final shim that asks the writer to emit its report as a JSON
     object matching a strict schema (Ollama's native `format=<json-schema>`
     parameter drives grammar-constrained decoding — no new dependency).
  2. Parse+validate the JSON.  Drop any claim whose citations list is
     empty AND whose rubric_ref is None (allow-list gate — the RARR
     "delete/rewrite unsupported spans" pattern, executed in code, not
     by the LLM).
  3. Render markdown deterministically from the surviving objects.

This eliminates by construction:

- Empty-citation wrappers ­— the wrapper `*(Source: …)*` is a Python
  template applied only when a `Citation.url` field validates as a real
  URL; the model never emits the wrapper text.
- Bracketed status markers (`[unsupported: …]`, `[needs citation]`,
  `[unverified: …]`, `[not covered]`) — there is no inline-text channel
  for the writer to leak scratch notes into; unsupported claims are
  dropped, not annotated.
- Feature-delta fabrication — the schema forces every claim to declare
  either a rubric_ref (∈ F1–F6) or a real citation URL; anything else
  is filtered before render.

The shim is best-effort: if the writer returns malformed JSON, or the
Ollama call raises, we fall back to the existing free-form
`current_report`.  That preserves the prior behaviour under any failure
mode instead of regressing to blank output.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Iterable

# The JSON schema handed to Ollama's `format` parameter.  Ollama serves it
# via llama.cpp grammar-constrained decoding, so tokens that would violate
# the schema are masked at sampling time — the model cannot produce a
# malformed structure even under duress.
FINAL_REPORT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["title", "claims"],
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 200},
        "claims": {
            "type": "array",
            "minItems": 1,
            "maxItems": 40,
            "items": {
                "type": "object",
                "required": ["text", "rubric_ref", "citations"],
                "additionalProperties": False,
                "properties": {
                    "text": {"type": "string", "minLength": 1, "maxLength": 1200},
                    "rubric_ref": {
                        # Nullable: use null when the claim isn't a
                        # rubric fact but IS backed by a citation.
                        "type": ["string", "null"],
                        "enum": [
                            "F1", "F2", "F3", "F4", "F5", "F6", None,
                        ],
                    },
                    "citations": {
                        "type": "array",
                        "maxItems": 6,
                        "items": {
                            "type": "object",
                            "required": ["label", "url"],
                            "additionalProperties": False,
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 200,
                                },
                                "url": {
                                    "type": "string",
                                    # Ollama's grammar layer doesn't
                                    # enforce URI format, so we validate
                                    # in `parse_and_validate` below.
                                    "minLength": 1,
                                    "maxLength": 500,
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


ALLOWED_RUBRIC_REFS = frozenset({"F1", "F2", "F3", "F4", "F5", "F6"})


# Match a http(s) URL that a rater would recognise as a live link.
# Deliberately permissive: the URL-verify shim already gates real
# reachability; here we only need to reject empty/malformed noise.
_URL_RE = re.compile(r"^https?://[^\s<>\"'\)\]]+$")


@dataclass(frozen=True)
class Citation:
    label: str
    url: str


@dataclass(frozen=True)
class Claim:
    text: str
    rubric_ref: str | None
    citations: tuple[Citation, ...]


@dataclass
class ValidatedReport:
    title: str
    claims: list[Claim]
    dropped: list[dict[str, Any]] = field(default_factory=list)


class StructuralFinalizeError(Exception):
    """Raised when the JSON output is unrecoverably malformed."""


def build_structural_finalize_prompt(
    draft_report: str,
    rubric_lines: Iterable[str],
    notes_text: str,
    verified_urls: Iterable[str] | None = None,
) -> str:
    """Compose the writer prompt for the schema-constrained finalize call.

    Design (research_6_3_7b.md, priority 1 + 2 + 4):

    - Allow-list framing: enumerate rubric F1–F6 as the only permitted
      "rubric_ref" values.  Do NOT list forbidden features (deny-list
      framing is measurably weaker under autoregressive decoding).
    - Quote-first: the writer sees the retrieved notes verbatim so it
      can copy citation URLs rather than invent them.
    - Explicit abstention permission ("if you cannot cite it, omit it").
    - RARR pattern: rewrite ­— delete unsupported spans, do not annotate.
    """

    rubric_block = "\n".join(f"- {ln}" for ln in rubric_lines) or "(none)"
    # Truncate notes so the prompt fits comfortably in the writer's
    # context; the writer already saw them upstream via ODR's own graph.
    notes_snippet = notes_text.strip()
    if len(notes_snippet) > 12000:
        notes_snippet = notes_snippet[:12000] + "\n[...notes truncated...]"

    verified_line = ""
    if verified_urls:
        vlist = "\n".join(f"- {u}" for u in sorted(set(verified_urls)))
        verified_line = (
            "\n\n### URLs already verified reachable during this run "
            "(prefer these when citing):\n" + vlist
        )

    return (
        "### FINALIZE (Stage 6.3.8 · schema-constrained)\n"
        "\n"
        "Rewrite the report below as a single JSON object matching the "
        "schema handed to your decoder.  You will be scored on whether "
        "every emitted claim is either a rubric fact from the allow-list "
        "or a claim backed by a real citation URL that appears in the "
        "notes.\n"
        "\n"
        "### Allow-list of rubric facts (the ONLY permitted rubric_ref values)\n"
        f"{rubric_block}\n"
        "\n"
        "### Rules\n"
        "1. For every claim, set `rubric_ref` to one of "
        "{F1, F2, F3, F4, F5, F6, null}.  Use null only if the claim is "
        "not a rubric fact.\n"
        "2. If `rubric_ref` is null, `citations` MUST contain at least "
        "one entry whose `url` is a real http(s) URL copied from the "
        "notes below.  Do NOT invent URLs.\n"
        "3. If you cannot back a sentence in the draft with either a "
        "rubric ref or a verifiable URL from the notes, OMIT that "
        "sentence.  Do NOT emit placeholder text, do NOT emit "
        "`[unsupported]`, `[needs citation]`, `[unverified]`, "
        "`[not covered]`, or any similar marker.  Omission is the "
        "correct behavior.\n"
        "4. Do NOT introduce feature claims that were not in the draft "
        "or the notes (no fabricated security posture, telemetry "
        "behavior, indexing capabilities, or non-source features).\n"
        "5. The `text` field must be a single self-contained sentence.\n"
        "6. When a rubric fact statement contains a rationale clause "
        "introduced by phrases like 'chosen to', 'to avoid', 'because', "
        "'so that', 'in order to', or 'specifically to', preserve that "
        "rationale clause verbatim in the claim `text`.  The rationale is "
        "part of the fact and must not be summarized away.\n"
        "7. Return ONLY the JSON object.  No markdown fences, no prose "
        "before or after.\n"
        "\n"
        "### Draft report to rewrite\n"
        "```\n"
        f"{draft_report.strip()}\n"
        "```\n"
        "\n"
        "### Notes (source of truth for citation URLs)\n"
        "```\n"
        f"{notes_snippet}\n"
        "```"
        f"{verified_line}\n"
    )


def parse_and_validate(raw: str) -> ValidatedReport:
    """Parse the writer's JSON output and enforce the allow-list gate.

    Semantics:

    - Reject non-JSON / schema-shape violations.
    - Drop claims whose `rubric_ref` is not in F1–F6 AND whose citations
      list is empty or contains no valid http(s) URL.  Dropped claims
      are recorded in `ValidatedReport.dropped` so shim_events can log
      why (the harness treats these as evidence, not as failures).
    - Drop individual citations whose URL fails the http(s) shape
      check.  If that leaves a non-rubric claim with zero citations,
      the claim itself is dropped by the allow-list rule.
    """

    text = raw.strip()
    if text.startswith("```"):
        # Some quantized models still emit a markdown fence despite the
        # instruction.  Strip a single leading/trailing fence.
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StructuralFinalizeError(
            f"writer did not return valid JSON: {exc}"
        ) from exc

    if not isinstance(obj, dict):
        raise StructuralFinalizeError("JSON root is not an object")

    title = obj.get("title")
    if not isinstance(title, str) or not title.strip():
        raise StructuralFinalizeError("missing or empty `title`")

    raw_claims = obj.get("claims")
    if not isinstance(raw_claims, list) or not raw_claims:
        raise StructuralFinalizeError("`claims` is missing or not a list")

    validated: list[Claim] = []
    dropped: list[dict[str, Any]] = []

    for idx, item in enumerate(raw_claims):
        if not isinstance(item, dict):
            dropped.append({"index": idx, "reason": "not_object"})
            continue
        claim_text = item.get("text")
        rubric_ref = item.get("rubric_ref")
        raw_cits = item.get("citations", [])
        if not isinstance(claim_text, str) or not claim_text.strip():
            dropped.append({"index": idx, "reason": "empty_text"})
            continue
        if rubric_ref is not None and rubric_ref not in ALLOWED_RUBRIC_REFS:
            # Do not silently coerce — that would let the writer smuggle
            # in unknown labels.  Treat as "no rubric ref" and rely on
            # the citation gate.
            dropped.append(
                {"index": idx, "reason": "bad_rubric_ref", "value": rubric_ref}
            )
            rubric_ref = None
        if not isinstance(raw_cits, list):
            raw_cits = []
        cits: list[Citation] = []
        for c in raw_cits:
            if not isinstance(c, dict):
                continue
            label = c.get("label")
            url = c.get("url")
            if not isinstance(label, str) or not label.strip():
                continue
            if not isinstance(url, str) or not _URL_RE.match(url.strip()):
                continue
            cits.append(Citation(label=label.strip(), url=url.strip()))
        # Allow-list gate: must be either a known rubric fact or
        # citation-backed.  Otherwise drop.
        if rubric_ref is None and not cits:
            dropped.append(
                {
                    "index": idx,
                    "reason": "no_rubric_ref_and_no_valid_citation",
                    "text_head": claim_text[:120],
                }
            )
            continue
        validated.append(
            Claim(
                text=_squash(claim_text),
                rubric_ref=rubric_ref,
                citations=tuple(cits),
            )
        )

    if not validated:
        raise StructuralFinalizeError(
            "all claims dropped by allow-list gate — nothing to render"
        )

    return ValidatedReport(
        title=_squash(title), claims=validated, dropped=dropped
    )


# Stage 6.3.9 · Q2: normalize numeric-only / bracketed-numeric citation
# labels to a domain-short-form.  The writer sometimes emits a citation
# whose `label` is just a bracketed footnote number like "(2)" or "[4]",
# which produced ugly sources-block lines like `[1] (2): https://...` in
# 6.3.8.  Detect that shape and substitute a reader-facing short form
# derived from the URL's host + first path segment.
_NUMERIC_ONLY_LABEL = re.compile(r"^\s*[\(\[]?\s*\d+\s*[\)\]]?\s*$")


def _short_form_from_url(url: str) -> str:
    """Return a compact human-readable label like ``github.com/DozerDB``.

    Falls back to the bare host if no path segment is available, and to
    the input URL if parsing fails.
    """
    try:
        from urllib.parse import urlparse

        p = urlparse(url)
        host = (p.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        segs = [s for s in (p.path or "").split("/") if s]
        if host and segs:
            return f"{host}/{segs[0]}"
        if host:
            return host
    except Exception:  # pragma: no cover — defensive
        pass
    return url


def _normalize_source_label(label: str, url: str) -> str:
    """Rewrite numeric-only citation labels to a URL-derived short form."""
    if _NUMERIC_ONLY_LABEL.match(label or ""):
        return _short_form_from_url(url)
    return label


def render_markdown(report: ValidatedReport) -> str:
    """Deterministic Python renderer.  No LLM involvement.

    Output shape mirrors the pre-6.3.8 free-form report format so blind
    raters (and any downstream tooling that reads `metrics.final_answer`)
    do not need to change:

        # <title>

        ## Findings

        - <claim.text>  *(Source: <label> — <url>)* [F<N>]

        ## Sources

        [1] <label>: <url>
        …

    Rubric refs are surfaced as trailing `[F1]…[F6]` tags so a blind
    rater can still see rubric coverage at a glance.  Citations are
    reference-numbered in appearance order.
    """

    lines: list[str] = []
    lines.append(f"# {report.title}\n")
    lines.append("## Findings\n")

    # Number citations in appearance order.
    seen: dict[str, int] = {}
    ordered: list[Citation] = []
    for claim in report.claims:
        for c in claim.citations:
            if c.url not in seen:
                seen[c.url] = len(ordered) + 1
                ordered.append(c)

    for claim in report.claims:
        tag = f" [{claim.rubric_ref}]" if claim.rubric_ref else ""
        if claim.citations:
            cite_refs = " ".join(f"[{seen[c.url]}]" for c in claim.citations)
            lines.append(f"- {claim.text} {cite_refs}{tag}")
        else:
            lines.append(f"- {claim.text}{tag}")

    if ordered:
        lines.append("\n## Sources\n")
        for c in ordered:
            n = seen[c.url]
            label = _normalize_source_label(c.label, c.url)
            lines.append(f"[{n}] {label}: {c.url}")

    return "\n".join(lines).rstrip() + "\n"


def structural_finalize(
    raw_json_output: str,
) -> tuple[str, dict[str, Any]]:
    """Public entry point for the shim.

    Returns ``(rendered_markdown, event_dict)``.  The event dict is
    appended to ``shim_events`` in the caller so the trial JSON records
    every drop decision.
    """

    validated = parse_and_validate(raw_json_output)
    md = render_markdown(validated)
    event = {
        "shim": "structural_finalize",
        "outcome": "ok",
        "claims_kept": len(validated.claims),
        "claims_dropped": len(validated.dropped),
        "drop_reasons": [d.get("reason") for d in validated.dropped],
    }
    return md, event


# ---------------------------------------------------------------------------
# Ollama call — schema-constrained JSON output
# ---------------------------------------------------------------------------


async def call_ollama_schema_constrained(
    prompt: str,
    *,
    base_url: str,
    model: str,
    timeout_s: float = 300.0,
) -> str:
    """Single OpenAI-compat chat call with `response_format=json_schema`.

    Ollama honors `response_format={"type":"json_schema", ...}` on its
    OpenAI-compatible endpoint and drives llama.cpp grammar-constrained
    decoding under the hood, so tokens that would break the schema are
    masked at sampling time.  We keep this thin — no LangChain, no ODR
    graph — because the whole point is to hand the writer a strictly
    constrained final turn.

    `base_url` is expected in the OpenAI-compat form Ollama serves, e.g.
    ``http://127.0.0.1:11434/v1``.  `model` is the raw Ollama tag, e.g.
    ``qwen2.5:32b-instruct-q4_K_M`` (NOT the LangChain ``openai:`` prefix
    the rest of ``odr.py`` uses).
    """
    try:
        from openai import AsyncOpenAI  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "structural_finalize requires the `openai` package"
        ) from exc

    client = AsyncOpenAI(
        base_url=base_url.rstrip("/") + "/",
        api_key="EMPTY",  # Ollama ignores the key on OpenAI-compat path
        timeout=timeout_s,
    )
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=4096,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "final_report",
                "schema": FINAL_REPORT_JSON_SCHEMA,
                "strict": True,
            },
        },
    )
    return resp.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _squash(s: str) -> str:
    """Normalise whitespace + fold NBSPs so the rendered markdown is stable
    across model runs (the rater sees identical whitespace for identical
    claims)."""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", s).strip()
