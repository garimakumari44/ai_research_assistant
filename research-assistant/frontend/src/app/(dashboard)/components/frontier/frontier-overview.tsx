"use client";

import {
  ArrowUpRight,
  Lightbulb,
  Radar,
  TrendingUp,
} from "lucide-react";

import { TrendCard } from "./trend-card";
import { ResearchGapCard } from "./research-gap-card";
import { NoveltyCard } from "./novelty-card";
import { FrontierDirection } from "./frontier-direction";

export interface FrontierTrend {
  id: string;
  title: string;
  description?: string;
  score?: number;
  direction?: "up" | "down" | "stable";
  evidenceCount?: number;
}

export interface ResearchGap {
  id: string;
  title: string;
  description?: string;
  importance?: number;
  evidenceCount?: number;
}

export interface NoveltyInsight {
  score: number;
  summary?: string;
  uniqueContributions?: string[];
}

export interface FrontierDirectionData {
  id: string;
  title: string;
  description?: string;
  confidence?: number;
  evidenceCount?: number;
}

export interface FrontierOverviewProps {
  trends?: FrontierTrend[];
  researchGaps?: ResearchGap[];
  novelty?: NoveltyInsight;
  directions?: FrontierDirectionData[];
  isLoading?: boolean;
}

export function FrontierOverview({
  trends = [],
  researchGaps = [],
  novelty,
  directions = [],
  isLoading = false,
}: FrontierOverviewProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-32 animate-pulse rounded-xl border border-white/10 bg-white/[0.02]" />
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="h-48 animate-pulse rounded-xl border border-white/10 bg-white/[0.02]" />
          <div className="h-48 animate-pulse rounded-xl border border-white/10 bg-white/[0.02]" />
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Radar className="h-4 w-4 text-blue-400" />

            <h2 className="text-sm font-semibold text-zinc-100">
              Research Frontier
            </h2>
          </div>

          <p className="mt-1 text-xs text-zinc-500">
            Emerging trends, gaps, novelty signals, and future research
            directions.
          </p>
        </div>

        <div className="hidden items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.02] px-2.5 py-1.5 text-[10px] text-zinc-500 sm:flex">
          <TrendingUp className="h-3 w-3" />
          Frontier analysis
        </div>
      </div>

      {trends.length > 0 && (
        <section>
          <SectionHeader
            icon={<TrendingUp className="h-3.5 w-3.5" />}
            title="Emerging trends"
          />

          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {trends.map((trend) => (
              <TrendCard key={trend.id} trend={trend} />
            ))}
          </div>
        </section>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        {researchGaps.length > 0 && (
          <section>
            <SectionHeader
              icon={<Lightbulb className="h-3.5 w-3.5" />}
              title="Research gaps"
            />

            <div className="space-y-3">
              {researchGaps.map((gap) => (
                <ResearchGapCard key={gap.id} gap={gap} />
              ))}
            </div>
          </section>
        )}

        {novelty && (
          <section>
            <SectionHeader
              icon={<ArrowUpRight className="h-3.5 w-3.5" />}
              title="Novelty assessment"
            />

            <NoveltyCard novelty={novelty} />
          </section>
        )}
      </div>

      {directions.length > 0 && (
        <section>
          <SectionHeader
            icon={<ArrowUpRight className="h-3.5 w-3.5" />}
            title="Future research directions"
          />

          <div className="grid gap-3 md:grid-cols-2">
            {directions.map((direction) => (
              <FrontierDirection
                key={direction.id}
                direction={direction}
              />
            ))}
          </div>
        </section>
      )}
    </section>
  );
}

function SectionHeader({
  icon,
  title,
}: {
  icon: React.ReactNode;
  title: string;
}) {
  return (
    <div className="mb-2.5 flex items-center gap-2 text-zinc-400">
      {icon}

      <span className="text-[10px] font-medium uppercase tracking-wider">
        {title}
      </span>
    </div>
  );
}