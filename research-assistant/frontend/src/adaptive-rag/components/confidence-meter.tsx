"use client";

import { AlertTriangle, CheckCircle2, MinusCircle } from "lucide-react";

interface ConfidenceMeterProps {
  value: number;
  label?: string;
  showPercentage?: boolean;
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

function normalizeConfidence(value: number): number {
  if (!Number.isFinite(value)) return 0;

  // Accept either 0..1 or 0..100.
  const normalized = value <= 1 ? value * 100 : value;

  return Math.max(0, Math.min(100, normalized));
}

function getConfidenceState(value: number) {
  if (value >= 80) {
    return {
      label: "High",
      icon: CheckCircle2,
      text: "text-emerald-400",
      bar: "bg-emerald-500",
    };
  }

  if (value >= 50) {
    return {
      label: "Moderate",
      icon: MinusCircle,
      text: "text-amber-400",
      bar: "bg-amber-500",
    };
  }

  return {
    label: "Low",
    icon: AlertTriangle,
    text: "text-red-400",
    bar: "bg-red-500",
  };
}

export function ConfidenceMeter({
  value,
  label = "Confidence",
  showPercentage = true,
  showIcon = true,
  size = "md",
  className = "",
}: ConfidenceMeterProps) {
  const percentage = normalizeConfidence(value);
  const state = getConfidenceState(percentage);
  const Icon = state.icon;

  const heights = {
    sm: "h-1",
    md: "h-1.5",
    lg: "h-2",
  };

  return (
    <div className={["w-full", className].join(" ")}>
      <div className="mb-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {showIcon && (
            <Icon className={`h-3.5 w-3.5 ${state.text}`} />
          )}

          <span className="text-xs font-medium text-slate-400">
            {label}
          </span>
        </div>

        <span className={`text-xs font-semibold ${state.text}`}>
          {showPercentage
            ? `${Math.round(percentage)}%`
            : state.label}
        </span>
      </div>

      <div
        className={[
          "w-full overflow-hidden rounded-full bg-slate-800",
          heights[size],
        ].join(" ")}
      >
        <div
          className={[
            "h-full rounded-full transition-all duration-500",
            state.bar,
          ].join(" ")}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export default ConfidenceMeter;