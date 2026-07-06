import { useNavigate } from "react-router-dom";
import { PlusIcon, ZapIcon, PlayIcon, Trash2Icon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useWorkflows, useDeleteWorkflow, useTriggerRun } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function WorkflowsPage() {
  const navigate = useNavigate();
  const { data: workflows, isLoading } = useWorkflows();
  const deleteMutation = useDeleteWorkflow();
  const triggerMutation = useTriggerRun();

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Workflows</h1>
          <p className="mt-1 text-sm text-[hsl(var(--text-muted))]">
            Manage and trigger your automations
          </p>
        </div>
        <Button onClick={() => navigate("/workflows/new")} size="sm">
          <PlusIcon className="h-3.5 w-3.5" />
          New workflow
        </Button>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-[hsl(var(--bg-subtle))]" />
          ))}
        </div>
      )}

      {workflows && workflows.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[hsl(var(--border))] py-20 text-center">
          <ZapIcon className="h-10 w-10 text-[hsl(var(--text-faint))]" />
          <p className="mt-3 text-sm font-medium">No workflows yet</p>
          <p className="mt-1 text-xs text-[hsl(var(--text-faint))]">
            Create your first automation
          </p>
          <Button
            size="sm"
            className="mt-4"
            onClick={() => navigate("/workflows/new")}
          >
            <PlusIcon className="h-3.5 w-3.5" />
            New workflow
          </Button>
        </div>
      )}

      {workflows && workflows.length > 0 && (
        <div className="divide-y divide-[hsl(var(--border))] rounded-lg border border-[hsl(var(--border))]">
          {workflows.map((wf) => (
            <div
              key={wf.id}
              className="flex items-center gap-4 px-4 py-3 hover:bg-[hsl(var(--bg-subtle))] transition-colors"
            >
              <div
                className={`h-2 w-2 flex-shrink-0 rounded-full ${
                  wf.is_active ? "bg-green-500" : "bg-[hsl(var(--border))]"
                }`}
              />
              <button
                className="min-w-0 flex-1 text-left"
                onClick={() => navigate(`/workflows/${wf.id}`)}
              >
                <p className="text-sm font-medium truncate">{wf.name}</p>
                <p className="text-xs text-[hsl(var(--text-faint))]">
                  {wf.trigger_type} · {formatDate(wf.updated_at)}
                </p>
              </button>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  title="Trigger run"
                  disabled={triggerMutation.isPending}
                  onClick={() => triggerMutation.mutate({ workflowId: wf.id })}
                >
                  <PlayIcon className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  title="Delete"
                  disabled={deleteMutation.isPending}
                  onClick={() => {
                    if (confirm(`Delete "${wf.name}"?`)) {
                      deleteMutation.mutate(wf.id);
                    }
                  }}
                >
                  <Trash2Icon className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
