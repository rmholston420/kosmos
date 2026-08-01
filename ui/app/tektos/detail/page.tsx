"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  kernelClient,
  KernelHttpError,
  type ApprovalRecord,
  type TektosDiffResult,
  type TektosExecutionResult,
  type TektosPlanDetail,
} from "../../../lib/kernel-client";

// Stage 3.13.1 (ADR-077). Read-only detail page for a scaffolded Tektos plan.
// Renders the APEX ApprovalRecord + the scaffolded proposal.md + tasks.md.
// Approve/Reject route through the existing /api/approvals/{id}/{approve,reject}
// surface (kernelClient.resolveApproval).
//
// Stage 3.14b step 3 (ADR-080). Execute + Show Diff wired to the kernel-
// composed TektosExecutorLoop. Execute unlocks post-approval; Show Diff
// unlocks after a successful execute (the kernel snapshots the diff before
// tearing the worktree down and caches it by approval_id).

function DetailInner() {
  const searchParams = useSearchParams();
  const approvalId = searchParams?.get("id") ?? "";

  const [detail, setDetail] = useState<TektosPlanDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [execResult, setExecResult] = useState<TektosExecutionResult | null>(null);
  const [diffResult, setDiffResult] = useState<TektosDiffResult | null>(null);

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

  async function onExecute() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      const r = await kernelClient.executeTektosPlan(detail.approval.approval_id);
      setExecResult(r);
      setDiffResult(null); // stale on repeat execute
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onShowDiff() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      const r = await kernelClient.getTektosDiff(detail.approval.approval_id);
      setDiffResult(r);
    } catch (e) {
      if (e instanceof KernelHttpError && e.status === 404) {
        setError("no diff cached \u2014 execute the plan first");
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
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
  const approved = rec.status === "APPROVED" || rec.status === "MODIFIED";
  const canExecute = approved && !busy;
  // Show Diff is enabled once we have a cached diff (either from a prior
  // execute in this session or if the server returns a 200 on GET). We
  // gate the initial click on "executed at least once this session" to
  // avoid a guaranteed 404 round-trip.
  const canShowDiff = approved && (execResult !== null || diffResult !== null) && !busy;

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
          Execute runs the plan inside a bwrap-boundaried <code>git worktree</code> under
          ColossusResourceGuard; Show Diff reads the cached snapshot taken before the
          worktree was torn down (ADR-080).
        </p>
        <button
          data-testid="tektos-plan-execute"
          onClick={onExecute}
          disabled={!canExecute}
          title={approved ? "Run the executor loop" : "Approve the plan first"}
        >
          Execute
        </button>
        <button
          data-testid="tektos-plan-show-diff"
          onClick={onShowDiff}
          disabled={!canShowDiff}
          title={
            execResult !== null || diffResult !== null
              ? "Show the cached worktree diff"
              : "Execute the plan first"
          }
          style={{ marginLeft: "0.5rem" }}
        >
          Show Diff
        </button>
      </section>

      {execResult && (
        <section
          data-testid="tektos-exec-result"
          style={{
            padding: "0.75rem",
            border: "1px solid var(--border, #586e75)",
            borderRadius: "4px",
            margin: "1rem 0",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Execution result</h2>
          <ul style={{ margin: 0 }}>
            <li>
              execution_id: <code data-testid="tektos-exec-id">{execResult.execution_id}</code>
            </li>
            <li>
              final_status:{" "}
              <span data-testid="tektos-exec-final-status">{execResult.final_status}</span>
            </li>
            <li>
              tasks:{" "}
              <span data-testid="tektos-exec-tasks-succeeded">{execResult.tasks_succeeded}</span>{" "}
              /{" "}
              <span data-testid="tektos-exec-tasks-attempted">{execResult.tasks_attempted}</span>{" "}
              succeeded (<span data-testid="tektos-exec-tasks-failed">{execResult.tasks_failed}</span>{" "}
              failed)
            </li>
            <li>
              change_id: <code>{execResult.change_id}</code>
            </li>
            <li>
              commits (<span data-testid="tektos-exec-commit-count">{execResult.commit_shas.length}</span>):
              <ul data-testid="tektos-exec-commit-list" style={{ margin: 0 }}>
                {execResult.commit_shas.map((sha) => (
                  <li key={sha}>
                    <code style={{ fontSize: "0.85rem" }}>{sha}</code>
                  </li>
                ))}
              </ul>
            </li>
          </ul>
        </section>
      )}

      {diffResult && (
        <section
          data-testid="tektos-diff-render"
          style={{
            padding: "0.75rem",
            border: "1px solid var(--border, #586e75)",
            borderRadius: "4px",
            margin: "1rem 0",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Worktree diff</h2>
          <p style={{ fontSize: "0.85rem", opacity: 0.7 }}>
            base_ref: <code data-testid="tektos-diff-base-ref">{diffResult.base_ref}</code>{" "}
            · task_count:{" "}
            <span data-testid="tektos-diff-task-count">{diffResult.task_count}</span>
          </p>
          <pre
            data-testid="tektos-diff-body"
            style={{
              whiteSpace: "pre-wrap",
              padding: "0.75rem",
              border: "1px solid var(--border, #586e75)",
              borderRadius: "4px",
              maxHeight: "24rem",
              overflow: "auto",
              fontSize: "0.85rem",
            }}
          >
            {diffResult.diff || "(empty diff)"}
          </pre>
        </section>
      )}

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
