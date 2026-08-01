/**
 * Shared 2D/3D toggle store — ADR-074 D5.
 *
 * Ported from Rigpa-LMS (Apache-2.0) `frontend/src/shell/graphDimensionStore.ts`.
 * Adaptations for Kosmos:
 *   - localStorage key renamed `rigpa-graph-dimension` → `kosmos-graph-dimension`.
 *   - Dev-only Demo-data checkbox removed (single-user local-first;
 *     `import.meta.env.DEV` doesn't exist under Next.js anyway).
 *   - Kept the same eager-hydrate + selector pattern so returning users
 *     don't see a 2D→3D flash on first render.
 *
 * See docs/adrs/ADR-074-semantic-memory-and-graph-visualization.md §D5.
 */
import { create } from "zustand";

export type GraphDimension = "2d" | "3d";

export const GRAPH_DIMENSION_STORAGE_KEY = "kosmos-graph-dimension";

function readPersistedDimension(): GraphDimension | null {
  if (typeof window === "undefined") return null;
  try {
    const value = window.localStorage.getItem(GRAPH_DIMENSION_STORAGE_KEY);
    return value === "2d" || value === "3d" ? value : null;
  } catch {
    return null;
  }
}

function persistDimension(dimension: GraphDimension): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(GRAPH_DIMENSION_STORAGE_KEY, dimension);
  } catch {
    // localStorage may be unavailable (private mode / SSR); the in-memory
    // store still drives the current session's dimension.
  }
}

/** Resolve the dimension to use on first load: stored choice, else 2D. */
function resolveInitialDimension(): GraphDimension {
  return readPersistedDimension() ?? "2d";
}

export interface GraphDimensionState {
  namespace: "graph-dimension";
  dimension: GraphDimension;
  /** Set an explicit dimension and persist it. */
  setDimension: (dimension: GraphDimension) => void;
  /** Flip between 2D and 3D. */
  toggleDimension: () => void;
}

export const useGraphDimensionStore = create<GraphDimensionState>(
  (set, get) => ({
    namespace: "graph-dimension",
    // Resolve eagerly so the initial render already matches the persisted
    // choice (no 2D→3D flash for returning 3D users).
    dimension: resolveInitialDimension(),

    setDimension: (dimension) => {
      persistDimension(dimension);
      set({ dimension });
    },

    toggleDimension: () => {
      get().setDimension(get().dimension === "3d" ? "2d" : "3d");
    },
  }),
);

// ---- Documented selectors (external consumers only through these) ----

export const selectGraphDimension = (s: GraphDimensionState) => s.dimension;
