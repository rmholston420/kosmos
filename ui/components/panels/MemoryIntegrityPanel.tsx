"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import type { ElementDefinition, StylesheetStyle, Core } from "cytoscape";
import {
  kernelClient,
  type GraphCommunities,
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

// ADR-071 D5: Golden-ratio hue spacing keeps adjacent communities
// perceptually distinct without any tuned palette.
function communityColor(cid: number | null | undefined): string {
  if (cid == null) return "hsl(0, 0%, 60%)";
  const hue = (cid * 137.508) % 360;
  return `hsl(${hue.toFixed(1)}, 60%, 50%)`;
}

function toElements(
  nodes: GraphNode[],
  edges: GraphEdge[],
  communities: Record<string, number> | null,
): ElementDefinition[] {
  const nodeEls: ElementDefinition[] = nodes.map((n) => {
    const cid = communities ? communities[n.id] ?? null : null;
    return {
      data: {
        id: n.id,
        label: n.label,
        kind: n.kind,
        provenance: n.provenance ?? "",
        confidence: n.confidence ?? 0,
        community_id: cid,
        community_color: communityColor(cid),
      },
    };
  });
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

// ADR-071 D5: two stylesheets — kind-based (Wave D) vs community-based
// (Wave E). Toggle switches the selector "paint" via a class name on the
// cytoscape container; both paint from ``data(community_color)`` when
// the toggle is ON so the coloring is data-driven and deterministic.
const STYLESHEET_KIND: StylesheetStyle[] = [
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

const STYLESHEET_COMMUNITY: StylesheetStyle[] = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      "font-size": "10px",
      color: "#e6e6e6",
      "text-outline-color": "#111",
      "text-outline-width": 1,
      "background-color": "data(community_color)",
      width: 22,
      height: 22,
    },
  },
  {
    selector: 'node[kind = "zetesis_report"]',
    style: { shape: "diamond" },
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
  const [communities, setCommunities] = useState<GraphCommunities | null>(null);
  const [groupByCommunity, setGroupByCommunity] = useState<boolean>(false);
  // ADR-071 D6: annotation form state (only used when a memory-triple
  // node is selected; hidden on zetesis_report nodes).
  const [annotNote, setAnnotNote] = useState("");
  const [annotProvenance, setAnnotProvenance] = useState("");
  const [annotConfidence, setAnnotConfidence] = useState(1.0);
  const [annotReason, setAnnotReason] = useState("");
  const [annotSubmitting, setAnnotSubmitting] = useState(false);
  const [annotToast, setAnnotToast] = useState<string | null>(null);
  const [annotError, setAnnotError] = useState<string | null>(null);
  const cyRef = useRef<Core | null>(null);

  const load = useCallback(async (choice: CorpusChoice) => {
    setState((s) => ({ ...s, loading: true, errorClass: null }));
    try {
      const corpusParam = choice === "all" ? undefined : choice;
      const [nodesRes, edgesRes, commRes] = await Promise.all([
        kernelClient.fetchGraphNodes({ corpus: corpusParam, limit: 100 }),
        kernelClient.fetchGraphEdges({ corpus: corpusParam, limit: 100 }),
        kernelClient
          .fetchGraphCommunities({ corpus: corpusParam })
          .catch(() => null),
      ]);
      setState({
        nodes: nodesRes.nodes,
        edges: edgesRes.edges,
        loading: false,
        errorClass: null,
      });
      setCommunities(commRes);
    } catch (err) {
      setState({
        nodes: [],
        edges: [],
        loading: false,
        errorClass: err instanceof Error ? err.constructor.name : "Error",
      });
      setCommunities(null);
    }
  }, []);

  useEffect(() => {
    void load(corpus);
  }, [corpus, load]);

  const elements = useMemo(
    () =>
      toElements(
        state.nodes,
        state.edges,
        groupByCommunity && communities ? communities.communities : null,
      ),
    [state.nodes, state.edges, groupByCommunity, communities]
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

  const closeInspector = useCallback(() => {
    setInspectorOpen(false);
    setAnnotToast(null);
    setAnnotError(null);
  }, []);

  // ADR-071 D6: reset the form whenever the inspected node changes so the
  // user never sees stale text after clicking a different node.
  useEffect(() => {
    if (selected == null) return;
    setAnnotNote("");
    setAnnotProvenance(
      // Default "user:local" — Wave E ships as a single-user Colossus build.
      (typeof process !== "undefined" &&
        process.env?.NEXT_PUBLIC_ANNOTATOR_NAME) ||
        "user:local",
    );
    setAnnotConfidence(1.0);
    setAnnotReason("");
    setAnnotError(null);
    setAnnotToast(null);
  }, [selected?.node.id]);

  const submitAnnotation = useCallback(async () => {
    if (selected == null) return;
    if (
      annotNote.trim() === "" ||
      annotProvenance.trim() === "" ||
      annotReason.trim() === "" ||
      annotConfidence < 0 ||
      annotConfidence > 1
    ) {
      setAnnotError("All fields required; confidence must be in [0, 1].");
      return;
    }
    setAnnotSubmitting(true);
    setAnnotError(null);
    try {
      const res = await kernelClient.annotateGraphNode({
        node_id: selected.node.id,
        provenance: annotProvenance,
        confidence: annotConfidence,
        note: annotNote,
        reason: annotReason,
      });
      setAnnotToast(`Annotation saved (event ${res.memory_event_id})`);
      setAnnotNote("");
      setAnnotReason("");
    } catch (err) {
      setAnnotError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setAnnotSubmitting(false);
    }
  }, [selected, annotNote, annotProvenance, annotConfidence, annotReason]);

  return (
    <article
      data-testid="panel-MEMORY_INTEGRITY"
      data-populated="true"
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
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          {/* ADR-071 D5: modularity badge — tells the user whether the
              community coloring is meaningful (Q > 0.3) or noise (< 0.1). */}
          {communities && communities.node_count > 0 && (
            <span
              data-testid="memory-integrity-modularity"
              title={`Louvain modularity Q (algorithm=${communities.algorithm})`}
              style={{
                fontSize: "11px",
                color: "var(--rgpa-fg-2, #999)",
                fontFamily: "var(--rgpa-mono, monospace)",
              }}
            >
              Q = {communities.modularity.toFixed(2)}
            </span>
          )}
          {/* ADR-071 D5: community toggle — defaults OFF (Wave D kind coloring). */}
          <label
            data-testid="memory-integrity-community-toggle-label"
            style={{ display: "flex", gap: "6px", alignItems: "center", fontSize: "12px" }}
          >
            <input
              type="checkbox"
              data-testid="memory-integrity-community-toggle"
              checked={groupByCommunity}
              onChange={(e) => setGroupByCommunity(e.target.checked)}
              disabled={!communities || communities.node_count === 0}
            />
            <span>Group by community</span>
          </label>
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
        </div>
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
            stylesheet={
              (groupByCommunity && communities
                ? STYLESHEET_COMMUNITY
                : STYLESHEET_KIND) as unknown as StylesheetStyle[]
            }
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

          {/* ADR-071 D6: annotation form. Only visible for memory-triple
              nodes (subject/object). Zetesis-report nodes are read-only. */}
          {selected.node.kind !== "zetesis_report" && (
            <form
              data-testid="memory-integrity-annotate-form"
              onSubmit={(e) => {
                e.preventDefault();
                void submitAnnotation();
              }}
              style={{
                marginTop: "16px",
                paddingTop: "12px",
                borderTop: "1px solid var(--rgpa-border, #333)",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                fontSize: "12px",
              }}
            >
              <h5
                data-testid="memory-integrity-annotate-title"
                style={{ margin: "0 0 4px 0", fontSize: "12px" }}
              >
                Annotate
              </h5>
              <label style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span>Note</span>
                <textarea
                  data-testid="memory-integrity-annotate-note"
                  value={annotNote}
                  onChange={(e) => setAnnotNote(e.target.value)}
                  rows={2}
                  required
                />
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span>Provenance</span>
                <input
                  data-testid="memory-integrity-annotate-provenance"
                  value={annotProvenance}
                  onChange={(e) => setAnnotProvenance(e.target.value)}
                  required
                />
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span>Confidence: {annotConfidence.toFixed(2)}</span>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  data-testid="memory-integrity-annotate-confidence"
                  value={annotConfidence}
                  onChange={(e) => setAnnotConfidence(Number(e.target.value))}
                />
              </label>
              <label style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span>Reason</span>
                <input
                  data-testid="memory-integrity-annotate-reason"
                  value={annotReason}
                  onChange={(e) => setAnnotReason(e.target.value)}
                  required
                />
              </label>
              <button
                type="submit"
                data-testid="memory-integrity-annotate-submit"
                disabled={annotSubmitting}
                style={{ padding: "6px 10px", cursor: annotSubmitting ? "wait" : "pointer" }}
              >
                {annotSubmitting ? "Saving…" : "Save annotation"}
              </button>
              {annotToast && (
                <p
                  data-testid="memory-integrity-annotate-toast"
                  role="status"
                  style={{ color: "var(--rgpa-success, #4ae2a2)", margin: 0 }}
                >
                  {annotToast}
                </p>
              )}
              {annotError && (
                <p
                  data-testid="memory-integrity-annotate-error"
                  role="alert"
                  style={{ color: "var(--rgpa-danger, #e24a4a)", margin: 0 }}
                >
                  {annotError}
                </p>
              )}
            </form>
          )}
        </aside>
      )}
    </article>
  );
}
