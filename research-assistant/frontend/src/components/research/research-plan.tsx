"use client";

import {
  Check,
  Circle,
  Loader2,
  Search,
  Sparkles,
} from "lucide-react";

import type {
  ResearchPlan as ResearchPlanType,
  ResearchTaskStatus,
} from "@/research/types";

interface ResearchPlanProps {
  plan?: ResearchPlanType;
}

function StatusIcon({
  status,
}: {
  status: ResearchTaskStatus;
}) {
  if (status === "completed") {
    return (
      <Check className="h-3.5 w-3.5" />
    );
  }

  if (status === "running") {
    return (
      <Loader2 className="h-3.5 w-3.5 animate-spin" />
    );
  }

  if (status === "failed") {
    return (
      <Circle className="h-3.5 w-3.5 text-destructive" />
    );
  }

  return (
    <Circle className="h-3.5 w-3.5" />
  );
}

export function ResearchPlan({
  plan,
}: ResearchPlanProps) {
  if (!plan) {
    return null;
  }

  return (
    <section className="rounded-2xl border bg-background">
      <div className="flex items-start justify-between gap-4 border-b p-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />

            <h2 className="text-sm font-semibold">
              Research Plan
            </h2>
          </div>

          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            The Research Engine decomposed the question into
            executable evidence-gathering tasks.
          </p>
        </div>

        <span className="rounded-full border px-2 py-1 text-[10px] font-medium uppercase tracking-wider">
          {plan.strategy}
        </span>
      </div>

      <div className="p-4">
        <div className="mb-4 rounded-xl bg-muted/40 p-3">
          <p className="text-xs font-medium">
            Objective
          </p>

          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            {plan.objective}
          </p>
        </div>

        <div className="space-y-3">
          {plan.steps.map((step) => (
            <div
              key={step.id}
              className="flex gap-3"
            >
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border">
                <StatusIcon
                  status={step.status}
                />
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium">
                    {step.order}. {step.title}
                  </p>

                  {step.strategy && (
                    <span className="text-[10px] uppercase text-muted-foreground">
                      {step.strategy}
                    </span>
                  )}
                </div>

                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}