import JobPage from "../../components/JobPage";

// Memory — Gnosis knowledge-graph browser, quarantine review, provenance
// inspection. Wave D lands the Cytoscape node-link view (UX Design Spec
// §"Data-Type Taxonomy" #1 — ontology-aware, ≤150 visible nodes, Louvain
// community collapse). Wave A shows the MEMORY_INTEGRITY health card only.
export default function MemoryPage() {
  return (
    <JobPage
      jobId="memory"
      title="Memory"
      description="Knowledge-graph browser, quarantine review, provenance inspection."
      slots={["MEMORY_INTEGRITY"]}
    />
  );
}
