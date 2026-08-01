"use client";
import { useEffect, useState } from "react";
import {
  kernelClient,
  type Panel,
  type PraxisConstitution,
  type PraxisApexPolicy,
} from "../../lib/kernel-client";

// ADR-068 Wave B — GOVERNANCE surface.
// Reads constitution (D2) + apex policies (D3). Phrouros oversight
// surface rendered visible-but-disabled (backend not yet exposed).

type LoadState = "idle" | "loading" | "ok" | "error";

export default function GovernancePanel({ panels }: { panels: Panel[] }) {
  const [constitution, setConstitution] = useState<PraxisConstitution | null>(null);
  const [policies, setPolicies] = useState<PraxisApexPolicy[]>([]);
  const [constState, setConstState] = useState<LoadState>("idle");
  const [polState, setPolState] = useState<LoadState>("idle");

  useEffect(() => {
    setConstState("loading");
    kernelClient
      .getPraxisConstitution()
      .then((c) => {
        setConstitution(c);
        setConstState("ok");
      })
      .catch(() => setConstState("error"));

    setPolState("loading");
    kernelClient
      .getPraxisApexPolicies()
      .then((p) => {
        setPolicies(Array.isArray(p) ? p : []);
        setPolState("ok");
      })
      .catch(() => setPolState("error"));
  }, []);

  return (
    <article data-testid="panel-GOVERNANCE" data-populated="true">
      <h2>Governance</h2>

      {/* Constitution card */}
      <section data-testid="governance-constitution">
        <h3>Constitution</h3>
        {constState === "loading" && (
          <p data-testid="governance-constitution-loading">Loading constitution…</p>
        )}
        {constState === "error" && (
          <p data-testid="governance-constitution-error" role="alert">
            Failed to load constitution
          </p>
        )}
        {constState === "ok" && constitution && (
          <dl>
            <dt>Title</dt>
            <dd data-testid="governance-constitution-title">{constitution.title}</dd>
            <dt>Version</dt>
            <dd data-testid="governance-constitution-version">{constitution.version}</dd>
            <dt>Ratified</dt>
            <dd data-testid="governance-constitution-ratified">{constitution.ratified_at}</dd>
            <dt>Articles</dt>
            <dd data-testid="governance-constitution-articles">{constitution.article_count}</dd>
            <dt>SHA-256</dt>
            <dd data-testid="governance-constitution-sha">
              <code>{constitution.sha256.slice(0, 12)}…</code>
            </dd>
          </dl>
        )}
      </section>

      {/* Apex policies list */}
      <section data-testid="governance-apex-policies">
        <h3>Apex Policies (Tier-2 escalation triggers)</h3>
        {polState === "loading" && (
          <p data-testid="governance-policies-loading">Loading policies…</p>
        )}
        {polState === "error" && (
          <p data-testid="governance-policies-error" role="alert">
            Failed to load apex policies
          </p>
        )}
        {polState === "ok" && policies.length === 0 && (
          <p data-testid="governance-policies-empty">No apex policies registered</p>
        )}
        {polState === "ok" && policies.length > 0 && (
          <ul data-testid="governance-policies-list">
            {policies.map((p) => (
              <li data-testid={`governance-policy-${p.policy_id}`} key={p.policy_id}>
                <span data-testid={`governance-policy-name-${p.policy_id}`}>{p.name}</span>
                <span data-testid={`governance-policy-tier-${p.policy_id}`}>{p.tier}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Phrouros adversarial oversight surface — visible but disabled
          until backend anomaly-review + veto endpoints land. */}
      <section
        data-testid="governance-phrouros"
        data-enabled="false"
        aria-disabled="true"
      >
        <h3>Phrouros Adversarial Oversight</h3>
        <p data-testid="governance-phrouros-status">
          Not yet wired · anomaly-review + veto endpoints pending
        </p>
      </section>

      {/* Panel refs (preserved from prior contract) */}
      {panels.length > 0 && (
        <section data-testid="governance-panel-refs">
          <h3>Registered governance panels</h3>
          <ul>
            {panels.map((p) => (
              <li data-testid={`governance-panel-${p.id}`} key={p.id}>
                {p.plugin_name} · priority {p.priority}
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
