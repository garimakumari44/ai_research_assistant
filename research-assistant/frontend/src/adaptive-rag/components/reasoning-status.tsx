"use client";

import {
  CheckCircle2,
  Circle,
  Loader2,
  PauseCircle,
  XCircle,
} from "lucide-react";

export type ReasoningStatusValue =
  | "idle"
  | "planning"
  | "retrieving"
  | "evaluating"
  | "reasoning"
  | "generating"
  | "completed"
  | "paused"
  | "failed"
  | string;

interface ReasoningStatusProps {
  status: ReasoningStatusValue;
  label?: string;
  compact?: boolean;
  className?: string;
}

const STATUS_CONFIG: Record<
  string,
  {
    label: string;
    icon: typeof Circle;
    color: string;
    animate?: boolean;
  }
> = {
  idle: {
    label: "Idle",
    icon: Circle,
    color: "text-slate-400",
  },
  planning: {
    label: "Planning",
    icon: Loader2,
    color: "text-violet-400",
    animate: true,
  },
  retrieving: {
    label: "Retrieving",
    icon: Loader2,
    color: "text-cyan-400",
    animate: true,
  },
  evaluating: {
    label: "Evaluating evidence",
    icon: Loader2,
    color: "text-amber-400",
    animate: true,
  },
  reasoning: {
    label: "Reasoning",
    icon: Loader2,
    color: "text-blue-400",
    animate: true,
  },
  generating: {
    label: "Generating",
    icon: Loader2,
    color: "text-indigo-400",
    animate: true,
  },
  completed: {
    label: "Completed",
    icon: CheckCircle2,
    color: "text-emerald-400",
  },
  paused: {
    label: "Paused",
    icon: PauseCircle,
    color: "text-amber-400",
  },
  failed: {
    label: "Failed",
    icon: XCircle,
    color: "text-red-400",
  },
};

export function ReasoningStatus({
  status,
  label,
  compact = false,
  className = "",
}: ReasoningStatusProps) {
  const normalized = status.toLowerCase();

  const config = STATUS_CONFIG[normalized] ?? {
    label: status,
    icon: Circle,
    color: "text-slate-400",
  };

  const Icon = config.icon;

  return (
    <div
      className={[
        "inline-flex items-center rounded-md",
        compact ? "gap-1.5 px-2 py-1" : "gap-2 px-2.5 py-1.5",
        "border border-slate-800 bg-slate-950/70",
        className,
      ].join(" ")}
    >
      <Icon
        className={[
          compact ? "h-3 w-3" : "h-3.5 w-3.5",
          config.color,
          config.animate ? "animate-spin" : "",
        ].join(" ")}
      />

      <span
        className={[
          compact ? "text-xs" : "text-sm",
          "font-medium text-slate-300",
        ].join(" ")}
      >
        {label ?? config.label}
      </span>
    </div>
  );
}

export default ReasoningStatus;