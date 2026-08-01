"use client";
// Wave F · F2 · MODEL_SWAP_SLO
// -------------------------------------------------------------------------
// Live view of the local Ollama runtime: hot model, VRAM usage, capacity
// headroom. Complements the top-bar ModelSwapIndicator with a full-size
// surface for the Operate/Observe pages. Refreshes every 5s from
// /api/ollama/status (ADR-068 D1).
// -------------------------------------------------------------------------
import { useEffect, useState } from "react";
import { kernelClient, type OllamaStatus } from "../../lib/kernel-client";

const POLL_MS = 5000;
const GIB = 1024 ** 3;

function pct(size: number, cap: number): number {
  if (cap <= 0) return 0;
  return Math.min(100, Math.round((size / cap) * 100));
}

export default function ModelSwapSLOPanel() {
  const [status, setStatus] = useState<OllamaStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = () => {
      kernelClient
        .getOllamaStatus()
        .then((s) => {
          if (!cancelled) {
            setStatus(s);
            setError(null);
          }
        })
        .catch((e: unknown) => {
          if (!cancelled) setError(String(e));
        });
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const cap = status?.vram_capacity_bytes ?? 32 * GIB;
  const capGib = (cap / GIB).toFixed(0);
  const usedVram = status?.size_vram ?? 0;
  const usedRam = status?.size_ram ?? 0;
  const usedGib = (usedVram / GIB).toFixed(1);
  const ramGib = (usedRam / GIB).toFixed(1);
  const usagePct = pct(usedVram, cap);

  return (
    <article data-testid="panel-MODEL_SWAP_SLO" data-populated="true">
      <h2>Model Runtime</h2>
      {error && (
        <p data-testid="model-swap-slo-error" role="alert">
          {error}
        </p>
      )}
      <dl data-testid="model-swap-slo-dl">
        <dt>Hot model</dt>
        <dd data-testid="model-swap-slo-model">{status?.model ?? "—"}</dd>
        <dt>VRAM used</dt>
        <dd data-testid="model-swap-slo-vram">
          {usedGib} / {capGib} GB ({usagePct}%)
        </dd>
        <dt>RAM used</dt>
        <dd data-testid="model-swap-slo-ram">{ramGib} GB</dd>
      </dl>
      <div
        data-testid="model-swap-slo-bar"
        role="progressbar"
        aria-valuenow={usagePct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="VRAM usage"
      >
        <div
          data-testid="model-swap-slo-bar-fill"
          style={{ width: `${usagePct}%` }}
        />
      </div>
    </article>
  );
}
