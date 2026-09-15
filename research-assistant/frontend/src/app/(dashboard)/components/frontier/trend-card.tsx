"use client";

import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  TrendingUp,
} from "lucide-react";

import type { FrontierTrend } from "./frontier-overview";

interface TrendCardProps {
  trend: FrontierTrend;
}

export function TrendCard({ trend }: TrendCardProps) {
  const direction = trend.direction ?? "stable";

  const DirectionIcon =
    direction === "up"
      ? ArrowUpRight
      : direction === "down"
        ? ArrowDownRight
        : ArrowRight;

  const directionLabel =
    direction === "up"
      ? "Growing"
      : direction === "down"
        ? "Declining"
        : "Stable";

  return (
    <article className="rounded-xl border border-white/10 bg-zinc-950 p-4 transition hover:border-white/15">
      <div className="flex items-start justify-between gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
          <TrendingUp className="h-4 w-4 text-blue-400" />
        </div>

        <div className="flex items-center gap-1 rounded-md bg-white/[0.03] px-2 py-1 text-[10px] text-zinc-500">
          <DirectionIcon
            className={[
              "h-3 w-3",
              direction === "up"
                ? "text-emerald-400"
                : direction === "down"
                  ? "text-red-400"
                  : "text-zinc-500",
            ].join(" ")}
          />

          {directionLabel}
        </div>
      </div>

      <h3 className="mt-4 text-sm font-medium text-zinc-100">
        {trend.title}
      </h3>

      {trend.description && (
        <p className="mt-1.5 line-clamp-3 text-xs leading-relaxed text-zinc-500">
          {trend.description}
        </p>
      )}

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        {trend.score !== undefined ? (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-zinc-600">
              Trend score
            </div>

            <div className="mt-0.5 text-sm font-medium text-zinc-300">
              {Math.round(trend.score * 100)}%
            </div>
          </div>
        ) : (
          <div />
        )}

        {trend.evidenceCount !== undefined && (
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-zinc-600">
              Evidence
            </div>

            <div className="mt-0.5 text-sm text-zinc-400">
              {trend.evidenceCount}
            </div>
          </div>
        )}
      </div>
    </article>
  );
}