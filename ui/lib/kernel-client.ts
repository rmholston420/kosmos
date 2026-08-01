// Typed client for FrontendContractPort + Approval/Notification/Resource/Trace ports.
// All shapes mirror the frozen dataclasses in ports/*.py exactly — do not rename fields.

export type PanelSlot =
  | "ALGEDONIC" | "GOVERNANCE" | "MEMORY_INTEGRITY" | "MODEL_SWAP_SLO"
  | "STUB_DEGRADATION" | "CONTEXT_PRESSURE" | "HARDWARE_RESILIENCE"
  | "APPROVALS_QUEUE" | "AGENT_TRACE";

export interface Route { path: string; label: string; icon: string; lazy_module: string; }
export interface Panel { id: string; slot: PanelSlot; priority: number; lazy_module: string; plugin_name: string; }
export interface PluginDescriptor {
  name: string; state_namespace: string; version: string; kernel_compat: string;
  design_tokens: Record<string, string>; routes: Route[]; panels: Panel[];
}
export interface KernelSchema {
  title: string; plugins: PluginDescriptor[]; panels: Panel[];
  design_tokens: Record<string, string>; generated_at: string;
}

export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED" | "MODIFIED" | "REVIEW_MISSED";
export type ChangeApprovalTier = "AUTONOMOUS" | "HUMAN_REVIEW" | "HUMAN_REQUIRED";

export interface ApprovalRecord {
  approval_id: string; intention_id: string; proposing_domain: string;
  tier: ChangeApprovalTier; delta: Record<string, unknown>; status: ApprovalStatus;
  proposed_at: string; resolved_at: string | null; resolved_by: string | null;
  reason: string | null; modifications: Record<string, unknown>;
  diff_preview: Record<string, unknown>;
}

export type AnomalyKind = "loop" | "model_swap_slo" | "stub_degradation" | "bus_factor_1" | "unauthorized_tool";
export type AnomalyStatus = "detected" | "notified" | "reserved" | "resolved";
export interface AnomalyRecord {
  id: string; kind: AnomalyKind; detected_at: string; trace_id: string;
  plugin: string; tool_name: string; detector: string; status: AnomalyStatus;
  payload: Record<string, unknown>; notification_id: string | null;
  allocation_id: string | null; queued_request_id: string | null;
}

export interface DiffRender { approval_id: string; change_id: string; body: string; diff_sha256: string; }
export interface ExecutionResult { approval_id: string; change_id: string; before: string; after: string; diff_sha256: string; }

export interface DeliverySloReport {
  window: number; sample_count: number; p50_ms: number; p95_ms: number;
  p99_ms: number; max_ms: number; breach_count_over_500ms: number;
}
export interface AlgedonicReceipt {
  id: string; source: string; title: string; body: string;
  attributes: Record<string, unknown>; created_at: string; delivered_at: string;
  latency_ms: number; sink_count: number;
}

export type ResourceKind = "time" | "money" | "attention" | "compute" | "knowledge" | "energy";
export type PriorityClass = 10 | 50 | 100;
export interface ResourceBalance { kind: ResourceKind; current_balance: string; unit: string; }
export interface QueuedRequest {
  id: string; kind: ResourceKind; amount: string; intent: string;
  priority_class: PriorityClass; requester: string; enqueued_at: string; status: string;
}

const BASE = process.env.NEXT_PUBLIC_KERNEL_BASE ?? "";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}
async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export const kernelClient = {
  renderKernelSchema: () => getJSON<KernelSchema>("/api/kernel/schema"),
  getRouteManifest: () => getJSON<Route[]>("/api/kernel/routes"),
  getPanelManifest: (slot?: PanelSlot) =>
    getJSON<Panel[]>(`/api/kernel/panels${slot ? `?slot=${slot}` : ""}`),
  getDesignTokens: () => getJSON<Record<string, string>>("/api/kernel/design-tokens"),

  listPendingApprovals: (proposingDomain?: string) =>
    getJSON<ApprovalRecord[]>(
      `/api/approvals${proposingDomain ? `?proposing_domain=${proposingDomain}` : ""}`
    ),
  getApprovalById: (id: string) => getJSON<ApprovalRecord>(`/api/approvals/${id}`),
  // ADR-062 splits resolve into approve + reject. reject requires non-empty reason.
  resolveApproval: (
    id: string,
    approved: boolean,
    opts?: { reason?: string; modifications?: Record<string, unknown>; resolved_by?: string }
  ) =>
    approved
      ? postJSON<ApprovalRecord>(`/api/approvals/${id}/approve`, {
          reason: opts?.reason ?? null,
          modifications: opts?.modifications ?? {},
          resolved_by: opts?.resolved_by ?? "kosmos_ui",
        })
      : postJSON<ApprovalRecord>(`/api/approvals/${id}/reject`, {
          reason: opts?.reason ?? "",
          resolved_by: opts?.resolved_by ?? "kosmos_ui",
        }),

  // ADR-067 D4: Tektos Plan→Approve→Execute→Diff route surface deferred to Stage 2
  // pending a dedicated Tektos-plan-surface ADR. Kernel currently exposes only
  // POST /api/tektos/turn (ADR-063). The four calls below will 404 until then.
  getPlanDetail: (approvalId: string) => getJSON<ApprovalRecord>(`/api/tektos/plan/${approvalId}`),
  approveTektosPlan: (approvalId: string) =>
    postJSON<ApprovalRecord>(`/api/tektos/plan/${approvalId}/approve`, {}),
  executeTektosPlan: (approvalId: string) =>
    postJSON<ExecutionResult>(`/api/tektos/plan/${approvalId}/execute`, {}),
  getTektosDiff: (approvalId: string) => getJSON<DiffRender>(`/api/tektos/plan/${approvalId}/diff`),

  listAnomalies: () => getJSON<AnomalyRecord[]>("/api/phrouros/anomalies"),

  checkDeliverySlo: (window = 100) =>
    getJSON<DeliverySloReport>(`/api/notifications/slo?window=${window}`),
  ackReceipt: (notificationId: string, subscriberId: string) =>
    postJSON<{ acked: boolean }>(`/api/notifications/${notificationId}/ack`, {
      subscriber_id: subscriberId,
    }),

  // /api/resources/balances returns {kind: ResourceBalance | null} per ADR-066 D2.
  getResourceBalances: () =>
    getJSON<Record<string, ResourceBalance | null>>("/api/resources/balances"),
  getResourceQueue: () => getJSON<QueuedRequest[]>("/api/resources/queue"),

  // ADR-068 Stage 1.5 GUI-realization backend deltas.
  getOllamaStatus: () => getJSON<OllamaStatus>("/api/ollama/status"),
  getPraxisConstitution: () => getJSON<PraxisConstitution>("/api/praxis/constitution"),
  getPraxisApexPolicies: () => getJSON<PraxisApexPolicy[]>("/api/praxis/apex/policies"),

  // ADR-069 Stage 1.5 Wave C — kernel kill-switch.
  killKernel: (reason?: string) =>
    postJSON<KernelKillResponse>("/api/kernel/kill", reason ? { reason } : {}),
  resumeKernel: () => postJSON<KernelResumeResponse>("/api/kernel/resume", {}),
  getSuspensionStatus: () =>
    getJSON<KernelSuspensionStatus>("/api/kernel/suspension"),
};

// --- ADR-068 D1: /api/ollama/status ---
export interface OllamaStatus {
  /** Hot model name (Ollama /api/ps `models[0].name`) or null when idle. */
  model: string | null;
  /** Bytes currently resident in VRAM across all loaded models. */
  size_vram: number;
  /** Bytes currently resident in system RAM across all loaded models. */
  size_ram: number;
  /** Host VRAM capacity in bytes (constant 34_359_738_368 for RTX 5090). */
  vram_capacity_bytes: number;
}

// --- ADR-068 D2: /api/praxis/constitution ---
export interface PraxisConstitution {
  version: number;
  sha256: string;
  ratified_at: string;
  title: string;
  article_count: number;
}

// --- ADR-068 D3: /api/praxis/apex/policies ---
export interface PraxisApexPolicy {
  policy_id: string;
  name: string;
  tier: ChangeApprovalTier;
  active_since: string;
}

// --- ADR-069 kernel kill-switch (Wave C) ---
export interface KernelSuspensionStatus {
  suspended: boolean;
  suspended_at: string | null;
  reason: string | null;
}
export interface KernelKillResponse {
  status: "suspended";
  suspended_at: string | null;
  reason: string | null;
}
export interface KernelResumeResponse {
  status: "running";
  resumed_at: string;
}

export type AlgedonicWSEvent = { type: "algedonic"; payload: AlgedonicReceipt };
export function connectAlgedonicSocket(onEvent: (e: AlgedonicWSEvent) => void): WebSocket | null {
  if (typeof window === "undefined") return null;
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${window.location.host}/api/algedonic/ws`);
  ws.onmessage = (msg) => {
    try {
      const parsed = JSON.parse(msg.data);
      if (parsed.type === "algedonic") onEvent(parsed as AlgedonicWSEvent);
    } catch {
      /* ignore malformed frame */
    }
  };
  return ws;
}

export interface CorpusSummary {
  name: string;
  n_facts: number;
  n_edges: number;
  edge_kind_census: [string, number][];
  licenses: string[];
}

export interface ClaimEnvelope {
  event_id: string;
  corpus_name: string;
  subject: string;
  predicate: string;
  object_: string;
  as_of: string;
  provenance: string;
  confidence: number;
  upstream_url: string | null;
  license: string | null;
  source_commit: string | null;
  crm_class: string | null;
}

export interface EdgeEnvelope {
  src_event_id: string;
  kind: string;
  dst_event_id: string;
  dst_subject: string;
  dst_confidence: number;
  attributes: Record<string, unknown>;
}

export interface ProvenanceChain {
  claim: ClaimEnvelope;
  outbound: EdgeEnvelope[];
  inbound: EdgeEnvelope[];
  edge_count: number;
}

const GNOSIS_GATE_BASE = process.env.NEXT_PUBLIC_GNOSIS_GATE_BASE ?? "/gnosis-gate";

async function getJSONFromBase(base: string, path: string): Promise<unknown> {
  const res = await fetch(base + path, { cache: "no-store" });
  if (!res.ok) throw new Error("GET " + base + path + " -> " + res.status);
  return res.json();
}

export const gnosisGateClient = {
  listCorpora: () => getJSONFromBase(GNOSIS_GATE_BASE, "/api/corpora"),
  getCorpusDetail: (corpusName: string) =>
    getJSONFromBase(GNOSIS_GATE_BASE, "/api/corpus/" + corpusName),
  getProvenance: (corpusName: string, eventId: string) =>
    getJSONFromBase(GNOSIS_GATE_BASE, "/api/corpus/" + corpusName + "/provenance/" + eventId),
  query: (corpusName: string, q: string, asOf?: string, limit?: number) =>
    getJSONFromBase(
      GNOSIS_GATE_BASE,
      "/api/corpus/" + corpusName + "/query?q=" + encodeURIComponent(q || "") +
      (asOf ? "&as_of=" + asOf : "") + "&limit=" + (limit || 20)
    ),
  traverse: (corpusName: string, eventId: string) =>
    getJSONFromBase(GNOSIS_GATE_BASE, "/api/corpus/" + corpusName + "/traverse/" + eventId),
  htmlIndexUrl: () => GNOSIS_GATE_BASE + "/",
  htmlCorpusUrl: (corpusName: string) => GNOSIS_GATE_BASE + "/corpus/" + corpusName,
};
