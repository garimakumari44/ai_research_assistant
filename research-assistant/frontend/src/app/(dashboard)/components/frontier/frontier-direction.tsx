"use client";

import {
  ArrowUpRight,
  Compass,
} from "lucide-react";

import type { FrontierDirectionData } from "./frontier-overview";

interface FrontierDirectionProps {
  direction: FrontierDirectionData;
}

export function FrontierDirection({
  direction,
}: FrontierDirectionProps) {
  const confidence =
    direction.confidence !== undefined
      ? Math.max(0, Math.min(1, direction.confidence))
      : undefined;

  return (
    <article className="group rounded-xl border border-white/10 bg-zinc-950 p-4 transition hover:border-white/15">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">
          <Compass className="h-4 w-4 text-cyan-400" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-sm font-medium text-zinc-100">
              {direction.title}
            </h3>

            <ArrowUpRight className="h-4 w-4 shrink-0 text-zinc-700 transition group-hover:text-zinc-400" />
          </div>

          {direction.description && (
            <p className="mt-1.5 text-xs leading-relaxed text-zinc-500">
              {direction.description}
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        {confidence !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-wider text-zinc-600">
              Confidence
            </span>

            <span className="text-xs font-medium text-zinc-300">
              {Math.round(confidence * 100)}%
            </span>
          </div>
        )}

        {direction.evidenceCount !== undefined && (
          <span className="text-[11px] text-zinc-600">
            {direction.evidenceCount} supporting signals
          </span>
        )}
      </div>
    </article>
  );
}