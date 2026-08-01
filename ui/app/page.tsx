"use client";
import { useEffect, useState } from "react";
import { kernelClient, type KernelSchema } from "../lib/kernel-client";
import PanelGrid from "../components/PanelGrid";
import Sidebar from "../components/Sidebar";
import AlgedonicBanner from "../components/AlgedonicBanner";

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
      <AlgedonicBanner />
      <h1 data-testid="kernel-title">{schema.title}</h1>
      <div style={{ display: "flex" }}>
        <Sidebar routes={schema.plugins.flatMap((p) => p.routes)} />
        <PanelGrid panels={schema.panels} />
      </div>
    </div>
  );
}
