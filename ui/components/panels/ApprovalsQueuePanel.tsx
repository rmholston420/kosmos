"use client";
import { useEffect, useState } from "react";
import { kernelClient, type ApprovalRecord, type Panel } from "../../lib/kernel-client";

export default function ApprovalsQueuePanel({ panels }: { panels: Panel[] }) {
  const [records, setRecords] = useState<ApprovalRecord[]>([]);
  const [domainFilter, setDomainFilter] = useState<string>("");
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});

  const owners = Array.from(new Set(panels.map((p) => p.plugin_name)));

  const refresh = () => {
    kernelClient
      .listPendingApprovals(domainFilter || undefined)
      .then((r: unknown) => setRecords(Array.isArray(r) ? (r as ApprovalRecord[]) : []))
      .catch(() => setRecords([]));
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [domainFilter]);

  const approve = (id: string) => {
    kernelClient.resolveApproval(id, true, { resolved_by: "kosmos_ui" }).then(refresh);
  };

  const reject = (id: string) => {
    const reason = rejectReason[id]?.trim();
    if (!reason) return;
    kernelClient.resolveApproval(id, false, { reason, resolved_by: "kosmos_ui" }).then(refresh);
  };

  return (
    <article data-testid="panel-APPROVALS_QUEUE" data-populated="true">
      <h2>Approvals Queue</h2>
      <div>
        {owners.map((o) => (
          <button
            key={o}
            data-testid={`approvals-filter-${o}`}
            onClick={() => setDomainFilter(o)}
          >
            {o}
          </button>
        ))}
        <button data-testid="approvals-filter-all" onClick={() => setDomainFilter("")}>
          All
        </button>
      </div>

      {records.length === 0 ? (
        <p data-testid="approvals-empty">No pending approvals</p>
      ) : (
        <ul data-testid="approvals-list">
          {records.map((r) => (
            <li data-testid={`approval-${r.approval_id}`} key={r.approval_id}>
              <span data-testid={`approval-tier-${r.approval_id}`}>{r.tier}</span>
              <span data-testid={`approval-domain-${r.approval_id}`}>{r.proposing_domain}</span>
              <span data-testid={`approval-status-${r.approval_id}`}>{r.status}</span>

              <button
                data-testid={`approval-approve-${r.approval_id}`}
                onClick={() => approve(r.approval_id)}
              >
                Approve
              </button>

              <input
                data-testid={`approval-reason-${r.approval_id}`}
                placeholder="Rejection reason"
                value={rejectReason[r.approval_id] ?? ""}
                onChange={(e) =>
                  setRejectReason((prev) => ({ ...prev, [r.approval_id]: e.target.value }))
                }
              />
              <button
                data-testid={`approval-reject-${r.approval_id}`}
                onClick={() => reject(r.approval_id)}
              >
                Reject
              </button>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
