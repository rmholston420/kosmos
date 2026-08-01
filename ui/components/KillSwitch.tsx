"use client";
import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";

// Kill-switch stub per UX Design Spec §"Persistent Shell": destructive
// affordance behind an explicit confirmation modal, never a bare button.
// Wave A: stub only — the "Confirm" button dispatches a client-side
// console message. Wave C ratifies the wire-up ADR (Praxis emergency
// suspend semantics: HUMAN_REQUIRED, mirrors ADR-045 kill semantics).
export default function KillSwitch() {
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const onConfirm = () => {
    // Placeholder — no backend endpoint ratified yet. Do NOT wire to any
    // /api/*/kill route until the ADR exists.
    // eslint-disable-next-line no-console
    console.warn("[kosmos] kill-switch confirmed — stub, no backend action");
    setConfirming(false);
    setOpen(false);
  };

  return (
    <>
      <button
        data-testid="kill-switch-trigger"
        aria-label="Emergency suspend"
        title="Emergency suspend (confirm required)"
        onClick={() => setOpen(true)}
      >
        ⏻
      </button>

      <Dialog.Root open={open} onOpenChange={setOpen}>
        <Dialog.Portal>
          <Dialog.Overlay data-testid="kill-switch-overlay" />
          <Dialog.Content
            data-testid="kill-switch-dialog"
            aria-label="Kill-switch confirmation"
          >
            <Dialog.Title data-testid="kill-switch-title">
              Emergency suspend
            </Dialog.Title>
            <Dialog.Description data-testid="kill-switch-description">
              Stub — no backend endpoint ratified yet. This will suspend all
              autonomous agents once the ADR wires up Praxis emergency
              semantics.
            </Dialog.Description>
            <button
              data-testid="kill-switch-cancel"
              onClick={() => setOpen(false)}
            >
              Cancel
            </button>
            <button
              data-testid="kill-switch-confirm"
              data-confirming={confirming}
              onClick={() => (confirming ? onConfirm() : setConfirming(true))}
            >
              {confirming ? "Really suspend" : "Confirm"}
            </button>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
