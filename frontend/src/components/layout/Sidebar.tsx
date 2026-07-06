import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import {
  ActivityIcon,
  BoltIcon,
  LayoutDashboardIcon,
  PlugIcon,
  SettingsIcon,
  ZapIcon,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const nav = [
  { to: "/", icon: LayoutDashboardIcon, label: "Dashboard" },
  { to: "/workflows", icon: ZapIcon, label: "Workflows" },
  { to: "/runs", icon: ActivityIcon, label: "Activity" },
  { to: "/settings", icon: SettingsIcon, label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-[220px] flex-shrink-0 flex-col border-r border-[hsl(var(--border))] bg-[hsl(var(--bg-subtle))]">
      {/* Logo */}
      <div className="flex h-12 items-center justify-between border-b border-[hsl(var(--border))] px-4">
        <div className="flex items-center gap-2.5">
          <BoltIcon className="h-4 w-4 text-[hsl(var(--accent))]" strokeWidth={2.5} />
          <span className="text-sm font-semibold tracking-tight">Nexus</span>
        </div>
        <ThemeToggle />
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 p-2">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
                isActive
                  ? "bg-[hsl(var(--bg-surface))] text-[hsl(var(--text))] font-medium shadow-sm"
                  : "text-[hsl(var(--text-muted))] hover:bg-[hsl(var(--bg-surface))] hover:text-[hsl(var(--text))]"
              )
            }
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-[hsl(var(--border))] p-3">
        <div className="flex items-center gap-1.5">
          <kbd className="rounded border border-[hsl(var(--border))] px-1.5 py-0.5 text-[10px] text-[hsl(var(--text-faint))]">
            ⌘K
          </kbd>
          <span className="text-[11px] text-[hsl(var(--text-faint))]">
            Command palette
          </span>
        </div>
      </div>
    </aside>
  );
}
