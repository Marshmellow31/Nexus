/**
 * Typed API client. All server communication flows through here.
 * In dev, Vite proxies /api → localhost:8000, so no CORS issues.
 * Auth: sends X-Dev-User-Id in dev (matches backend AUTH_DEV_BYPASS=true).
 */

const BASE = "/api";
const DEV_USER_ID = "dev-user-001";

function headers(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  h["X-Dev-User-Id"] = DEV_USER_ID;
  return h;
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    method,
    headers: headers(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: { message: resp.statusText } }));
    throw new Error(err?.error?.message ?? `HTTP ${resp.status}`);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  role: string;
  created_at: string;
}

export interface NodeSpec {
  type: string;
  title: string;
  category: string;
  description: string;
  config_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  requires_connection: string | null;
  is_trigger: boolean;
  icon: string;
}

export interface WorkflowNodeDef {
  id: string;
  type: string;
  label?: string;
  config: Record<string, unknown>;
  position?: { x: number; y: number };
}

export interface WorkflowEdgeDef {
  id?: string;
  source: string;
  target: string;
  source_handle?: string | null;
}

export interface WorkflowDefinition {
  nodes: WorkflowNodeDef[];
  edges: WorkflowEdgeDef[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  trigger_type: string;
  definition: WorkflowDefinition;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface RunStep {
  id: string;
  node_id: string;
  node_type: string;
  status: "running" | "succeeded" | "failed" | "skipped";
  output: Record<string, unknown> | null;
  error: string | null;
  attempts: number;
  duration_ms: number | null;
  created_at: string;
}

export interface Run {
  id: string;
  workflow_id: string;
  status: "pending" | "running" | "succeeded" | "failed" | "cancelled";
  trigger_type: string;
  trigger_payload: Record<string, unknown> | null;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  steps: RunStep[];
}

export type RunSummary = Omit<Run, "steps">;

export interface GeneratedWorkflow {
  name: string;
  description: string | null;
  definition: WorkflowDefinition;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const api = {
  me: () => req<User>("GET", "/auth/me"),
  nodes: () => req<{ nodes: NodeSpec[] }>("GET", "/nodes"),

  workflows: {
    list: () => req<Workflow[]>("GET", "/workflows"),
    get: (id: string) => req<Workflow>("GET", `/workflows/${id}`),
    create: (body: {
      name: string;
      description?: string;
      trigger_type?: string;
      definition?: WorkflowDefinition;
    }) => req<Workflow>("POST", "/workflows", body),
    update: (
      id: string,
      body: Partial<{
        name: string;
        description: string;
        definition: WorkflowDefinition;
        is_active: boolean;
      }>
    ) => req<Workflow>("PATCH", `/workflows/${id}`, body),
    delete: (id: string) => req<void>("DELETE", `/workflows/${id}`),
  },

  runs: {
    list: () => req<RunSummary[]>("GET", "/runs"),
    get: (id: string) => req<Run>("GET", `/runs/${id}`),
    trigger: (workflowId: string, payload?: Record<string, unknown>) =>
      req<RunSummary>("POST", `/runs/workflows/${workflowId}/trigger`, {
        trigger_payload: payload,
      }),
    stream: (runId: string) => new EventSource(`${BASE}/runs/${runId}/stream`),
  },

  ai: {
    generateWorkflow: (description: string, apiKey?: string) =>
      req<GeneratedWorkflow>("POST", "/ai/generate-workflow", {
        description,
        api_key: apiKey ?? null,
      }),
  },
};
