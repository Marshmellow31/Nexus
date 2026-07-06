import { cn } from "@/lib/utils";
import { type ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "ghost" | "outline" | "destructive" | "link";
  size?: "sm" | "md" | "lg" | "icon";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--accent))] focus-visible:ring-offset-1",
          "disabled:pointer-events-none disabled:opacity-40",
          {
            "bg-[hsl(var(--accent))] text-[hsl(var(--accent-fg))] hover:bg-[hsl(var(--accent-hover))]":
              variant === "default",
            "hover:bg-[hsl(var(--bg-subtle))] hover:text-[hsl(var(--text))] text-[hsl(var(--text-muted))]":
              variant === "ghost",
            "border border-[hsl(var(--border))] bg-transparent hover:bg-[hsl(var(--bg-subtle))]":
              variant === "outline",
            "bg-[hsl(var(--destructive))] text-white hover:opacity-90":
              variant === "destructive",
            "text-[hsl(var(--accent))] underline-offset-4 hover:underline":
              variant === "link",
          },
          {
            "h-7 px-2.5 text-xs": size === "sm",
            "h-8 px-3.5 text-sm": size === "md",
            "h-10 px-5 text-base": size === "lg",
            "h-8 w-8 p-0": size === "icon",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
