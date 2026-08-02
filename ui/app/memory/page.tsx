import Link from "next/link";
import JobPage from "../../components/JobPage";
import AmgStatusPill from "../../components/memory/AmgStatusPill";

// Memory — Gnosis knowledge-graph browser, quarantine review, provenance
// inspection. Wave D lands the Cytoscape node-link view (UX Design Spec
// §"Data-Type Taxonomy" #1 — ontology-aware, ≤150 visible nodes, Louvain
// community collapse). Wave A shows the MEMORY_INTEGRITY health card only.
// ADR-075 D2 adds a sub-route `/memory/search` for semantic hit lists.
export default function MemoryPage() {
  return (
    <>
      <nav
        data-testid="memory-nav"
        style={{
          display: "flex",
          gap: "var(--space-3)",
          marginBottom: "var(--space-2)",
        }}
      >
        <Link data-testid="memory-search-link" href="/memory/search/">
          Semantic search →
        </Link>
        <Link data-testid="memory-quarantine-link" href="/memory/quarantine/">
          Quarantine review →
        </Link>
        {/* ADR-076 D6 — AMG status pill on the memory header. */}
        <span style={{ marginLeft: "auto" }}>
          <AmgStatusPill />
        </span>
      </nav>
      <JobPage
        jobId="memory"
        title="Memory"
        description="Knowledge-graph browser, quarantine review, provenance inspection."
        slots={["MEMORY_INTEGRITY"]}
      />
    </>
  );
}
