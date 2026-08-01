"use client";
// Wave F · F1 · EventsWSProvider
// ---------------------------------------------------------------------------
// Subscribes once (per session) to /api/events/ws with the same default
// event-type set the kernel advertises in `WS_DEFAULT_EVENT_TYPES` and
// exposes a small React context so any panel can:
//
//   const { lastEvent, useEventListener } = useEventsWS();
//   useEventListener("phrouros.anomaly.detected", () => refetch());
//
// A single WebSocket is shared across all consumers. Reconnect uses
// exponential backoff (500ms → 8s cap). Server-sent `{frame: "ready"}`
// handshake frames are ignored downstream.
//
// This provider does *not* fabricate frames — if the WS is closed or the
// kernel is degraded, listeners simply never fire. Existing polling in
// panels remains as the correctness floor; WS is a freshness accelerator.
// ---------------------------------------------------------------------------
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

export const WS_DEFAULT_EVENT_TYPES = [
  "phrouros.anomaly.detected",
  "zetesis.research.started",
  "zetesis.research.completed",
  "kernel.suspended",
  "kernel.resumed",
] as const;

export type WSEventType = (typeof WS_DEFAULT_EVENT_TYPES)[number];

export interface WSEnvelope {
  event_type: string;
  payload: Record<string, unknown>;
  ts?: string;
  event_id?: string;
}

type Listener = (env: WSEnvelope) => void;

interface EventsWSContextValue {
  lastEvent: WSEnvelope | null;
  connected: boolean;
  subscribe: (eventType: string, listener: Listener) => () => void;
}

const EventsWSContext = createContext<EventsWSContextValue | null>(null);

function buildWsUrl(types: readonly string[]): string | null {
  if (typeof window === "undefined") return null;
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const qs = new URLSearchParams({ types: types.join(",") });
  return `${proto}://${window.location.host}/api/events/ws?${qs}`;
}

export function EventsWSProvider({
  children,
  types = WS_DEFAULT_EVENT_TYPES,
}: {
  children: ReactNode;
  types?: readonly string[];
}) {
  const [lastEvent, setLastEvent] = useState<WSEnvelope | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const listenersRef = useRef<Map<string, Set<Listener>>>(new Map());
  const backoffRef = useRef<number>(500);
  const closedRef = useRef<boolean>(false);

  const dispatch = useCallback((env: WSEnvelope) => {
    setLastEvent(env);
    const set = listenersRef.current.get(env.event_type);
    if (!set) return;
    for (const listener of set) {
      try {
        listener(env);
      } catch {
        /* swallow listener errors so one bad handler can't break others */
      }
    }
  }, []);

  const connect = useCallback(() => {
    const url = buildWsUrl(types);
    if (!url) return;
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch {
      // Malformed URL / offline — schedule retry.
      setTimeout(() => {
        if (!closedRef.current) connect();
      }, backoffRef.current);
      backoffRef.current = Math.min(backoffRef.current * 2, 8000);
      return;
    }
    wsRef.current = ws;

    ws.onopen = () => {
      backoffRef.current = 500;
      setConnected(true);
    };
    ws.onmessage = (msg) => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(msg.data);
      } catch {
        return;
      }
      if (!parsed || typeof parsed !== "object") return;
      const obj = parsed as Record<string, unknown>;
      // Handshake frame: {frame: "ready", subscribed: [...]} — ignore.
      if (typeof obj.frame === "string") return;
      if (typeof obj.event_type === "string" && typeof obj.payload === "object") {
        dispatch(obj as unknown as WSEnvelope);
      }
    };
    ws.onerror = () => {
      /* onclose will fire and drive reconnect */
    };
    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      if (closedRef.current) return;
      const delay = backoffRef.current;
      backoffRef.current = Math.min(backoffRef.current * 2, 8000);
      setTimeout(() => {
        if (!closedRef.current) connect();
      }, delay);
    };
  }, [dispatch, types]);

  useEffect(() => {
    closedRef.current = false;
    connect();
    return () => {
      closedRef.current = true;
      const ws = wsRef.current;
      wsRef.current = null;
      if (ws && ws.readyState <= 1) {
        try {
          ws.close();
        } catch {
          /* ignore */
        }
      }
    };
  }, [connect]);

  const subscribe = useCallback((eventType: string, listener: Listener) => {
    let set = listenersRef.current.get(eventType);
    if (!set) {
      set = new Set();
      listenersRef.current.set(eventType, set);
    }
    set.add(listener);
    return () => {
      const s = listenersRef.current.get(eventType);
      if (!s) return;
      s.delete(listener);
      if (s.size === 0) listenersRef.current.delete(eventType);
    };
  }, []);

  const value = useMemo<EventsWSContextValue>(
    () => ({ lastEvent, connected, subscribe }),
    [lastEvent, connected, subscribe],
  );

  return <EventsWSContext.Provider value={value}>{children}</EventsWSContext.Provider>;
}

export function useEventsWS(): EventsWSContextValue {
  const ctx = useContext(EventsWSContext);
  if (ctx === null) {
    // Provider not mounted — return a safe no-op so pages/panels never
    // crash. This matters for unit tests that mount panels in isolation.
    return {
      lastEvent: null,
      connected: false,
      subscribe: () => () => undefined,
    };
  }
  return ctx;
}

/**
 * Subscribe a listener to a specific event type. Automatically unsubscribes
 * on unmount. Safe to call outside a Provider (becomes a no-op).
 */
export function useEventListener(eventType: string, listener: Listener): void {
  const { subscribe } = useEventsWS();
  useEffect(() => subscribe(eventType, listener), [subscribe, eventType, listener]);
}
