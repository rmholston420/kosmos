/**
 * Memory Search — ADR-075 D2.
 *
 * Wraps POST /api/memory/search-semantic (MemoryPort.search_semantic).
 * Sibling of /gnosis/graph/: same header layout, same testid discipline,
 * same styling tokens.
 *
 * Degrades gracefully:
 *   - `degraded: true` from backend ⇒ shows a banner, empty hit list.
 *   - Network / non-degraded error ⇒ shows the error string in role="alert".
 *   - Empty query ⇒ shows an inline hint, does not fire the request.
 */
"use client";

import Link from "next/link";
import { useState } from "react";

import {
  kernelClient,
  type MemoryHitRow,
  type MemorySearchSemanticResult,
} from "@/lib/kernel-client";

// Backend caps `limit` at 100 (kernel/app.py `_MemorySearchSemanticBody`).
const DEFAULT_LIMIT = 20;
const DEFAULT_MIN_SCORE = 0.0;

export default function MemorySearchPage() {
  const [query, setQuery] = useState<string>("");
  const [corpus, setCorpus] = useState<string>("");
  const [result, setResult] = useState<MemorySearchSemanticResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function runSearch(): Promise<void> {
    setError(null);
    if (!query.trim()) {
      setResult(null);
      return;
    }
    setLoading(true);
    try {
      const res = await kernelClient.memorySearchSemantic({
        query: query.trim(),
        corpus: corpus.trim() || null,
        limit: DEFAULT_LIMIT,
        min_score: DEFAULT_MIN_SCORE,
      });
      setResult(res);
    } catch (e: unknown) {
      setError(String(e));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: React.FormEvent<HTMLFormElement>): void {
    e.preventDefault();
    void runSearch();
  }

  return (
    <main data-testid="memory-search-page">
      <header
        style={{
          display: "flex",
          gap: "var(--space-4)",
          alignItems: "center",
          marginBottom: "var(--space-3)",
        }}
      >
        <h1 style={{ marginRight: "auto" }}>Memory Search</h1>
        <Link data-testid="memory-back-link" href="/memory/">
          ← Memory
        </Link>
      </header>

      <form
        onSubmit={onSubmit}
        data-testid="memory-search-form"
        style={{
          display: "flex",
          gap: "var(--space-2)",
          alignItems: "center",
          marginBottom: "var(--space-3)",
          flexWrap: "wrap",
        }}
      >
        <label style={{ flex: 1, minWidth: "20ch" }}>
          Query:{" "}
          <input
            data-testid="memory-search-query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Semantic search over MemoryPort"
            style={{ width: "100%" }}
          />
        </label>
        <label>
          Corpus:{" "}
          <input
            data-testid="memory-search-corpus"
            value={corpus}
            onChange={(e) => setCorpus(e.target.value)}
            placeholder="(default)"
            style={{ width: "12ch" }}
          />
        </label>
        <button
          data-testid="memory-search-submit"
          type="submit"
          disabled={loading || query.trim().length === 0}
        >
          Search
        </button>
      </form>

      {loading && (
        <p data-testid="memory-search-loading">Searching…</p>
      )}
      {error && (
        <p data-testid="memory-search-error" role="alert">
          {error}
        </p>
      )}
      {result?.degraded && (
        <p
          data-testid="memory-search-degraded"
          style={{ opacity: 0.85 }}
        >
          Semantic memory lane not booted — search is running in degraded mode
          (empty hit list). {result.reason ? `Reason: ${result.reason}` : null}
        </p>
      )}
      {result && !result.degraded && result.hits.length === 0 && !loading && (
        <p data-testid="memory-search-empty">
          No hits for “{result.query}” in corpus{" "}
          {result.corpus ?? "(default)"}.
        </p>
      )}

      {result && result.hits.length > 0 && (
        <ul
          data-testid="memory-search-hits"
          style={{
            listStyle: "none",
            padding: 0,
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
          }}
        >
          {result.hits.map((h: MemoryHitRow) => (
            <li
              key={h.id}
              data-testid="memory-search-hit"
              data-hit-id={h.id}
              style={{
                border: "1px solid var(--color-border, #333)",
                borderRadius: "var(--radius-2, 6px)",
                padding: "var(--space-2)",
              }}
            >
              <header
                style={{
                  display: "flex",
                  gap: "var(--space-2)",
                  alignItems: "center",
                  marginBottom: "var(--space-1)",
                }}
              >
                <code
                  data-testid="memory-search-hit-id"
                  style={{ opacity: 0.85 }}
                >
                  {h.id}
                </code>
                {h.score != null && (
                  <span data-testid="memory-search-hit-score">
                    {h.score.toFixed(3)}
                  </span>
                )}
                {h.as_of && (
                  <span
                    data-testid="memory-search-hit-as-of"
                    style={{ opacity: 0.6 }}
                  >
                    {h.as_of}
                  </span>
                )}
              </header>
              <pre
                data-testid="memory-search-hit-payload"
                style={{
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  margin: 0,
                  opacity: 0.9,
                }}
              >
                {JSON.stringify(h.payload, null, 2)}
              </pre>
            </li>
          ))}
        </ul>
      )}

      {result && (
        <footer
          data-testid="memory-search-stats"
          style={{ marginTop: "var(--space-2)", opacity: 0.75 }}
        >
          {result.hits.length} hits · limit {DEFAULT_LIMIT} · min_score{" "}
          {DEFAULT_MIN_SCORE}
        </footer>
      )}
    </main>
  );
}
