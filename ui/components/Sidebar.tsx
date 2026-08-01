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
// /gnosis and /zetesis are still statically appended because neither has a
// FrontendContractPort registration to derive them from yet. Gnosis's
// Stage 4.6 gate never registers (adapter-level app, no plugin wrapper).
// Zetesis's descriptor is locked to zero routes by a Stage 6.1 contract
// test even though research() is functionally complete as of Stage 6.3
// (see build spec "Second Audit Correction"). Remove each static entry
// once the corresponding backend registers its own real Route.
const STATIC_ROUTES: Route[] = [
  { path: "/gnosis", label: "Gnosis (corpora)", icon: "database", lazy_module: "" },
  { path: "/zetesis", label: "Zetesis (research)", icon: "search", lazy_module: "" },
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
  const pluginRoutes = [...routes, ...STATIC_ROUTES];

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
