/**
 * Global command palette — the keyboard-first entry point to everything.
 * Trigger: Cmd+K / Ctrl+K.
 *
 * Includes: navigation, workflow actions, AI workflow generation.
 */

import { useState } from "react";
import { Command } from "cmdk";
import { useNavigate } from "react-router-dom";
import {
  ActivityIcon,
  LayoutDashboardIcon,
  LoaderIcon,
  PlusIcon,
  SettingsIcon,
  SparklesIcon,
  ZapIcon,
} from "lucide-react";
import { useWorkflows, useGenerateWorkflow, useCreateWorkflow } from "@/lib/queries";
import { cn } from "@/lib/utils";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type Mode = "search" | "generate";

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("search");
  const [description, setDescription] = useState("");
  const [apiKey, setApiKey] = useState("");

  const { data: workflows } = useWorkflows();
  const generateMutation = useGenerateWorkflow();
  const createMutation = useCreateWorkflow();

  function close() {
    onOpenChange(false);
    setMode("search");
    setDescription("");
  }

  function run(fn: () => void) {
    fn();
    close();
  }

  async function handleGenerate() {
    if (!description.trim()) return;
    try {
      const result = await generateMutation.mutateAsync({
        description,
        apiKey: apiKey || undefined,
      });
      const wf = await createMutation.mutateAsync({
        name: result.name,
        description: result.description ?? undefined,
        definition: result.definition,
      });
      close();
      navigate(`/workflows/${wf.id}`);
    } catch {
      // error shown via mutation state
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[18vh]"
      onClick={close}
    >
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      <div
        className="relative w-full max-w-[560px] overflow-hidden rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--bg-surface))] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {mode === "generate" ? (
          <GenerateMode
            description={description}
            apiKey={apiKey}
            onDescriptionChange={setDescription}
            onApiKeyChange={setApiKey}
            onGenerate={handleGenerate}
            onBack={() => setMode("search")}
            isPending={generateMutation.isPending || createMutation.isPending}
            error={generateMutation.error?.message}
          />
        ) : (
          <Command className="flex flex-col">
            <div className="flex items-center border-b border-[hsl(var(--border))] px-3">
              <ZapIcon className="mr-2 h-3.5 w-3.5 flex-shrink-0 text-[hsl(var(--text-faint))]" />
              <Command.Input
                autoFocus
                placeholder="Type a command or search…"
                className="w-full bg-transparent py-3.5 text-sm outline-none placeholder:text-[hsl(var(--text-faint))]"
              />
            </div>

            <Command.List className="max-h-[380px] overflow-y-auto p-1.5">
              <Command.Empty className="py-8 text-center text-sm text-[hsl(var(--text-faint))]">
                No results.
              </Command.Empty>

              <CmdGroup heading="AI">
                <CmdItem
                  icon={<SparklesIcon className="h-3.5 w-3.5 text-violet-500" />}
                  onSelect={() => setMode("generate")}
                >
                  <span>Generate workflow with AI</span>
                  <span className="ml-auto text-[10px] text-[hsl(var(--text-faint))]">
                    ✦ new
                  </span>
                </CmdItem>
              </CmdGroup>

              <CmdGroup heading="Actions">
                <CmdItem
                  icon={<PlusIcon className="h-3.5 w-3.5" />}
                  onSelect={() => run(() => navigate("/workflows/new"))}
                >
                  New workflow
                </CmdItem>
              </CmdGroup>

              <CmdGroup heading="Navigation">
                <CmdItem
                  icon={<LayoutDashboardIcon className="h-3.5 w-3.5" />}
                  onSelect={() => run(() => navigate("/"))}
                >
                  Dashboard
                </CmdItem>
                <CmdItem
                  icon={<ZapIcon className="h-3.5 w-3.5" />}
                  onSelect={() => run(() => navigate("/workflows"))}
                >
                  Workflows
                </CmdItem>
                <CmdItem
                  icon={<ActivityIcon className="h-3.5 w-3.5" />}
                  onSelect={() => run(() => navigate("/runs"))}
                >
                  Activity
                </CmdItem>
                <CmdItem
                  icon={<SettingsIcon className="h-3.5 w-3.5" />}
                  onSelect={() => run(() => navigate("/settings"))}
                >
                  Settings
                </CmdItem>
              </CmdGroup>

              {workflows && workflows.length > 0 && (
                <CmdGroup heading="Workflows">
                  {workflows.slice(0, 6).map((wf) => (
                    <CmdItem
                      key={wf.id}
                      icon={<ZapIcon className="h-3.5 w-3.5" />}
                      onSelect={() => run(() => navigate(`/workflows/${wf.id}`))}
                    >
                      {wf.name}
                    </CmdItem>
                  ))}
                </CmdGroup>
              )}
            </Command.List>
          </Command>
        )}
      </div>
    </div>
  );
}

function GenerateMode({
  description,
  apiKey,
  onDescriptionChange,
  onApiKeyChange,
  onGenerate,
  onBack,
  isPending,
  error,
}: {
  description: string;
  apiKey: string;
  onDescriptionChange: (v: string) => void;
  onApiKeyChange: (v: string) => void;
  onGenerate: () => void;
  onBack: () => void;
  isPending: boolean;
  error?: string;
}) {
  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-2 border-b border-[hsl(var(--border))] px-4 py-3">
        <SparklesIcon className="h-4 w-4 flex-shrink-0 text-violet-500" />
        <span className="text-sm font-medium">Generate workflow with AI</span>
        <button
          onClick={onBack}
          className="ml-auto text-xs text-[hsl(var(--text-faint))] hover:text-[hsl(var(--text-muted))] transition-colors"
        >
          ← Back
        </button>
      </div>

      <div className="space-y-3 p-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-[hsl(var(--text-muted))]">
            Describe your automation
          </label>
          <textarea
            autoFocus
            value={description}
            onChange={(e) => onDescriptionChange(e.target.value)}
            placeholder="e.g. When I get a GitHub push, review the code with AI and send a Discord notification"
            rows={4}
            className="w-full resize-none rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--bg-subtle))] px-3 py-2 text-sm outline-none transition-colors focus:border-[hsl(var(--accent))] placeholder:text-[hsl(var(--text-faint))]"
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onGenerate();
            }}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-[hsl(var(--text-muted))]">
            Gemini API key{" "}
            <span className="font-normal text-[hsl(var(--text-faint))]">(optional — leave blank to use system key)</span>
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            placeholder="AIza…"
            className="w-full rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--bg-subtle))] px-3 py-2 text-sm outline-none transition-colors focus:border-[hsl(var(--accent))] placeholder:text-[hsl(var(--text-faint))]"
          />
        </div>

        {error && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-600 dark:bg-red-950 dark:text-red-400">
            {error}
          </p>
        )}

        <button
          onClick={onGenerate}
          disabled={isPending || !description.trim()}
          className={cn(
            "flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all",
            "bg-[hsl(var(--accent))] text-white",
            "hover:bg-[hsl(var(--accent-hover))]",
            "disabled:opacity-40 disabled:cursor-not-allowed"
          )}
        >
          {isPending ? (
            <>
              <LoaderIcon className="h-4 w-4 animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <SparklesIcon className="h-4 w-4" />
              Generate workflow
            </>
          )}
        </button>

        <p className="text-center text-[10px] text-[hsl(var(--text-faint))]">
          ⌘↵ to generate · Keys are never stored server-side
        </p>
      </div>
    </div>
  );
}

function CmdGroup({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <Command.Group
      heading={heading}
      className="[&>[cmdk-group-heading]]:px-2 [&>[cmdk-group-heading]]:py-1.5 [&>[cmdk-group-heading]]:text-[10px] [&>[cmdk-group-heading]]:font-medium [&>[cmdk-group-heading]]:uppercase [&>[cmdk-group-heading]]:tracking-wider [&>[cmdk-group-heading]]:text-[hsl(var(--text-faint))]"
    >
      {children}
    </Command.Group>
  );
}

function CmdItem({
  children,
  icon,
  onSelect,
}: {
  children: React.ReactNode;
  icon?: React.ReactNode;
  onSelect: () => void;
}) {
  return (
    <Command.Item
      onSelect={onSelect}
      className={cn(
        "flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-1.5 text-sm",
        "text-[hsl(var(--text-muted))] transition-colors",
        "data-[selected=true]:bg-[hsl(var(--bg-subtle))] data-[selected=true]:text-[hsl(var(--text))]"
      )}
    >
      <span className="text-[hsl(var(--text-faint))]">{icon}</span>
      {children}
    </Command.Item>
  );
}
