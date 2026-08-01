"use client";

// Stage 3.13 (ADR-077) — Tektos intention submission form.
//
// Renders a single-line textarea + Submit button on /tektos. On submit,
// POSTs to /api/tektos/intention and shows the returned PlanCard summary.
// On failure, surfaces the FastAPI `detail` from the response body so
// the user sees the validation reason (e.g. "intention too short: 5
// chars, min 8") rather than a generic HTTP status.
//
// This is a client-only surface. State is intentionally local; the
// approval workflow after render happens on the existing detail page
// via kernelClient.resolveApproval(...).

import { useState } from "react";
import Link from "next/link";
import type { TektosIntentionResult } from "../lib/kernel-client";

const INTENTION_ENDPOINT = "/api/tektos/intention";
const MIN_LEN = 8;
const MAX_LEN = 512;

type SubmitState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "ok"; result: TektosIntentionResult }
  | { kind: "error"; message: string };

async function submitIntention(intention: string): Promise<TektosIntentionResult> {
  const base = (typeof window !== "undefined" && (window as { __KERNEL_BASE__?: string }).__KERNEL_BASE__) || "";
  const res = await fetch(`${base}${INTENTION_ENDPOINT}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ intention }),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // ignore JSON parse errors — fall through to status-only message
    }
    throw new Error(detail || `POST ${INTENTION_ENDPOINT} -> ${res.status}`);
  }
  return (await res.json()) as TektosIntentionResult;
}

export default function IntentionForm() {
  const [intention, setIntention] = useState("");
  const [state, setState] = useState<SubmitState>({ kind: "idle" });

  const trimmed = intention.trim();
  const tooShort = trimmed.length > 0 && trimmed.length < MIN_LEN;
  const tooLong = trimmed.length > MAX_LEN;
  const canSubmit =
    state.kind !== "submitting" && trimmed.length >= MIN_LEN && trimmed.length <= MAX_LEN;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setState({ kind: "submitting" });
    try {
      const result = await submitIntention(trimmed);
      setState({ kind: "ok", result });
      setIntention("");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setState({ kind: "error", message });
    }
  }

  return (
    <section data-testid="tektos-intention-form" style={{ marginTop: "1.5rem" }}>
      <h2 style={{ marginBottom: "0.5rem" }}>Submit an intention</h2>
      <p style={{ fontSize: "0.9rem", opacity: 0.8, marginBottom: "0.75rem" }}>
        Type a one-line intention. Tektos scaffolds an OpenSpec change directory,
        produces a plan, and gates it for your approval. Nothing runs against the
        Kosmos working tree at this stage — code execution lands with Stage 3.14.
      </p>
      <form onSubmit={onSubmit}>
        <textarea
          data-testid="tektos-intention-input"
          value={intention}
          onChange={(e) => setIntention(e.target.value)}
          placeholder="Add a dark mode toggle to the settings panel"
          rows={3}
          maxLength={MAX_LEN}
          style={{
            width: "100%",
            padding: "0.5rem",
            fontFamily: "inherit",
            fontSize: "1rem",
            boxSizing: "border-box",
          }}
          disabled={state.kind === "submitting"}
        />
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", marginTop: "0.5rem" }}>
          <button
            type="submit"
            data-testid="tektos-intention-submit"
            disabled={!canSubmit}
          >
            {state.kind === "submitting" ? "Submitting…" : "Submit intention"}
          </button>
          <span data-testid="tektos-intention-charcount" style={{ fontSize: "0.85rem", opacity: 0.7 }}>
            {trimmed.length} / {MAX_LEN}
          </span>
          {tooShort && (
            <span data-testid="tektos-intention-tooshort" style={{ color: "var(--warn, #b58900)", fontSize: "0.85rem" }}>
              minimum {MIN_LEN} characters
            </span>
          )}
          {tooLong && (
            <span data-testid="tektos-intention-toolong" style={{ color: "var(--danger, #cb4b16)", fontSize: "0.85rem" }}>
              maximum {MAX_LEN} characters
            </span>
          )}
        </div>
      </form>

      {state.kind === "error" && (
        <p
          data-testid="tektos-intention-error"
          role="alert"
          style={{ color: "var(--danger, #cb4b16)", marginTop: "0.75rem" }}
        >
          {state.message}
        </p>
      )}

      {state.kind === "ok" && (
        <div
          data-testid="tektos-intention-result"
          style={{
            marginTop: "1rem",
            padding: "0.75rem",
            border: "1px solid var(--border, #586e75)",
            borderRadius: "4px",
          }}
        >
          <p style={{ margin: 0 }}>
            <strong>Plan gated for approval.</strong>
          </p>
          <ul style={{ marginTop: "0.5rem", marginBottom: "0.5rem" }}>
            <li>
              <span data-testid="tektos-intention-result-change-id">
                change_id: <code>{state.result.change_id}</code>
              </span>
            </li>
            <li>
              approval_id:{" "}
              <code data-testid="tektos-intention-result-approval-id">
                {state.result.plan_card.approval_id}
              </code>
            </li>
            <li>tier: {state.result.plan_card.tier}</li>
            <li>
              tasks: {state.result.plan_card.done_task_count} /{" "}
              {state.result.plan_card.task_count}
            </li>
            <li>confidence: {state.result.plan_card.confidence.toFixed(3)}</li>
          </ul>
          <Link
            data-testid="tektos-intention-result-link"
            href={`/tektos/detail?id=${encodeURIComponent(state.result.plan_card.approval_id)}`}
          >
            Review plan →
          </Link>
        </div>
      )}
    </section>
  );
}
