"use client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { useEventsWS, WS_DEFAULT_EVENT_TYPES, type WSEnvelope } from "../lib/events-ws";

// ADR-072 Wave F · F4 · NotificationTray
// -------------------------------------------------------------------------
// Top-bar tray + drawer-backed history of events consumed from the
// shared EventsWSProvider (F1). Renders a bell icon with an unread
// badge; opening the tray reveals the full received-event log and
// clears the unread count. Everything is client-only — the tray never
// polls, never issues fetches — it strictly reflects what the WS
// stream has already delivered.
//
// Design notes:
//   - Uses `Dialog` from radix (already vendored for the contextual
//     drawer in PersistentShell) for accessible focus trap + Escape.
//   - Retains the last N envelopes only, keyed by monotonic id, so
//     long-running sessions can't grow the array unboundedly.
//   - Event kind classification mirrors the F1 default type list so
//     the badge color scheme stays coherent with the algedonic pill:
//       * `phrouros.*` / `kernel.suspended` → danger (Rakta red)
//       * `zetesis.*.completed`             → success (Nagtang gold)
//       * everything else                   → info (Vairocana blue)
// -------------------------------------------------------------------------

const MAX_HISTORY = 100;

type Tone = "danger" | "success" | "info";

function toneOf(evt: WSEnvelope): Tone {
  const t = evt.event_type;
  if (t === "phrouros.anomaly.detected" || t === "kernel.suspended") return "danger";
  if (t === "zetesis.research.completed") return "success";
  return "info";
}

function toneColorVar(tone: Tone): string {
  if (tone === "danger") return "var(--rgpa-danger, oklch(60% 0.2 25))";
  if (tone === "success") return "var(--rgpa-accent-gold, oklch(80% 0.15 85))";
  return "var(--rgpa-accent-blue, oklch(60% 0.15 240))";
}

interface TrayEntry {
  key: string;
  envelope: WSEnvelope;
  receivedAt: number;
}

export default function NotificationTray() {
  const { subscribe, connected } = useEventsWS();
  const [entries, setEntries] = useState<TrayEntry[]>([]);
  const [unread, setUnread] = useState<number>(0);
  const [open, setOpen] = useState<boolean>(false);
  // Monotonic id counter; the envelope's `event_id` may not be unique
  // (dev fixtures replay), so we combine it with a local sequence.
  const seqRef = useRef<number>(0);

  const push = useCallback((env: WSEnvelope) => {
    seqRef.current += 1;
    const key = `${env.event_id ?? env.event_type}#${seqRef.current}`;
    setEntries((prev) => {
      const next = [{ key, envelope: env, receivedAt: Date.now() }, ...prev];
      return next.length > MAX_HISTORY ? next.slice(0, MAX_HISTORY) : next;
    });
    setUnread((n) => n + 1);
  }, []);

  // Subscribe once to every default event type; keeps the tray in sync
  // with the same catalog the provider defaults to. Additional types
  // added later via a wider Provider config will need this list bumped.
  useEffect(() => {
    const unsubs = WS_DEFAULT_EVENT_TYPES.map((type) => subscribe(type, push));
    return () => {
      for (const u of unsubs) u();
    };
  }, [subscribe, push]);

  // Opening the tray marks everything read.
  useEffect(() => {
    if (open) setUnread(0);
  }, [open]);

  const clear = useCallback(() => {
    setEntries([]);
    setUnread(0);
  }, []);

  const badgeLabel = useMemo(() => (unread > 99 ? "99+" : String(unread)), [unread]);

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <button
          data-testid="notification-tray-trigger"
          aria-label={`Notifications (${unread} unread)`}
          data-connected={connected ? "true" : "false"}
          style={{
            position: "relative",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "32px",
            height: "32px",
            background: "transparent",
            border: "1px solid var(--rgpa-border, #333)",
            borderRadius: "4px",
            color: "var(--rgpa-fg-1, #e6e6e6)",
            cursor: "pointer",
          }}
        >
          {/* Bell glyph — minimal SVG, no external icon deps. */}
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
            <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
          </svg>
          {unread > 0 && (
            <span
              data-testid="notification-tray-badge"
              aria-hidden="true"
              style={{
                position: "absolute",
                top: "-4px",
                right: "-4px",
                minWidth: "16px",
                height: "16px",
                padding: "0 4px",
                background: "var(--rgpa-danger, oklch(60% 0.2 25))",
                color: "#fff",
                fontSize: "10px",
                lineHeight: "16px",
                borderRadius: "8px",
                textAlign: "center",
                fontFamily: "var(--rgpa-mono, monospace)",
              }}
            >
              {badgeLabel}
            </span>
          )}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay data-testid="notification-tray-overlay" />
        <Dialog.Content
          data-testid="notification-tray"
          aria-label="Notification tray"
          style={{
            position: "fixed",
            right: 0,
            top: 0,
            bottom: 0,
            width: "min(400px, 100vw)",
            background: "var(--rgpa-surface-1, #1a1a1a)",
            borderLeft: "1px solid var(--rgpa-border, #333)",
            padding: "16px",
            zIndex: 50,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "12px",
          }}
        >
          <header
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Dialog.Title
              data-testid="notification-tray-title"
              style={{ margin: 0, fontSize: "14px", color: "var(--rgpa-fg-1, #e6e6e6)" }}
            >
              Notifications
            </Dialog.Title>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <span
                data-testid="notification-tray-connection"
                title="WebSocket connection state"
                style={{
                  fontSize: "11px",
                  color: connected
                    ? "var(--rgpa-accent-gold, oklch(80% 0.15 85))"
                    : "var(--rgpa-fg-2, #999)",
                  fontFamily: "var(--rgpa-mono, monospace)",
                }}
              >
                {connected ? "live" : "offline"}
              </span>
              <button
                data-testid="notification-tray-clear"
                onClick={clear}
                disabled={entries.length === 0}
                style={{
                  fontSize: "11px",
                  padding: "2px 8px",
                  background: "transparent",
                  border: "1px solid var(--rgpa-border, #333)",
                  color: "var(--rgpa-fg-2, #999)",
                  borderRadius: "3px",
                  cursor: entries.length === 0 ? "not-allowed" : "pointer",
                }}
              >
                Clear
              </button>
              <Dialog.Close asChild>
                <button
                  data-testid="notification-tray-close"
                  aria-label="Close"
                  style={{
                    fontSize: "14px",
                    padding: "2px 8px",
                    background: "transparent",
                    border: "1px solid var(--rgpa-border, #333)",
                    color: "var(--rgpa-fg-1, #e6e6e6)",
                    borderRadius: "3px",
                    cursor: "pointer",
                  }}
                >
                  ×
                </button>
              </Dialog.Close>
            </div>
          </header>

          <Dialog.Description
            data-testid="notification-tray-description"
            style={{ margin: 0, fontSize: "11px", color: "var(--rgpa-fg-2, #999)" }}
          >
            Live event stream from the kernel WebSocket. History retained
            for this session only (up to {MAX_HISTORY} entries).
          </Dialog.Description>

          {entries.length === 0 ? (
            <p
              data-testid="notification-tray-empty"
              role="status"
              style={{ fontSize: "12px", color: "var(--rgpa-fg-2, #999)" }}
            >
              No events received yet.
            </p>
          ) : (
            <ul
              data-testid="notification-tray-list"
              style={{
                listStyle: "none",
                margin: 0,
                padding: 0,
                display: "flex",
                flexDirection: "column",
                gap: "6px",
              }}
            >
              {entries.map((e, i) => {
                const tone = toneOf(e.envelope);
                const ts = e.envelope.ts ?? new Date(e.receivedAt).toISOString();
                return (
                  <li
                    key={e.key}
                    data-testid={`notification-tray-item-${i}`}
                    data-tone={tone}
                    style={{
                      padding: "6px 8px",
                      background: "var(--rgpa-surface-2, #161616)",
                      border: "1px solid var(--rgpa-border, #333)",
                      borderLeft: `3px solid ${toneColorVar(tone)}`,
                      borderRadius: "3px",
                      fontSize: "12px",
                      color: "var(--rgpa-fg-1, #e6e6e6)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "8px",
                      }}
                    >
                      <code
                        data-testid={`notification-tray-item-type-${i}`}
                        style={{
                          fontFamily: "var(--rgpa-mono, monospace)",
                          fontSize: "11px",
                          color: toneColorVar(tone),
                        }}
                      >
                        {e.envelope.event_type}
                      </code>
                      <time
                        dateTime={ts}
                        style={{
                          fontFamily: "var(--rgpa-mono, monospace)",
                          fontSize: "10px",
                          color: "var(--rgpa-fg-2, #999)",
                        }}
                      >
                        {ts.slice(11, 19)}
                      </time>
                    </div>
                    {/* Payload preview — one-line JSON summary, full
                        detail accessible via title tooltip. */}
                    <div
                      title={JSON.stringify(e.envelope.payload)}
                      style={{
                        fontFamily: "var(--rgpa-mono, monospace)",
                        fontSize: "10px",
                        color: "var(--rgpa-fg-2, #999)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {JSON.stringify(e.envelope.payload)}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
