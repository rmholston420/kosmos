// ADR-076 D6 — AMG status pill for the /memory header.
//
// Color:
//   green   quarantined_count == 0 (system healthy)
//   yellow  quarantined_count > 0
//   red     503 (AMG unavailable)
//
// Click expands a compact card showing version, policy_preset, detectors,
// and verdict counts.

"use client";

import { useEffect, useState } from "react";
import { kernelClient, type AmgStatus } from "../../lib/kernel-client";

type LoadState = "loading" | "ok" | "unavailable" | "error";

// Kept in sync with the Stage 4.6 confidence-pill palette so operators
// see the same semantics across surfaces.
const COLOR_GREEN = "#1b7f3a";
const COLOR_YELLOW = "#8a6a1b";
const COLOR_RED = "#7a1f1f";
const COLOR_GREY = "#555";

export default function AmgStatusPill() {
  const [status, setStatus] = useState<AmgStatus | null>(null);
  const [state, setState] = useState<LoadState>("loading");
  const [errText, setErrText] = useState<string>("");
  const [open, setOpen] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    kernelClient
      .getAmgStatus()
      .then((s) => {
        if (cancelled) return;
        setStatus(s);
        setState("ok");
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        const msg = e instanceof Error ? e.message : String(e);
        if (msg.includes("503")) {
          setState("unavailable");
        } else {
          setErrText(msg);
          setState("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  let color = COLOR_GREY;
  let label = "AMG …";
  let terminalTid = "amg-pill-loading";
  if (state === "ok" && status !== null) {
    if (status.quarantined_count > 0) {
      color = COLOR_YELLOW;
      label = `AMG · ${status.quarantined_count} quarantined`;
      terminalTid = "amg-pill-warn";
    } else {
      color = COLOR_GREEN;
      label = `AMG · ok`;
      terminalTid = "amg-pill-ok";
    }
  } else if (state === "unavailable") {
    color = COLOR_RED;
    label = "AMG · unavailable";
    terminalTid = "amg-pill-unavailable";
  } else if (state === "error") {
    color = COLOR_RED;
    label = "AMG · error";
    terminalTid = "amg-pill-error";
  }

  return (
    <span data-testid="amg-status-pill" style={{ display: "inline-block" }}>
      <button
        data-testid={terminalTid}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        style={{
          padding: "2px 8px",
          borderRadius: "999px",
          background: color,
          color: "#fff",
          border: "none",
          cursor: "pointer",
          fontSize: "0.85em",
          fontWeight: 500,
        }}
      >
        {label}
      </button>
      {open && (
        <div
          data-testid="amg-pill-details"
          style={{
            marginTop: "var(--space-2)",
            padding: "var(--space-2)",
            border: "1px solid var(--border, #333)",
            borderRadius: "var(--radius-2, 8px)",
            fontSize: "0.9em",
            maxWidth: "36rem",
          }}
        >
          {state === "ok" && status !== null && (
            <>
              <div data-testid="amg-pill-version">
                <strong>version:</strong> <code>{status.version}</code>
              </div>
              <div data-testid="amg-pill-preset">
                <strong>policy_preset:</strong>{" "}
                <code>{status.policy_preset}</code>
              </div>
              <div data-testid="amg-pill-detectors">
                <strong>active_detectors:</strong>{" "}
                {status.active_detectors.length === 0 ? (
                  <em>(none reported)</em>
                ) : (
                  status.active_detectors.map((d) => (
                    <code
                      key={d}
                      style={{
                        marginRight: "var(--space-1)",
                        padding: "0 4px",
                        background: "rgba(255,255,255,0.06)",
                        borderRadius: "4px",
                      }}
                    >
                      {d}
                    </code>
                  ))
                )}
              </div>
              <div data-testid="amg-pill-verdicts">
                <strong>verdict_counts:</strong> allow={" "}
                {status.verdict_counts.allow}, redact={" "}
                {status.verdict_counts.redact}, quarantine={" "}
                {status.verdict_counts.quarantine}, block={" "}
                {status.verdict_counts.block}
              </div>
              <div data-testid="amg-pill-quarantined">
                <strong>quarantined_count:</strong> {status.quarantined_count}
              </div>
            </>
          )}
          {state === "unavailable" && (
            <p>AMG subsystem returned 503 (unavailable).</p>
          )}
          {state === "error" && (
            <p>Error fetching AMG status: {errText}</p>
          )}
          {state === "loading" && <p>Loading…</p>}
        </div>
      )}
    </span>
  );
}
