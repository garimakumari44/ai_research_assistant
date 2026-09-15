"use client";

import {
  ArrowDown,
  ArrowUp,
  BarChart3,
  CheckCircle2,
  Clock3,
  Database,
  Target,
  TrendingUp,
} from "lucide-react";

export interface StrategyPerformanceData {
  id: string;
  name: string;
  description?: string;
  executions: number;
  successRate: number;
  averageScore: number;
  averageLatencyMs: number;
  citationAccuracy?: number;
  retrievalPrecision?: number;
  trend?: number;
  isActive?: boolean;
}

interface StrategyPerformanceProps {
  strategies?: StrategyPerformanceData[];
  loading?: boolean;
}

function percentage(value: number) {
  return `${Math.round(value * 100)}%`;
}

function scoreClass(value: number) {
  if (value >= 0.9) return "text-emerald-400";
  if (value >= 0.75) return "text-blue-400";
  if (value >= 0.6) return "text-amber-400";
  return "text-red-400";
}

export function StrategyPerformance({
  strategies = [],
  loading = false,
}: StrategyPerformanceProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((item) => (
          <div
            key={item}
            className="h-32 animate-pulse rounded-lg border border-zinc-800 bg-zinc-950"
          />
        ))}
      </div>
    );
  }

  const ranked = [...strategies].sort(
    (a, b) => b.averageScore - a.averageScore,
  );

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950">
      <header className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-4 w-4 text-zinc-500" />

          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              Strategy Performance
            </h2>

            <p className="mt-1 text-xs text-zinc-600">
              Compare research strategies using historical evaluations.
            </p>
          </div>
        </div>

        <TrendingUp className="h-4 w-4 text-zinc-700" />
      </header>

      <div className="overflow-x-auto">
        {ranked.length === 0 ? (
          <div className="p-8 text-center">
            <BarChart3 className="mx-auto h-7 w-7 text-zinc-700" />

            <p className="mt-3 text-sm text-zinc-500">
              No strategy performance data.
            </p>
          </div>
        ) : (
          <div className="min-w-[760px]">
            <div className="grid grid-cols-[2fr_100px_120px_120px_120px_100px] gap-4 border-b border-zinc-800 px-5 py-3 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              <span>Strategy</span>
              <span>Runs</span>
              <span>Score</span>
              <span>Success</span>
              <span>Latency</span>
              <span>Trend</span>
            </div>

            <div className="divide-y divide-zinc-800">
              {ranked.map((strategy, index) => (
                <div
                  key={strategy.id}
                  className="grid grid-cols-[2fr_100px_120px_120px_120px_100px] items-center gap-4 px-5 py-4 transition hover:bg-zinc-900/40"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900 text-[10px] font-medium text-zinc-600">
                      #{index + 1}
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-xs font-medium text-zinc-300">
                          {strategy.name}
                        </span>

                        {strategy.isActive && (
                          <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 text-[8px] uppercase tracking-wide text-emerald-400">
                            Active
                          </span>
                        )}
                      </div>

                      {strategy.description && (
                        <p className="mt-1 truncate text-[10px] text-zinc-600">
                          {strategy.description}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="text-xs text-zinc-500">
                    {strategy.executions.toLocaleString()}
                  </div>

                  <div>
                    <span
                      className={`text-xs font-medium ${scoreClass(
                        strategy.averageScore,
                      )}`}
                    >
                      {percentage(strategy.averageScore)}
                    </span>

                    <div className="mt-1 h-1 w-20 overflow-hidden rounded-full bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-current"
                        style={{
                          width: `${Math.min(
                            100,
                            strategy.averageScore * 100,
                          )}%`,
                        }}
                      />
                    </div>
                  </div>

                  <div className="inline-flex items-center gap-1.5 text-xs text-zinc-500">
                    <CheckCircle2 className="h-3.5 w-3.5 text-zinc-600" />
                    {percentage(strategy.successRate)}
                  </div>

                  <div className="inline-flex items-center gap-1.5 text-xs text-zinc-500">
                    <Clock3 className="h-3.5 w-3.5 text-zinc-600" />
                    {strategy.averageLatencyMs >= 1000
                      ? `${(
                          strategy.averageLatencyMs / 1000
                        ).toFixed(1)}s`
                      : `${Math.round(
                          strategy.averageLatencyMs,
                        )}ms`}
                  </div>

                  <div>
                    {strategy.trend === undefined ? (
                      <span className="text-xs text-zinc-700">
                        —
                      </span>
                    ) : strategy.trend >= 0 ? (
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-400">
                        <ArrowUp className="h-3 w-3" />
                        {Math.abs(strategy.trend).toFixed(1)}%
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-red-400">
                        <ArrowDown className="h-3 w-3" />
                        {Math.abs(strategy.trend).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {ranked.length > 0 && (
        <footer className="border-t border-zinc-800 px-5 py-3">
          <div className="flex flex-wrap items-center gap-5 text-[10px] text-zinc-600">
            <span className="inline-flex items-center gap-1.5">
              <Target className="h-3.5 w-3.5" />
              Score = evaluation quality
            </span>

            <span className="inline-flex items-center gap-1.5">
              <Database className="h-3.5 w-3.5" />
              Runs = historical executions
            </span>
          </div>
        </footer>
      )}
    </section>
  );
}