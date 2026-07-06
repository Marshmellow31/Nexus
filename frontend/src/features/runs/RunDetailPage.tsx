/**
 * Run Inspector — shows every node's input, output, timing, and status.
 * This is where engineering quality is visible to recruiters/reviewers.
 */

import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeftIcon, CheckCircleIcon, XCircleIcon, ClockIcon, LoaderIcon } from "lucide-react";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useRun } from "@/lib/queries";
import { formatDate, formatDuration, cn } from "@/lib/utils";

export function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const { data: run, isLoading } = useRun(runId!);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoaderIcon className="h-5 w-5 animate-spin text-[hsl(var(--text-faint))]" />
      </div>
    );
  }

  if (!run) return null;

  return (
    <div className="mx-auto max-w-3xl px-8 py-10">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="mb-4 flex items-center gap-1.5 text-xs text-[hsl(var(--text-faint))] hover:text-[hsl(var(--text-muted))] transition-colors"
        >
          <ArrowLeftIcon className="h-3 w-3" />
          Back
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-mono text-sm font-medium">{run.id}</h1>
            <p className="mt-0.5 text-xs text-[hsl(var(--text-faint))]">
              Started {run.started_at ? formatDate(run.started_at) : "—"} ·{" "}
              {run.trigger_type}
            </p>
          </div>
          <StatusBadge status={run.status} />
        </div>

        {run.error && (
          <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-950 dark:text-red-400">
            {run.error}
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        <h2 className="text-xs font-medium uppercase tracking-wider text-[hsl(var(--text-faint))]">
          Steps
        </h2>
        {run.steps.length === 0 ? (
          <p className="text-xs text-[hsl(var(--text-faint))]">No steps recorded yet.</p>
        ) : (
          <div className="space-y-2">
            {run.steps.map((step) => (
              <StepCard key={step.id} step={step} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StepCard({ step }: { step: ReturnType<typeof useRun>["data"] extends infer R ? R extends { steps: infer S } ? S extends (infer T)[] ? T : never : never : never }) {
  return (
    <details className="group rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--bg-surface))]">
      <summary className="flex cursor-pointer list-none items-center gap-3 px-4 py-3">
        <StepIcon status={step.status} />
        <div className="min-w-0 flex-1">
          <span className="font-mono text-xs font-medium">{step.node_type}</span>
          <span className="ml-2 text-[11px] text-[hsl(var(--text-faint))]">
            {step.node_id}
          </span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-[hsl(var(--text-faint))]">
          <span>{formatDuration(step.duration_ms)}</span>
          {step.attempts > 1 && (
            <span className="rounded bg-[hsl(var(--bg-subtle))] px-1 py-0.5">
              {step.attempts} attempts
            </span>
          )}
          <StatusBadge status={step.status} />
        </div>
      </summary>

      <div className="border-t border-[hsl(var(--border))] px-4 py-3 space-y-3">
        {step.error && (
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-red-500">
              Error
            </p>
            <pre className="text-xs text-red-600 dark:text-red-400 whitespace-pre-wrap">
              {step.error}
            </pre>
          </div>
        )}
        {step.output && (
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-[hsl(var(--text-faint))]">
              Output
            </p>
            <pre className="overflow-x-auto rounded bg-[hsl(var(--bg-subtle))] p-2.5 text-xs text-[hsl(var(--text-muted))]">
              {JSON.stringify(step.output, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </details>
  );
}

function StepIcon({ status }: { status: string }) {
  if (status === "succeeded") return <CheckCircleIcon className="h-4 w-4 flex-shrink-0 text-green-500" />;
  if (status === "failed") return <XCircleIcon className="h-4 w-4 flex-shrink-0 text-red-500" />;
  if (status === "running") return <LoaderIcon className="h-4 w-4 flex-shrink-0 animate-spin text-amber-500" />;
  return <ClockIcon className="h-4 w-4 flex-shrink-0 text-[hsl(var(--text-faint))]" />;
}
