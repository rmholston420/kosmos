/**
 * Memory Search — ADR-075 D2 + ADR-076 D2 (polish).
 *
 * Wraps POST /api/memory/search-semantic (MemoryPort.search_semantic).
 * Sibling of /gnosis/graph/: same header layout, same testid discipline,
 * same styling tokens.
 *
 * ADR-076 D2 additions (all UI-only; no kernel change):
 *   - Result highlighting via <mark data-testid="search-highlight">.
 *   - Corpus selector is a <select> populated from GET /api/gnosis/corpora
 *     with an "All corpora" option that sends corpus: null; when the
 *     selected corpus isn't in the manifest (e.g. a Zetesis-scoped corpus
 *     surfaced through hits), it's added dynamically.
 *   - Empty-state <p data-testid="search-empty"> for non-empty queries
 *     that return zero hits.
 *   - Error surface distinguishes:
 *       * `degraded: true`  (kernel HTTP 200)         → degraded banner
 *       * KernelHttpError 4xx (bad request)           → search-error 4xx
 *       * KernelHttpError 5xx (kernel fault)          → search-error 5xx
 *       * Network / non-HTTP failure                  → search-error network
 *   - Facet count breakdown <ul data-testid="search-facets"> renders
 *     `<corpus>: <N> hits` per corpus in the current hit set.
 *
 * Degradation contract (unchanged):
 *   - Empty query never fires the request.
 */
"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  gnosisGateClient,
  KernelHttpError,
  kernelClient,
  type MemoryHitRow,
  type MemorySearchSemanticResult,
} from "@/lib/kernel-client";

// Backend caps `limit` at 100 (kernel/app.py `_MemorySearchSemanticBody`).
const DEFAULT_LIMIT = 20;
const DEFAULT_MIN_SCORE = 0.0;

// "All corpora" sentinel — never a real corpus name because the kernel
// stores corpora as lowercase identifiers with dashes/underscores only.
const ALL_CORPORA = "__all__";

/**
 * Extract word-boundary tokens from a query for highlight matching.
 * Case-insensitive, deduped, longest-first so "buddhist" beats "budd".
 * Discards tokens shorter than 2 chars to avoid painting the whole page.
 */
function extractHighlightTokens(query: string): string[] {
  const raw = query.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];
  const seen = new Set<string>();
  for (const t of raw) if (t.length >= 2) seen.add(t);
  return Array.from(seen).sort((a, b) => b.length - a.length);
}

/**
 * Escape a token for use inside a RegExp source.
 */
function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Split `text` into interleaved plain / <mark> segments for React.
 * Uses a single global regex with all tokens OR-joined; returns a stable
 * key on each span so React reconciliation stays cheap.
 */
function renderWithHighlights(
  text: string,
  tokens: string[],
): React.ReactNode {
  if (tokens.length === 0 || text.length === 0) return text;
  const pattern = new RegExp(
    "(" + tokens.map(escapeRegex).join("|") + ")",
    "gi",
  );
  const parts = text.split(pattern);
  return parts.map((part, i) => {
    // Odd-indexed parts come from the capture group ⇒ matches.
    if (i % 2 === 1) {
      return (
        <mark data-testid="search-highlight" key={i}>
          {part}
        </mark>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

/**
 * Render a hit payload as a searchable string block. Prefers a single
 * "content" field if present (Zetesis writes it there); falls back to
 * pretty-printed JSON. Kept out of the JSX for easier testing.
 */
function payloadToText(payload: Record<string, unknown>): string {
  const content = payload["content"];
  if (typeof content === "string" && content.length > 0) return content;
  const obj = payload["object"];
  if (typeof obj === "string" && obj.length > 0) return obj;
  return JSON.stringify(payload, null, 2);
}

/**
 * Group hits by their payload corpus for the facet breakdown. Hits
 * without a corpus field fall into "(default)" to keep the row visible.
 */
function facetCorpora(hits: MemoryHitRow[]): Array<[string, number]> {
  const counts = new Map<string, number>();
  for (const h of hits) {
    const c =
      typeof h.payload["corpus"] === "string" && h.payload["corpus"].length > 0
        ? (h.payload["corpus"] as string)
        : "(default)";
    counts.set(c, (counts.get(c) ?? 0) + 1);
  }
  // Sort by count desc, then name asc for stable UI.
  return Array.from(counts.entries()).sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1];
    return a[0].localeCompare(b[0]);
  });
}

/**
 * Classify a caught exception into a stable error kind for the UI.
 */
type ErrorKind = "bad_request" | "kernel_fault" | "network";
interface UiError {
  kind: ErrorKind;
  status: number;
  message: string;
}
function classifyError(e: unknown): UiError {
  if (e instanceof KernelHttpError) {
    if (e.status >= 400 && e.status < 500) {
      return { kind: "bad_request", status: e.status, message: String(e) };
    }
    return { kind: "kernel_fault", status: e.status, message: String(e) };
  }
  return { kind: "network", status: 0, message: String(e) };
}

export default function MemorySearchPage() {
  const [query, setQuery] = useState<string>("");
  const [corpusChoice, setCorpusChoice] = useState<string>(ALL_CORPORA);
  const [availableCorpora, setAvailableCorpora] = useState<string[]>([]);
  const [result, setResult] = useState<MemorySearchSemanticResult | null>(null);
  const [error, setError] = useState<UiError | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Load the static Gnosis corpora manifest once. Non-fatal if it fails —
  // the selector degrades to just "All corpora" + any corpora surfaced
  // through hits.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const raw = await gnosisGateClient.listCorpora();
        if (cancelled) return;
        const names: string[] = [];
        for (const row of raw) {
          if (
            row &&
            typeof row === "object" &&
            "name" in row &&
            typeof (row as { name: unknown }).name === "string"
          ) {
            names.push((row as { name: string }).name);
          }
        }
        setAvailableCorpora(names);
      } catch {
        // Silent: manifest is a nice-to-have, not a blocker.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Union manifest corpora + any corpus surfaced by current hits so a
  // Zetesis-scoped corpus (not in the manifest) is still selectable.
  const corpusOptions = useMemo(() => {
    const set = new Set<string>(availableCorpora);
    if (result) {
      for (const h of result.hits) {
        const c = h.payload["corpus"];
        if (typeof c === "string" && c.length > 0) set.add(c);
      }
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [availableCorpora, result]);

  const highlightTokens = useMemo(() => extractHighlightTokens(query), [query]);
  const facets = useMemo(
    () => (result ? facetCorpora(result.hits) : []),
    [result],
  );

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
        corpus: corpusChoice === ALL_CORPORA ? null : corpusChoice,
        limit: DEFAULT_LIMIT,
        min_score: DEFAULT_MIN_SCORE,
      });
      setResult(res);
    } catch (e: unknown) {
      setError(classifyError(e));
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
          <select
            data-testid="memory-search-corpus"
            value={corpusChoice}
            onChange={(e) => setCorpusChoice(e.target.value)}
            style={{ width: "20ch" }}
          >
            <option value={ALL_CORPORA} data-testid="memory-search-corpus-all">
              All corpora
            </option>
            {corpusOptions.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <button
          data-testid="memory-search-submit"
          type="submit"
          disabled={loading || query.trim().length === 0}
        >
          Search
        </button>
      </form>

      {loading && <p data-testid="memory-search-loading">Searching…</p>}

      {/*
        Error surface: 4xx/5xx/network are all rendered inside
        <p data-testid="search-error"> per ADR-076 D2. A data-kind
        attribute preserves the distinction for automation without
        duplicating the DOM node.
      */}
      {error && (
        <p
          data-testid="search-error"
          data-kind={error.kind}
          data-status={String(error.status)}
          role="alert"
        >
          {error.kind === "bad_request"
            ? `Bad request (${error.status}): ${error.message}`
            : error.kind === "kernel_fault"
              ? `Kernel error (${error.status}): ${error.message}`
              : `Network error: ${error.message}`}
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

      {/*
        ADR-076 D2 empty-state. Renders ONLY when the search actually ran
        (result !== null), was not degraded, returned zero hits, and the
        query is non-empty. Empty query renders nothing so the initial
        page state stays clean.
      */}
      {result &&
        !result.degraded &&
        result.hits.length === 0 &&
        !loading &&
        query.trim().length > 0 && (
          <p data-testid="search-empty">
            No memory events match this query.
          </p>
        )}

      {/*
        Facet breakdown — shows only when there is at least one hit and
        we are not in a degraded state. Renders one <li> per corpus
        surfaced in the current hit set.
      */}
      {result && !result.degraded && result.hits.length > 0 && (
        <ul
          data-testid="search-facets"
          style={{
            listStyle: "none",
            padding: 0,
            margin: "0 0 var(--space-2) 0",
            display: "flex",
            gap: "var(--space-3)",
            flexWrap: "wrap",
            opacity: 0.85,
            fontSize: "0.9em",
          }}
        >
          {facets.map(([corpus, count]) => (
            <li
              key={corpus}
              data-testid="search-facet"
              data-corpus={corpus}
              data-count={String(count)}
            >
              {corpus}: {count} hit{count === 1 ? "" : "s"}
            </li>
          ))}
        </ul>
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
          {result.hits.map((h: MemoryHitRow) => {
            const snippet = payloadToText(h.payload);
            return (
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
                  {typeof h.payload["corpus"] === "string" &&
                    h.payload["corpus"].length > 0 && (
                      <span
                        data-testid="memory-search-hit-corpus"
                        style={{ opacity: 0.6 }}
                      >
                        {h.payload["corpus"] as string}
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
                  {renderWithHighlights(snippet, highlightTokens)}
                </pre>
              </li>
            );
          })}
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
