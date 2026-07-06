import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Trash2Icon, PlusIcon, CheckCircleIcon, KeyIcon, XIcon } from "lucide-react";
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

function useConnectApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { provider: string; api_key: string; display_name?: string }) => {
      const r = await fetch("/api/integrations/connect-key", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Dev-User-Id": "dev-user-001" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error("Failed to connect");
      return r.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["connections"] }),
  });
}

type ConnectMethod = "oauth" | "apikey" | "webhook";

interface IntegrationDef {
  provider: string;
  label: string;
  icon: string;
  method: ConnectMethod;
  keyLabel?: string;
  keyHelp?: string;
  placeholder?: string;
}

const INTEGRATIONS: IntegrationDef[] = [
  { provider: "google", label: "Google (Gmail & Calendar)", icon: "G", method: "oauth" },
  { provider: "github", label: "GitHub", icon: "GH", method: "oauth" },
  {
    provider: "notion",
    label: "Notion",
    icon: "N",
    method: "apikey",
    keyLabel: "Integration token",
    keyHelp: "notion.com/my-integrations → New integration → copy Internal Integration Token",
    placeholder: "secret_…",
  },
  {
    provider: "linear",
    label: "Linear",
    icon: "LN",
    method: "apikey",
    keyLabel: "Personal API key",
    keyHelp: "linear.app/settings/api → Personal API keys → Create key",
    placeholder: "lin_api_…",
  },
  {
    provider: "discord",
    label: "Discord",
    icon: "DC",
    method: "webhook",
    keyLabel: "Webhook URL",
    keyHelp: "Server Settings → Integrations → Webhooks → New Webhook → Copy URL",
    placeholder: "https://discord.com/api/webhooks/…",
  },
  {
    provider: "slack",
    label: "Slack",
    icon: "SL",
    method: "webhook",
    keyLabel: "Incoming Webhook URL",
    keyHelp: "api.slack.com/apps → Incoming Webhooks → Add New Webhook to Workspace → Copy URL",
    placeholder: "https://hooks.slack.com/services/…",
  },
];

interface ModalState {
  provider: string;
  keyLabel: string;
  keyHelp: string;
  placeholder: string;
}

export function SettingsPage() {
  const { data: user } = useMe();
  const { data: connections = [] } = useConnections();
  const deleteMutation = useDeleteConnection();
  const connectKeyMutation = useConnectApiKey();

  const [modal, setModal] = useState<ModalState | null>(null);
  const [keyValue, setKeyValue] = useState("");
  const [keyError, setKeyError] = useState("");

  function openModal(def: IntegrationDef) {
    setModal({
      provider: def.provider,
      keyLabel: def.keyLabel!,
      keyHelp: def.keyHelp!,
      placeholder: def.placeholder ?? "",
    });
    setKeyValue("");
    setKeyError("");
  }

  function handleConnect(def: IntegrationDef) {
    if (def.method === "oauth") {
      window.location.href = `/api/integrations/connect/${def.provider}`;
    } else {
      openModal(def);
    }
  }

  async function handleSubmit() {
    if (!modal || !keyValue.trim()) return;
    setKeyError("");
    try {
      const name = modal.provider.charAt(0).toUpperCase() + modal.provider.slice(1);
      await connectKeyMutation.mutateAsync({
        provider: modal.provider,
        api_key: keyValue.trim(),
        display_name: `${name} (connected)`,
      });
      setModal(null);
    } catch {
      setKeyError("Failed to save. Check the value and try again.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-8 py-10 space-y-6">
      <div className="mb-8">
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-[hsl(var(--text-muted))]">
          Account, connections, and preferences
        </p>
      </div>

      <Section title="Profile">
        <Row label="Email">{user?.email ?? "—"}</Row>
        <Row label="Name">{user?.display_name ?? "—"}</Row>
        <Row label="Role">{user?.role ?? "—"}</Row>
      </Section>

      <Section title="Connections">
        <p className="mb-3 text-xs text-[hsl(var(--text-faint))]">
          Connect external services to use them in workflow nodes.
        </p>

        {INTEGRATIONS.map((def) => {
          const existing = connections.filter((c) => c.provider === def.provider);
          return (
            <div key={def.provider} className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[hsl(var(--bg-subtle))] text-[10px] font-bold flex-shrink-0">
                  {def.icon}
                </span>
                <div>
                  <div className="flex items-center gap-1.5">
                    <p className="text-sm">{def.label}</p>
                    {def.method !== "oauth" && (
                      <span className="rounded px-1 py-0.5 text-[9px] font-medium uppercase tracking-wide bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-faint))]">
                        {def.method}
                      </span>
                    )}
                  </div>
                  {existing.map((c) => (
                    <div key={c.id} className="mt-0.5 flex items-center gap-1.5">
                      <CheckCircleIcon className="h-3 w-3 text-green-500 flex-shrink-0" />
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
              </div>
              <Button variant="outline" size="sm" onClick={() => handleConnect(def)} className="flex-shrink-0 ml-3">
                {def.method === "oauth"
                  ? <PlusIcon className="h-3 w-3" />
                  : <KeyIcon className="h-3 w-3" />}
                {existing.length > 0 ? "Reconnect" : "Connect"}
              </Button>
            </div>
          );
        })}
      </Section>

      <Section title="Keyboard shortcuts">
        {[
          ["Command palette", "⌘K / Ctrl+K"],
          ["Run workflow", "⌘↵ (in builder)"],
          ["Generate with AI", "⌘K → Generate workflow"],
        ].map(([label, kbd]) => (
          <div key={label} className="flex items-center justify-between py-1.5">
            <span className="text-sm text-[hsl(var(--text-muted))]">{label}</span>
            <kbd className="rounded border border-[hsl(var(--border))] px-1.5 py-0.5 text-[11px] text-[hsl(var(--text-faint))]">
              {kbd}
            </kbd>
          </div>
        ))}
      </Section>

      {/* API key / webhook modal */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setModal(null)}>
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
          <div
            className="relative w-full max-w-md rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--bg-surface))] p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold capitalize">Connect {modal.provider}</h2>
              <button onClick={() => setModal(null)} className="text-[hsl(var(--text-faint))] hover:text-[hsl(var(--text-muted))]">
                <XIcon className="h-4 w-4" />
              </button>
            </div>

            <p className="mb-4 text-xs text-[hsl(var(--text-faint))] leading-relaxed">{modal.keyHelp}</p>

            <label className="mb-1.5 block text-xs font-medium text-[hsl(var(--text-muted))]">
              {modal.keyLabel}
            </label>
            <input
              autoFocus
              type="password"
              value={keyValue}
              onChange={(e) => setKeyValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              placeholder={modal.placeholder}
              className="w-full rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--bg-subtle))] px-3 py-2 text-sm outline-none focus:border-[hsl(var(--accent))] placeholder:text-[hsl(var(--text-faint))] mb-4"
            />

            {keyError && <p className="mb-3 text-xs text-red-500">{keyError}</p>}

            <Button className="w-full" onClick={handleSubmit} disabled={!keyValue.trim() || connectKeyMutation.isPending}>
              {connectKeyMutation.isPending ? "Saving…" : "Save connection"}
            </Button>
          </div>
        </div>
      )}
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
