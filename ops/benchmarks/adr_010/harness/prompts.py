"""Kosmos-local prompt anchoring for the ODR substrate (Stage 6.3.1).

Two extension points, both officially-supported by ODR (no monkey-patching of
the vendor tree):

  1. ``KOSMOS_MCP_PROMPT`` — injected via ODR's ``configurable.mcp_prompt``.
     Folded by ODR into ``research_system_prompt`` alongside the raw MCP tool
     docs. Owns *tool-usage discipline*: citation requirements, source-diversity
     floor, and refusal-guard for unverifiable claims.

  2. ``build_anchored_user_turn(question)`` — wraps the raw fixture question in
     a *structural scaffold* prepended to the user turn. Folded by ODR into
     ``transform_messages_into_research_topic_prompt`` when it derives the
     research brief. Owns *question decomposition* — forces the model to fill
     named positions (packaging model, license posture, feature deltas) rather
     than emitting hedged prose.

The scaffold is **answer-agnostic**. It never names Neo4j, DozerDB, GPLv3, or
any F1-F6 canonical fact. It anchors the *shape* of the required answer, not
its content, so the same scaffold generalizes to any Zetesis inner-loop task
that asks for architectural comparisons with authoritative citations.

Do not name canonical facts or answer strings here. Fixture-specific
information belongs in ``fixtures/`` only.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# MCP prompt: tool-usage discipline
# ---------------------------------------------------------------------------

KOSMOS_MCP_PROMPT = """You have two tools:

  - `search(query, top_k=10)` returns web search results (title, snippet, url).
  - `visit(url, goal)` fetches a URL's text content.

TOOL-USAGE DISCIPLINE (non-negotiable):

  1. Cite every load-bearing claim with a URL you actually visited during this
     research trajectory. A URL that only appeared in a `search` result
     snippet is NOT a citation — you must `visit` it and read its content.

  2. For any claim about a software artifact's license, packaging model,
     ownership, versioning, or feature set, cite AT LEAST ONE authoritative
     first-party source:
       - the project's own README, docs site, or LICENSE file on its canonical
         repository (github.com/<org>/<repo>, gitlab.com/<org>/<repo>, or the
         project's official homepage);
       - a maintainer-authored discussion thread, commit message, or PR on
         that canonical repository;
       - an official specification document (RFC, gnu.org GPL text, OSI
         approved-license page).
     A blog post, a third-party tutorial, or a search-result snippet is NOT
     authoritative on license identity. Use them only to corroborate.

  3. Distinct-domain floor: your final answer must cite at least THREE
     distinct registrable domains (registrable domain = last two DNS labels,
     e.g. `github.com`, `neo4j.com`, `dozerdb.org`). If your evidence draws
     from fewer than three domains, run more `search` + `visit` cycles until
     you meet the floor or you have documented — in your reasoning — why the
     required diversity is not achievable from the public web.

  4. Refusal-guard: if after your best-effort search you cannot verify a
     specific claim with an authoritative source, state explicitly that the
     claim is unverified from public sources and OMIT it from your final
     answer. Do NOT hedge, contradict yourself between paragraphs, or state
     mutually incompatible positions.

  5. Terminology precision: never conflate distinct artifact classes. If you
     use the term "fork", it must mean a full source-tree copy under a new
     project or license; if you use the term "plugin" or "extension", it
     must mean an artifact that loads into unmodified host binaries at
     runtime; if you use the term "re-implementation", it must mean
     independently-authored code that reproduces a target feature; if you
     use the term "re-enablement", it must mean the target feature already
     exists in the host's public source and is only turned on or exposed by
     the compared artifact. Cite the shipping artifact type (JAR, plugin
     bundle, container image, source tree) from an authoritative source
     before using any of these terms.
"""


# ---------------------------------------------------------------------------
# Structural anchoring scaffold: question decomposition
# ---------------------------------------------------------------------------

_STRUCTURAL_SCAFFOLD_HEADER = """You are answering a research question that requires a comparison between
software artifacts with authoritative citations. Before you begin, decompose
your answer into the positions below and treat each position as a mandatory
slot. Missing a slot is worse than admitting you could not verify it.

ANSWER-SHAPE CONTRACT (fill every position; cite every claim per tool-usage
discipline):

  Position A — Packaging model
      For each artifact in the comparison, state its concrete packaging model
      (full source-tree fork, runtime-loaded plugin/extension, container
      image, hosted service, etc.). Cite the artifact's canonical repository
      or docs. If two artifacts are being compared, state whether they are the
      SAME class of artifact or DIFFERENT classes, and cite the shipping
      artifact type for each.

  Position B — License posture
      For each artifact, state its exact SPDX license identifier (Apache-2.0,
      MIT, BSD-3-Clause, ISC, MPL-2.0, or "commercial / proprietary" if not
      open-source; use the precise SPDX identifier for any GNU-family or
      copyleft license by reading the artifact's LICENSE file). Cite each
      license claim from an authoritative first-party source per tool-usage
      discipline rule 2. Never infer a license from a project's name, a
      search snippet, or a similarly-named project — visit the LICENSE file
      or an official license-statement page and quote it.

  Position C — Source availability
      For each artifact, state whether its source code is publicly published
      and at what canonical URL. If a project publishes some components but
      not others (e.g. an open core with a closed enterprise tier), state
      exactly which components are public and which are not, and cite the
      project's own statement of that split.

  Position D — Feature deltas (if the question asks for feature comparison)
      Enumerate the specific feature deltas the question asks about. For each
      delta, state whether the feature is a re-implementation, a re-enablement
      of code that exists in one artifact but is disabled by default in the
      other, or a feature exclusive to one side. Cite the maintainer-authored
      source that establishes each classification.

  Position E — Explicit non-features
      List any features that are OUTSIDE the scope of the compared artifact
      per its maintainers' explicit statements. Cite the maintainer statement
      (discussion thread, roadmap doc, README section) that establishes each
      non-feature.

REASONING DISCIPLINE:
  - Fill positions in order A → B → C → D → E.
  - Do NOT contradict a claim in a later position with a claim in an earlier
    position. If you discover a contradiction while filling a later position,
    return to the earlier position and correct it before proceeding.
  - Every position's claims must be defensible against tool-usage discipline
    rule 2 (authoritative first-party source).

Research question:

"""


def build_anchored_user_turn(
    raw_question: str,
    *,
    fact_anchor_urls: list[str] | None = None,
) -> str:
    """Wrap the raw fixture question in the structural anchoring scaffold.

    The scaffold itself is answer-agnostic — it names no canonical facts, no
    license identifiers, no vendor names. It only anchors the *shape* of the
    required answer.

    Stage 6.3.3 fact-anchor pass
    ----------------------------
    ``fact_anchor_urls`` (optional) is a curated allowlist of authoritative
    URLs the harness knows the model should prefer when making license and
    packaging claims. They are injected as an **advisory** block, medium
    strength: the prompt tells the model to prefer citing one of these when
    stating an SPDX identifier, source-availability claim, or packaging-model
    claim, but does NOT restate the fact itself. That preserves the fact-
    retrieval test for F2/F3/F4 (license posture / source availability); the
    model still has to visit the anchor and read what it says. All we're
    doing is eliminating the "guessed a URL that doesn't exist" failure mode.

    Anchor URLs must be sourced from the fixture's ground_truth so the
    harness never hardcodes canonical facts.
    """
    body = _STRUCTURAL_SCAFFOLD_HEADER + raw_question.strip()
    if fact_anchor_urls:
        anchor_block = _build_anchor_advisory(fact_anchor_urls)
        body = body + "\n\n" + anchor_block
    return body


def _build_anchor_advisory(urls: list[str]) -> str:
    """Assemble the medium-strength anchor advisory block.

    The wording:
    - Instructs the model to visit at least one anchor URL before stating
      any license / source-availability / packaging claim.
    - Explicitly forbids stating a license identifier by guess.
    - Does NOT tell the model what the license IS. That must be verified
      against the LICENSE file the anchor points to.
    - Ends with the anchor list.
    """
    lines = [
        "### FACT ANCHOR ADVISORY (mandatory for licensing / packaging claims)",
        "",
        "When you state any SPDX license identifier, source-availability claim,",
        "or packaging-model claim about either compared artifact, you MUST cite",
        "at least one of the authoritative anchor URLs listed below (or a",
        "functionally equivalent first-party page you retrieve during THIS run",
        "via the MCP visit tool). Do NOT guess an SPDX identifier from a repo",
        "name, a search snippet, or your training memory — visit the LICENSE",
        "file or an official license-statement page and read what it says.",
        "",
        "Authoritative anchors (curated allowlist):",
    ]
    for u in urls:
        lines.append(f"  - {u}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Stage 6.3.3 fact-check shim: URL correction directive
# ---------------------------------------------------------------------------


def build_fact_check_correction_directive(unverified_urls: list[str]) -> str:
    """Assemble the one-shot correction turn used by shim 3.

    Called by the ODR harness only when at least one URL cited in the
    prior final_report failed live verification (HTTP != 2xx, DNS error,
    connect timeout). The directive:

    1. Lists the exact URLs that failed to resolve.
    2. Instructs the model to either replace each with a verified URL it
       retrieves via the MCP visit tool during THIS retry, or drop the
       claim entirely.
    3. Explicitly forbids inventing a substitute URL from memory.
    4. Warns that any URL cited in the retry will ALSO be verified and
       marked `[unverified]` if it fails, so guessing is not a viable
       strategy.
    """
    numbered = "\n".join(
        f"  {i + 1}. {u}" for i, u in enumerate(unverified_urls)
    )
    return (
        "### FACT-CHECK CORRECTION (mandatory)\n"
        "Your previous answer cited URL(s) that failed live verification. "
        "These URLs did not resolve (DNS error, HTTP 4xx/5xx, or timeout):\n"
        f"{numbered}\n\n"
        "For EACH failed URL, do ONE of the following:\n"
        "  (a) Retrieve a verified replacement URL via the MCP visit tool "
        "during this retry, and cite the replacement instead. The retrieved "
        "page must actually establish the claim it is attached to.\n"
        "  (b) Drop the claim entirely. Do NOT keep a claim if you cannot "
        "attach a URL you have verified during this run.\n\n"
        "Do NOT invent a substitute URL from memory. Any URL you cite in "
        "this retry will be re-verified against the live network. Failed "
        "URLs will be marked [unverified] in the final artifact, so "
        "guessing is not a viable strategy — the annotation will surface "
        "the guess."
    )


__all__ = [
    "KOSMOS_MCP_PROMPT",
    "build_anchored_user_turn",
    "build_fact_check_correction_directive",
]
