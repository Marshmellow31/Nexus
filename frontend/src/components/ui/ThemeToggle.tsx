import { useEffect, useState } from "react";
import { MoonIcon, SunIcon, MonitorIcon } from "lucide-react";
import { getTheme, setTheme, type Theme } from "@/lib/theme";
import { Button } from "./button";

const THEMES: { value: Theme; icon: React.ElementType; label: string }[] = [
  { value: "light", icon: SunIcon, label: "Light" },
  { value: "dark", icon: MoonIcon, label: "Dark" },
  { value: "system", icon: MonitorIcon, label: "System" },
];

export function ThemeToggle() {
  const [current, setCurrent] = useState<Theme>(getTheme);

  function cycle() {
    const idx = THEMES.findIndex((t) => t.value === current);
    const next = THEMES[(idx + 1) % THEMES.length].value;
    setTheme(next);
    setCurrent(next);
  }

  const active = THEMES.find((t) => t.value === current)!;
  const Icon = active.icon;

  return (
    <Button variant="ghost" size="icon" onClick={cycle} title={`Theme: ${active.label}`}>
      <Icon className="h-3.5 w-3.5" />
    </Button>
  );
}
