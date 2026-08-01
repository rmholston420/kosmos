"use client";
import type { Route } from "../lib/kernel-client";

// /gnosis and /zetesis are statically appended -- neither has a
// FrontendContractPort registration to derive them from yet. Gnosis's
// Stage 4.6 gate never registers (adapter-level app, no plugin wrapper).
// Zetesis's descriptor is locked to zero routes by a Stage 6.1 contract
// test even though research() is functionally complete as of Stage 6.3
// (see build spec "Second Audit Correction"). Remove each static entry
// once the corresponding backend registers its own real Route.
const STATIC_ROUTES = [
  { path: "/gnosis", label: "Gnosis (corpora)", icon: "database", lazy_module: "" },
  { path: "/zetesis", label: "Zetesis (research)", icon: "search", lazy_module: "" },
];

export default function Sidebar({ routes }: { routes: Route[] }) {
  const allRoutes = [...routes, ...STATIC_ROUTES];
  return (
    <nav data-testid="sidebar" aria-label="Plugin routes">
      {allRoutes.length === 0 ? (
        <p data-testid="sidebar-empty">No routes registered</p>
      ) : (
        <ul>
          {allRoutes.map((r) => (
            <li key={r.path}>
              <a data-testid={`route-${r.path}`} href={r.path}>
                {r.label}
              </a>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
