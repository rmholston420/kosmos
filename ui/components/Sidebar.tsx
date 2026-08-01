"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "../lib/kernel-client";

// Job-segmented navigation per UX Design Spec §"Information Architecture:
// Job-Segmented, Not Data-Segmented". Top section = the five VSM-derived
// user jobs (Command / Operate / Govern / Observe / Memory), which map
// directly onto build-spec §1 systems. Second section = per-plugin route
// manifest surfaced by FrontendContractPort — never hardcoded; the shell
// resolves Route.path/label/icon from the live registry.
//
// /gnosis is still statically appended because it has no plugin wrapper —
// Stage 4.6 gate lives at adapter level and never registers a FrontendContractPort
// Route. Zetesis's descriptor now publishes `/zetesis` live (plugins/zetesis/plugin.py
// ZETESIS_ROUTE_PATH); the Stage 6.1 zero-routes contract test was retired by
// ADR-074/075 event-bus wiring. Duplicate sidebar entry removed 2026-08-01.
const STATIC_ROUTES: Route[] = [
  { path: "/gnosis", label: "Gnosis (corpora)", icon: "database", lazy_module: "" },
];

const JOB_ROUTES: { path: string; label: string; description: string }[] = [
  { path: "/command", label: "Command", description: "What needs a decision now" },
  { path: "/operate", label: "Operate", description: "Plugin operational surfaces" },
  { path: "/govern", label: "Govern", description: "Constitution & policy ledger" },
  { path: "/observe", label: "Observe", description: "Traces, anomalies, telemetry" },
  { path: "/memory", label: "Memory", description: "Knowledge graph & provenance" },
  { path: "/kernel", label: "Kernel", description: "Plugin registry & schema introspection" },
];

// Normalize the current pathname so "/command/" (trailingSlash: true in
// next.config.js static export) and "/command" both match the job link.
function normalize(p: string | null): string {
  if (!p) return "/";
  const stripped = p.replace(/\/+$/, "");
  return stripped === "" ? "/" : stripped;
}

export default function Sidebar({ routes }: { routes: Route[] }) {
  const pathname = normalize(usePathname());
  // De-dupe by path so a plugin that registers a route which also exists in
  // STATIC_ROUTES only renders once. Live registry rows win; static entries
  // are fallbacks for routes without a FrontendContractPort registration.
  const seen = new Set<string>();
  const pluginRoutes = [...routes, ...STATIC_ROUTES].filter((r) => {
    if (seen.has(r.path)) return false;
    seen.add(r.path);
    return true;
  });

  return (
    <nav data-testid="sidebar" aria-label="Kosmos navigation">
      <section data-testid="sidebar-jobs" aria-label="Jobs">
        <h2 data-testid="sidebar-jobs-heading">Jobs</h2>
        <ul>
          {JOB_ROUTES.map((r) => {
            const active = pathname === r.path;
            return (
              <li key={r.path}>
                <Link
                  data-testid={`job-link-${r.path}`}
                  data-active={active}
                  href={r.path}
                  title={r.description}
                  aria-current={active ? "page" : undefined}
                >
                  {r.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </section>

      <section data-testid="sidebar-plugins" aria-label="Plugin routes">
        <h2 data-testid="sidebar-plugins-heading">Plugins</h2>
        {pluginRoutes.length === 0 ? (
          <p data-testid="sidebar-empty">No routes registered</p>
        ) : (
          <ul>
            {pluginRoutes.map((r) => {
              const active = pathname === normalize(r.path);
              return (
                <li key={r.path}>
                  <Link
                    data-testid={`route-${r.path}`}
                    data-active={active}
                    href={r.path}
                    aria-current={active ? "page" : undefined}
                  >
                    {r.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </nav>
  );
}
