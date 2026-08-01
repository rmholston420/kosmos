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

import {
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactElement,
} from "react";
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
  linkDirectionalParticles?: number | ((link: unknown) => number);
  nodeRelSize?: number;
}

// 2026-08-01 hotfix: `react-force-graph-3d` (WebGL) needs explicit numeric
// `width`/`height` props. When the parent uses CSS `height: 70vh` and no
// numeric props reach the renderer, the WebGL viewport initializes at 0×0
// on first mount and never resizes — producing a blank canvas. 2D reads
// the container bounds itself so it survives. We measure the wrapper via
// ResizeObserver and pass width/height numerically to both renderers.
export default function DimensionalForceGraph(
  props: DimensionalForceGraphProps,
) {
  const dimension = useGraphDimensionStore(selectGraphDimension);
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const [size, setSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 });

  // Measure synchronously on layout so first paint has valid dims.
  useLayoutEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setSize({ w: Math.max(1, Math.floor(rect.width)), h: Math.max(1, Math.floor(rect.height)) });
  }, []);

  useEffect(() => {
    const el = wrapperRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setSize({ w: Math.max(1, Math.floor(width)), h: Math.max(1, Math.floor(height)) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Graph = useMemo(
    () => (dimension === "3d" ? ForceGraph3D : ForceGraph2D),
    [dimension],
  ) as unknown as (p: DimensionalForceGraphProps) => ReactElement;

  return (
    <div
      ref={wrapperRef}
      data-testid="dimensional-force-graph-wrapper"
      data-dimension={dimension}
      style={{ width: "100%", height: "100%", position: "relative" }}
    >
      {size.w > 0 && size.h > 0 ? (
        <Graph {...props} width={size.w} height={size.h} />
      ) : null}
    </div>
  );
}
