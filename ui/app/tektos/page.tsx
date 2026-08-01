"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { kernelClient, type ApprovalRecord } from "../../lib/kernel-client";
import IntentionForm from "../../components/IntentionForm";

export default function TektosIndex() {
  const [records, setRecords] = useState<ApprovalRecord[]>([]);

  useEffect(() => {
    kernelClient
      .listPendingApprovals("tektos")
      .then((r: unknown) => setRecords(Array.isArray(r) ? (r as ApprovalRecord[]) : []))
      .catch(() => setRecords([]));
  }, []);

  return (
    <main data-testid="tektos-index">
      <h1>Tektos Plans</h1>
      <IntentionForm />
      <section style={{ marginTop: "2rem" }}>
        <h2>Pending plans</h2>
        {records.length === 0 ? (
          <p data-testid="tektos-index-empty">No pending Tektos plans</p>
        ) : (
          <ul data-testid="tektos-index-list">
            {records.map((r) => (
              <li key={r.approval_id}>
                <Link data-testid={`tektos-index-link-${r.approval_id}`} href={`/tektos/detail?id=${encodeURIComponent(r.approval_id)}`}>
                  {r.intention_id}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
