"use client";
import type { Panel } from "../../lib/kernel-client";

export default function GovernancePanel({ panels }: { panels: Panel[] }) {
  return (
    <article data-testid="panel-GOVERNANCE" data-populated="true">
      <h2>Governance</h2>
      <ul>
        {panels.map((p) => (
          <li data-testid={`governance-panel-${p.id}`} key={p.id}>
            {p.plugin_name} · priority {p.priority}
          </li>
        ))}
      </ul>
    </article>
  );
}
