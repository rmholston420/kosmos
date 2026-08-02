// ADR-076 D5 — Provenance chain UI.
//
// Route: /memory/provenance?event=<event_id>
//
// Query-parameter based to stay compatible with `output: 'export'` in
// next.config.js (a dynamic segment `[event_id]` would require
// generateStaticParams at build time, which does not fit runtime-
// unknown ids). Renders the chain returned by
// GET /api/memory/provenance/{event_id}:
// - Root card at top (source + timestamp + confidence pill)
// - Predecessors below in depth order (ProvenanceLink cards)
// - Confidence pill palette matches Stage 4.6 gate template:
//     green ≥ 0.9   yellow ≥ 0.5   red < 0.5
//
// Deep-linked from /memory/search hit rows.

"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  kernelClient,
  type ProvenanceChain,
  type ProvenanceLink,
} from "../../../lib/kernel-client";

type LoadState =
  | "idle"
  | "missing_param"
  | "loading"
  | "ok"
  | "not_found"
  | "unavailable"
  | "error";

function confidencePill(conf: number): { bg: string; label: string } {
  if (conf >= 0.9) return { bg: "#1b7f3a", label: conf.toFixed(3) };
  if (conf >= 0.5) return { bg: "#8a6a1b", label: conf.toFixed(3) };
  return { bg: "#7a1f1f", label: conf.toFixed(3) };
}

function ProvenanceInner() {
  const searchParams = useSearchParams();
  const eventId = searchParams.get("event") ?? "";
  const [chain, setChain] = useState<ProvenanceChain | null>(null);
  const [state, setState] = useState<LoadState>("idle");
  const [errText, setErrText] = useState<string>("");

  useEffect(() => {
    if (!eventId) {
      setState("missing_param");
      return;
    }
    let cancelled = false;
    setState("loading");
    (async () => {
      try {
        const c = await kernelClient.getProvenanceChain(eventId);
        if (cancelled) return;
        setChain(c);
        setState("ok");
      } catch (e: unknown) {
        if (cancelled) return;
        const msg = e instanceof Error ? e.message : String(e);
        if (msg.includes("404")) {
          setState("not_found");
        } else if (msg.includes("503")) {
          setState("unavailable");
        } else {
          setErrText(msg);
          setState("error");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  return (
    <main
      data-testid="memory-provenance-page"
      style={{
        padding: "var(--space-4)",
        maxWidth: "48rem",
        margin: "0 auto",
      }}
    >
      <header style={{ marginBottom: "var(--space-3)" }}>
        <Link data-testid="memory-provenance-back-link" href="/memory/search">
          ← Back to search
        </Link>
        <h1 style={{ marginTop: "var(--space-2)" }}>Provenance</h1>
        <code
          data-testid="memory-provenance-event-id"
          style={{ opacity: 0.85 }}
        >
          {eventId || "(no event id)"}
        </code>
      </header>

      {state === "missing_param" && (
        <p data-testid="memory-provenance-missing-param">
          Missing ?event= parameter.
        </p>
      )}
      {state === "loading" && (
        <p data-testid="memory-provenance-loading">Loading…</p>
      )}
      {state === "not_found" && (
        <p data-testid="memory-provenance-not-found">
          No memory event with that id.
        </p>
      )}
      {state === "unavailable" && (
        <p data-testid="memory-provenance-unavailable">
          Memory port unavailable (503).
        </p>
      )}
      {state === "error" && (
        <p data-testid="memory-provenance-error">Error: {errText}</p>
      )}

      {state === "ok" && chain && (
        <section data-testid="memory-provenance-chain">
          <RootCard chain={chain} />
          {chain.predecessors.length === 0 ? (
            <p
              data-testid="memory-provenance-empty-predecessors"
              style={{ opacity: 0.7, marginTop: "var(--space-3)" }}
            >
              No recorded predecessors.
            </p>
          ) : (
            <ol
              data-testid="memory-provenance-predecessors"
              style={{
                listStyle: "none",
                padding: 0,
                marginTop: "var(--space-3)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-2)",
              }}
            >
              {chain.predecessors.map((p) => (
                <li key={p.event_id}>
                  <PredecessorCard link={p} />
                </li>
              ))}
            </ol>
          )}
        </section>
      )}
    </main>
  );
}

export default function ProvenancePage() {
  return (
    <Suspense fallback={<p>Loading…</p>}>
      <ProvenanceInner />
    </Suspense>
  );
}

function RootCard({ chain }: { chain: ProvenanceChain }) {
  const pill = confidencePill(chain.confidence);
  return (
    <article
      data-testid="memory-provenance-root"
      style={{
        border: "1px solid var(--border, #333)",
        padding: "var(--space-3)",
        borderRadius: "var(--radius-2, 8px)",
      }}
    >
      <header
        style={{
          display: "flex",
          gap: "var(--space-2)",
          alignItems: "center",
          marginBottom: "var(--space-2)",
        }}
      >
        <strong>Root event</strong>
        <span
          data-testid="memory-provenance-root-confidence"
          style={{
            background: pill.bg,
            color: "white",
            padding: "2px 8px",
            borderRadius: "999px",
            fontSize: "0.85em",
          }}
        >
          {pill.label}
        </span>
      </header>
      <dl style={{ margin: 0 }}>
        <dt style={{ opacity: 0.6 }}>source</dt>
        <dd data-testid="memory-provenance-root-source">{chain.source || "—"}</dd>
        <dt style={{ opacity: 0.6 }}>timestamp</dt>
        <dd data-testid="memory-provenance-root-timestamp">
          {chain.timestamp}
        </dd>
      </dl>
    </article>
  );
}

function PredecessorCard({ link }: { link: ProvenanceLink }) {
  return (
    <article
      data-testid="memory-provenance-predecessor"
      data-depth={link.depth}
      style={{
        border: "1px solid var(--border, #333)",
        padding: "var(--space-3)",
        borderRadius: "var(--radius-2, 8px)",
      }}
    >
      <header
        style={{
          display: "flex",
          gap: "var(--space-2)",
          alignItems: "center",
          marginBottom: "var(--space-2)",
        }}
      >
        <span style={{ opacity: 0.6 }}>depth {link.depth}</span>
        {link.edge_kind && (
          <code style={{ opacity: 0.75 }}>{link.edge_kind}</code>
        )}
      </header>
      <div>
        <Link
          data-testid="memory-provenance-predecessor-link"
          href={`/memory/provenance?event=${encodeURIComponent(link.event_id)}`}
        >
          <code>{link.event_id}</code>
        </Link>
      </div>
      {link.source && (
        <div style={{ opacity: 0.7, marginTop: "var(--space-1)" }}>
          {link.source}
        </div>
      )}
    </article>
  );
}
