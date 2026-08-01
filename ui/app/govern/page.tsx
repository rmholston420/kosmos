import JobPage from "../../components/JobPage";

// Govern — Praxis constitution, APEX policies, ADR ledger, approvals audit.
// Wave B wires the real content over /api/praxis/constitution +
// /api/praxis/apex/policies (ADR-068 D2/D3) and enables tier-grouped
// approvals view via governanceMode.
export default function GovernPage() {
  return (
    <JobPage
      jobId="govern"
      title="Govern"
      description="Constitution, escalation policies, ADR ledger, approvals audit."
      slots={["GOVERNANCE", "APPROVALS_QUEUE"]}
      governanceMode
    />
  );
}
