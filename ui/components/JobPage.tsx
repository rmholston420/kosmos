"use client";
import { useEffect, useState } from "react";
import { kernelClient, type KernelSchema, type PanelSlot } from "../lib/kernel-client";
import PanelGrid from "./PanelGrid";

// A JobPage renders only the panels relevant to a single job segment
// (Command / Operate / Govern / Observe / Memory) per the UX Design
// Spec §"Information Architecture: Job-Segmented, Not Data-Segmented".
// The `slots` prop names which PanelSlots this job cares about; the
// grid is filtered accordingly. Slots the job does not care about are
// omitted entirely (no placeholder cards) — the shell page at `/` is
// the only surface that renders all nine.

export default function JobPage({
  jobId,
  title,
  description,
  slots,
}: {
  jobId: string;
  title: string;
  description: string;
  slots: PanelSlot[];
}) {
  const [schema, setSchema] = useState<KernelSchema | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    kernelClient.renderKernelSchema().then(setSchema).catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return <main data-testid={`job-${jobId}-error`}>Kernel unreachable: {error}</main>;
  }
  if (!schema) {
    return <main data-testid={`job-${jobId}-loading`}>Loading…</main>;
  }

  return (
    <main data-testid={`job-${jobId}`} data-slots={slots.join(",")}>
      <header data-testid={`job-${jobId}-header`}>
        <h1 data-testid={`job-${jobId}-title`}>{title}</h1>
        <p data-testid={`job-${jobId}-description`}>{description}</p>
      </header>
      <PanelGrid panels={schema.panels} slots={slots} />
    </main>
  );
}
