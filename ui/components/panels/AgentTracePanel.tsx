"use client";
import { useEffect, useState } from "react";
import { kernelClient, type AnomalyRecord, type Panel } from "../../lib/kernel-client";

export default function AgentTracePanel({ panels }: { panels: Panel[] }) {
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);

  useEffect(() => {
    kernelClient.listAnomalies().then(setAnomalies).catch(() => setAnomalies([]));
  }, []);

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
