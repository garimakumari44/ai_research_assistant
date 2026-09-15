"use client";

import {
  AlertTriangle,
  CircleAlert,
} from "lucide-react";

import type { ResearchGap } from "./frontier-overview";

interface ResearchGapCardProps {
  gap: ResearchGap;
}

function getImportanceLabel(value?: number) {
  if (value === undefined) return "Unknown";

  if (value >= 0.8) return "High";
  if (value >= 0.5) return "Medium";

  return "Low";
}

export function ResearchGapCard({
  gap,
}: ResearchGapCardProps) {
  const importance = getImportanceLabel(gap.importance);

  return (
    <article className="rounded-xl border border-white/10 bg-zinc-950 p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-500/10">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-sm font-medium text-zinc-100">
              {gap.title}
            </h3>

            <span className="shrink-0 rounded-md border border-amber-500/20 bg-amber-500/5 px-2 py-0.5 text-[10px] text-amber-400">
              {importance}
            </span>
          </div>

          {gap.description && (
            <p className="mt-2 text-xs leading-relaxed text-zinc-500">
              {gap.description}
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        {gap.importance !== undefined ? (
          <div className="flex items-center gap-2">
            <CircleAlert className="h-3.5 w-3.5 text-zinc-600" />

            <span className="text-[11px] text-zinc-500">
              Importance
            </span>

            <span className="text-[11px] font-medium text-zinc-300">
              {Math.round(gap.importance * 100)}%
            </span>
          </div>
        ) : (
          <span />
        )}

        {gap.evidenceCount !== undefined && (
          <span className="text-[11px] text-zinc-600">
            {gap.evidenceCount} evidence items
          </span>
        )}
      </div>
    </article>
  );
}