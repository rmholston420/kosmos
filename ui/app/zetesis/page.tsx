"use client";
import { useState } from "react";

// -------------------------------------------------------------------------
// SSE reader
// -------------------------------------------------------------------------
// `POST /api/zetesis/research` returns `text/event-stream`, not JSON.
// Per ADR-060 the stream emits three frame types:
//   event: started    data: {query, trial_id}
//   event: error      data: {error, error_type, trial_id}   (terminal)
//   event: completed  data: <ResearchReport>                (terminal)
// This reader consumes the raw byte stream, buffers by `\n\n` frame
// boundary, and resolves the promise with the payload from the
// terminal frame. Non-terminal frames (`started`) are surfaced via
// `onProgress` so the UI can show live status without waiting the
// full ~540s Stage 6.3 DoD trial duration.
// -------------------------------------------------------------------------
async function readResearchStream(
  response: Response,
  onProgress: (event: string, data: unknown) => void,
): Promise<Report> {
  if (!response.body) throw new Error("response has no body");
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buf = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buf.indexOf("\n\n")) !== -1) {
      const frame = buf.slice(0, sep);
      buf = buf.slice(sep + 2);

      // Parse the frame's `event:` and `data:` lines. We accept any
      // whitespace after the colon per the SSE spec.
      let evt = "message";
      const dataLines: string[] = [];
      for (const line of frame.split("\n")) {
        if (line.startsWith(":")) continue; // SSE comment/keepalive
        if (line.startsWith("event:")) evt = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
      }
      if (dataLines.length === 0) continue;

      let payload: unknown;
      try {
        payload = JSON.parse(dataLines.join("\n"));
      } catch (e) {
        throw new Error(
          "malformed SSE data on event '" + evt + "': " + String(e),
        );
      }

      if (evt === "completed") {
        return payload as Report;
      }
      if (evt === "error") {
        const err = payload as { error?: string; error_type?: string };
        throw new Error(
          (err.error_type ? err.error_type + ": " : "") +
            (err.error ?? "research failed"),
        );
      }
      onProgress(evt, payload);
    }
  }
  throw new Error("research stream closed without a terminal event");
}

type Report = {
  query?: string;
  answer?: string;
  source_diversity?: number;
  latency_seconds?: number;
  citations?: string[];
  evidences?: unknown[];
  memory_event_id?: string;
  error?: string;
};

export default function ZetesisResearch() {
  const [query, setQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [elapsed, setElapsed] = useState<number>(0);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

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
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) throw new Error("POST /api/zetesis/research -> " + res.status);
      // Kernel emits SSE per ADR-060; parse the stream, resolve on
      // `event: completed`, throw on `event: error` (see readResearchStream).
      const data = await readResearchStream(res, () => {
        /* progress: `started` frame is emitted immediately after POST;
         * we already show the elapsed timer, so nothing extra to do. */
      });
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
            Latency: {(report.latency_seconds ?? 0).toFixed(1)}s
          </p>

          {report.citations && report.citations.length > 0 && (
            <ul data-testid="zetesis-report-citations">
              {report.citations.map((c: string, i: number) => (
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
                {report.evidences.map((ev: unknown, i: number) => (
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
