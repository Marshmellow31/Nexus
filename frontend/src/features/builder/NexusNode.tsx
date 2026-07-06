/**
 * Custom React Flow node. Shows:
 * - Node type icon + label
 * - Category colour stripe
 * - Live run status overlay (running / succeeded / failed)
 * - Selected state ring
 */

import { Handle, Position, type NodeProps } from "reactflow";
import {
  BrainIcon,
  CheckCircleIcon,
  ClockIcon,
  DatabaseIcon,
  GlobeIcon,
  GitBranchIcon,
  LoaderIcon,
  SparklesIcon,
  XCircleIcon,
  ZapIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useBuilderStore } from "./store";

const CATEGORY_COLORS: Record<string, string> = {
  ai: "bg-violet-500",
  action: "bg-blue-500",
  logic: "bg-amber-500",
  trigger: "bg-green-500",
  integration: "bg-rose-500",
};

const ICON_MAP: Record<string, React.ElementType> = {
  sparkles: SparklesIcon,
  globe: GlobeIcon,
  "git-branch": GitBranchIcon,
  clock: ClockIcon,
  database: DatabaseIcon,
  brain: BrainIcon,
  zap: ZapIcon,
};

export interface NexusNodeData {
  label: string;
  nodeType: string;
  category: string;
  icon: string;
  config: Record<string, unknown>;
}

export function NexusNode({ id, data, selected }: NodeProps<NexusNodeData>) {
  const status = useBuilderStore((s) => s.nodeRunStatus[id]);
  const Icon = ICON_MAP[data.icon] ?? SparklesIcon;
  const stripe = CATEGORY_COLORS[data.category] ?? "bg-gray-400";

  return (
    <div
      className={cn(
        "relative flex min-w-[160px] flex-col rounded-lg border bg-[hsl(var(--bg-surface))] shadow-sm transition-all",
        selected
          ? "border-[hsl(var(--accent))] shadow-[0_0_0_2px_hsl(var(--accent)/0.2)]"
          : "border-[hsl(var(--border))]",
        status === "running" && "border-amber-400 shadow-amber-100",
        status === "succeeded" && "border-green-400 shadow-green-100",
        status === "failed" && "border-red-400 shadow-red-100"
      )}
    >
      {/* Category stripe */}
      <div className={cn("h-0.5 rounded-t-lg", stripe)} />

      <div className="flex items-center gap-2 px-3 py-2.5">
        <div
          className={cn(
            "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md",
            stripe.replace("bg-", "bg-").replace("-500", "-100")
          )}
        >
          <Icon className={cn("h-3.5 w-3.5", stripe.replace("bg-", "text-"))} />
        </div>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium leading-none">{data.label}</p>
          <p className="mt-0.5 truncate text-[10px] text-[hsl(var(--text-faint))]">
            {data.nodeType}
          </p>
        </div>

        {/* Status indicator */}
        {status && (
          <div className="ml-auto flex-shrink-0">
            {status === "running" && (
              <LoaderIcon className="h-3.5 w-3.5 animate-spin text-amber-500" />
            )}
            {status === "succeeded" && (
              <CheckCircleIcon className="h-3.5 w-3.5 text-green-500" />
            )}
            {status === "failed" && (
              <XCircleIcon className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
        )}
      </div>

      <Handle
        type="target"
        position={Position.Top}
        className="!h-2 !w-2 !border-2 !border-[hsl(var(--border))] !bg-[hsl(var(--bg-surface))]"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-2 !w-2 !border-2 !border-[hsl(var(--border))] !bg-[hsl(var(--bg-surface))]"
        id="default"
      />
      {/* Condition node gets labelled handles */}
      {data.category === "logic" && data.nodeType === "logic.condition" && (
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            style={{ left: "30%" }}
            className="!h-2 !w-2 !border-2 !border-green-400 !bg-[hsl(var(--bg-surface))]"
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            style={{ left: "70%" }}
            className="!h-2 !w-2 !border-2 !border-red-400 !bg-[hsl(var(--bg-surface))]"
          />
        </>
      )}
    </div>
  );
}
