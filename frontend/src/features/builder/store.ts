/**
 * Builder UI state — canvas selection, config panel, run overlay.
 * Zustand handles UI-only state; server state stays in TanStack Query.
 */

import { create } from "zustand";

interface BuilderStore {
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;

  // Live run status overlay: nodeId → step status
  nodeRunStatus: Record<string, "running" | "succeeded" | "failed" | "skipped">;
  setNodeRunStatus: (
    status: Record<string, "running" | "succeeded" | "failed" | "skipped">
  ) => void;
  clearRunStatus: () => void;

  isRunning: boolean;
  setIsRunning: (v: boolean) => void;
}

export const useBuilderStore = create<BuilderStore>((set) => ({
  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),

  nodeRunStatus: {},
  setNodeRunStatus: (nodeRunStatus) => set({ nodeRunStatus }),
  clearRunStatus: () => set({ nodeRunStatus: {} }),

  isRunning: false,
  setIsRunning: (isRunning) => set({ isRunning }),
}));
