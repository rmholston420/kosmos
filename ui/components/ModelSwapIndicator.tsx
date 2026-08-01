"use client";
import { useEffect, useState } from "react";
import { kernelClient, type OllamaStatus } from "../lib/kernel-client";

// Live model-swap indicator per UX Design Spec §"Persistent Shell": hot
// model + VRAM used of 32GB, refreshed every 5s from /api/ollama/status
// (ADR-068 D1). Placeholder "—" renders until first response.

const POLL_MS = 5000;
const GIB = 1024 ** 3;

function formatModel(status: OllamaStatus | null): string {
  if (!status || !status.model) return "—";
  return status.model;
}

function formatVram(status: OllamaStatus | null): string {
  const cap = status?.vram_capacity_bytes ?? 32 * GIB;
  const capGib = (cap / GIB).toFixed(0);
  if (!status || status.size_vram === 0) {
    return `— / ${capGib}GB VRAM`;
  }
  const usedGib = (status.size_vram / GIB).toFixed(1);
  return `${usedGib} / ${capGib}GB VRAM`;
}

export default function ModelSwapIndicator() {
  const [status, setStatus] = useState<OllamaStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = () => {
      kernelClient
        .getOllamaStatus()
        .then((s) => {
          if (!cancelled) setStatus(s);
        })
        .catch(() => {
          /* keep last known value; UI stays on the previous reading */
        });
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <div data-testid="model-swap-indicator">
      <span data-testid="model-swap-model-name">{formatModel(status)}</span>
      <span data-testid="model-swap-vram">{formatVram(status)}</span>
    </div>
  );
}
