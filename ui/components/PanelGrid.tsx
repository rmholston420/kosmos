"use client";
import type { Panel } from "../lib/kernel-client";
import ApprovalsQueuePanel from "./panels/ApprovalsQueuePanel";
import GovernancePanel from "./panels/GovernancePanel";
import AgentTracePanel from "./panels/AgentTracePanel";
import MemoryIntegrityPanel from "./panels/MemoryIntegrityPanel";
import PlaceholderPanel from "./panels/PlaceholderPanel";
// Wave F · F2 — realized Operate-page panels replacing PlaceholderPanel
// on STUB_DEGRADATION / MODEL_SWAP_SLO / CONTEXT_PRESSURE / HARDWARE_RESILIENCE.
import StubDegradationPanel from "./panels/StubDegradationPanel";
import ModelSwapSLOPanel from "./panels/ModelSwapSLOPanel";
import ContextPressurePanel from "./panels/ContextPressurePanel";
import HardwareResiliencePanel from "./panels/HardwareResiliencePanel";

const ALL_SLOTS = [
  "ALGEDONIC", "GOVERNANCE", "MEMORY_INTEGRITY", "MODEL_SWAP_SLO",
  "STUB_DEGRADATION", "CONTEXT_PRESSURE", "HARDWARE_RESILIENCE",
  "APPROVALS_QUEUE", "AGENT_TRACE",
] as const;

type AnySlot = (typeof ALL_SLOTS)[number];

export interface PanelGridOptions {
  /**
   * Wave B — governance-mode surfaces (tier-grouped approvals + full
   * governance panel) render on `/govern`. Passed through to opting-in
   * panels; ignored by others.
   */
  governanceMode?: boolean;
}

function renderPanelBySlot(slot: string, panels: Panel[], opts: PanelGridOptions) {
  const slotPanels = panels
    .filter((p) => p.slot === slot)
    .sort((a, b) => b.priority - a.priority);

  // AGENT_TRACE reads directly from Phrouros (/api/phrouros/anomalies)
  // and is not owned by any panel-registering plugin.
  if (slot === "AGENT_TRACE") {
    return <AgentTracePanel key={slot} panels={slotPanels} />;
  }

  // GOVERNANCE (Wave B): reads constitution + apex policies directly from
  // /api/praxis/*; always render even when zero panels are registered.
  if (slot === "GOVERNANCE") {
    return <GovernancePanel key={slot} panels={slotPanels} />;
  }

  // MEMORY_INTEGRITY (Wave D, ADR-070): reads /api/gnosis/graph/* directly;
  // always render even when zero panels are registered.
  if (slot === "MEMORY_INTEGRITY") {
    return <MemoryIntegrityPanel key={slot} panels={slotPanels} />;
  }

  // Wave F · F2 — always-render telemetry panels backed by kernel routes.
  // No plugin-registered panel is required; kernel data is authoritative.
  if (slot === "STUB_DEGRADATION") {
    return <StubDegradationPanel key={slot} />;
  }
  if (slot === "MODEL_SWAP_SLO") {
    return <ModelSwapSLOPanel key={slot} />;
  }
  if (slot === "CONTEXT_PRESSURE") {
    return <ContextPressurePanel key={slot} />;
  }
  if (slot === "HARDWARE_RESILIENCE") {
    return <HardwareResiliencePanel key={slot} />;
  }

  if (slotPanels.length === 0) {
    return <PlaceholderPanel key={slot} slot={slot} />;
  }
  switch (slot) {
    case "APPROVALS_QUEUE":
      return (
        <ApprovalsQueuePanel
          key={slot}
          panels={slotPanels}
          governanceMode={opts.governanceMode ?? false}
        />
      );
    default:
      return <PlaceholderPanel key={slot} slot={slot} populated />;
  }
}

export default function PanelGrid({
  panels,
  slots,
  governanceMode,
}: {
  panels: Panel[];
  /**
   * Optional slot allow-list. When provided, only these slots render (and
   * they render in the given order). When omitted, all nine PanelSlots
   * render in the canonical ALL_SLOTS order — the shell page at `/`
   * preserves this behaviour so the existing Playwright shell contract
   * (all nine slots visible) stays green.
   */
  slots?: readonly AnySlot[];
  governanceMode?: boolean;
}) {
  const activeSlots = slots ?? ALL_SLOTS;
  const opts: PanelGridOptions = { governanceMode: governanceMode ?? false };
  return (
    <section data-testid="panel-grid">
      {panels.length === 0 && (
        <p data-testid="panel-grid-empty">No panels registered</p>
      )}
      {activeSlots.map((slot) => renderPanelBySlot(slot, panels, opts))}
    </section>
  );
}
