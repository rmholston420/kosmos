"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  kernelClient,
  type ApprovalRecord,
  type DiffRender,
  type ExecutionResult,
} from "../../../lib/kernel-client";

export default function TektosPlanDetail() {
  const params = useParams<{ approvalId: string }>();
  const approvalId = params.approvalId;

  const [record, setRecord] = useState<ApprovalRecord | null>(null);
  const [execResult, setExecResult] = useState<ExecutionResult | null>(null);
  const [diff, setDiff] = useState<DiffRender | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    kernelClient
      .getPlanDetail(approvalId)
      .then(setRecord)
      .catch((e) => setError(String(e)));
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [approvalId]);

  const approve = () => kernelClient.approveTektosPlan(approvalId).then((r) => setRecord(r));

  const execute = () =>
    kernelClient.executeTektosPlan(approvalId).then((res) => setExecResult(res));

  const showDiff = () => kernelClient.getTektosDiff(approvalId).then((d) => setDiff(d));

  if (error) return <main data-testid="tektos-plan-error">{error}</main>;
  if (!record) return <main data-testid="tektos-plan-loading">Loading plan…</main>;

  const canExecute = record.status === "APPROVED" || record.status === "MODIFIED";

  return (
    <main data-testid="tektos-plan-detail">
      <h1 data-testid="tektos-plan-id">{record.approval_id}</h1>
      <p data-testid="tektos-plan-status">{record.status}</p>
      <p data-testid="tektos-plan-tier">{record.tier}</p>

      <button data-testid="tektos-plan-approve" onClick={approve} disabled={record.status !== "PENDING"}>
        Approve
      </button>

      <button data-testid="tektos-plan-execute" onClick={execute} disabled={!canExecute}>
        Execute
      </button>

      <button data-testid="tektos-plan-show-diff" onClick={showDiff}>
        Show Diff
      </button>

      {execResult && (
        <div data-testid="tektos-exec-result">
          <span data-testid="tektos-exec-sha">{execResult.diff_sha256}</span>
        </div>
      )}

      {diff && (
        <div data-testid="tektos-diff-render">
          <span data-testid="tektos-diff-sha-badge">{diff.diff_sha256}</span>
          <pre data-testid="tektos-diff-body">{diff.body}</pre>
        </div>
      )}
    </main>
  );
}
