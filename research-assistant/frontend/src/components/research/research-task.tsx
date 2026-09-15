import {
  Check,
  Circle,
  Loader2,
  XCircle,
} from "lucide-react";

import type {
  ResearchTask as ResearchTaskType,
} from "@/research/types";

export function ResearchTask({
  task,
}: {
  task: ResearchTaskType;
}) {
  const icon =
    task.status === "completed" ? (
      <Check className="h-3.5 w-3.5" />
    ) : task.status === "running" ? (
      <Loader2 className="h-3.5 w-3.5 animate-spin" />
    ) : task.status === "failed" ? (
      <XCircle className="h-3.5 w-3.5 text-destructive" />
    ) : (
      <Circle className="h-3.5 w-3.5 text-muted-foreground" />
    );

  return (
    <div className="rounded-xl border p-3">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">
          {icon}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold">
              {task.title}
            </p>

            {task.strategy && (
              <span className="text-[9px] uppercase tracking-wider text-muted-foreground">
                {task.strategy}
              </span>
            )}
          </div>

          {task.description && (
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              {task.description}
            </p>
          )}

          {task.query && (
            <div className="mt-2 rounded-lg bg-muted/50 p-2 text-[11px] text-muted-foreground">
              {task.query}
            </div>
          )}

          {(task.resultCount !==
            undefined ||
            task.durationMs !==
              undefined) && (
            <div className="mt-2 text-[10px] text-muted-foreground">
              {task.resultCount ?? 0} evidence
              {task.durationMs !==
              undefined
                ? ` · ${Math.round(
                    task.durationMs,
                  )}ms`
                : ""}
            </div>
          )}

          {task.error && (
            <p className="mt-2 text-xs text-destructive">
              {task.error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}