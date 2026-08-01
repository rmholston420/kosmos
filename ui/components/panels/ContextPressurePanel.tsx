"use client";
// Wave F · F2 · CONTEXT_PRESSURE
// -------------------------------------------------------------------------
// Reads /api/resources/balances to show pressure across the six canonical
// ResourceKinds (time, money, attention, compute, knowledge, energy). This
// is the S3 (VSM Resource Bargain) surface: how much of each currency is
// currently available versus contested.
//
// Zero-trust: if a resource returns null (adapter missing / storage
// backend unreachable), the row shows "unavailable" rather than a
// fabricated zero.
// -------------------------------------------------------------------------
import { useCallback, useEffect, useState } from "react";
import { kernelClient, type ResourceBalance } from "../../lib/kernel-client";
import { useEventListener } from "../../lib/events-ws";

const KINDS = ["time", "money", "attention", "compute", "knowledge", "energy"] as const;

const POLL_MS = 15000;

export default function ContextPressurePanel() {
  const [balances, setBalances] = useState<Record<string, ResourceBalance | null> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    kernelClient
      .getResourceBalances()
      .then((b) => {
        setBalances(b);
        setError(null);
      })
      .catch((e: unknown) => {
        setError(String(e));
        setBalances({});
      });
  }, []);

  useEffect(() => {
    refetch();
    const id = setInterval(refetch, POLL_MS);
    return () => clearInterval(id);
  }, [refetch]);

  useEventListener("kernel.resumed", refetch);

  return (
    <article data-testid="panel-CONTEXT_PRESSURE" data-populated="true">
      <h2>Resource Balances</h2>
      {error && (
        <p data-testid="context-pressure-error" role="alert">
          {error}
        </p>
      )}
      {balances === null ? (
        <p data-testid="context-pressure-loading">Loading…</p>
      ) : (
        <ul data-testid="context-pressure-list">
          {KINDS.map((kind) => {
            const b = balances[kind];
            return (
              <li
                key={kind}
                data-testid={`context-pressure-row-${kind}`}
                data-available={b !== null && b !== undefined}
              >
                <span data-testid={`context-pressure-kind-${kind}`}>{kind}</span>
                {b ? (
                  <>
                    <span data-testid={`context-pressure-balance-${kind}`}>
                      {b.current_balance}
                    </span>
                    <span data-testid={`context-pressure-unit-${kind}`}>{b.unit}</span>
                  </>
                ) : (
                  <span data-testid={`context-pressure-unavailable-${kind}`} role="status">
                    unavailable
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </article>
  );
}
