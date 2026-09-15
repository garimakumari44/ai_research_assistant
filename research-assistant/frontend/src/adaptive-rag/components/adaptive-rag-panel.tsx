"use client";

import {
  Activity,
  BrainCircuit,
  ChevronDown,
  ChevronUp,
  Gauge,
  Layers3,
  Search,
} from "lucide-react";
import { useState } from "react";

import type { RAGStrategy } from "../types";

import ConfidenceMeter from "./confidence-meter";
import EvidenceEvaluation, {
  type EvidenceItem,
} from "./evidence-evaluation";
import RAGTrace, {
  type RAGTraceStep,
} from "./rag-trace";
import ReasoningStatus from "./reasoning-status";
import RetrievalAttempt, {
  type RetrievalAttemptData,
} from "./retrieval-attempt";
import StrategyBadge from "./strategy-badge";
import StrategySelector from "./strategy-selector";

export interface AdaptiveRAGPanelProps {
  strategy?: RAGStrategy | string;
  status?: string;
  confidence?: number;
  trace?: RAGTraceStep[];
  retrievalAttempts?: RetrievalAttemptData[];
  evidence?: EvidenceItem[];
  onStrategyChange?: (strategy: RAGStrategy | string) => void;
  collapsible?: boolean;
  defaultExpanded?: boolean;
  className?: string;
}

export function AdaptiveRAGPanel({
  strategy = "auto",
  status = "idle",
  confidence = 0,
  trace = [],
  retrievalAttempts = [],
  evidence = [],
  onStrategyChange,
  collapsible = false,
  defaultExpanded = true,
  className = "",
}: AdaptiveRAGPanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const isRunning = [
    "planning",
    "retrieving",
    "evaluating",
    "reasoning",
    "generating",
  ].includes(status.toLowerCase());

  return (
    <section
      className={[
        "overflow-hidden rounded-xl border border-slate-800",
        "bg-slate-950/80 shadow-xl shadow-black/10",
        className,
      ].join(" ")}
    >
      <div className="flex items-center gap-3 border-b border-slate-800 px-4 py-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">
          <BrainCircuit className="h-5 w-5 text-cyan-400" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-100">
              Adaptive RAG
            </h2>

            {isRunning && (
              <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
            )}
          </div>

          <p className="mt-0.5 text-xs text-slate-500">
            Dynamic retrieval and reasoning controller
          </p>
        </div>

        <StrategyBadge
          strategy={strategy}
          size="sm"
        />

        <ReasoningStatus
          status={status}
          compact
        />

        {collapsible && (
          <button
            type="button"
            onClick={() => setExpanded((previous) => !previous)}
            className="rounded-md p-1.5 text-slate-500 hover:bg-slate-900 hover:text-slate-300"
            aria-label={
              expanded
                ? "Collapse adaptive RAG panel"
                : "Expand adaptive RAG panel"
            }
          >
            {expanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        )}
      </div>

      {expanded && (
        <div className="space-y-4 p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
              <div className="mb-2 flex items-center gap-2">
                <Activity className="h-4 w-4 text-cyan-400" />
                <span className="text-xs text-slate-500">
                  Status
                </span>
              </div>

              <ReasoningStatus status={status} />
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
              <div className="mb-2 flex items-center gap-2">
                <Gauge className="h-4 w-4 text-emerald-400" />
                <span className="text-xs text-slate-500">
                  Confidence
                </span>
              </div>

              <ConfidenceMeter
                value={confidence}
                size="sm"
              />
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3">
              <div className="mb-2 flex items-center gap-2">
                <Search className="h-4 w-4 text-violet-400" />
                <span className="text-xs text-slate-500">
                  Retrieval Attempts
                </span>
              </div>

              <div className="text-lg font-semibold text-slate-200">
                {retrievalAttempts.length}
              </div>
            </div>
          </div>

          {onStrategyChange && (
            <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-4">
              <StrategySelector
                value={strategy}
                onChange={onStrategyChange}
              />
            </div>
          )}

          {retrievalAttempts.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <Layers3 className="h-4 w-4 text-cyan-400" />
                <h3 className="text-sm font-semibold text-slate-200">
                  Retrieval Attempts
                </h3>
              </div>

              <div className="space-y-2">
                {retrievalAttempts.map((attempt, index) => (
                  <RetrievalAttempt
                    key={attempt.id ?? index}
                    attempt={attempt}
                    index={index}
                  />
                ))}
              </div>
            </div>
          )}

          {evidence.length > 0 && (
            <EvidenceEvaluation evidence={evidence} />
          )}

          <RAGTrace steps={trace} />
        </div>
      )}
    </section>
  );
}

export default AdaptiveRAGPanel;