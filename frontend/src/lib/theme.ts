/**
 * Theme management. Persists to localStorage, applies class on <html>.
 * Reactive via a custom event so any component can subscribe.
 */

export type Theme = "light" | "dark" | "system";

const KEY = "nexus-theme";

export function getTheme(): Theme {
  return (localStorage.getItem(KEY) as Theme) ?? "system";
}

export function setTheme(theme: Theme) {
  localStorage.setItem(KEY, theme);
  applyTheme(theme);
  window.dispatchEvent(new CustomEvent("nexus-theme-change", { detail: theme }));
}

export function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const isDark =
    theme === "dark" ||
    (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  root.classList.toggle("dark", isDark);
}

// Apply on page load
applyTheme(getTheme());
