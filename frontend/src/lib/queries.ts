/**
 * TanStack Query hooks. All server state lives here — never in Zustand.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type WorkflowDefinition } from "./api";

export const keys = {
  me: ["me"] as const,
  nodes: ["nodes"] as const,
  workflows: ["workflows"] as const,
  workflow: (id: string) => ["workflows", id] as const,
  runs: ["runs"] as const,
  run: (id: string) => ["runs", id] as const,
};

export function useMe() {
  return useQuery({ queryKey: keys.me, queryFn: api.me });
}

export function useNodes() {
  return useQuery({
    queryKey: keys.nodes,
    queryFn: api.nodes,
    staleTime: Infinity,
  });
}

export function useWorkflows() {
  return useQuery({ queryKey: keys.workflows, queryFn: api.workflows.list });
}

export function useWorkflow(id: string) {
  return useQuery({
    queryKey: keys.workflow(id),
    queryFn: () => api.workflows.get(id),
    enabled: !!id,
  });
}

export function useCreateWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.workflows.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.workflows }),
  });
}

export function useUpdateWorkflow(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (
      body: Partial<{
        name: string;
        description: string;
        definition: WorkflowDefinition;
        is_active: boolean;
      }>
    ) => api.workflows.update(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.workflow(id) });
      qc.invalidateQueries({ queryKey: keys.workflows });
    },
  });
}

export function useDeleteWorkflow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.workflows.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.workflows }),
  });
}

export function useRuns() {
  return useQuery({ queryKey: keys.runs, queryFn: api.runs.list });
}

export function useRun(id: string) {
  return useQuery({
    queryKey: keys.run(id),
    queryFn: () => api.runs.get(id),
    enabled: !!id,
  });
}

export function useTriggerRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      workflowId,
      payload,
    }: {
      workflowId: string;
      payload?: Record<string, unknown>;
    }) => api.runs.trigger(workflowId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.runs }),
  });
}

export function useGenerateWorkflow() {
  return useMutation({
    mutationFn: ({
      description,
      apiKey,
    }: {
      description: string;
      apiKey?: string;
    }) => api.ai.generateWorkflow(description, apiKey),
  });
}
