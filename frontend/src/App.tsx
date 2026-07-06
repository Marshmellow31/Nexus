import { lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { LoaderIcon } from "lucide-react";
import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { WorkflowsPage } from "./features/workflows/WorkflowsPage";
import { RunsPage } from "./features/runs/RunsPage";
import { SettingsPage } from "./features/settings/SettingsPage";

// Lazy-load heavy pages to keep initial bundle small
const BuilderPage = lazy(() =>
  import("./features/builder/BuilderPage").then((m) => ({ default: m.BuilderPage }))
);
const RunDetailPage = lazy(() =>
  import("./features/runs/RunDetailPage").then((m) => ({ default: m.RunDetailPage }))
);

function PageLoader() {
  return (
    <div className="flex h-full items-center justify-center">
      <LoaderIcon className="h-5 w-5 animate-spin text-[hsl(var(--text-faint))]" />
    </div>
  );
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="workflows" element={<WorkflowsPage />} />
            <Route
              path="workflows/new"
              element={<Suspense fallback={<PageLoader />}><BuilderPage /></Suspense>}
            />
            <Route
              path="workflows/:workflowId"
              element={<Suspense fallback={<PageLoader />}><BuilderPage /></Suspense>}
            />
            <Route path="runs" element={<RunsPage />} />
            <Route
              path="runs/:runId"
              element={<Suspense fallback={<PageLoader />}><RunDetailPage /></Suspense>}
            />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
