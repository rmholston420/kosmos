"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { gnosisGateClient } from "../../../lib/kernel-client";

type Claim = {
  event_id: string;
  subject: string;
  predicate: string;
  object_: string;
  confidence: number;
};

type Provenance = {
  claim: { event_id: string };
  outbound: unknown[];
  inbound: unknown[];
};

type Edge = { kind: string; dst_subject: string };

export default function GnosisCorpusDetail() {
  const params = useParams();
  const rawCorpus = params?.corpusName;
  const corpusName = Array.isArray(rawCorpus) ? rawCorpus[0] : (rawCorpus ?? "");

  const [detail, setDetail] = useState<unknown | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState<string>("");
  const [queryResults, setQueryResults] = useState<Claim[] | null>(null);
  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [edges, setEdges] = useState<Edge[] | null>(null);

  useEffect(() => {
    if (!corpusName) return;
    gnosisGateClient
      .getCorpusDetail(corpusName)
      .then((d: unknown) => setDetail(d))
      .catch((e: unknown) => setError(String(e)));
  }, [corpusName]);

  const runQuery = () => {
    gnosisGateClient.query(corpusName, query).then((r: unknown) => setQueryResults(r as Claim[]));
  };

  const showProvenance = (eventId: string) => {
    gnosisGateClient
      .getProvenance(corpusName, eventId)
      .then((p: unknown) => setProvenance(p as Provenance));
  };

  const showTraversal = (eventId: string) => {
    gnosisGateClient
      .traverse(corpusName, eventId)
      .then((e: unknown) => setEdges(e as Edge[]));
  };

  if (error) return <main data-testid="gnosis-detail-error">{error}</main>;
  if (!detail) return <main data-testid="gnosis-detail-loading">Loading corpus…</main>;

  return (
    <main data-testid="gnosis-corpus-detail">
      <h1 data-testid="gnosis-detail-name">{corpusName}</h1>

      <div>
        <input
          data-testid="gnosis-query-input"
          placeholder="predicate filter (empty = sample)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button data-testid="gnosis-query-run" onClick={runQuery}>
          Query
        </button>
      </div>

      {queryResults && (
        <ul data-testid="gnosis-query-results">
          {queryResults.map((c) => (
            <li data-testid={"gnosis-claim-" + c.event_id} key={c.event_id}>
              <span data-testid={"gnosis-claim-triple-" + c.event_id}>
                {c.subject} — {c.predicate} — {c.object_}
              </span>
              <span data-testid={"gnosis-claim-confidence-" + c.event_id}>
                {c.confidence.toFixed(3)}
              </span>
              <button
                data-testid={"gnosis-claim-provenance-" + c.event_id}
                onClick={() => showProvenance(c.event_id)}
              >
                Provenance
              </button>
              <button
                data-testid={"gnosis-claim-traverse-" + c.event_id}
                onClick={() => showTraversal(c.event_id)}
              >
                Traverse
              </button>
            </li>
          ))}
        </ul>
      )}

      {provenance && (
        <section data-testid="gnosis-provenance-chain">
          <p data-testid="gnosis-provenance-claim">{provenance.claim.event_id}</p>
          <p data-testid="gnosis-provenance-outbound-count">{provenance.outbound.length}</p>
          <p data-testid="gnosis-provenance-inbound-count">{provenance.inbound.length}</p>
        </section>
      )}

      {edges && (
        <section data-testid="gnosis-traversal-result">
          <ul>
            {edges.map((e, i) => (
              <li data-testid={"gnosis-edge-" + i} key={i}>
                <span data-testid={"gnosis-edge-kind-" + i}>{e.kind}</span>
                <span data-testid={"gnosis-edge-dst-" + i}>{e.dst_subject}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
