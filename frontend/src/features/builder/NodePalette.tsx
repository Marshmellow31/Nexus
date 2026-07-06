/**
 * Node palette — drag-to-canvas node picker, grouped by category.
 * Fetched from /api/nodes — zero hardcoding of node types here.
 */

import { type NodeSpec } from "@/lib/api";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<string, string> = {
  trigger: "Triggers",
  ai: "AI",
  action: "Actions",
  logic: "Logic",
  integration: "Integrations",
};

const CATEGORY_ORDER = ["trigger", "ai", "action", "logic", "integration"];

const CATEGORY_COLORS: Record<string, string> = {
  ai: "text-violet-500 bg-violet-50 dark:bg-violet-950",
  action: "text-blue-500 bg-blue-50 dark:bg-blue-950",
  logic: "text-amber-500 bg-amber-50 dark:bg-amber-950",
  trigger: "text-green-500 bg-green-50 dark:bg-green-950",
  integration: "text-rose-500 bg-rose-50 dark:bg-rose-950",
};

interface NodePaletteProps {
  specs: NodeSpec[];
  onAddNode: (spec: NodeSpec) => void;
}

export function NodePalette({ specs, onAddNode }: NodePaletteProps) {
  const grouped = groupByCategory(specs);

  return (
    <div className="flex h-full w-[200px] flex-shrink-0 flex-col border-r border-[hsl(var(--border))] bg-[hsl(var(--bg-subtle))] overflow-y-auto">
      <div className="border-b border-[hsl(var(--border))] px-3 py-2.5">
        <p className="text-[11px] font-medium text-[hsl(var(--text-faint))] uppercase tracking-wider">
          Nodes
        </p>
      </div>

      <div className="space-y-1 p-2">
        {CATEGORY_ORDER.map((cat) => {
          const nodes = grouped[cat];
          if (!nodes || nodes.length === 0) return null;
          return (
            <div key={cat}>
              <p className="px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-[hsl(var(--text-faint))]">
                {CATEGORY_LABELS[cat] ?? cat}
              </p>
              {nodes.map((spec) => (
                <button
                  key={spec.type}
                  onClick={() => onAddNode(spec)}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left transition-colors",
                    "hover:bg-[hsl(var(--bg-surface))] hover:shadow-sm"
                  )}
                  title={spec.description}
                >
                  <span
                    className={cn(
                      "flex h-5 w-5 flex-shrink-0 items-center justify-center rounded text-[10px]",
                      CATEGORY_COLORS[spec.category] ?? "bg-gray-100 text-gray-500"
                    )}
                  >
                    {spec.title[0]}
                  </span>
                  <span className="truncate text-xs">{spec.title}</span>
                </button>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function groupByCategory(specs: NodeSpec[]): Record<string, NodeSpec[]> {
  return specs.reduce<Record<string, NodeSpec[]>>((acc, s) => {
    (acc[s.category] ??= []).push(s);
    return acc;
  }, {});
}
