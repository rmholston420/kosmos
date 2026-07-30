"""HTML fragment rendering for the Stage 4.6 gate app (ADR-051).

Pure-Python string templates — no jinja / mako / any template engine.
Kosmos owns every character emitted to the browser. Each public
function is one HTML fragment; the server routes concatenate
fragments into full responses. Mirrors
:mod:`plugins.tektos.ui.templates` shape.

All user-supplied strings (corpus name, event id, subject, object,
predicate) are escaped via :func:`html.escape` before interpolation.
"""

from __future__ import annotations

from collections.abc import Iterable
from html import escape

from .models import ClaimEnvelope, CorpusSummary, EdgeEnvelope, ProvenanceChain
from .policy import (
    STAGE_46_CORPUS_DETAIL_PATH,
    STAGE_46_INDEX_PATH,
    STAGE_46_PROVENANCE_PATH,
    STAGE_46_QUERY_PATH,
    STAGE_46_TRAVERSE_PATH,
)

__all__ = [
    "render_claim_row",
    "render_corpus_detail",
    "render_dashboard_index",
    "render_edge_row",
    "render_provenance_chain",
    "render_query_results",
    "render_traverse_result",
]


_SHELL_HEAD = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <style>
      body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 72rem; }}
      table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
      th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #ddd; vertical-align: top; }}
      pre {{ background: #f4f4f4; padding: 0.75rem; overflow-x: auto; font-size: 0.85rem; }}
      code {{ background: #f4f4f4; padding: 0.1rem 0.3rem; border-radius: 0.2rem; }}
      .empty {{ color: #666; font-style: italic; }}
      .kind {{ font-family: ui-monospace, monospace; color: #4a5568; }}
      .conf {{ font-family: ui-monospace, monospace; }}
      nav {{ margin-bottom: 1rem; }}
      nav a {{ margin-right: 1rem; }}
      h1, h2 {{ margin-top: 1.5rem; }}
    </style>
  </head>
  <body>
    <nav><a href="{index}">← Dashboard</a></nav>
"""


def _shell(title: str) -> str:
    return _SHELL_HEAD.format(title=escape(title), index=STAGE_46_INDEX_PATH)


def _shell_close() -> str:
    return "  </body>\n</html>\n"


def _fmt_conf(v: float) -> str:
    return f"{v:.3f}"


def _fmt_ts(v: object) -> str:
    return escape(str(v))


def _corpus_detail_url(corpus_name: str) -> str:
    return STAGE_46_CORPUS_DETAIL_PATH.format(corpus_name=corpus_name)


def _provenance_url(corpus_name: str, event_id: str) -> str:
    return STAGE_46_PROVENANCE_PATH.format(
        corpus_name=corpus_name, event_id=event_id
    )


def _traverse_url(corpus_name: str, event_id: str) -> str:
    return STAGE_46_TRAVERSE_PATH.format(
        corpus_name=corpus_name, event_id=event_id
    )


def _query_url(corpus_name: str) -> str:
    return STAGE_46_QUERY_PATH.format(corpus_name=corpus_name)


def render_dashboard_index(summaries: Iterable[CorpusSummary]) -> str:
    """Root dashboard: every landed corpus + its fact/edge counts."""

    rows: list[str] = []
    for s in summaries:
        kind_cell = (
            "<br>".join(
                f'<span class="kind">{escape(k)}</span>: {n}'
                for k, n in s.edge_kind_census
            )
            or '<span class="empty">no typed edges</span>'
        )
        license_cell = (
            ", ".join(escape(li) for li in s.licenses)
            or '<span class="empty">unlicensed</span>'
        )
        rows.append(
            "        <tr>"
            f'<td><a href="{_corpus_detail_url(s.name)}"><code>{escape(s.name)}</code></a></td>'
            f"<td>{s.n_facts}</td>"
            f"<td>{s.n_edges}</td>"
            f"<td>{kind_cell}</td>"
            f"<td>{license_cell}</td>"
            "</tr>"
        )
    body = "\n".join(rows) if rows else (
        '        <tr><td colspan="5" class="empty">no corpora registered</td></tr>'
    )
    return (
        _shell("Kosmos Stage 4.6 gate — corpora")
        + '    <h1>Stage 4.6 exit-gate dashboard</h1>\n'
        + '    <p>Every claim below carries <code>provenance</code>,'
          ' <code>as_of</code>, and <code>confidence</code>'
          ' at the port layer (spec §7 zero-trust).</p>\n'
        + '    <table id="corpora">\n'
        + '      <thead><tr>'
          '<th>Corpus</th><th>Facts</th><th>Edges</th>'
          '<th>Edge kinds</th><th>Licenses</th>'
          '</tr></thead>\n'
        + '      <tbody>\n' + body + '\n      </tbody>\n'
        + '    </table>\n'
        + _shell_close()
    )


def render_corpus_detail(
    summary: CorpusSummary,
    sample_claims: Iterable[ClaimEnvelope],
) -> str:
    rows: list[str] = []
    for c in sample_claims:
        rows.append(
            "        <tr>"
            f'<td><a href="{_provenance_url(c.corpus_name, c.event_id)}">'
            f"<code>{escape(c.event_id)}</code></a></td>"
            f"<td><code>{escape(c.subject)}</code></td>"
            f"<td><code>{escape(c.predicate)}</code></td>"
            f'<td class="conf">{_fmt_conf(c.confidence)}</td>'
            f"<td>{_fmt_ts(c.as_of)}</td>"
            "</tr>"
        )
    body = "\n".join(rows) if rows else (
        '        <tr><td colspan="5" class="empty">no facts</td></tr>'
    )
    return (
        _shell(f"corpus {summary.name}")
        + f'    <h1>Corpus <code>{escape(summary.name)}</code></h1>\n'
        + f"    <p>{summary.n_facts} facts · {summary.n_edges} typed edges · "
          f'<a href="{_query_url(summary.name)}?q=&limit=10">query passthrough</a>'
          '</p>\n'
        + '    <h2>Sample claims</h2>\n'
        + '    <table>\n'
        + '      <thead><tr>'
          '<th>event_id</th><th>subject</th><th>predicate</th>'
          '<th>confidence</th><th>as_of</th>'
          '</tr></thead>\n'
        + '      <tbody>\n' + body + '\n      </tbody>\n'
        + '    </table>\n'
        + _shell_close()
    )


def render_claim_row(claim: ClaimEnvelope) -> str:
    """One row inside a query-result table."""

    return (
        "        <tr>"
        f'<td><a href="{_provenance_url(claim.corpus_name, claim.event_id)}">'
        f"<code>{escape(claim.event_id)}</code></a></td>"
        f"<td><code>{escape(claim.subject)}</code></td>"
        f"<td><code>{escape(claim.predicate)}</code></td>"
        f"<td><code>{escape(claim.object_)}</code></td>"
        f'<td class="conf">{_fmt_conf(claim.confidence)}</td>'
        f"<td>{_fmt_ts(claim.as_of)}</td>"
        "</tr>"
    )


def render_edge_row(edge: EdgeEnvelope, *, corpus_name: str) -> str:
    return (
        "        <tr>"
        f'<td><span class="kind">{escape(edge.kind)}</span></td>'
        f'<td><a href="{_provenance_url(corpus_name, edge.dst_event_id)}">'
        f"<code>{escape(edge.dst_event_id)}</code></a></td>"
        f"<td><code>{escape(edge.dst_subject)}</code></td>"
        f'<td class="conf">{_fmt_conf(edge.dst_confidence)}</td>'
        "</tr>"
    )


def _render_edge_table(
    edges: Iterable[EdgeEnvelope],
    corpus_name: str,
    empty_label: str,
) -> str:
    rows = [render_edge_row(e, corpus_name=corpus_name) for e in edges]
    body = "\n".join(rows) if rows else (
        f'        <tr><td colspan="4" class="empty">{escape(empty_label)}</td></tr>'
    )
    return (
        '    <table>\n'
        '      <thead><tr>'
        '<th>kind</th><th>dst event_id</th><th>dst subject</th><th>dst confidence</th>'
        '</tr></thead>\n'
        '      <tbody>\n' + body + '\n      </tbody>\n'
        '    </table>\n'
    )


def render_provenance_chain(chain: ProvenanceChain) -> str:
    claim = chain.claim
    upstream_cell = (
        f'<a href="{escape(claim.upstream_url)}">{escape(claim.upstream_url)}</a>'
        if claim.upstream_url
        else '<span class="empty">—</span>'
    )
    license_cell = escape(claim.license) if claim.license else '<span class="empty">—</span>'
    source_commit_cell = (
        f"<code>{escape(claim.source_commit)}</code>"
        if claim.source_commit
        else '<span class="empty">—</span>'
    )
    crm_class_cell = (
        f"<code>{escape(claim.crm_class)}</code>"
        if claim.crm_class
        else '<span class="empty">—</span>'
    )
    return (
        _shell(f"provenance · {claim.event_id}")
        + '    <h1>Provenance chain</h1>\n'
        + f'    <p>Corpus <a href="{_corpus_detail_url(claim.corpus_name)}">'
          f'<code>{escape(claim.corpus_name)}</code></a> · '
          f'event <code>{escape(claim.event_id)}</code></p>\n'
        + '    <table>\n'
        + '      <tbody>\n'
        + f'        <tr><th>subject</th><td><code>{escape(claim.subject)}</code></td></tr>\n'
        + f'        <tr><th>predicate</th><td><code>{escape(claim.predicate)}</code></td></tr>\n'
        + f'        <tr><th>object</th><td><code>{escape(claim.object_)}</code></td></tr>\n'
        + f'        <tr><th>as_of</th><td>{_fmt_ts(claim.as_of)}</td></tr>\n'
        + f'        <tr><th>provenance</th><td><code>{escape(claim.provenance)}</code></td></tr>\n'
        + f'        <tr><th>confidence</th><td class="conf">{_fmt_conf(claim.confidence)}</td></tr>\n'
        + f'        <tr><th>source_commit</th><td>{source_commit_cell}</td></tr>\n'
        + f'        <tr><th>license</th><td>{license_cell}</td></tr>\n'
        + f'        <tr><th>upstream_url</th><td>{upstream_cell}</td></tr>\n'
        + f'        <tr><th>crm_class</th><td>{crm_class_cell}</td></tr>\n'
        + '      </tbody>\n'
        + '    </table>\n'
        + '    <h2>Outbound typed edges</h2>\n'
        + _render_edge_table(chain.outbound, claim.corpus_name, "no outbound edges")
        + '    <h2>Inbound typed edges</h2>\n'
        + _render_edge_table(chain.inbound, claim.corpus_name, "no inbound edges")
        + f'    <p><a href="{_traverse_url(claim.corpus_name, claim.event_id)}">Traverse outbound edges only →</a></p>\n'
        + _shell_close()
    )


def render_query_results(
    *,
    corpus_name: str,
    query: str,
    hits: Iterable[ClaimEnvelope],
) -> str:
    rows = [render_claim_row(c) for c in hits]
    body = "\n".join(rows) if rows else (
        '        <tr><td colspan="6" class="empty">no hits</td></tr>'
    )
    return (
        _shell(f"query · {corpus_name}")
        + f'    <h1>Temporal query — <code>{escape(corpus_name)}</code></h1>\n'
        + f'    <p>Query: <code>{escape(query) if query else "(no filter)"}</code></p>\n'
        + '    <table>\n'
        + '      <thead><tr>'
          '<th>event_id</th><th>subject</th><th>predicate</th>'
          '<th>object</th><th>confidence</th><th>as_of</th>'
          '</tr></thead>\n'
        + '      <tbody>\n' + body + '\n      </tbody>\n'
        + '    </table>\n'
        + _shell_close()
    )


def render_traverse_result(
    *,
    corpus_name: str,
    event_id: str,
    edges: Iterable[EdgeEnvelope],
) -> str:
    return (
        _shell(f"traverse · {event_id}")
        + '    <h1>Outbound edges</h1>\n'
        + f'    <p>Corpus <code>{escape(corpus_name)}</code> · '
          f'event <a href="{_provenance_url(corpus_name, event_id)}">'
          f'<code>{escape(event_id)}</code></a></p>\n'
        + _render_edge_table(edges, corpus_name, "no outbound edges")
        + _shell_close()
    )
