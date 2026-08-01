/**
 * GraphDimensionToggle — ADR-074 D5.
 *
 * Ported from Rigpa-LMS (Apache-2.0)
 * `frontend/src/shell/GraphDimensionToggle.tsx`.
 *
 * A tiny radiogroup that drives the shared `graphDimensionStore`.
 * Because the store is app-wide, one control changes every
 * force-graph view at once — matching the Rigpa placement pattern
 * where the same toggle sits inside Knowsys BacklinkGraph and
 * Gnosis ArgumentGraph views.
 *
 * Kosmos-specific: the Rigpa "Demo data" checkbox is dropped
 * (single-user local-first — dev-verification affordances live in
 * Playwright specs, not the shipped UI).
 */
"use client";

import {
  selectGraphDimension,
  useGraphDimensionStore,
  type GraphDimension,
} from "@/lib/graph/graphDimensionStore";

const OPTIONS: readonly GraphDimension[] = ["2d", "3d"] as const;
const LABEL: Record<GraphDimension, string> = { "2d": "2D", "3d": "3D" };

export default function GraphDimensionToggle() {
  const dimension = useGraphDimensionStore(selectGraphDimension);
  const setDimension = useGraphDimensionStore((s) => s.setDimension);

  return (
    <div
      role="radiogroup"
      aria-label="Graph dimension"
      data-testid="graph-dimension-toggle"
      style={{ display: "inline-flex", gap: "var(--space-2)" }}
    >
      {OPTIONS.map((opt) => (
        <label
          key={opt}
          data-testid={`graph-dimension-option-${opt}`}
          style={{ display: "flex", gap: "var(--space-1)", alignItems: "center" }}
        >
          <input
            type="radio"
            name="graph-dimension"
            value={opt}
            checked={dimension === opt}
            onChange={() => setDimension(opt)}
            aria-label={`Render force-graph in ${LABEL[opt]}`}
          />
          {LABEL[opt]}
        </label>
      ))}
    </div>
  );
}
