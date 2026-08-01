"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  kernelClient,
  type ApprovalRecord,
  type TektosPlanDetail,
} from "../../../lib/kernel-client";

// Stage 3.13.1 (ADR-077). Read-only detail page for a scaffolded Tektos plan.
// Renders the APEX ApprovalRecord + the scaffolded proposal.md + tasks.md.
// Approve/Reject route through the existing /api/approvals/{id}/{approve,reject}
// surface (kernelClient.resolveApproval). Execute + Diff are disabled — the
// sandboxed executor lands in Stage 3.14.

function DetailInner() {
  const searchParams = useSearchParams();
  const approvalId = searchParams?.get("id") ?? "";

  const [detail, setDetail] = useState<TektosPlanDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  useEffect(() => {
    if (!approvalId) {
      setError("missing ?id= parameter");
      return;
    }
    kernelClient
      .getPlanDetail(approvalId)
      .then((r) => {
        setDetail(r);
        setError(null);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, [approvalId]);

  async function onApprove() {
    if (!detail) return;
    setBusy(true);
    try {
      const updated: ApprovalRecord = await kernelClient.resolveApproval(
        detail.approval.approval_id,
        true,
      );
      setDetail({ ...detail, approval: updated });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onReject() {
    if (!detail) return;
    const reason = rejectReason.trim();
    if (!reason) {
      setError("reject requires a non-empty reason");
      return;
    }
    setBusy(true);
    try {
      const updated: ApprovalRecord = await kernelClient.resolveApproval(
        detail.approval.approval_id,
        false,
        { reason },
      );
      setDetail({ ...detail, approval: updated });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return (
      <main data-testid="tektos-plan-error" style={{ padding: "1rem" }}>
        <p>Error: {error}</p>
        <Link href="/tektos">← back to Tektos</Link>
      </main>
    );
  }
  if (!detail) {
    return (
      <main data-testid="tektos-plan-loading" style={{ padding: "1rem" }}>
        Loading plan…
      </main>
    );
  }

  const rec = detail.approval;
  const pending = rec.status === "PENDING";

  return (
    <main data-testid="tektos-plan-detail" style={{ padding: "1rem" }}>
      <p>
        <Link href="/tektos">← back to Tektos</Link>
      </p>

      <h1 data-testid="tektos-plan-id" style={{ wordBreak: "break-all" }}>
        {rec.approval_id}
      </h1>

      <section
        data-testid="tektos-plan-meta"
        style={{
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          rowGap: "0.25rem",
          columnGap: "1rem",
          margin: "0.75rem 0",
        }}
      >
        <span>intention_id</span>
        <code>{rec.intention_id}</code>
        <span>status</span>
        <span data-testid="tektos-plan-status">{rec.status}</span>
        <span>tier</span>
        <span data-testid="tektos-plan-tier">{rec.tier}</span>
        <span>proposed_at</span>
        <code>{rec.proposed_at}</code>
        {rec.resolved_at && (
          <>
            <span>resolved_at</span>
            <code>{rec.resolved_at}</code>
            <span>resolved_by</span>
            <code>{rec.resolved_by ?? "—"}</code>
          </>
        )}
        {rec.reason && (
          <>
            <span>reason</span>
            <span data-testid="tektos-plan-reason">{rec.reason}</span>
          </>
        )}
        {detail.change_id && (
          <>
            <span>change_id</span>
            <code data-testid="tektos-plan-change-id">{detail.change_id}</code>
          </>
        )}
        {detail.change_dir && (
          <>
            <span>change_dir</span>
            <code data-testid="tektos-plan-change-dir" style={{ fontSize: "0.85rem" }}>
              {detail.change_dir}
            </code>
          </>
        )}
      </section>

      <section
        data-testid="tektos-plan-card"
        style={{
          padding: "0.75rem",
          border: "1px solid var(--border, #586e75)",
          borderRadius: "4px",
          margin: "1rem 0",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Plan card</h2>
        <p data-testid="tektos-plan-summary">{String(rec.delta?.rendered_summary ?? "")}</p>
        <ul style={{ margin: 0 }}>
          <li>tasks: {String(rec.delta?.done_task_count ?? 0)} / {String(rec.delta?.task_count ?? 0)}</li>
          <li>
            delta: +{String(rec.delta?.delta_added ?? 0)} / ~{String(rec.delta?.delta_modified ?? 0)} / -{String(rec.delta?.delta_removed ?? 0)}
          </li>
          <li>confidence: {Number(rec.delta?.confidence ?? 0).toFixed(3)}</li>
        </ul>
      </section>

      <section data-testid="tektos-plan-actions" style={{ margin: "1rem 0" }}>
        <button
          data-testid="tektos-plan-approve"
          onClick={onApprove}
          disabled={!pending || busy}
          style={{ marginRight: "0.5rem" }}
        >
          Approve
        </button>
        <button
          data-testid="tektos-plan-reject"
          onClick={onReject}
          disabled={!pending || busy || !rejectReason.trim()}
        >
          Reject
        </button>
        <input
          data-testid="tektos-plan-reject-reason"
          type="text"
          placeholder="reject reason (required)"
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          disabled={!pending || busy}
          style={{ marginLeft: "0.5rem", padding: "0.25rem", width: "20rem" }}
        />
        <p style={{ fontSize: "0.85rem", opacity: 0.7, marginTop: "0.5rem" }}>
          Execute + Diff land with Stage 3.14 (sandboxed <code>git worktree</code> executor + <code>git apply</code>).
        </p>
        <button data-testid="tektos-plan-execute" disabled title="Stage 3.14">
          Execute (Stage 3.14)
        </button>
        <button
          data-testid="tektos-plan-show-diff"
          disabled
          title="Stage 3.14"
          style={{ marginLeft: "0.5rem" }}
        >
          Show Diff (Stage 3.14)
        </button>
      </section>

      <section data-testid="tektos-plan-proposal" style={{ marginTop: "1.5rem" }}>
        <h2>proposal.md</h2>
        {detail.files.proposal_md === null ? (
          <p data-testid="tektos-plan-proposal-missing" style={{ opacity: 0.7 }}>
            (not available)
          </p>
        ) : (
          <pre
            data-testid="tektos-plan-proposal-body"
            style={{
              whiteSpace: "pre-wrap",
              padding: "0.75rem",
              border: "1px solid var(--border, #586e75)",
              borderRadius: "4px",
              maxHeight: "24rem",
              overflow: "auto",
            }}
          >
            {detail.files.proposal_md}
          </pre>
        )}
      </section>

      <section data-testid="tektos-plan-tasks" style={{ marginTop: "1.5rem" }}>
        <h2>tasks.md</h2>
        {detail.files.tasks_md === null ? (
          <p data-testid="tektos-plan-tasks-missing" style={{ opacity: 0.7 }}>
            (not available)
          </p>
        ) : (
          <pre
            data-testid="tektos-plan-tasks-body"
            style={{
              whiteSpace: "pre-wrap",
              padding: "0.75rem",
              border: "1px solid var(--border, #586e75)",
              borderRadius: "4px",
              maxHeight: "24rem",
              overflow: "auto",
            }}
          >
            {detail.files.tasks_md}
          </pre>
        )}
      </section>
    </main>
  );
}

export default function TektosPlanDetailPage() {
  return (
    <Suspense fallback={<main data-testid="tektos-plan-loading">Loading plan…</main>}>
      <DetailInner />
    </Suspense>
  );
}
