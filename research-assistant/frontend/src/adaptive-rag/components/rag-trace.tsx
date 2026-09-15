"use client";

import {
  BrainCircuit,
  CheckCircle2,
  Circle,
  Clock3,
  Database,
  GitBranch,
  Loader2,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import StrategyBadge from "./strategy-badge";

export interface RAGTraceStep {
  id?: string;
  type:
    | "planning"
    | "routing"
    | "retrieval"
    | "evaluation"
    | "reasoning"
    | "generation"
    | "completed"
    | "failed"
    | string;
  title?: string;
  description?: string;
  strategy?: string;
  status?: "pending" | "running" | "completed" | "failed" | string;
  timestamp?: string;
  duration_ms?: number;
}

interface RAGTraceProps {
  steps: RAGTraceStep[];
  className?: string;
}

const ICONS: Record<string, typeof Circle> = {
  planning: BrainCircuit,
  routing: GitBranch,
  retrieval: Search,
  evaluation: ShieldCheck,
  reasoning: BrainCircuit,
  generation: Database,
  completed: CheckCircle2,
  failed: XCircle,
};

function TraceIcon({
  step,
}: {
  step: RAGTraceStep;
}) {
  if (step.status === "running") {
    return (
      <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
    );
  }

  const Icon = ICONS[step.type] ?? Circle;

  return (
    <Icon
      className={[
        "h-4 w-4",
        step.status === "failed"
          ? "text-red-400"
          : step.status === "completed"
            ? "text-emerald-400"
            : "text-cyan-400",
      ].join(" ")}
    />
  );
}

export function RAGTrace({
  steps,
  className = "",
}: RAGTraceProps) {
  return (
    <section
      className={[
        "rounded-xl border border-slate-800 bg-slate-950/40",
        className,
      ].join(" ")}
    >
      <div className="border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-cyan-400" />

          <h3 className="text-sm font-semibold text-slate-200">
            RAG Execution Trace
          </h3>

          <span className="ml-auto text-xs text-slate-500">
            {steps.length} steps
          </span>
        </div>
      </div>

      <div className="p-4">
        {steps.length === 0 ? (
          <div className="py-8 text-center text-sm text-slate-500">
            Waiting for execution trace...
          </div>
        ) : (
          <div className="relative space-y-0">
            {steps.map((step, index) => {
              const isLast = index === steps.length - 1;

              return (
                <div
                  key={step.id ?? index}
                  className="relative flex gap-3"
                >
                  {!isLast && (
                    <div className="absolute left-[7px] top-8 h-full w-px bg-slate-800" />
                  )}

                  <div className="relative z-10 flex h-4 w-4 shrink-0 items-center justify-center">
                    <TraceIcon step={step} />
                  </div>

                  <div
                    className={[
                      "min-w-0 flex-1",
                      isLast ? "pb-0" : "pb-6",
                    ].join(" ")}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-medium text-slate-200">
                        {step.title ?? step.type}
                      </span>

                      {step.strategy && (
                        <StrategyBadge
                          strategy={step.strategy}
                          size="sm"
                        />
                      )}
                    </div>

                    {step.description && (
                      <p className="mt-1 text-xs leading-5 text-slate-500">
                        {step.description}
                      </p>
                    )}

                    <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-slate-600">
                      {step.timestamp && (
                        <span>{step.timestamp}</span>
                      )}

                      {step.duration_ms !== undefined && (
                        <span className="flex items-center gap-1">
                          <Clock3 className="h-3 w-3" />
                          {step.duration_ms}ms
                        </span>
                      )}

                      {step.status && (
                        <span className="capitalize">
                          {step.status}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

export default RAGTrace;