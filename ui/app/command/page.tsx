import JobPage from "../../components/JobPage";

// Command — algedonic status, active approvals, "what needs a decision now."
// Per UX Design Spec §"Information Architecture: Job-Segmented, Not Data-Segmented".
export default function CommandPage() {
  return (
    <JobPage
      jobId="command"
      title="Command"
      description="Algedonic status, active approvals — what needs a decision now."
      slots={["ALGEDONIC", "APPROVALS_QUEUE"]}
    />
  );
}
