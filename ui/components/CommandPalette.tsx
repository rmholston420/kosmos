"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import * as Dialog from "@radix-ui/react-dialog";

// Cmd+K palette per UX Design Spec §"Persistent Shell". Vendored `cmdk`
// (MIT, PORTING_LEDGER) provides the a11y-correct combobox behaviour;
// Radix Dialog provides the modal surface + focus trap.
// Wave A scope: static navigation targets only (job pages + plugin routes
// come from the kernel schema in a later wave — this list stays typed so
// tests can rely on the presence of at least the 5 job commands).

const COMMANDS: { id: string; label: string; hint: string; href: string }[] = [
  { id: "goto-command", label: "Go to Command", hint: "What needs a decision now", href: "/command" },
  { id: "goto-operate", label: "Go to Operate", hint: "Plugin operational surfaces", href: "/operate" },
  { id: "goto-govern",  label: "Go to Govern",  hint: "Constitution & policy ledger", href: "/govern" },
  { id: "goto-observe", label: "Go to Observe", hint: "Traces, anomalies, telemetry", href: "/observe" },
  { id: "goto-memory",  label: "Go to Memory",  hint: "Knowledge graph & provenance", href: "/memory" },
  { id: "goto-home",    label: "Go to Home",    hint: "Full nine-panel dashboard", href: "/" },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

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
                  {COMMANDS.map((c) => (
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
              </Command.List>
            </Command>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
