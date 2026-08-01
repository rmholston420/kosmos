"use client";
import { useEffect, useState } from "react";
import { gnosisGateClient } from "../../lib/kernel-client";

type Corpus = {
  name: string;
  n_facts: number;
  n_edges: number;
  licenses: string[];
};

export default function GnosisIndex() {
  const [corpora, setCorpora] = useState<Corpus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [fallback, setFallback] = useState<boolean>(false);

  useEffect(() => {
    gnosisGateClient
      .listCorpora()
      .then((c: unknown) => setCorpora(c as Corpus[]))
      .catch((e: unknown) => {
        setError(String(e));
        setFallback(true);
      });
  }, []);

  if (fallback) {
    return (
      <main data-testid="gnosis-html-fallback">
        <p>JSON API unavailable -- falling back to the Stage 4.6 HTML gate.</p>
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
      <h1>Gnosis Corpora (Stage 4.6 gate)</h1>
      {corpora.length === 0 ? (
        <p data-testid="gnosis-empty">No corpora registered</p>
      ) : (
        <table data-testid="gnosis-corpus-table">
          <thead>
            <tr>
              <th>Corpus</th>
              <th>Facts</th>
              <th>Edges</th>
              <th>Licenses</th>
            </tr>
          </thead>
          <tbody>
            {corpora.map((c) => (
              <tr data-testid={"gnosis-corpus-row-" + c.name} key={c.name}>
                <td>
                  <a data-testid={"gnosis-corpus-link-" + c.name} href={"/gnosis/detail?corpus=" + encodeURIComponent(c.name)}>
                    {c.name}
                  </a>
                </td>
                <td data-testid={"gnosis-corpus-facts-" + c.name}>{c.n_facts}</td>
                <td data-testid={"gnosis-corpus-edges-" + c.name}>{c.n_edges}</td>
                <td>{c.licenses.join(", ") || "unlicensed"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
