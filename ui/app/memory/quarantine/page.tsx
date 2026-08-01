/**
 * Memory Quarantine Review — ADR-076 D4.
 *
 * Wraps:
 *   - GET  /api/memory/quarantined
 *   - POST /api/memory/quarantined/{event_id}/approve
 *   - POST /api/memory/quarantined/{event_id}/reject
 *   - GET  /api/kernel/identity            (reviewer identity source)
 *
 * Zero-trust discipline (spec §115): a :Quarantined row is untrusted until
 * a human reviews it. Approve promotes it into MemoryPort under
 * ``provenance=quarantine.approved:<reviewer>``; reject deletes it.
 *
 * Degradation contract:
 *   - kernel HTTP 200 with `degraded: true` → banner, no rows
 *   - KernelHttpError 4xx/5xx / network     → error surface
 */
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  KernelHttpError,
  kernelClient,
  type QuarantinedEntry,
  type QuarantinedListResult,
} from "@/lib/kernel-client";

type PageState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ok"; page: QuarantinedListResult }
  | { kind: "error"; status: number | "network"; message: string };

const DEFAULT_LIMIT = 50;

export default function QuarantineReviewPage() {
  const [reviewer, setReviewer] = useState<string>("");
  const [state, setState] = useState<PageState>({ kind: "idle" });
  const [reasonById, setReasonById] = useState<Record<string, string>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState<string>("");

  // Fetch reviewer identity + initial page on mount.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const id = await kernelClient.getKernelIdentity();
        if (!cancelled) setReviewer(id.reviewer);
      } catch {
        // Non-fatal; user can still act if they type an override.
      }
      await refresh();
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refresh() {
    setState({ kind: "loading" });
    try {
      const page = await kernelClient.listQuarantined({
        limit: DEFAULT_LIMIT,
      });
      setState({ kind: "ok", page });
    } catch (err) {
      if (err instanceof KernelHttpError) {
        setState({
          kind: "error",
          status: err.status,
          message: err.message,
        });
      } else {
        setState({
          kind: "error",
          status: "network",
          message: err instanceof Error ? err.message : String(err),
        });
      }
    }
  }

  async function doAction(entry: QuarantinedEntry, action: "approve" | "reject") {
    const reason = (reasonById[entry.event_id] || "").trim();
    if (!reason) {
      setLastAction(`reason required to ${action}`);
      return;
    }
    if (!reviewer.trim()) {
      setLastAction("reviewer identity not loaded");
      return;
    }
    setBusyId(entry.event_id);
    setLastAction("");
    try {
      if (action === "approve") {
        const res = await kernelClient.approveQuarantined(entry.event_id, {
          reviewer,
          reason,
        });
        setLastAction(`approved → promoted ${res.promoted_event_id}`);
      } else {
        await kernelClient.rejectQuarantined(entry.event_id, {
          reviewer,
          reason,
        });
        setLastAction(`rejected ${entry.event_id}`);
      }
      await refresh();
    } catch (err) {
      if (err instanceof KernelHttpError) {
        setLastAction(`error ${err.status}: ${err.message}`);
      } else {
        setLastAction(
          `network error: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main data-testid="memory-quarantine-page">
      <header
        style={{
          display: "flex",
          gap: "var(--space-4)",
          alignItems: "center",
          marginBottom: "var(--space-3)",
        }}
      >
        <h1 style={{ marginRight: "auto" }}>Quarantine Review</h1>
        <span data-testid="quarantine-reviewer" style={{ opacity: 0.7 }}>
          reviewer: {reviewer || "(unknown)"}
        </span>
        <Link data-testid="memory-back-link" href="/memory/">
          ← Memory
        </Link>
      </header>

      {state.kind === "loading" && (
        <p data-testid="quarantine-loading">Loading…</p>
      )}

      {state.kind === "error" && (
        <p
          data-testid="quarantine-error"
          data-kind={state.status === "network" ? "network" : "http"}
          data-status={String(state.status)}
          style={{ color: "var(--color-error, tomato)" }}
        >
          {String(state.status)}: {state.message}
        </p>
      )}

      {state.kind === "ok" && state.page.degraded && (
        <p
          data-testid="quarantine-degraded"
          style={{ color: "var(--color-warning, goldenrod)" }}
        >
          Memory port unavailable{state.page.reason ? `: ${state.page.reason}` : ""}
        </p>
      )}

      {state.kind === "ok" && !state.page.degraded && state.page.entries.length === 0 && (
        <p data-testid="quarantine-empty">No quarantined entries.</p>
      )}

      {state.kind === "ok" && state.page.entries.length > 0 && (
        <ul data-testid="quarantine-list" style={{ listStyle: "none", padding: 0 }}>
          {state.page.entries.map((e) => {
            const reason = reasonById[e.event_id] || "";
            const busy = busyId === e.event_id;
            return (
              <li
                key={e.event_id}
                data-testid="quarantine-entry"
                data-event-id={e.event_id}
                style={{
                  border: "1px solid var(--color-border, #333)",
                  padding: "var(--space-2)",
                  marginBottom: "var(--space-2)",
                }}
              >
                <header style={{ display: "flex", gap: "var(--space-3)", flexWrap: "wrap" }}>
                  <code data-testid="quarantine-event-id">{e.event_id}</code>
                  <span data-testid="quarantine-provenance">
                    provenance: {e.provenance || "(none)"}
                  </span>
                  <span data-testid="quarantine-confidence">
                    conf: {e.confidence.toFixed(3)}
                  </span>
                  <span data-testid="quarantine-quarantined-at" style={{ marginLeft: "auto" }}>
                    {e.quarantined_at}
                  </span>
                </header>
                <p data-testid="quarantine-reason-original">
                  reason: {e.reason || "(none)"}
                </p>
                <details>
                  <summary>payload</summary>
                  <pre data-testid="quarantine-payload" style={{ overflow: "auto" }}>
                    {JSON.stringify(e.payload, null, 2)}
                  </pre>
                </details>
                <div
                  style={{
                    display: "flex",
                    gap: "var(--space-2)",
                    marginTop: "var(--space-2)",
                    alignItems: "center",
                  }}
                >
                  <label style={{ flex: 1 }}>
                    Review reason:{" "}
                    <input
                      data-testid="quarantine-reason-input"
                      value={reason}
                      onChange={(ev) =>
                        setReasonById((prev) => ({
                          ...prev,
                          [e.event_id]: ev.target.value,
                        }))
                      }
                      placeholder="required for approve/reject"
                      style={{ width: "100%" }}
                    />
                  </label>
                  <button
                    data-testid="quarantine-approve"
                    type="button"
                    onClick={() => doAction(e, "approve")}
                    disabled={busy || !reason.trim()}
                  >
                    Approve
                  </button>
                  <button
                    data-testid="quarantine-reject"
                    type="button"
                    onClick={() => doAction(e, "reject")}
                    disabled={busy || !reason.trim()}
                  >
                    Reject
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {lastAction && (
        <p data-testid="quarantine-last-action" style={{ opacity: 0.8 }}>
          {lastAction}
        </p>
      )}
    </main>
  );
}
