import JobPage from "../../components/JobPage";
import PhrourosAnomaliesTable from "../../components/observe/PhrourosAnomaliesTable";

// Observe — Phrouros anomalies, agent-execution traces, model-swap SLO,
// context pressure. Read-only observability surface.
export default function ObservePage() {
  return (
    <>
      <JobPage
        jobId="observe"
        title="Observe"
        description="Agent traces, anomalies, telemetry — read-only observability."
        slots={[
          "ALGEDONIC",
          "AGENT_TRACE",
          "MODEL_SWAP_SLO",
          "CONTEXT_PRESSURE",
        ]}
      />
      {/* ADR-076 D6.5 — Phrouros anomalies table with WS live-invalidate. */}
      <PhrourosAnomaliesTable />
    </>
  );
}
