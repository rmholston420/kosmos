/**
 * Gnosis Graph — ADR-074 D5.
 *
 * Ports the Rigpa-LMS force-graph pattern to Kosmos and wires it to
 * the existing Kosmos kernel endpoints:
 *   - GET /api/gnosis/graph/nodes?corpus&limit
 *   - GET /api/gnosis/graph/edges?corpus&limit
 *
 * The 2D/3D toggle is a shared store (`useGraphDimensionStore`) so the
 * same choice applies to future graph views (Zetesis argument graph,
 * Knowsys backlink graph, etc.) — exactly how Rigpa uses it.
 *
 * SSR safety: `react-force-graph-{2d,3d}` are DOM-only. We import
 * `DimensionalForceGraph` through `next/dynamic({ ssr: false })` to
 * keep Next 16's static export happy.
 */
"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import GraphDimensionToggle from "@/components/graph/GraphDimensionToggle";
import {
  kernelClient,
  type GraphEdge,
  type GraphNode,
} from "@/lib/kernel-client";

// SSR-off wrapper — DOM-only libs cannot run during Next build/export.
const DimensionalForceGraph = dynamic(
  () => import("@/components/graph/DimensionalForceGraph"),
  { ssr: false, loading: () => <p data-testid="graph-loading">Loading graph…</p> },
);

interface ForceGraphNode {
  id: string;
  label: string;
  kind: GraphNode["kind"];
  provenance: string | null;
  confidence: number | null;
}

interface ForceGraphLink {
  id: string;
  source: string;
  target: string;
  kind: string;
  label: string;
  provenance: string | null;
  confidence: number | null;
}

interface GraphViewData {
  nodes: ForceGraphNode[];
  links: ForceGraphLink[];
}

// Backend `_graph_validate_limit` in `kernel/app.py` rejects any
// value outside [1, 100] with HTTP 400. Client pages until `next_cursor`
// is null, capped at `MAX_PAGES` to keep the DOM sane on large corpora
// (community-collapse per ADR-070 D3 is the correct answer at scale).
const NODE_LIMIT = 100;
const EDGE_LIMIT = 100;
const MAX_PAGES = 10; // ADR-075 D4 ceiling: 1000 nodes + 1000 edges.

const KIND_COLOR: Record<GraphNode["kind"], string> = {
  subject: "var(--color-accent, #7dd3fc)",
  object: "var(--color-muted, #a3a3a3)",
  zetesis_report: "var(--color-primary, #f472b6)",
};

export default function GnosisGraphPage() {
  const [corpus, setCorpus] = useState<string>("");
  const [data, setData] = useState<GraphViewData>({ nodes: [], links: [] });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const [pagesFetched, setPagesFetched] = useState<number>(0);
  const [truncated, setTruncated] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setPagesFetched(0);
    setTruncated(false);

    async function loadPaged(): Promise<void> {
      const nodes: ForceGraphNode[] = [];
      const edges: GraphEdge[] = [];
      let nodeCursor: string | undefined = undefined;
      let edgeCursor: string | undefined = undefined;
      let hitCeiling = false;

      // ADR-075 D4: page both node + edge streams in lock-step until
      // either both cursors are null or the MAX_PAGES ceiling is hit.
      for (let page = 0; page < MAX_PAGES; page += 1) {
        if (cancelled) return;
        const [nodePage, edgePage] = await Promise.all([
          nodeCursor === null
            ? Promise.resolve({ nodes: [], next_cursor: null })
            : kernelClient.fetchGraphNodes({
                corpus: corpus || undefined,
                limit: NODE_LIMIT,
                cursor: nodeCursor,
              }),
          edgeCursor === null
            ? Promise.resolve({ edges: [], next_cursor: null })
            : kernelClient.fetchGraphEdges({
                corpus: corpus || undefined,
                limit: EDGE_LIMIT,
                cursor: edgeCursor,
              }),
        ]);
        nodes.push(
          ...nodePage.nodes.map((n) => ({
            id: n.id,
            label: n.label,
            kind: n.kind,
            provenance: n.provenance,
            confidence: n.confidence,
          })),
        );
        edges.push(...(edgePage.edges as GraphEdge[]));
        nodeCursor = nodePage.next_cursor ?? undefined;
        edgeCursor = edgePage.next_cursor ?? undefined;
        if (!cancelled) setPagesFetched(page + 1);
        if (
          (nodePage.next_cursor == null || nodeCursor === null) &&
          (edgePage.next_cursor == null || edgeCursor === null)
        ) {
          nodeCursor = undefined;
          edgeCursor = undefined;
          break;
        }
        if (page === MAX_PAGES - 1 && (nodePage.next_cursor || edgePage.next_cursor)) {
          hitCeiling = true;
        }
      }
      if (cancelled) return;

      const nodeIds = new Set(nodes.map((n) => n.id));
      // Drop edges whose endpoints didn't survive the node page limit.
      const links: ForceGraphLink[] = edges
        .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
        .map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          kind: e.kind,
          label: e.label,
          provenance: e.provenance,
          confidence: e.confidence,
        }));
      setData({ nodes, links });
      setTruncated(hitCeiling);
    }

    loadPaged()
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [corpus]);

  const graphData = useMemo(
    () => ({ nodes: data.nodes, links: data.links }),
    [data],
  );

  return (
    <main data-testid="gnosis-graph-page">
      <header
        style={{
          display: "flex",
          gap: "var(--space-4)",
          alignItems: "center",
          marginBottom: "var(--space-3)",
        }}
      >
        <h1 style={{ marginRight: "auto" }}>Gnosis Graph</h1>
        <label>
          Corpus:{" "}
          <input
            data-testid="graph-corpus-filter"
            value={corpus}
            onChange={(e) => setCorpus(e.target.value)}
            placeholder="(all)"
            style={{ width: "12ch" }}
          />
        </label>
        <GraphDimensionToggle />
        <Link data-testid="graph-back-link" href="/gnosis">
          ← Corpora
        </Link>
      </header>

      {error && (
        <p data-testid="graph-error" role="alert">
          {error}
        </p>
      )}
      {loading && !error && (
        <p data-testid="graph-loading-indicator">Loading…</p>
      )}
      {!loading && !error && data.nodes.length === 0 && (
        <p data-testid="graph-empty">
          No nodes in this corpus. Try another corpus name or leave blank for all.
        </p>
      )}

      <section
        data-testid="graph-canvas-wrapper"
        style={{
          width: "100%",
          height: "70vh",
          border: "1px solid var(--color-border, #333)",
          borderRadius: "var(--radius-2, 6px)",
          background: "var(--color-canvas, #0b0b0b)",
        }}
      >
        <DimensionalForceGraph
          graphData={graphData}
          backgroundColor="var(--color-canvas, #0b0b0b)"
          nodeColor={(n) => KIND_COLOR[(n as ForceGraphNode).kind] ?? "#888"}
          linkColor={() => "var(--color-muted, #6b7280)"}
          nodeLabel={(n) => {
            const node = n as ForceGraphNode;
            const conf =
              node.confidence == null ? "" : ` · ${node.confidence.toFixed(2)}`;
            const prov = node.provenance ? ` · ${node.provenance}` : "";
            return `${node.label} (${node.kind})${conf}${prov}`;
          }}
          linkLabel={(l) => {
            const link = l as ForceGraphLink;
            return link.label || link.kind;
          }}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={0.9}
        />
      </section>

      <footer
        data-testid="graph-stats"
        style={{ marginTop: "var(--space-2)", opacity: 0.75 }}
      >
        {data.nodes.length} nodes · {data.links.length} edges · pages{" "}
        {pagesFetched}/{MAX_PAGES}
        {truncated ? (
          <span data-testid="graph-truncated" style={{ marginLeft: 8 }}>
            · truncated at ceiling; use community collapse for full graph
          </span>
        ) : null}
      </footer>
    </main>
  );
}
