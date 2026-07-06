import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2Icon, PlusIcon, CheckCircleIcon } from "lucide-react";
import { useMe } from "@/lib/queries";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";

interface Connection {
  id: string;
  provider: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
}

function useConnections() {
  return useQuery<Connection[]>({
    queryKey: ["connections"],
    queryFn: async () => {
      const r = await fetch("/api/integrations/connections", {
        headers: { "X-Dev-User-Id": "dev-user-001" },
      });
      if (!r.ok) throw new Error("Failed to fetch connections");
      return r.json();
    },
  });
}

function useDeleteConnection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const r = await fetch(`/api/integrations/connections/${id}`, {
        method: "DELETE",
        headers: { "X-Dev-User-Id": "dev-user-001" },
      });
      if (!r.ok) throw new Error("Failed to delete");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connections"] }),
  });
}

const INTEGRATIONS = [
  { provider: "google", label: "Google (Gmail & Calendar)", icon: "G" },
  { provider: "github", label: "GitHub", icon: "GH" },
];

export function SettingsPage() {
  const { data: user } = useMe();
  const { data: connections = [] } = useConnections();
  const deleteMutation = useDeleteConnection();

  function handleConnect(provider: string) {
    // Opens the OAuth flow in the same tab; the callback redirects back
    window.location.href = `/api/integrations/connect/${provider}`;
  }

  return (
    <div className="mx-auto max-w-2xl px-8 py-10 space-y-6">
      <div className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-[hsl(var(--text-muted))]">
          Account, connections, and preferences
        </p>
      </div>

      {/* Profile */}
      <Section title="Profile">
        <Row label="Email">{user?.email ?? "—"}</Row>
        <Row label="Name">{user?.display_name ?? "—"}</Row>
        <Row label="Role">{user?.role ?? "—"}</Row>
      </Section>

      {/* Connections */}
      <Section title="Connections">
        <p className="mb-3 text-xs text-[hsl(var(--text-faint))]">
          Connect external services to use them in your workflow nodes.
        </p>

        {INTEGRATIONS.map(({ provider, label, icon }) => {
          const existing = connections.filter((c) => c.provider === provider);
          return (
            <div key={provider} className="flex items-center justify-between py-2">
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[hsl(var(--bg-subtle))] text-[10px] font-bold">
                  {icon}
                </span>
                <div>
                  <p className="text-sm">{label}</p>
                  {existing.length > 0 && (
                    <div className="mt-0.5 flex flex-col gap-0.5">
                      {existing.map((c) => (
                        <div key={c.id} className="flex items-center gap-1.5">
                          <CheckCircleIcon className="h-3 w-3 text-green-500" />
                          <span className="text-[11px] text-[hsl(var(--text-faint))]">
                            {c.display_name} · {formatDate(c.created_at)}
                          </span>
                          <button
                            onClick={() => deleteMutation.mutate(c.id)}
                            className="ml-1 text-[hsl(var(--text-faint))] hover:text-red-500 transition-colors"
                          >
                            <Trash2Icon className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleConnect(provider)}
              >
                <PlusIcon className="h-3 w-3" />
                {existing.length > 0 ? "Reconnect" : "Connect"}
              </Button>
            </div>
          );
        })}
      </Section>

      {/* Keyboard shortcuts */}
      <Section title="Keyboard shortcuts">
        {[
          ["Command palette", "⌘K"],
          ["Run workflow", "⌘↵ (in builder)"],
          ["Generate workflow", "⌘K → Generate"],
        ].map(([label, kbd]) => (
          <div key={label} className="flex items-center justify-between py-1.5">
            <span className="text-sm text-[hsl(var(--text-muted))]">{label}</span>
            <kbd className="rounded border border-[hsl(var(--border))] px-1.5 py-0.5 text-[11px] text-[hsl(var(--text-faint))]">
              {kbd}
            </kbd>
          </div>
        ))}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-[hsl(var(--border))] p-4">
      <h2 className="mb-3 text-[11px] font-medium uppercase tracking-wider text-[hsl(var(--text-faint))]">
        {title}
      </h2>
      {children}
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-sm text-[hsl(var(--text-muted))]">{label}</span>
      <span className="text-sm">{children}</span>
    </div>
  );
}
