"use client";

import {
  CheckCircle2,
  Sparkles,
} from "lucide-react";

import type { NoveltyInsight } from "./frontier-overview";

interface NoveltyCardProps {
  novelty: NoveltyInsight;
}

function getNoveltyLabel(score: number) {
  if (score >= 0.8) return "High novelty";
  if (score >= 0.6) return "Moderate novelty";
  if (score >= 0.4) return "Limited novelty";

  return "Low novelty";
}

export function NoveltyCard({
  novelty,
}: NoveltyCardProps) {
  const score = Math.max(0, Math.min(1, novelty.score));

  return (
    <article className="rounded-xl border border-white/10 bg-zinc-950 p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/10">
            <Sparkles className="h-4 w-4 text-violet-400" />
          </div>

          <div>
            <div className="text-[10px] uppercase tracking-wider text-zinc-600">
              Novelty
            </div>

            <div className="text-sm font-medium text-zinc-200">
              {getNoveltyLabel(score)}
            </div>
          </div>
        </div>

        <div className="text-2xl font-semibold text-zinc-100">
          {Math.round(score * 100)}
          <span className="text-sm text-zinc-600">%</span>
        </div>
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-white/5">
        <div
          className="h-full rounded-full bg-violet-500 transition-all"
          style={{
            width: `${score * 100}%`,
          }}
        />
      </div>

      {novelty.summary && (
        <p className="mt-4 text-xs leading-relaxed text-zinc-500">
          {novelty.summary}
        </p>
      )}

      {novelty.uniqueContributions &&
        novelty.uniqueContributions.length > 0 && (
          <div className="mt-4 space-y-2 border-t border-white/5 pt-4">
            <div className="text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              Unique signals
            </div>

            {novelty.uniqueContributions.map(
              (contribution, index) => (
                <div
                  key={`${contribution}-${index}`}
                  className="flex items-start gap-2"
                >
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500/70" />

                  <span className="text-xs leading-relaxed text-zinc-400">
                    {contribution}
                  </span>
                </div>
              ),
            )}
          </div>
        )}
    </article>
  );
}