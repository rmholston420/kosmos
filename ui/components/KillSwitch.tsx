"use client";
import { useEffect, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { kernelClient, type KernelSuspensionStatus } from "../lib/kernel-client";

// Kill-switch per UX Design Spec §"Persistent Shell": destructive
// affordance behind an explicit two-step confirmation modal, never a bare
// button. Wave C wires to ADR-069 `POST /api/kernel/kill` +
// `POST /api/kernel/resume` with soft-suspend semantics — the UI stays
// alive in suspended state; middleware gates mutating routes.

const POLL_MS = 3000;

export default function KillSwitch() {
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [reason, setReason] = useState("");
  const [status, setStatus] = useState<KernelSuspensionStatus | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = () => {
    kernelClient
      .getSuspensionStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
  };

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, []);

  const suspended = status?.suspended === true;

  const onConfirm = async () => {
    setBusy(true);
    try {
      await kernelClient.killKernel(reason.trim() || undefined);
      refresh();
      setConfirming(false);
      setOpen(false);
      setReason("");
    } catch {
      // Leave dialog open so user sees the state didn't flip.
    } finally {
      setBusy(false);
    }
  };

  const onResume = async () => {
    setBusy(true);
    try {
      await kernelClient.resumeKernel();
      refresh();
    } catch {
      // Ignore; next poll will refresh.
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        data-testid="kill-switch-trigger"
        data-suspended={suspended ? "true" : "false"}
        aria-label={suspended ? "Kernel suspended · click to resume" : "Emergency suspend"}
        title={
          suspended
            ? "Kernel suspended · click to resume"
            : "Emergency suspend (confirm required)"
        }
        onClick={() => (suspended ? onResume() : setOpen(true))}
        disabled={busy}
      >
        {suspended ? "⏵" : "⏻"}
      </button>

      {/* Suspended banner — visible whenever the kernel is soft-suspended,
          regardless of the confirm dialog. */}
      {suspended && (
        <div
          data-testid="kernel-suspended-banner"
          role="status"
          aria-live="polite"
        >
          <span data-testid="kernel-suspended-label">Kernel suspended</span>
          {status?.reason && (
            <span data-testid="kernel-suspended-reason"> · {status.reason}</span>
          )}
          <button
            data-testid="kernel-resume-button"
            onClick={onResume}
            disabled={busy}
          >
            Resume
          </button>
        </div>
      )}

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
              Halts all mutating kernel routes (approvals, tektos turns, zetesis
              research). Introspection stays available. Reversible via Resume.
            </Dialog.Description>
            <label>
              <span>Reason (optional)</span>
              <input
                data-testid="kill-switch-reason-input"
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. runaway agent, load spike"
                disabled={busy}
              />
            </label>
            <button
              data-testid="kill-switch-cancel"
              onClick={() => {
                setConfirming(false);
                setReason("");
                setOpen(false);
              }}
              disabled={busy}
            >
              Cancel
            </button>
            <button
              data-testid="kill-switch-confirm"
              data-confirming={confirming}
              onClick={() => (confirming ? onConfirm() : setConfirming(true))}
              disabled={busy}
            >
              {confirming ? (busy ? "Suspending…" : "Really suspend") : "Confirm"}
            </button>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
