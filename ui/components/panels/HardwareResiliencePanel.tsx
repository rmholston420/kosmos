"use client";
// Wave F · F2 · HARDWARE_RESILIENCE
// -------------------------------------------------------------------------
// A quick-glance surface for Colossus's own health. Reads:
//   - /health  (kernel liveness + subsystem states)
//   - /api/ollama/status  (GPU/VRAM headroom)
//
// This is intentionally coarse — VSM S3* audit, not a metrics dashboard.
// Detailed telemetry lives on the Observe page.
// -------------------------------------------------------------------------
import { useEffect, useState } from "react";
import { kernelClient, type OllamaStatus } from "../../lib/kernel-client";

const POLL_MS = 10000;
const GIB = 1024 ** 3;

interface HealthPayload {
  status?: string;
  subsystems?: Record<string, string | boolean | null>;
  version?: string;
  [k: string]: unknown;
}

async function fetchHealth(): Promise<HealthPayload | null> {
  try {
    const res = await fetch("/health", { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as HealthPayload;
  } catch {
    return null;
  }
}

export default function HardwareResiliencePanel() {
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [ollama, setOllama] = useState<OllamaStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      const [h, o] = await Promise.all([
        fetchHealth(),
        kernelClient.getOllamaStatus().catch(() => null),
      ]);
      if (cancelled) return;
      setHealth(h);
      setOllama(o);
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const subs = health?.subsystems ?? {};
  const subsystemEntries = Object.entries(subs);
  const cap = ollama?.vram_capacity_bytes ?? 32 * GIB;
  const used = ollama?.size_vram ?? 0;
  const freeGib = ((cap - used) / GIB).toFixed(1);
  const capGib = (cap / GIB).toFixed(0);

  const overall = health?.status ?? "unknown";

  return (
    <article
      data-testid="panel-HARDWARE_RESILIENCE"
      data-populated="true"
      data-overall={overall}
    >
      <h2>Hardware Resilience</h2>
      <dl>
        <dt>Kernel</dt>
        <dd data-testid="hardware-resilience-kernel-status">{overall}</dd>
        <dt>Kernel version</dt>
        <dd data-testid="hardware-resilience-version">
          {health?.version ?? "—"}
        </dd>
        <dt>VRAM headroom</dt>
        <dd data-testid="hardware-resilience-vram-free">
          {freeGib} / {capGib} GB free
        </dd>
      </dl>
      {subsystemEntries.length > 0 && (
        <ul data-testid="hardware-resilience-subsystems">
          {subsystemEntries.map(([name, state]) => {
            const stateStr = state === null ? "down" : String(state);
            const ok = state === true || state === "ok" || state === "healthy";
            return (
              <li
                key={name}
                data-testid={`hardware-resilience-sub-${name}`}
                data-ok={ok}
              >
                <span>{name}</span>
                <span data-testid={`hardware-resilience-sub-state-${name}`}>
                  {stateStr}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </article>
  );
}
