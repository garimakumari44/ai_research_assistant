"use client";

import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Info,
  RefreshCw,
  Star,
  Target,
} from "lucide-react";

import { useState } from "react";

export interface EvaluationMetric {
  id: string;
  name: string;
  score: number;
  description?: string;
  threshold?: number;
  details?: string;
}

export interface EvaluationResult {
  id?: string;
  overallScore: number;
  passed: boolean;
  metrics: EvaluationMetric[];
  summary?: string;
  evaluatedAt?: string;
}

interface EvaluationPanelProps {
  evaluation?: EvaluationResult;
  loading?: boolean;
  onEvaluate?: () => void;
}

function scoreLabel(score: number) {
  if (score >= 0.9) return "Excellent";
  if (score >= 0.75) return "Good";
  if (score >= 0.6) return "Needs improvement";
  return "Poor";
}

function scoreClass(score: number) {
  if (score >= 0.9) return "text-emerald-400";
  if (score >= 0.75) return "text-blue-400";
  if (score >= 0.6) return "text-amber-400";
  return "text-red-400";
}

export function EvaluationPanel({
  evaluation,
  loading = false,
  onEvaluate,
}: EvaluationPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(
    null,
  );

  if (loading) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-6">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Evaluating research quality...
        </div>
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-8 text-center">
        <Target className="mx-auto h-7 w-7 text-zinc-700" />

        <h2 className="mt-3 text-sm font-medium text-zinc-300">
          No evaluation available
        </h2>

        <p className="mx-auto mt-1 max-w-sm text-xs leading-5 text-zinc-600">
          Run an evaluation to measure the quality of this research
          execution.
        </p>

        <button
          type="button"
          onClick={onEvaluate}
          className="mt-4 inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-blue-500"
        >
          <Target className="h-3.5 w-3.5" />
          Run evaluation
        </button>
      </div>
    );
  }

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950">
      <header className="border-b border-zinc-800 px-5 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              Evaluation
            </h2>

            <p className="mt-1 text-xs text-zinc-600">
              Research quality assessment
            </p>
          </div>

          <button
            type="button"
            onClick={onEvaluate}
            className="inline-flex items-center gap-2 rounded-md border border-zinc-800 px-2.5 py-1.5 text-xs text-zinc-400 transition hover:bg-zinc-900 hover:text-zinc-200"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Re-evaluate
          </button>
        </div>
      </header>

      <div className="p-5">
        <div className="grid gap-4 md:grid-cols-[180px_1fr]">
          <div className="flex flex-col items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900/30 p-5">
            <div
              className={`text-4xl font-semibold ${scoreClass(
                evaluation.overallScore,
              )}`}
            >
              {Math.round(evaluation.overallScore * 100)}
            </div>

            <div className="mt-1 text-xs text-zinc-600">
              overall score
            </div>

            <div
              className={`mt-3 text-xs font-medium ${scoreClass(
                evaluation.overallScore,
              )}`}
            >
              {scoreLabel(evaluation.overallScore)}
            </div>

            <div className="mt-3">
              {evaluation.passed ? (
                <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Passed
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] text-red-400">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  Failed
                </span>
              )}
            </div>
          </div>

          <div className="space-y-2">
            {evaluation.metrics.map((metric) => {
              const isExpanded = expanded === metric.id;

              return (
                <div
                  key={metric.id}
                  className="rounded-md border border-zinc-800"
                >
                  <button
                    type="button"
                    onClick={() =>
                      setExpanded(
                        isExpanded ? null : metric.id,
                      )
                    }
                    className="flex w-full items-center gap-3 px-3 py-3 text-left"
                  >
                    <Star
                      className={`h-3.5 w-3.5 ${scoreClass(
                        metric.score,
                      )}`}
                    />

                    <span className="flex-1 text-xs font-medium text-zinc-300">
                      {metric.name}
                    </span>

                    <span
                      className={`text-xs font-medium ${scoreClass(
                        metric.score,
                      )}`}
                    >
                      {Math.round(metric.score * 100)}
                    </span>

                    {isExpanded ? (
                      <ChevronUp className="h-3.5 w-3.5 text-zinc-600" />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5 text-zinc-600" />
                    )}
                  </button>

                  <div className="px-3 pb-3">
                    <div className="h-1 overflow-hidden rounded-full bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-current transition-all"
                        style={{
                          width: `${Math.max(
                            0,
                            Math.min(100, metric.score * 100),
                          )}%`,
                        }}
                      />
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-zinc-800 px-3 py-3">
                      {metric.description && (
                        <p className="text-xs leading-5 text-zinc-500">
                          {metric.description}
                        </p>
                      )}

                      {metric.details && (
                        <div className="mt-3 rounded-md bg-zinc-900/50 p-3 text-xs leading-5 text-zinc-500">
                          {metric.details}
                        </div>
                      )}

                      {metric.threshold !== undefined && (
                        <div className="mt-2 text-[10px] text-zinc-700">
                          Threshold:{" "}
                          {Math.round(metric.threshold * 100)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {evaluation.summary && (
          <div className="mt-5 flex gap-3 rounded-md border border-zinc-800 bg-zinc-900/30 p-4">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-zinc-500" />

            <p className="text-xs leading-5 text-zinc-500">
              {evaluation.summary}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}