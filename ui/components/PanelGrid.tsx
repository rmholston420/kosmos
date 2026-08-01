"use client";
import type { Panel } from "../lib/kernel-client";
import ApprovalsQueuePanel from "./panels/ApprovalsQueuePanel";
import GovernancePanel from "./panels/GovernancePanel";
import AgentTracePanel from "./panels/AgentTracePanel";
import PlaceholderPanel from "./panels/PlaceholderPanel";

const ALL_SLOTS = [
  "ALGEDONIC", "GOVERNANCE", "MEMORY_INTEGRITY", "MODEL_SWAP_SLO",
  "STUB_DEGRADATION", "CONTEXT_PRESSURE", "HARDWARE_RESILIENCE",
  "APPROVALS_QUEUE", "AGENT_TRACE",
] as const;

function renderPanelBySlot(slot: string, panels: Panel[]) {
  const slotPanels = panels
    .filter((p) => p.slot === slot)
    .sort((a, b) => b.priority - a.priority);

  // AGENT_TRACE reads directly from Phrouros (/api/phrouros/anomalies)
  // and is not owned by any panel-registering plugin. Always render its
  // real component so it can surface anomalies (or the empty state)
  // regardless of PanelSlot registration.
  if (slot === "AGENT_TRACE") {
    return <AgentTracePanel key={slot} panels={slotPanels} />;
  }

  if (slotPanels.length === 0) {
    return <PlaceholderPanel key={slot} slot={slot} />;
  }
  switch (slot) {
    case "APPROVALS_QUEUE":
      return <ApprovalsQueuePanel key={slot} panels={slotPanels} />;
    case "GOVERNANCE":
      return <GovernancePanel key={slot} panels={slotPanels} />;
    default:
      return <PlaceholderPanel key={slot} slot={slot} populated />;
  }
}

export default function PanelGrid({ panels }: { panels: Panel[] }) {
  return (
    <section data-testid="panel-grid">
      {panels.length === 0 && (
        <p data-testid="panel-grid-empty">No panels registered</p>
      )}
      {ALL_SLOTS.map((slot) => renderPanelBySlot(slot, panels))}
    </section>
  );
}
