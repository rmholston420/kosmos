"use client";
import { useEffect, useState } from "react";
import { kernelClient, type KernelSchema } from "../lib/kernel-client";
import PanelGrid from "../components/PanelGrid";

// Home ("/") — the single surface that renders all nine PanelSlots.
// Job pages under /command, /operate, /govern, /observe, /memory each
// render only the slots relevant to their job (UX Design Spec
// §"Information Architecture: Job-Segmented, Not Data-Segmented").
export default function KosmosDashboard() {
  const [schema, setSchema] = useState<KernelSchema | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    kernelClient
      .renderKernelSchema()
      .then(setSchema)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return <main data-testid="kernel-error">Kernel unreachable: {error}</main>;
  }
  if (!schema) {
    return <main data-testid="kernel-loading">Loading Kosmos…</main>;
  }

  return (
    <div data-testid="kosmos-root">
      <h1 data-testid="kernel-title">{schema.title}</h1>
      <PanelGrid panels={schema.panels} />
    </div>
  );
}
