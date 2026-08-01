"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import * as Dialog from "@radix-ui/react-dialog";
import { kernelClient, type Route } from "../lib/kernel-client";

// Cmd+K palette per UX Design Spec §"Persistent Shell". Vendored `cmdk`
// (MIT, PORTING_LEDGER) provides the a11y-correct combobox behaviour;
// Radix Dialog provides the modal surface + focus trap.
//
// Wave A: static navigation targets (job pages + home).
// Wave C: adds a "Plugins" group enumerated from the live KernelSchema so
// plugin-registered routes (/tektos, /zetesis, /gnosis, /tektos-ui, etc.)
// are reachable from the palette without a code change.

const STATIC_COMMANDS: { id: string; label: string; hint: string; href: string }[] = [
  { id: "goto-command", label: "Go to Command", hint: "What needs a decision now", href: "/command" },
  { id: "goto-operate", label: "Go to Operate", hint: "Plugin operational surfaces", href: "/operate" },
  { id: "goto-govern",  label: "Go to Govern",  hint: "Constitution & policy ledger", href: "/govern" },
  { id: "goto-observe", label: "Go to Observe", hint: "Traces, anomalies, telemetry", href: "/observe" },
  { id: "goto-memory",  label: "Go to Memory",  hint: "Knowledge graph & provenance", href: "/memory" },
  { id: "goto-home",    label: "Go to Home",    hint: "Full nine-panel dashboard", href: "/" },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [pluginRoutes, setPluginRoutes] = useState<Route[]>([]);
  const router = useRouter();

  // Fetch plugin routes once on mount. If the kernel is unreachable the
  // palette still works with static commands only.
  useEffect(() => {
    kernelClient
      .renderKernelSchema()
      .then((schema) => {
        const routes = schema.plugins.flatMap((p) => p.routes ?? []);
        // Dedupe by path — plugins should not double-register but be safe.
        const seen = new Set<string>();
        const unique: Route[] = [];
        for (const r of routes) {
          if (!seen.has(r.path)) {
            seen.add(r.path);
            unique.push(r);
          }
        }
        setPluginRoutes(unique);
      })
      .catch(() => setPluginRoutes([]));
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const isK = e.key === "k" || e.key === "K";
      if (isK && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((v) => !v);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const run = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  return (
    <>
      <button
        data-testid="cmdk-trigger"
        aria-label="Open command palette"
        title="Cmd+K"
        onClick={() => setOpen(true)}
      >
        ⌘K
      </button>

      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay data-testid="cmdk-overlay" />
          <Dialog.Content
            data-testid="cmdk-dialog"
            aria-label="Command palette"
          >
            <Dialog.Title data-testid="cmdk-title">Command Palette</Dialog.Title>
            <Dialog.Description data-testid="cmdk-description">
              Type to filter — Enter to run.
            </Dialog.Description>
            <Command label="Kosmos command palette">
              <Command.Input
                data-testid="cmdk-input"
                autoFocus
                placeholder="Type a command…"
              />
              <Command.List data-testid="cmdk-list">
                <Command.Empty>No matches.</Command.Empty>
                <Command.Group heading="Navigate">
                  {STATIC_COMMANDS.map((c) => (
                    <Command.Item
                      key={c.id}
                      value={`${c.label} ${c.hint}`}
                      data-testid={`cmdk-item-${c.id}`}
                      onSelect={() => run(c.href)}
                    >
                      <span>{c.label}</span>
                      <span data-testid={`cmdk-hint-${c.id}`}>{c.hint}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
                {pluginRoutes.length > 0 && (
                  <Command.Group
                    heading="Plugins"
                    data-testid="cmdk-group-plugins"
                  >
                    {pluginRoutes.map((r) => {
                      const slug = r.path.replace(/^\//, "").replace(/\//g, "-") || "root";
                      return (
                        <Command.Item
                          key={`plugin-${r.path}`}
                          value={`plugin ${r.label} ${r.path}`}
                          data-testid={`cmdk-item-plugin-${slug}`}
                          data-plugin-path={r.path}
                          onSelect={() => run(r.path)}
                        >
                          <span>{r.label}</span>
                          <span data-testid={`cmdk-hint-plugin-${slug}`}>{r.path}</span>
                        </Command.Item>
                      );
                    })}
                  </Command.Group>
                )}
              </Command.List>
            </Command>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
