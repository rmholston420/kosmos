"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import type { ElementDefinition, StylesheetCSS, Core } from "cytoscape";
import {
  kernelClient,
  type GraphEdge,
  type GraphNode,
  type GraphNodeDetail,
  type Panel,
} from "../../lib/kernel-client";

// ADR-070 (Stage 1.5 Wave D). Reads the kernel /api/gnosis/graph/*
// endpoints and renders a MemoryPort ⊕ Zetesis provenance graph via
// cytoscape.js (vendored per PORTING_LEDGER entry). Zero-trust
// discipline preserved: never fabricates provenance/confidence; empty
// or error state uses class name only, never a raw exception message.

// Dynamic import: ``react-cytoscapejs`` (and its transitive cytoscape
// import) touches ``window`` at module scope. Static-export Next builds
// pre-render pages once at build time — loading with ``ssr: false`` keeps
// the initial HTML clean and defers the graph runtime to the browser.
const CytoscapeComponent = dynamic(
  () => import("react-cytoscapejs"),
  { ssr: false, loading: () => null },
);

const CORPORA: readonly (
  | "all"
  | "synthetic-lifeline"
  | "humanities-cidoc-sample"
  | "rigpa-export"
  | "superpowers"
  | "humanities-bilara"
)[] = [
  "all",
  "synthetic-lifeline",
  "humanities-cidoc-sample",
  "rigpa-export",
  "superpowers",
  "humanities-bilara",
];

type CorpusChoice = (typeof CORPORA)[number];

interface FetchState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  loading: boolean;
  errorClass: string | null;
}

const INITIAL: FetchState = {
  nodes: [],
  edges: [],
  loading: true,
  errorClass: null,
};

function toElements(nodes: GraphNode[], edges: GraphEdge[]): ElementDefinition[] {
  const nodeEls: ElementDefinition[] = nodes.map((n) => ({
    data: {
      id: n.id,
      label: n.label,
      kind: n.kind,
      provenance: n.provenance ?? "",
      confidence: n.confidence ?? 0,
    },
  }));
  const nodeIds = new Set(nodes.map((n) => n.id));
  const edgeEls: ElementDefinition[] = edges
    .filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target))
    .map((e) => ({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        kind: e.kind,
      },
    }));
  return [...nodeEls, ...edgeEls];
}

const STYLESHEET: StylesheetCSS[] = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "font-size": "10px",
      color: "#e6e6e6",
      "text-outline-color": "#111",
      "text-outline-width": 1,
      "background-color": "#4a90e2",
      width: 22,
      height: 22,
    },
  },
  {
    selector: 'node[kind = "zetesis_report"]',
    style: { "background-color": "#e2884a", shape: "diamond" },
  },
  {
    selector: 'node[kind = "object"]',
    style: { "background-color": "#7a4ae2" },
  },
  {
    selector: "edge",
    style: {
      width: 1,
      "line-color": "#666",
      "target-arrow-color": "#666",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      label: "data(label)",
      "font-size": "8px",
      color: "#aaa",
      "text-background-color": "#111",
      "text-background-opacity": 0.7,
      "text-background-padding": "2px",
    },
  },
];

export default function MemoryIntegrityPanel({ panels }: { panels: Panel[] }) {
  const [corpus, setCorpus] = useState<CorpusChoice>("all");
  const [state, setState] = useState<FetchState>(INITIAL);
  const [selected, setSelected] = useState<GraphNodeDetail | null>(null);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const cyRef = useRef<Core | null>(null);

  const load = useCallback(async (choice: CorpusChoice) => {
    setState((s) => ({ ...s, loading: true, errorClass: null }));
    try {
      const corpusParam = choice === "all" ? undefined : choice;
      const [nodesRes, edgesRes] = await Promise.all([
        kernelClient.fetchGraphNodes({ corpus: corpusParam, limit: 100 }),
        kernelClient.fetchGraphEdges({ corpus: corpusParam, limit: 100 }),
      ]);
      setState({
        nodes: nodesRes.nodes,
        edges: edgesRes.edges,
        loading: false,
        errorClass: null,
      });
    } catch (err) {
      setState({
        nodes: [],
        edges: [],
        loading: false,
        errorClass: err instanceof Error ? err.constructor.name : "Error",
      });
    }
  }, []);

  useEffect(() => {
    void load(corpus);
  }, [corpus, load]);

  const elements = useMemo(
    () => toElements(state.nodes, state.edges),
    [state.nodes, state.edges]
  );

  const onCy = useCallback((cy: Core) => {
    cyRef.current = cy;
    cy.on("tap", "node", async (evt) => {
      const nodeId = evt.target.id() as string;
      try {
        const detail = await kernelClient.fetchGraphNode(nodeId);
        setSelected(detail);
        setInspectorOpen(true);
      } catch {
        /* swallow — inspector stays closed on lookup failure */
      }
    });
  }, []);

  const closeInspector = useCallback(() => setInspectorOpen(false), []);

  return (
    <div
      data-testid="memory-integrity-panel"
      data-panel-count={panels.length}
      style={{
        border: "1px solid var(--rgpa-border, #333)",
        padding: "12px",
        margin: "12px 0",
        borderRadius: "6px",
        background: "var(--rgpa-surface-1, #1a1a1a)",
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "8px",
        }}
      >
        <h3
          data-testid="memory-integrity-title"
          style={{ margin: 0, fontSize: "14px", color: "var(--rgpa-fg-1, #e6e6e6)" }}
        >
          Memory Integrity — Provenance Graph
        </h3>
        <label
          data-testid="memory-integrity-corpus-label"
          style={{ display: "flex", gap: "6px", alignItems: "center", fontSize: "12px" }}
        >
          <span>Corpus:</span>
          <select
            data-testid="memory-integrity-corpus-select"
            value={corpus}
            onChange={(e) => setCorpus(e.target.value as CorpusChoice)}
          >
            {CORPORA.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      </header>

      {state.loading && (
        <p
          data-testid="memory-integrity-loading"
          role="status"
          style={{ color: "var(--rgpa-fg-2, #999)", fontSize: "12px" }}
        >
          Loading provenance graph…
        </p>
      )}

      {!state.loading && state.errorClass && (
        <p
          data-testid="memory-integrity-error"
          role="alert"
          style={{ color: "var(--rgpa-danger, #e24a4a)", fontSize: "12px" }}
        >
          Graph unavailable ({state.errorClass})
        </p>
      )}

      {!state.loading && !state.errorClass && state.nodes.length === 0 && (
        <p
          data-testid="memory-integrity-empty"
          role="status"
          style={{ color: "var(--rgpa-fg-2, #999)", fontSize: "12px" }}
        >
          No nodes for corpus{" "}
          <code>{corpus}</code>. Try a different corpus.
        </p>
      )}

      {!state.loading && !state.errorClass && state.nodes.length > 0 && (
        <div
          data-testid="memory-integrity-canvas-wrap"
          style={{
            width: "100%",
            height: "480px",
            border: "1px solid var(--rgpa-border, #333)",
            borderRadius: "4px",
            background: "#0e0e0e",
          }}
        >
          <CytoscapeComponent
            elements={elements}
            style={{ width: "100%", height: "100%" }}
            layout={{ name: "cose", animate: false }}
            stylesheet={STYLESHEET as unknown as StylesheetCSS[]}
            cy={onCy}
          />
        </div>
      )}

      {inspectorOpen && selected && (
        <aside
          data-testid="memory-integrity-inspector"
          role="dialog"
          aria-label="Node inspector"
          style={{
            position: "fixed",
            right: 0,
            top: 0,
            bottom: 0,
            width: "360px",
            background: "var(--rgpa-surface-1, #1a1a1a)",
            borderLeft: "1px solid var(--rgpa-border, #333)",
            padding: "16px",
            zIndex: 40,
            overflowY: "auto",
          }}
        >
          <button
            data-testid="memory-integrity-inspector-close"
            onClick={closeInspector}
            style={{ float: "right" }}
          >
            ×
          </button>
          <h4
            data-testid="memory-integrity-inspector-title"
            style={{ marginTop: 0 }}
          >
            {selected.node.label}
          </h4>
          <dl style={{ fontSize: "12px" }}>
            <dt>ID</dt>
            <dd data-testid="memory-integrity-inspector-id">
              <code>{selected.node.id}</code>
            </dd>
            <dt>Kind</dt>
            <dd data-testid="memory-integrity-inspector-kind">{selected.node.kind}</dd>
            <dt>Provenance</dt>
            <dd data-testid="memory-integrity-inspector-provenance">
              {selected.node.provenance ?? "—"}
            </dd>
            <dt>Confidence</dt>
            <dd data-testid="memory-integrity-inspector-confidence">
              {selected.node.confidence == null
                ? "—"
                : selected.node.confidence.toFixed(3)}
            </dd>
            <dt>Neighbors</dt>
            <dd data-testid="memory-integrity-inspector-neighbor-count">
              {selected.neighbor_count}
            </dd>
          </dl>
          {selected.neighbors.length > 0 && (
            <ul
              data-testid="memory-integrity-inspector-neighbors"
              style={{ fontSize: "11px", paddingLeft: "16px" }}
            >
              {selected.neighbors.map((n) => (
                <li key={n.id}>
                  <code>{n.via_edge_kind}</code> → {n.label}
                </li>
              ))}
            </ul>
          )}
        </aside>
      )}
    </div>
  );
}
