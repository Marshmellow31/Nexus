import { useNavigate } from "react-router-dom";
import { ActivityIcon } from "lucide-react";
import { StatusBadge } from "@/components/ui/badge";
import { useRuns } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function RunsPage() {
  const navigate = useNavigate();
  const { data: runs, isLoading } = useRuns();

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <div className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">Activity</h1>
        <p className="mt-1 text-sm text-[hsl(var(--text-muted))]">
          All workflow execution history
        </p>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-[hsl(var(--bg-subtle))]" />
          ))}
        </div>
      )}

      {runs && runs.length === 0 && (
        <div className="flex flex-col items-center py-20 text-center">
          <ActivityIcon className="h-10 w-10 text-[hsl(var(--text-faint))]" />
          <p className="mt-3 text-sm font-medium">No runs yet</p>
          <p className="mt-1 text-xs text-[hsl(var(--text-faint))]">
            Trigger a workflow to see activity here
          </p>
        </div>
      )}

      {runs && runs.length > 0 && (
        <div className="divide-y divide-[hsl(var(--border))] rounded-lg border border-[hsl(var(--border))]">
          {runs.map((run) => (
            <button
              key={run.id}
              onClick={() => navigate(`/runs/${run.id}`)}
              className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-[hsl(var(--bg-subtle))]"
            >
              <div>
                <p className="text-sm font-medium font-mono text-xs text-[hsl(var(--text-faint))]">
                  {run.id.slice(0, 8)}
                </p>
                <p className="text-xs text-[hsl(var(--text-faint))] mt-0.5">
                  {run.trigger_type} · {formatDate(run.created_at)}
                </p>
              </div>
              <StatusBadge status={run.status} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
