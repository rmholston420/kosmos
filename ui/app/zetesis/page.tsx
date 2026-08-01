"use client";
import { useState } from "react";

export default function ZetesisResearch() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const runResearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setReport(null);
    setElapsed(0);

    const timer = setInterval(() => setElapsed((e) => e + 1), 1000);

    try {
      const res = await fetch("/api/zetesis/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) throw new Error("POST /api/zetesis/research -> " + res.status);
      const data = await res.json();
      setReport(data);
    } catch (e) {
      setError(String(e));
    } finally {
      clearInterval(timer);
      setLoading(false);
    }
  };

  return (
    <main data-testid="zetesis-research">
      <h1>Zetesis Research</h1>

      <div>
        <input
          data-testid="zetesis-query-input"
          placeholder="Ask a research question…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button data-testid="zetesis-query-submit" onClick={runResearch} disabled={loading}>
          {loading ? "Researching…" : "Research"}
        </button>
      </div>

      {loading && (
        <p data-testid="zetesis-progress">
          Elapsed {elapsed}s (typical run ~540s per Stage 6.3 DoD trial)
        </p>
      )}

      {error && <p data-testid="zetesis-error">{error}</p>}

      {report && report.error && (
        <p data-testid="zetesis-report-error" role="alert">
          Research failed: {report.error}
        </p>
      )}

      {report && !report.error && (
        <article data-testid="zetesis-report">
          <p data-testid="zetesis-report-query">{report.query}</p>
          <div data-testid="zetesis-report-answer">{report.answer}</div>

          <p data-testid="zetesis-report-diversity">
            Source diversity: {report.source_diversity}
          </p>
          <p data-testid="zetesis-report-latency">
            Latency: {report.latency_seconds.toFixed(1)}s
          </p>

          {report.citations && report.citations.length > 0 && (
            <ul data-testid="zetesis-report-citations">
              {report.citations.map((c, i) => (
                <li data-testid={"zetesis-citation-" + i} key={i}>
                  <a href={c} target="_blank" rel="noreferrer">
                    {c}
                  </a>
                </li>
              ))}
            </ul>
          )}

          {report.evidences && report.evidences.length > 0 && (
            <details data-testid="zetesis-report-evidence">
              <summary>Evidence ({report.evidences.length})</summary>
              <ul>
                {report.evidences.map((ev, i) => (
                  <li data-testid={"zetesis-evidence-" + i} key={i}>
                    {JSON.stringify(ev)}
                  </li>
                ))}
              </ul>
            </details>
          )}

          {report.memory_event_id && (
            <p data-testid="zetesis-memory-link">
              Memory event: {report.memory_event_id}
            </p>
          )}
        </article>
      )}
    </main>
  );
}
