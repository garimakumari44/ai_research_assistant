import {
  Check,
  Circle,
  Loader2,
  ShieldCheck,
} from "lucide-react";

import type {
  ResearchStatus,
} from "@/research/types";

const stages = [
  {
    id: "planning",
    label: "Planning",
  },
  {
    id: "retrieving",
    label: "Retrieval",
  },
  {
    id: "synthesizing",
    label: "Generation",
  },
  {
    id: "verifying",
    label: "Verification",
  },
  {
    id: "completed",
    label: "Complete",
  },
] as const;

function getProgressOrder(
  status: ResearchStatus,
): number {
  switch (status) {
    case "idle":
      return 0;

    case "pending":
    case "queued":
    case "planning":
      return 1;

    case "searching":
    case "retrieving":
      return 2;

    case "running":
    case "synthesizing":
      return 3;

    case "verifying":
      return 4;

    case "completed":
      return 5;

    case "failed":
    case "cancelled":
      return -1;

    default:
      return 0;
  }
}

export function ResearchProgress({
  status,
}: {
  status: ResearchStatus;
}) {
  const current = getProgressOrder(status);

  return (
    <div className="rounded-2xl border p-4">
      <div className="mb-4 flex items-center gap-2">
        <ShieldCheck className="h-4 w-4" />

        <span className="text-sm font-semibold">
          Research Pipeline
        </span>
      </div>

      <div className="grid gap-2 md:grid-cols-5">
        {stages.map((stage, index) => {
          const stageIndex = index + 1;

          const active =
            current === stageIndex;

          const complete =
            current > stageIndex;

          const failed =
            status === "failed" &&
            stageIndex === Math.max(current + 1, 1);

          return (
            <div
              key={stage.id}
              className={`rounded-xl border p-3 ${
                active
                  ? "border-foreground/30 bg-muted"
                  : ""
              }`}
            >
              <div className="flex items-center gap-2">
                {complete ? (
                  <Check className="h-3.5 w-3.5" />
                ) : active ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : failed ? (
                  <Circle className="h-3.5 w-3.5 text-destructive" />
                ) : (
                  <Circle className="h-3.5 w-3.5 text-muted-foreground" />
                )}

                <span className="text-xs font-medium">
                  {stage.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}