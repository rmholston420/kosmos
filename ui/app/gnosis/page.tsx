"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { gnosisGateClient } from "../../lib/kernel-client";

// Corpus row shape per kernel `/api/gnosis/corpora` (kernel/app.py:1381).
// Fields are populated from GNOSIS_CORPORA_MANIFEST (name, provenance
// predicate, summary, stage) plus two runtime fields injected by the
// route: `fact_count` (live seeder count, or static fallback) and
// `last_ingested_at` (UTC ISO or null).
type Corpus = {
  name: string;
  provenance_predicate?: string;
  summary?: string;
  stage?: string;
  fact_count?: number;
  last_ingested_at?: string | null;
};

export default function GnosisIndex() {
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [fallback, setFallback] = useState<boolean>(false);

  useEffect(() => {
    gnosisGateClient
      .listCorpora()
      .then((c: unknown) => {
        // Client already unwraps the {corpora: [...]} envelope; this
        // second guard defends against a hand-written test double or
        // a future kernel change.
        if (!Array.isArray(c)) {
          throw new Error("expected corpora array, got " + typeof c);
        }
        setCorpora(c as Corpus[]);
      })
      .catch((e: unknown) => {
        setError(String(e));
        setFallback(true);
      });
  }, []);

  if (fallback) {
    return (
      <main data-testid="gnosis-html-fallback">
        <p>JSON API unavailable — falling back to the Stage 4.6 HTML gate.</p>
        <iframe
          data-testid="gnosis-html-frame"
          src={gnosisGateClient.htmlIndexUrl()}
          style={{ width: "100%", height: "80vh", border: "none" }}
          title="Kosmos Gnosis-surrogate gate"
        />
      </main>
    );
  }

  if (error) return <main data-testid="gnosis-error">{error}</main>;

  return (
    <main data-testid="gnosis-index">
      <header style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
        <h1 style={{ marginRight: "auto" }}>Gnosis Corpora</h1>
        <Link data-testid="gnosis-graph-link" href="/gnosis/graph">
          View graph →
        </Link>
      </header>
      {corpora.length === 0 ? (
        <p data-testid="gnosis-empty">No corpora registered</p>
      ) : (
        <table data-testid="gnosis-corpus-table">
          <thead>
            <tr>
              <th>Corpus</th>
              <th>Stage</th>
              <th>Facts</th>
              <th>Last ingested</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            {corpora.map((c) => (
              <tr data-testid={"gnosis-corpus-row-" + c.name} key={c.name}>
                <td>
                  <Link
                    data-testid={"gnosis-corpus-link-" + c.name}
                    href={"/gnosis/detail?corpus=" + encodeURIComponent(c.name)}
                  >
                    {c.name}
                  </Link>
                </td>
                <td data-testid={"gnosis-corpus-stage-" + c.name}>{c.stage ?? "—"}</td>
                <td data-testid={"gnosis-corpus-facts-" + c.name}>
                  {c.fact_count ?? 0}
                </td>
                <td data-testid={"gnosis-corpus-ingested-" + c.name}>
                  {c.last_ingested_at
                    ? c.last_ingested_at.slice(0, 19).replace("T", " ")
                    : "—"}
                </td>
                <td data-testid={"gnosis-corpus-summary-" + c.name}>
                  {c.summary ?? ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
