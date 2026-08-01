"use client";
import { useEffect, useState } from "react";
import { connectAlgedonicSocket, type AlgedonicReceipt } from "../lib/kernel-client";

// Top-bar algedonic status pill per UX Design Spec §"Persistent Shell":
// color + text (never color-only) — critical accessibility rule.
// Subscribes to /api/algedonic/ws; latest receipt sets `active` state until
// AlgedonicBanner acks it (banner drives the mutation; pill mirrors state).

export default function AlgedonicPill() {
  const [receipt, setReceipt] = useState<AlgedonicReceipt | null>(null);

  useEffect(() => {
    const ws = connectAlgedonicSocket((evt) => setReceipt(evt.payload));
    return () => ws?.close();
  }, []);

  const status = receipt ? "active" : "clear";
  const text = receipt ? `Algedonic: ${receipt.title}` : "Algedonic: Clear";

  return (
    <div data-testid="algedonic-pill" data-status={status} role="status">
      <span data-testid="algedonic-pill-text">{text}</span>
    </div>
  );
}
