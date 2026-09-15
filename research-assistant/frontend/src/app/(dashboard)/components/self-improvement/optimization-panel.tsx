"use client";

import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  FlaskConical,
  Gauge,
  Lightbulb,
  Loader2,
  Play,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  X,
} from "lucide-react";

import { useState } from "react";

export type OptimizationStatus =
  | "proposed"
  | "testing"
  | "approved"
  | "rejected"
  | "deployed";

export interface OptimizationProposal {
  id: string;
  title: string;
  description: string;
  strategy: string;
  expectedImprovement?: number;
  confidence?: number;
  status: OptimizationStatus;
  affectedComponents?: string[];
  rationale?: string;
  risks?: string[];
}

interface OptimizationPanelProps {
  proposals?: OptimizationProposal[];
  loading?: boolean;
  optimizing?: boolean;
  onGenerate?: () => void;
  onTest?: (proposal: OptimizationProposal) => void;
  onApprove?: (proposal: OptimizationProposal) => void;
  onReject?: (proposal: OptimizationProposal) => void;
}

const statusStyles: Record<OptimizationStatus, string> = {
  proposed:
    "border-blue-500/20 bg-blue-500/10 text-blue-400",
  testing:
    "border-amber-500/20 bg-amber-500/10 text-amber-400",
  approved:
    "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
  rejected:
    "border-red-500/20 bg-red-500/10 text-red-400",
  deployed:
    "border-purple-500/20 bg-purple-500/10 text-purple-400",
};

export function OptimizationPanel({
  proposals = [],
  loading = false,
  optimizing = false,
  onGenerate,
  onTest,
  onApprove,
  onReject,
}: OptimizationPanelProps) {
  const [expanded, setExpanded] = useState<string | null>(
    null,
  );

  if (loading) {
    return (
      <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-6">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading optimization proposals...
        </div>
      </div>
    );
  }

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-950">
      <header className="flex items-center gap-3 border-b border-zinc-800 px-5 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900">
          <SlidersHorizontal className="h-4 w-4 text-zinc-500" />
        </div>

        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-zinc-200">
            Optimization
          </h2>

          <p className="mt-1 text-xs text-zinc-600">
            Review proposed improvements to the research pipeline.
          </p>
        </div>

        <button
          type="button"
          disabled={optimizing}
          onClick={onGenerate}
          className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {optimizing ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Sparkles className="h-3.5 w-3.5" />
          )}

          Generate proposals
        </button>
      </header>

      <div className="p-5">
        <div className="mb-5 grid gap-3 md:grid-cols-3">
          <OptimizationStat
            icon={Lightbulb}
            label="Proposals"
            value={proposals.length.toString()}
          />

          <OptimizationStat
            icon={FlaskConical}
            label="Testing"
            value={proposals
              .filter((item) => item.status === "testing")
              .length.toString()}
          />

          <OptimizationStat
            icon={ShieldCheck}
            label="Approved"
            value={proposals
              .filter(
                (item) =>
                  item.status === "approved" ||
                  item.status === "deployed",
              )
              .length.toString()}
          />
        </div>

        {proposals.length === 0 ? (
          <div className="rounded-md border border-dashed border-zinc-800 p-8 text-center">
            <Gauge className="mx-auto h-7 w-7 text-zinc-700" />

            <h3 className="mt-3 text-sm font-medium text-zinc-400">
              No optimization proposals
            </h3>

            <p className="mx-auto mt-1 max-w-md text-xs leading-5 text-zinc-600">
              Generate proposals from evaluation results,
              execution traces, feedback, and strategy performance.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {proposals.map((proposal) => {
              const isExpanded = expanded === proposal.id;

              return (
                <div
                  key={proposal.id}
                  className="rounded-lg border border-zinc-800 bg-zinc-950"
                >
                  <button
                    type="button"
                    onClick={() =>
                      setExpanded(
                        isExpanded ? null : proposal.id,
                      )
                    }
                    className="flex w-full items-start gap-3 px-4 py-4 text-left"
                  >
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900">
                      <Lightbulb className="h-4 w-4 text-zinc-500" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-medium text-zinc-300">
                          {proposal.title}
                        </h3>

                        <span
                          className={`rounded-full border px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide ${statusStyles[proposal.status]}`}
                        >
                          {proposal.status}
                        </span>
                      </div>

                      <p className="mt-1 text-xs leading-5 text-zinc-600">
                        {proposal.description}
                      </p>

                      <div className="mt-3 flex flex-wrap items-center gap-4 text-[10px] text-zinc-600">
                        {proposal.expectedImprovement !==
                          undefined && (
                          <span className="text-emerald-400">
                            +{proposal.expectedImprovement.toFixed(
                              1,
                            )}
                            % expected
                          </span>
                        )}

                        {proposal.confidence !== undefined && (
                          <span>
                            {Math.round(
                              proposal.confidence * 100,
                            )}
                            % confidence
                          </span>
                        )}

                        {proposal.strategy && (
                          <span>
                            Strategy: {proposal.strategy}
                          </span>
                        )}
                      </div>
                    </div>

                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 shrink-0 text-zinc-600" />
                    ) : (
                      <ChevronDown className="h-4 w-4 shrink-0 text-zinc-600" />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="border-t border-zinc-800 p-4">
                      {proposal.rationale && (
                        <div className="mb-4">
                          <h4 className="mb-2 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
                            Rationale
                          </h4>

                          <p className="text-xs leading-5 text-zinc-500">
                            {proposal.rationale}
                          </p>
                        </div>
                      )}

                      {proposal.affectedComponents &&
                        proposal.affectedComponents.length >
                          0 && (
                          <div className="mb-4">
                            <h4 className="mb-2 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
                              Affected components
                            </h4>

                            <div className="flex flex-wrap gap-2">
                              {proposal.affectedComponents.map(
                                (component) => (
                                  <span
                                    key={component}
                                    className="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 font-mono text-[10px] text-zinc-500"
                                  >
                                    {component}
                                  </span>
                                ),
                              )}
                            </div>
                          </div>
                        )}

                      {proposal.risks &&
                        proposal.risks.length > 0 && (
                          <div className="mb-4 rounded-md border border-amber-500/10 bg-amber-500/5 p-3">
                            <div className="flex gap-2">
                              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />

                              <div>
                                <h4 className="text-[10px] font-medium uppercase tracking-wider text-amber-400">
                                  Risks
                                </h4>

                                <ul className="mt-2 space-y-1">
                                  {proposal.risks.map((risk) => (
                                    <li
                                      key={risk}
                                      className="text-xs leading-5 text-zinc-500"
                                    >
                                      • {risk}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </div>
                          </div>
                        )}

                      <div className="flex flex-wrap items-center gap-2 border-t border-zinc-800 pt-4">
                        {proposal.status === "proposed" && (
                          <>
                            <button
                              type="button"
                              onClick={() => onTest?.(proposal)}
                              className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-blue-500"
                            >
                              <Play className="h-3.5 w-3.5" />
                              Test
                            </button>

                            <button
                              type="button"
                              onClick={() =>
                                onReject?.(proposal)
                              }
                              className="inline-flex items-center gap-1.5 rounded-md border border-zinc-800 px-3 py-2 text-xs text-zinc-500 transition hover:bg-zinc-900 hover:text-red-400"
                            >
                              <X className="h-3.5 w-3.5" />
                              Reject
                            </button>
                          </>
                        )}

                        {proposal.status === "testing" && (
                          <button
                            type="button"
                            onClick={() =>
                              onApprove?.(proposal)
                            }
                            className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-emerald-500"
                          >
                            <Check className="h-3.5 w-3.5" />
                            Approve
                          </button>
                        )}

                        {(proposal.status === "approved" ||
                          proposal.status === "deployed") && (
                          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
                            <ShieldCheck className="h-3.5 w-3.5" />
                            {proposal.status === "deployed"
                              ? "Deployed"
                              : "Approved for deployment"}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

function OptimizationStat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Lightbulb;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-zinc-800 bg-zinc-900/30 p-3">
      <Icon className="h-4 w-4 text-zinc-600" />

      <div>
        <p className="text-[10px] uppercase tracking-wider text-zinc-600">
          {label}
        </p>

        <p className="mt-0.5 text-sm font-semibold text-zinc-300">
          {value}
        </p>
      </div>
    </div>
  );
}