"use client";
import { useEffect, useState } from "react";
import {
  kernelClient,
  type KernelSchema,
  type PluginDescriptor,
} from "../../lib/kernel-client";

// Stage 1.5 Wave F · F5 · Kernel introspection page (ADR-072).
//
// Renders the entire /api/kernel/schema payload as a browsable
// registry: plugins (name, state_namespace, version, kernel_compat,
// design_tokens, routes, panels), the aggregate design_tokens map,
// and the schema generation timestamp. Read-only introspection —
// no state changes. Useful during Stage 6.4 plugin bring-up when
// the operator wants to confirm exactly which descriptors the kernel
// is advertising.

function formatTokens(tokens: Record<string, string>): [string, string][] {
  return Object.entries(tokens).sort(([a], [b]) => a.localeCompare(b));
}

function PluginCard({ p }: { p: PluginDescriptor }) {
  const tokens = formatTokens(p.design_tokens ?? {});
  return (
    <article
      data-testid={`kernel-plugin-${p.name}`}
      style={{
        border: "1px solid var(--rgpa-border, #333)",
        borderRadius: "6px",
        padding: "12px 14px",
        marginBottom: "12px",
        background: "var(--rgpa-surface-1, #1a1a1a)",
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          gap: "12px",
          marginBottom: "8px",
        }}
      >
        <h3
          data-testid={`kernel-plugin-${p.name}-name`}
          style={{ margin: 0, fontFamily: "var(--rgpa-mono, monospace)" }}
        >
          {p.name}
        </h3>
        <span
          data-testid={`kernel-plugin-${p.name}-version`}
          style={{
            fontSize: "11px",
            color: "var(--rgpa-fg-2, #999)",
            fontFamily: "var(--rgpa-mono, monospace)",
          }}
        >
          v{p.version} · kernel {p.kernel_compat}
        </span>
      </header>

      <dl
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          gap: "4px 12px",
          fontSize: "12px",
          margin: 0,
        }}
      >
        <dt style={{ color: "var(--rgpa-fg-2, #999)" }}>state_namespace</dt>
        <dd
          data-testid={`kernel-plugin-${p.name}-namespace`}
          style={{ margin: 0, fontFamily: "var(--rgpa-mono, monospace)" }}
        >
          {p.state_namespace}
        </dd>

        <dt style={{ color: "var(--rgpa-fg-2, #999)" }}>routes</dt>
        <dd
          data-testid={`kernel-plugin-${p.name}-routes`}
          style={{ margin: 0 }}
        >
          {p.routes.length === 0 ? (
            <span style={{ color: "var(--rgpa-fg-3, #666)" }}>none</span>
          ) : (
            <ul style={{ margin: 0, paddingLeft: "16px" }}>
              {p.routes.map((r) => (
                <li key={r.path}>
                  <code>{r.path}</code> — {r.label}
                </li>
              ))}
            </ul>
          )}
        </dd>

        <dt style={{ color: "var(--rgpa-fg-2, #999)" }}>panels</dt>
        <dd
          data-testid={`kernel-plugin-${p.name}-panels`}
          style={{ margin: 0 }}
        >
          {p.panels.length === 0 ? (
            <span style={{ color: "var(--rgpa-fg-3, #666)" }}>none</span>
          ) : (
            <ul style={{ margin: 0, paddingLeft: "16px" }}>
              {p.panels.map((pn) => (
                <li key={pn.id}>
                  <code>{pn.id}</code> → slot <code>{pn.slot}</code>{" "}
                  (priority {pn.priority})
                </li>
              ))}
            </ul>
          )}
        </dd>

        {tokens.length > 0 && (
          <>
            <dt style={{ color: "var(--rgpa-fg-2, #999)" }}>design_tokens</dt>
            <dd
              data-testid={`kernel-plugin-${p.name}-tokens`}
              style={{ margin: 0 }}
            >
              <details>
                <summary style={{ cursor: "pointer" }}>
                  {tokens.length} token{tokens.length === 1 ? "" : "s"}
                </summary>
                <ul
                  style={{
                    margin: "4px 0 0 0",
                    paddingLeft: "16px",
                    fontFamily: "var(--rgpa-mono, monospace)",
                    fontSize: "11px",
                  }}
                >
                  {tokens.map(([k, v]) => (
                    <li key={k}>
                      <code>{k}</code>: <code>{v}</code>
                    </li>
                  ))}
                </ul>
              </details>
            </dd>
          </>
        )}
      </dl>
    </article>
  );
}

export default function KernelPage() {
  const [schema, setSchema] = useState<KernelSchema | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    kernelClient
      .renderKernelSchema()
      .then(setSchema)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <main data-testid="job-kernel-error" style={{ padding: "16px" }}>
        Kernel unreachable: {error}
      </main>
    );
  }
  if (!schema) {
    return (
      <main data-testid="job-kernel-loading" style={{ padding: "16px" }}>
        Loading kernel schema…
      </main>
    );
  }

  const tokens = formatTokens(schema.design_tokens ?? {});

  return (
    <main data-testid="job-kernel" style={{ padding: "16px" }}>
      <header data-testid="job-kernel-header" style={{ marginBottom: "16px" }}>
        <h1 data-testid="job-kernel-title">Kernel</h1>
        <p
          data-testid="job-kernel-description"
          style={{ color: "var(--rgpa-fg-2, #999)", marginBottom: "4px" }}
        >
          Plugin registry & schema introspection.
        </p>
        <p
          data-testid="job-kernel-generated"
          style={{
            fontSize: "11px",
            color: "var(--rgpa-fg-3, #666)",
            fontFamily: "var(--rgpa-mono, monospace)",
          }}
        >
          Schema generated {schema.generated_at} · title{" "}
          <code>{schema.title}</code> · {schema.plugins.length} plugin
          {schema.plugins.length === 1 ? "" : "s"} · {schema.panels.length}{" "}
          panel{schema.panels.length === 1 ? "" : "s"}
        </p>
      </header>

      <section
        data-testid="kernel-plugins"
        aria-label="Registered plugins"
        style={{ marginBottom: "20px" }}
      >
        <h2 style={{ fontSize: "13px", marginBottom: "8px" }}>Plugins</h2>
        {schema.plugins.length === 0 ? (
          <p data-testid="kernel-plugins-empty">No plugins registered.</p>
        ) : (
          schema.plugins.map((p) => <PluginCard key={p.name} p={p} />)
        )}
      </section>

      <section
        data-testid="kernel-panels"
        aria-label="Kernel-level panel registry"
        style={{ marginBottom: "20px" }}
      >
        <h2 style={{ fontSize: "13px", marginBottom: "8px" }}>
          All Panels ({schema.panels.length})
        </h2>
        {schema.panels.length === 0 ? (
          <p data-testid="kernel-panels-empty">No panels registered.</p>
        ) : (
          <ul
            data-testid="kernel-panels-list"
            style={{
              fontFamily: "var(--rgpa-mono, monospace)",
              fontSize: "12px",
              paddingLeft: "16px",
              margin: 0,
            }}
          >
            {schema.panels
              .slice()
              .sort((a, b) => a.priority - b.priority)
              .map((pn) => (
                <li
                  key={pn.id}
                  data-testid={`kernel-panel-${pn.id}`}
                >
                  <code>{pn.id}</code> · slot <code>{pn.slot}</code> ·
                  priority {pn.priority} · plugin <code>{pn.plugin_name}</code>
                </li>
              ))}
          </ul>
        )}
      </section>

      <section
        data-testid="kernel-design-tokens"
        aria-label="Kernel design tokens"
      >
        <h2 style={{ fontSize: "13px", marginBottom: "8px" }}>
          Design tokens ({tokens.length})
        </h2>
        {tokens.length === 0 ? (
          <p data-testid="kernel-design-tokens-empty">No design tokens.</p>
        ) : (
          <details>
            <summary style={{ cursor: "pointer", fontSize: "12px" }}>
              Show token map
            </summary>
            <ul
              data-testid="kernel-design-tokens-list"
              style={{
                fontFamily: "var(--rgpa-mono, monospace)",
                fontSize: "11px",
                paddingLeft: "16px",
                marginTop: "4px",
              }}
            >
              {tokens.map(([k, v]) => (
                <li key={k}>
                  <code>{k}</code>: <code>{v}</code>
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>
    </main>
  );
}
