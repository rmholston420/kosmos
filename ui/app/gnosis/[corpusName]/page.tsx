"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { gnosisGateClient } from "../../../lib/kernel-client";

export default function GnosisCorpusDetail() {
  const params = useParams();
  const corpusName = params.corpusName;

  const [detail, setDetail] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [queryResults, setQueryResults] = useState(null);
  const [provenance, setProvenance] = useState(null);
  const [edges, setEdges] = useState(null);

  useEffect(() => {
    gnosisGateClient
      .getCorpusDetail(corpusName)
      .then(setDetail)
      .catch((e) => setError(String(e)));
  }, [corpusName]);

  const runQuery = () => {
    gnosisGateClient.query(corpusName, query).then(setQueryResults);
  };

  const showProvenance = (eventId) => {
    gnosisGateClient.getProvenance(corpusName, eventId).then(setProvenance);
  };

  const showTraversal = (eventId) => {
    gnosisGateClient.traverse(corpusName, eventId).then(setEdges);
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
