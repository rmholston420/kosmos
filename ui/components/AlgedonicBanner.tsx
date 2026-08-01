"use client";
import { useEffect, useState } from "react";
import { connectAlgedonicSocket, kernelClient, type AlgedonicReceipt } from "../lib/kernel-client";

export default function AlgedonicBanner() {
  const [receipt, setReceipt] = useState<AlgedonicReceipt | null>(null);

  useEffect(() => {
    const ws = connectAlgedonicSocket((evt) => setReceipt(evt.payload));
    return () => ws?.close();
  }, []);

  if (!receipt) {
    return <div data-testid="algedonic-banner" data-active="false" style={{ display: "none" }} />;
  }

  const ack = () => {
    kernelClient.ackReceipt(receipt.id, "kosmos_ui").then(() => setReceipt(null));
  };

  return (
    <div data-testid="algedonic-banner" data-active="true" role="alert">
      <strong data-testid="algedonic-title">{receipt.title}</strong>
      <p data-testid="algedonic-body">{receipt.body}</p>
      <button data-testid="algedonic-ack" onClick={ack}>
        Acknowledge
      </button>
    </div>
  );
}
