import {
  Clock3,
  Database,
  GitBranch,
  Search,
} from "lucide-react";

import type {
  ResearchSession as ResearchSessionType,
} from "@/research/types";

import { ResearchPlan } from "./research-plan";
import { ResearchProgress } from "./research-progress";
import { ResearchTaskList } from "./research-task-list";

export function ResearchSession({
  session,
}: {
  session: ResearchSessionType;
}) {
  return (
    <div className="space-y-4">
      <ResearchProgress
        status={session.status ?? "idle"}
      />

      <div className="grid gap-2 sm:grid-cols-4">
        <Metric
          icon={<Search className="h-3.5 w-3.5" />}
          label="Strategy"
          value={
            session.strategy ??
            "adaptive"
          }
        />

        <Metric
          icon={<Database className="h-3.5 w-3.5" />}
          label="Retrieval"
          value={
            session.retrievalModes?.join(
              " + ",
            ) ?? "adaptive"
          }
        />

        <Metric
          icon={<GitBranch className="h-3.5 w-3.5" />}
          label="Iterations"
          value={String(
            session.iterations ?? 0,
          )}
        />

        <Metric
          icon={<Clock3 className="h-3.5 w-3.5" />}
          label="Duration"
          value={
            session.durationMs !== undefined
              ? `${Math.round(
                  session.durationMs,
                )}ms`
              : "—"
          }
        />
      </div>

      <ResearchPlan
        plan={session.plan ?? undefined}
      />

      <ResearchTaskList
        tasks={session.tasks ?? []}
      />
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border p-3">
      <div className="flex items-center gap-2 text-muted-foreground">
        {icon}

        <span className="text-[10px] uppercase tracking-wider">
          {label}
        </span>
      </div>

      <p className="mt-2 truncate text-xs font-medium">
        {value}
      </p>
    </div>
  );
}