// ADR-076 D6.5 — Phrouros anomalies table.
//
// Fetches GET /api/phrouros/anomalies (ADR-034 D1) and subscribes to
// phrouros.anomaly.detected on /api/events/ws to invalidate on new
// detections. Filter chip lets the user narrow by detector kind.
//
// Kernel returns 503 when the Phrouros engine is not booted — the
// table renders a degraded state (never fabricates rows).

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type LoadState = "idle" | "loading" | "ok" | "unavailable" | "error";

type AnomalyRow = {
  id: string;
  kind: string;
  detected_at: string;
  trace_id: string;
  plugin: string;
  tool_name: string;
  detector: string;
  status: string;
  payload?: Record<string, unknown>;
  notification_id?: string | null;
  allocation_id?: string | null;
  queued_request_id?: string | null;
};

const FETCH_URL = "/api/phrouros/anomalies";
const WS_URL_SUFFIX = "/api/events/ws?types=phrouros.anomaly.detected";

async function fetchAnomalies(): Promise<AnomalyRow[]> {
  const r = await fetch(FETCH_URL, { credentials: "same-origin" });
  if (r.status === 503) {
    const err = new Error("503");
    (err as Error & { code?: number }).code = 503;
    throw err;
  }
  if (!r.ok) {
    throw new Error(`${r.status}`);
  }
  return (await r.json()) as AnomalyRow[];
}

export default function PhrourosAnomaliesTable() {
  const [rows, setRows] = useState<AnomalyRow[]>([]);
  const [state, setState] = useState<LoadState>("idle");
  const [errText, setErrText] = useState<string>("");
  const [detectorFilter, setDetectorFilter] = useState<string>("__all__");
  const [flashId, setFlashId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const refresh = useCallback(async () => {
    setState("loading");
    try {
      const data = await fetchAnomalies();
      setRows(data);
      setState("ok");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg === "503") {
        setState("unavailable");
      } else {
        setErrText(msg);
        setState("error");
      }
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}${WS_URL_SUFFIX}`);
    wsRef.current = ws;
    ws.onmessage = (msg) => {
      try {
        const parsed = JSON.parse(msg.data);
        // Ignore the initial `frame: "ready"` handshake.
        if (parsed?.frame === "ready") return;
        // Any other frame on this subscription means an anomaly was
        // just detected — refetch the canonical list.
        void refresh();
        const newId =
          (parsed?.payload?.id as string | undefined) ??
          (parsed?.envelope?.payload?.id as string | undefined) ??
          null;
        if (newId) {
          setFlashId(newId);
          window.setTimeout(() => setFlashId((cur) => (cur === newId ? null : cur)), 3000);
        }
      } catch {
        /* ignore malformed frame */
      }
    };
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [refresh]);

  const detectors = useMemo(() => {
    const set = new Set<string>();
    for (const r of rows) set.add(r.detector);
    return Array.from(set).sort();
  }, [rows]);

  const filtered = useMemo(() => {
    if (detectorFilter === "__all__") return rows;
    return rows.filter((r) => r.detector === detectorFilter);
  }, [rows, detectorFilter]);

  return (
    <section
      data-testid="phrouros-anomalies"
      style={{
        marginTop: "var(--space-4)",
        padding: "var(--space-3)",
        border: "1px solid var(--border, #333)",
        borderRadius: "var(--radius-2, 8px)",
      }}
    >
      <header
        style={{
          display: "flex",
          gap: "var(--space-2)",
          alignItems: "center",
          marginBottom: "var(--space-3)",
        }}
      >
        <h2 style={{ margin: 0 }}>Phrouros anomalies</h2>
        <span
          data-testid="phrouros-anomalies-count"
          style={{ opacity: 0.6 }}
        >
          {state === "ok" ? `${filtered.length} of ${rows.length}` : ""}
        </span>
        <label style={{ marginLeft: "auto" }}>
          Detector:{" "}
          <select
            data-testid="phrouros-anomalies-detector-filter"
            value={detectorFilter}
            onChange={(e) => setDetectorFilter(e.target.value)}
          >
            <option value="__all__">All detectors</option>
            {detectors.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <button
          data-testid="phrouros-anomalies-refresh"
          onClick={() => {
            void refresh();
          }}
        >
          Refresh
        </button>
      </header>

      {state === "loading" && (
        <p data-testid="phrouros-anomalies-loading">Loading…</p>
      )}
      {state === "unavailable" && (
        <p data-testid="phrouros-anomalies-unavailable">
          Phrouros engine unavailable (503).
        </p>
      )}
      {state === "error" && (
        <p data-testid="phrouros-anomalies-error">Error: {errText}</p>
      )}

      {state === "ok" && filtered.length === 0 && (
        <p
          data-testid="phrouros-anomalies-empty"
          style={{ opacity: 0.7 }}
        >
          No anomalies recorded.
        </p>
      )}

      {state === "ok" && filtered.length > 0 && (
        <table
          data-testid="phrouros-anomalies-table"
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontSize: "0.9em",
          }}
        >
          <thead>
            <tr style={{ textAlign: "left", opacity: 0.7 }}>
              <th style={{ padding: "var(--space-1)" }}>detected_at</th>
              <th style={{ padding: "var(--space-1)" }}>detector</th>
              <th style={{ padding: "var(--space-1)" }}>kind</th>
              <th style={{ padding: "var(--space-1)" }}>plugin</th>
              <th style={{ padding: "var(--space-1)" }}>tool</th>
              <th style={{ padding: "var(--space-1)" }}>status</th>
              <th style={{ padding: "var(--space-1)" }}>trace_id</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr
                key={r.id}
                data-testid="phrouros-anomalies-row"
                data-anomaly-id={r.id}
                data-flash={r.id === flashId ? "1" : "0"}
                style={{
                  background:
                    r.id === flashId ? "rgba(255, 215, 0, 0.15)" : "transparent",
                  transition: "background 0.4s",
                  borderTop: "1px solid var(--border, #333)",
                }}
              >
                <td style={{ padding: "var(--space-1)" }}>{r.detected_at}</td>
                <td style={{ padding: "var(--space-1)" }}>
                  <code>{r.detector}</code>
                </td>
                <td style={{ padding: "var(--space-1)" }}>{r.kind}</td>
                <td style={{ padding: "var(--space-1)" }}>{r.plugin}</td>
                <td style={{ padding: "var(--space-1)" }}>{r.tool_name}</td>
                <td style={{ padding: "var(--space-1)" }}>{r.status}</td>
                <td style={{ padding: "var(--space-1)", opacity: 0.7 }}>
                  <code>{r.trace_id}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
