"use client";
// Wave F · F2 · STUB_DEGRADATION
// -------------------------------------------------------------------------
// Reads /api/kernel/plugins (FrontendContractPort.list_plugins) and shows
// each mounted plugin with its subsystem-health state. A "degraded" state
// means the plugin booted with one or more subsystems unavailable
// (registry.errors carries the reason). This surface answers the
// UX Design Spec §"Operate" question: "which parts of Kosmos are running
// in reduced-capability mode right now?"
//
// Zero-trust: this panel never fabricates state — if /api/kernel/plugins
// returns 503, the panel shows an error row and lets the user see that
// the FrontendContractPort itself is down.
// -------------------------------------------------------------------------
import { useCallback, useEffect, useState } from "react";
import { kernelClient, type PluginDescriptor } from "../../lib/kernel-client";
import { useEventListener } from "../../lib/events-ws";

interface PluginRow {
  name: string;
  version: string;
  routes: number;
  panels: number;
  degraded: boolean;
}

function summarize(plugins: PluginDescriptor[]): PluginRow[] {
  return plugins.map((p) => ({
    name: p.name,
    version: p.version,
    routes: p.routes.length,
    panels: p.panels.length,
    // A plugin is considered degraded when it advertises zero routes AND
    // zero panels — the FrontendContractPort convention for a boot-time
    // subsystem fault (kernel logs registry.errors[<name>]).
    degraded: p.routes.length === 0 && p.panels.length === 0,
  }));
}

export default function StubDegradationPanel() {
  const [rows, setRows] = useState<PluginRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    kernelClient
      .renderKernelSchema()
      .then((s) => {
        setRows(summarize(s.plugins));
        setError(null);
      })
      .catch((e: unknown) => {
        setError(String(e));
        setRows([]);
      });
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  // Refresh on kernel lifecycle events — a resume may reflect plugin re-boot.
  useEventListener("kernel.resumed", refetch);

  const degradedCount = (rows ?? []).filter((r) => r.degraded).length;

  return (
    <article
      data-testid="panel-STUB_DEGRADATION"
      data-populated="true"
      data-degraded-count={degradedCount}
    >
      <h2>Plugin Health</h2>
      {error && (
        <p data-testid="stub-degradation-error" role="alert">
          {error}
        </p>
      )}
      {rows === null ? (
        <p data-testid="stub-degradation-loading">Loading…</p>
      ) : rows.length === 0 ? (
        <p data-testid="stub-degradation-empty">No plugins mounted</p>
      ) : (
        <ul data-testid="stub-degradation-list">
          {rows.map((r) => (
            <li
              key={r.name}
              data-testid={`stub-degradation-row-${r.name}`}
              data-degraded={r.degraded}
            >
              <span data-testid={`stub-degradation-name-${r.name}`}>{r.name}</span>
              <span data-testid={`stub-degradation-version-${r.name}`}>v{r.version}</span>
              <span data-testid={`stub-degradation-routes-${r.name}`}>
                {r.routes} routes
              </span>
              <span data-testid={`stub-degradation-panels-${r.name}`}>
                {r.panels} panels
              </span>
              {r.degraded && (
                <span data-testid={`stub-degradation-badge-${r.name}`} role="status">
                  degraded
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
