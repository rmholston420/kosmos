"use client";
import "./globals.css";
import * as Dialog from "@radix-ui/react-dialog";
import { useState, type ReactNode } from "react";

// Note: Next.js `metadata` export requires a Server Component. This layout is
// a Client Component (required for the Radix Sheet drawer's open/close state
// and the top bar's interactive placeholders), so metadata is set directly on
// <head> below rather than via the `export const metadata` convention.

export default function RootLayout({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <html lang="en" data-theme="nagtang">
      <head>
        <title>Kosmos</title>
      </head>
      <body>
        <div id="kosmos-shell">
          {/* Top bar per UX Design Spec "Persistent Shell": Cmd+K trigger,
              algedonic status pill (color + text, never color-only),
              model-swap indicator (hot model, VRAM used of 32GB). */}
          <header data-testid="top-bar" role="banner">
            <button
              data-testid="cmdk-trigger"
              aria-label="Open command palette"
              title="Cmd+K"
              disabled
            >
              ⌘K
            </button>

            <div data-testid="algedonic-pill" data-status="clear" role="status">
              <span data-testid="algedonic-pill-text">Algedonic: Clear</span>
            </div>

            <div data-testid="model-swap-indicator">
              <span data-testid="model-swap-model-name">—</span>
              <span data-testid="model-swap-vram">— / 32GB VRAM</span>
            </div>

            <button
              data-testid="drawer-trigger"
              aria-label="Open contextual drawer"
              onClick={() => setDrawerOpen(true)}
            >
              Details
            </button>
          </header>

          {/* Radix Sheet right-hand contextual drawer (approvals, diffs,
              trace detail without full navigation), per UX Design Spec
              "Persistent Shell". Uses @radix-ui/react-dialog directly since
              shadcn's Sheet component is a styled wrapper around Dialog. */}
          <Dialog.Root open={drawerOpen} onOpenChange={setDrawerOpen}>
            <Dialog.Portal>
              <Dialog.Overlay data-testid="drawer-overlay" />
              <Dialog.Content
                data-testid="contextual-drawer"
                aria-label="Contextual drawer"
              >
                <Dialog.Title data-testid="drawer-title">Details</Dialog.Title>
                <Dialog.Description data-testid="drawer-description">
                  Contextual detail placeholder — populated per-view (approvals,
                  diffs, trace detail) in later Stage 1 steps.
                </Dialog.Description>
                <Dialog.Close asChild>
                  <button data-testid="drawer-close">Close</button>
                </Dialog.Close>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>

          {children}
        </div>
      </body>
    </html>
  );
}
