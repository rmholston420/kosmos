/**
 * DimensionalForceGraph — ADR-074 D5.
 *
 * Ported from Rigpa-LMS (Apache-2.0)
 * `frontend/src/shell/DimensionalForceGraph.tsx`.
 *
 * Renders a force-graph in either 2D or 3D depending on the shared
 * `graphDimensionStore`. Both `react-force-graph-2d` and
 * `react-force-graph-3d` ship the same author's near-identical prop
 * API, so the shared subset of props below spreads unchanged onto
 * whichever renderer is active.
 *
 * Next.js note: `react-force-graph-{2d,3d}` are DOM-only (they use
 * WebGL / canvas). Consumers must import this via `next/dynamic` with
 * `ssr: false` to avoid a "window is not defined" SSR error. See
 * `ui/app/gnosis/page.tsx` for the pattern.
 */
"use client";

import { useMemo, type ReactElement } from "react";
import ForceGraph2D from "react-force-graph-2d";
import ForceGraph3D from "react-force-graph-3d";

import {
  selectGraphDimension,
  useGraphDimensionStore,
} from "@/lib/graph/graphDimensionStore";

/**
 * The subset of props shared identically by both force-graph libraries.
 * See https://github.com/vasturiano/react-force-graph for the full
 * intersection surface.
 */
export interface DimensionalForceGraphProps {
  graphData: { nodes: unknown[]; links: unknown[] };
  width?: number;
  height?: number;
  backgroundColor?: string;
  nodeColor?: (node: unknown) => string;
  linkColor?: (link: unknown) => string;
  linkLabel?: (link: unknown) => string;
  nodeLabel?: (node: unknown) => string;
  linkDirectionalArrowLength?: number;
  linkDirectionalArrowRelPos?: number;
  linkDirectionalParticles?: number;
}

export default function DimensionalForceGraph(
  props: DimensionalForceGraphProps,
) {
  const dimension = useGraphDimensionStore(selectGraphDimension);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Graph = useMemo(
    () => (dimension === "3d" ? ForceGraph3D : ForceGraph2D),
    [dimension],
  ) as unknown as (p: DimensionalForceGraphProps) => ReactElement;
  return <Graph {...props} />;
}
