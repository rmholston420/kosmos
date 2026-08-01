"use client";
import { useEffect, useState, type ReactNode } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { kernelClient, type KernelSchema } from "../lib/kernel-client";
import Sidebar from "./Sidebar";
import AlgedonicPill from "./AlgedonicPill";
import AlgedonicBanner from "./AlgedonicBanner";
import ModelSwapIndicator from "./ModelSwapIndicator";
import CommandPalette from "./CommandPalette";
import KillSwitch from "./KillSwitch";
import DesignTokenHydrator from "./DesignTokenHydrator";

// PersistentShell wraps every page with the top bar (Cmd+K, algedonic pill,
// model-swap indicator, kill-switch), the left sidebar (job segments +
// plugin routes from the live kernel schema), the right-hand contextual
// drawer, and the full-width algedonic banner. Per UX Design Spec
// §"Persistent Shell". `children` are rendered as the main content area.
//
// One schema fetch here, cached in state, avoids per-page duplication —
// individual pages may still call `kernelClient.renderKernelSchema()` for
// their own use (e.g. JobPage) without conflicting.
export default function PersistentShell({ children }: { children: ReactNode }) {
  const [schema, setSchema] = useState<KernelSchema | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    kernelClient.renderKernelSchema().then(setSchema).catch(() => setSchema(null));
  }, []);

  const pluginRoutes = schema ? schema.plugins.flatMap((p) => p.routes) : [];

  return (
    <div id="kosmos-shell">
      <DesignTokenHydrator />

      <header data-testid="top-bar" role="banner">
        <CommandPalette />
        <AlgedonicPill />
        <ModelSwapIndicator />
        <button
          data-testid="drawer-trigger"
          aria-label="Open contextual drawer"
          onClick={() => setDrawerOpen(true)}
        >
          Details
        </button>
        <KillSwitch />
      </header>

      <AlgedonicBanner />

      <div data-testid="shell-body" style={{ display: "flex" }}>
        <Sidebar routes={pluginRoutes} />
        <div data-testid="shell-content" style={{ flex: 1 }}>
          {children}
        </div>
      </div>

      {/* Radix Sheet contextual drawer per UX Design Spec §"Persistent Shell". */}
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
    </div>
  );
}
