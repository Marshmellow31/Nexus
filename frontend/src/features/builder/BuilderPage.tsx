/**
 * Workflow Builder — the heart of Nexus's UI.
 *
 * Layout: [NodePalette | ReactFlow Canvas | ConfigPanel (when node selected)]
 *
 * Data flow:
 *  - Canvas nodes/edges are local React state (React Flow manages them).
 *  - On every change, a debounced PATCH saves to the API.
 *  - Triggering a run opens an SSE stream; node statuses are pushed to the
 *    BuilderStore and rendered as overlays on canvas nodes.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";

import {
  ArrowLeftIcon,
  LoaderIcon,
  PlayIcon,
  SaveIcon,
  SparklesIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNodes, useWorkflow, useCreateWorkflow, useUpdateWorkflow, useTriggerRun } from "@/lib/queries";
import { api, type NodeSpec, type WorkflowDefinition } from "@/lib/api";
import { cn } from "@/lib/utils";

import { NexusNode, type NexusNodeData } from "./NexusNode";
import { NodePalette } from "./NodePalette";
import { ConfigPanel } from "./ConfigPanel";
import { useBuilderStore } from "./store";

const NODE_TYPES = { nexusNode: NexusNode };

let nodeIdCounter = 1;
function nextId() {
  return `n${nodeIdCounter++}`;
}

export function BuilderPage() {
  const { workflowId } = useParams<{ workflowId: string }>();
  const navigate = useNavigate();
  const isNew = workflowId === "new";

  const { data: workflow, isLoading } = useWorkflow(isNew ? "" : workflowId!);
  const { data: nodesData } = useNodes();
  const createMutation = useCreateWorkflow();
  const updateMutation = useUpdateWorkflow(workflowId ?? "");
  const triggerMutation = useTriggerRun();

  const [rfNodes, setRfNodes, onNodesChange] = useNodesState<NexusNodeData>([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const [workflowName, setWorkflowName] = useState("Untitled workflow");
  const [savedId, setSavedId] = useState<string | null>(isNew ? null : (workflowId ?? null));
  const [isSaving, setIsSaving] = useState(false);

  const { selectedNodeId, setSelectedNodeId, nodeRunStatus, setNodeRunStatus, clearRunStatus, isRunning, setIsRunning } =
    useBuilderStore();

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const specMap = useRef<Record<string, NodeSpec>>({});

  // Build spec lookup
  useEffect(() => {
    if (nodesData?.nodes) {
      nodesData.nodes.forEach((s) => (specMap.current[s.type] = s));
    }
  }, [nodesData]);

  // Load workflow into canvas
  useEffect(() => {
    if (!workflow) return;
    setWorkflowName(workflow.name);
    setSavedId(workflow.id);
    setRfNodes(toRfNodes(workflow.definition));
    setRfEdges(toRfEdges(workflow.definition));
  }, [workflow, setRfNodes, setRfEdges]);

  // Debounced auto-save
  function scheduleAutoSave(nodes: Node<NexusNodeData>[], edges: Edge[]) {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => doSave(nodes, edges), 1500);
  }

  async function doSave(
    nodes: Node<NexusNodeData>[],
    edges: Edge[],
    name?: string
  ): Promise<string | null> {
    const definition = toDefinition(nodes, edges);
    setIsSaving(true);
    try {
      if (!savedId) {
        const wf = await createMutation.mutateAsync({
          name: name ?? workflowName,
          definition,
        });
        setSavedId(wf.id);
        navigate(`/workflows/${wf.id}`, { replace: true });
        return wf.id;
      } else {
        await updateMutation.mutateAsync({ definition, name: name ?? workflowName });
        return savedId;
      }
    } finally {
      setIsSaving(false);
    }
    return null;
  }

  // Add node from palette
  function handleAddNode(spec: NodeSpec) {
    const id = nextId();
    const newNode: Node<NexusNodeData> = {
      id,
      type: "nexusNode",
      position: { x: 300 + rfNodes.length * 30, y: 200 + rfNodes.length * 20 },
      data: {
        label: spec.title,
        nodeType: spec.type,
        category: spec.category,
        icon: spec.icon,
        config: defaultConfig(spec),
      },
    };
    const updated = [...rfNodes, newNode];
    setRfNodes(updated);
    scheduleAutoSave(updated, rfEdges);
  }

  // Connect nodes
  const onConnect = useCallback(
    (params: Connection) => {
      const updated = addEdge({ ...params, animated: false }, rfEdges);
      setRfEdges(updated);
      scheduleAutoSave(rfNodes, updated);
    },
    [rfNodes, rfEdges]
  );

  // Update node config from ConfigPanel
  function handleConfigSave(nodeId: string, config: Record<string, unknown>) {
    const updated = rfNodes.map((n) =>
      n.id === nodeId ? { ...n, data: { ...n.data, config } } : n
    );
    setRfNodes(updated);
    scheduleAutoSave(updated, rfEdges);
    setSelectedNodeId(null);
  }

  // Trigger run + stream status
  async function handleRun() {
    const id = savedId ?? await doSave(rfNodes, rfEdges);
    if (!id) return;
    clearRunStatus();
    setIsRunning(true);

    const run = await triggerMutation.mutateAsync({ workflowId: id });
    const src = api.runs.stream(run.id);

    src.addEventListener("status", (e) => {
      const data = JSON.parse((e as MessageEvent).data);
      const statusMap: Record<string, "running" | "succeeded" | "failed" | "skipped"> = {};
      for (const step of data.steps ?? []) {
        statusMap[step.node_id] = step.status;
      }
      setNodeRunStatus(statusMap);
    });

    src.addEventListener("done", () => {
      src.close();
      setIsRunning(false);
    });

    src.addEventListener("error", () => {
      src.close();
      setIsRunning(false);
    });
  }

  // Selected node spec
  const selectedNode = rfNodes.find((n) => n.id === selectedNodeId);
  const selectedSpec = selectedNode
    ? specMap.current[selectedNode.data.nodeType]
    : null;

  if (isLoading && !isNew) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoaderIcon className="h-5 w-5 animate-spin text-[hsl(var(--text-faint))]" />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Toolbar */}
      <div className="flex h-11 flex-shrink-0 items-center gap-3 border-b border-[hsl(var(--border))] bg-[hsl(var(--bg-surface))] px-4">
        <button
          onClick={() => navigate("/workflows")}
          className="flex items-center gap-1.5 text-xs text-[hsl(var(--text-faint))] hover:text-[hsl(var(--text-muted))] transition-colors"
        >
          <ArrowLeftIcon className="h-3 w-3" />
          Workflows
        </button>
        <div className="mx-2 h-4 w-px bg-[hsl(var(--border))]" />
        <input
          value={workflowName}
          onChange={(e) => {
            setWorkflowName(e.target.value);
            scheduleAutoSave(rfNodes, rfEdges);
          }}
          className="bg-transparent text-sm font-medium outline-none focus:underline decoration-[hsl(var(--border))] underline-offset-2"
          placeholder="Workflow name"
        />
        <div className="ml-auto flex items-center gap-2">
          {isSaving && (
            <span className="flex items-center gap-1 text-[11px] text-[hsl(var(--text-faint))]">
              <LoaderIcon className="h-3 w-3 animate-spin" /> Saving…
            </span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => doSave(rfNodes, rfEdges)}
            disabled={isSaving}
          >
            <SaveIcon className="h-3.5 w-3.5" />
            Save
          </Button>
          <Button
            size="sm"
            onClick={handleRun}
            disabled={isRunning || rfNodes.length === 0}
          >
            {isRunning ? (
              <LoaderIcon className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <PlayIcon className="h-3.5 w-3.5" />
            )}
            {isRunning ? "Running…" : "Run"}
          </Button>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Palette */}
        {nodesData?.nodes && (
          <NodePalette specs={nodesData.nodes} onAddNode={handleAddNode} />
        )}

        {/* Canvas */}
        <div className="flex-1 relative">
          {rfNodes.length === 0 && (
            <EmptyCanvas />
          )}
          <ReactFlow
            nodes={rfNodes}
            edges={rfEdges}
            nodeTypes={NODE_TYPES}
            onNodesChange={(changes) => {
              onNodesChange(changes);
              scheduleAutoSave(rfNodes, rfEdges);
            }}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            onPaneClick={() => setSelectedNodeId(null)}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            proOptions={{ hideAttribution: true }}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1}
              color="hsl(var(--border))"
            />
            <Controls
              className="!border-[hsl(var(--border))] !bg-[hsl(var(--bg-surface))] !shadow-sm [&>button]:!border-[hsl(var(--border))] [&>button]:!text-[hsl(var(--text-muted))]"
              showInteractive={false}
            />
            <MiniMap
              nodeColor={() => "hsl(var(--bg-subtle))"}
              maskColor="hsl(var(--bg)/0.7)"
              className="!border-[hsl(var(--border))] !bg-[hsl(var(--bg-surface))]"
            />
          </ReactFlow>
        </div>

        {/* Config panel */}
        {selectedNode && selectedSpec && (
          <ConfigPanel
            nodeId={selectedNode.id}
            nodeType={selectedNode.data.nodeType}
            config={selectedNode.data.config}
            spec={selectedSpec}
            onSave={handleConfigSave}
            onClose={() => setSelectedNodeId(null)}
          />
        )}
      </div>
    </div>
  );
}

function EmptyCanvas() {
  return (
    <div className="pointer-events-none absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 text-center">
      <SparklesIcon className="h-8 w-8 text-[hsl(var(--text-faint))]" />
      <p className="text-sm font-medium text-[hsl(var(--text-muted))]">
        Add nodes from the palette
      </p>
      <p className="text-xs text-[hsl(var(--text-faint))]">
        Or press ⌘K → "Generate workflow" to describe your automation
      </p>
    </div>
  );
}

// ── Conversion helpers ────────────────────────────────────────────────────────

function toRfNodes(def: WorkflowDefinition): Node<NexusNodeData>[] {
  return def.nodes.map((n, i) => ({
    id: n.id,
    type: "nexusNode",
    position: n.position ?? { x: 100 + i * 220, y: 200 },
    data: {
      label: n.label ?? n.type,
      nodeType: n.type,
      category: categoryFromType(n.type),
      icon: iconFromType(n.type),
      config: n.config ?? {},
    },
  }));
}

function toRfEdges(def: WorkflowDefinition): Edge[] {
  return def.edges.map((e, i) => ({
    id: e.id ?? `e${i}`,
    source: e.source,
    target: e.target,
    sourceHandle: e.source_handle ?? null,
  }));
}

function toDefinition(
  nodes: Node<NexusNodeData>[],
  edges: Edge[]
): WorkflowDefinition {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.data.nodeType,
      label: n.data.label,
      config: n.data.config,
      position: n.position,
    })),
    edges: edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      source_handle: e.sourceHandle ?? null,
    })),
  };
}

function defaultConfig(spec: NodeSpec): Record<string, unknown> {
  const schema = spec.config_schema as {
    properties?: Record<string, { default?: unknown }>;
  };
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(schema.properties ?? {})) {
    if (v.default !== undefined) out[k] = v.default;
  }
  return out;
}

function categoryFromType(type: string): string {
  const [cat] = type.split(".");
  const map: Record<string, string> = {
    ai: "ai",
    http: "action",
    logic: "logic",
    action: "action",
    webhook: "trigger",
  };
  return map[cat] ?? "action";
}

function iconFromType(type: string): string {
  const map: Record<string, string> = {
    "ai.generate": "sparkles",
    "http.request": "globe",
    "logic.condition": "git-branch",
    "logic.delay": "clock",
    "action.store": "database",
  };
  return map[type] ?? "zap";
}
