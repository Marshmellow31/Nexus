import { useNavigate } from "react-router-dom";
import { PlusIcon, ZapIcon, ActivityIcon, ArrowRightIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/badge";
import { useWorkflows, useRuns } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function DashboardPage() {
  const navigate = useNavigate();
  const { data: workflows } = useWorkflows();
  const { data: runs } = useRuns();

  const recentRuns = runs?.slice(0, 5) ?? [];
  const activeWorkflows = workflows?.filter((w) => w.is_active).length ?? 0;

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-8 py-10">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-[hsl(var(--text-muted))]">
            Your automation at a glance
          </p>
        </div>
        <Button onClick={() => navigate("/workflows/new")} size="sm">
          <PlusIcon className="h-3.5 w-3.5" />
          New workflow
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="Active workflows"
          value={activeWorkflows}
          icon={<ZapIcon className="h-4 w-4" />}
        />
        <StatCard
          label="Total workflows"
          value={workflows?.length ?? 0}
          icon={<ZapIcon className="h-4 w-4" />}
        />
        <StatCard
          label="Recent runs"
          value={runs?.length ?? 0}
          icon={<ActivityIcon className="h-4 w-4" />}
        />
      </div>

      {/* Recent runs */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-medium">Recent activity</h2>
          <button
            className="flex items-center gap-1 text-xs text-[hsl(var(--text-faint))] hover:text-[hsl(var(--text-muted))] transition-colors"
            onClick={() => navigate("/runs")}
          >
            View all <ArrowRightIcon className="h-3 w-3" />
          </button>
        </div>

        {recentRuns.length === 0 ? (
          <EmptyState
            icon={<ActivityIcon className="h-8 w-8" />}
            title="No runs yet"
            description="Trigger a workflow to see activity here"
          />
        ) : (
          <div className="divide-y divide-[hsl(var(--border))] rounded-lg border border-[hsl(var(--border))]">
            {recentRuns.map((run) => (
              <button
                key={run.id}
                onClick={() => navigate(`/runs/${run.id}`)}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-[hsl(var(--bg-subtle))]"
              >
                <div>
                  <p className="text-sm font-medium">Run</p>
                  <p className="text-xs text-[hsl(var(--text-faint))]">
                    {formatDate(run.created_at)}
                  </p>
                </div>
                <StatusBadge status={run.status} />
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Workflows */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-medium">Workflows</h2>
          <button
            className="flex items-center gap-1 text-xs text-[hsl(var(--text-faint))] hover:text-[hsl(var(--text-muted))] transition-colors"
            onClick={() => navigate("/workflows")}
          >
            View all <ArrowRightIcon className="h-3 w-3" />
          </button>
        </div>

        {!workflows || workflows.length === 0 ? (
          <EmptyState
            icon={<ZapIcon className="h-8 w-8" />}
            title="No workflows yet"
            description="Create your first automation workflow"
            action={
              <Button size="sm" onClick={() => navigate("/workflows/new")}>
                <PlusIcon className="h-3.5 w-3.5" />
                New workflow
              </Button>
            }
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {workflows.slice(0, 4).map((wf) => (
              <button
                key={wf.id}
                onClick={() => navigate(`/workflows/${wf.id}`)}
                className="group rounded-lg border border-[hsl(var(--border))] p-4 text-left transition-all hover:border-[hsl(var(--accent))] hover:shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <ZapIcon className="h-3.5 w-3.5 text-[hsl(var(--accent))]" />
                    <span className="text-sm font-medium">{wf.name}</span>
                  </div>
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${wf.is_active ? "bg-green-500" : "bg-[hsl(var(--border))]"}`}
                  />
                </div>
                {wf.description && (
                  <p className="mt-1.5 text-xs text-[hsl(var(--text-faint))] line-clamp-1">
                    {wf.description}
                  </p>
                )}
                <p className="mt-2 text-[11px] text-[hsl(var(--text-faint))]">
                  {wf.trigger_type} · v{wf.version}
                </p>
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-[hsl(var(--border))] p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-[hsl(var(--text-faint))]">{label}</span>
        <span className="text-[hsl(var(--text-faint))]">{icon}</span>
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value}</p>
    </div>
  );
}

function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[hsl(var(--border))] py-12 text-center">
      <div className="text-[hsl(var(--text-faint))]">{icon}</div>
      <p className="mt-3 text-sm font-medium">{title}</p>
      <p className="mt-1 text-xs text-[hsl(var(--text-faint))]">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
