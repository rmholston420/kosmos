"use client";
import { useCallback, useEffect, useState } from "react";
import { kernelClient, type AnomalyRecord, type Panel } from "../../lib/kernel-client";
import { useEventListener } from "../../lib/events-ws";

export default function AgentTracePanel({ panels }: { panels: Panel[] }) {
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);

  const refetch = useCallback(() => {
    kernelClient
      .listAnomalies()
      .then((r: unknown) => setAnomalies(Array.isArray(r) ? (r as AnomalyRecord[]) : []))
      .catch(() => setAnomalies([]));
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  // F1 · Wave F: live invalidate on phrouros anomaly events.
  useEventListener("phrouros.anomaly.detected", refetch);

  return (
    <article data-testid="panel-AGENT_TRACE" data-populated="true">
      <h2>Agent Trace</h2>
      {anomalies.length === 0 ? (
        <p data-testid="agent-trace-empty">No anomalies detected</p>
      ) : (
        <ul data-testid="agent-trace-list">
          {anomalies.map((a) => (
            <li data-testid={`anomaly-${a.id}`} key={a.id}>
              <span data-testid={`anomaly-kind-${a.id}`}>{a.kind}</span>
              <span data-testid={`anomaly-status-${a.id}`}>{a.status}</span>
              <span>{a.plugin}.{a.tool_name}</span>
            </li>
          ))}
        </ul>
      )}
      <p data-testid="agent-trace-owner">{panels.map((p) => p.plugin_name).join(", ")}</p>
    </article>
  );
}
