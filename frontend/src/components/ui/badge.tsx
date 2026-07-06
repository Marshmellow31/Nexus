import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "destructive" | "outline";
  className?: string;
}

const variantStyles = {
  default: "bg-[hsl(var(--bg-subtle))] text-[hsl(var(--text-muted))]",
  success: "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-400",
  warning: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-400",
  destructive: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-400",
  outline: "border border-[hsl(var(--border))] text-[hsl(var(--text-muted))]",
};

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeProps["variant"]> = {
    succeeded: "success",
    running: "warning",
    pending: "outline",
    failed: "destructive",
    cancelled: "default",
  };
  return <Badge variant={map[status] ?? "default"}>{status}</Badge>;
}
