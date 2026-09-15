"use client";

import {
  CheckCircle2,
  ChevronDown,
  Clock3,
  Database,
  FileText,
  XCircle,
} from "lucide-react";
import { useState } from "react";

import ConfidenceMeter from "./confidence-meter";

export interface RetrievalAttemptData {
  id?: string;
  query: string;
  strategy?: string;
  status?: "success" | "failed" | "pending" | string;
  result_count?: number;
  retrieved_count?: number;
  latency_ms?: number;
  confidence?: number;
  sources?: Array<{
    id?: string;
    title?: string;
    score?: number;
  }>;
}

interface RetrievalAttemptProps {
  attempt: RetrievalAttemptData;
  index?: number;
  expanded?: boolean;
  onToggle?: () => void;
}

export function RetrievalAttempt({
  attempt,
  index,
  expanded: controlledExpanded,
  onToggle,
}: RetrievalAttemptProps) {
  const [internalExpanded, setInternalExpanded] = useState(false);

  const expanded =
    controlledExpanded !== undefined
      ? controlledExpanded
      : internalExpanded;

  const toggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalExpanded((previous) => !previous);
    }
  };

  const status = attempt.status ?? "success";
  const successful = status === "success";

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60">
      <button
        type="button"
        onClick={toggle}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <div
          className={[
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
            successful
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-red-500/10 text-red-400",
          ].join(" ")}
        >
          {successful ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <XCircle className="h-4 w-4" />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {index !== undefined && (
              <span className="text-xs font-semibold text-slate-500">
                #{index + 1}
              </span>
            )}

            <span className="truncate text-sm font-medium text-slate-200">
              {attempt.query}
            </span>
          </div>

          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
            {attempt.strategy && (
              <span>{attempt.strategy}</span>
            )}

            {attempt.retrieved_count !== undefined && (
              <span className="flex items-center gap-1">
                <Database className="h-3 w-3" />
                {attempt.retrieved_count} results
              </span>
            )}

            {attempt.latency_ms !== undefined && (
              <span className="flex items-center gap-1">
                <Clock3 className="h-3 w-3" />
                {attempt.latency_ms}ms
              </span>
            )}
          </div>
        </div>

        <ChevronDown
          className={[
            "h-4 w-4 shrink-0 text-slate-500 transition-transform",
            expanded ? "rotate-180" : "",
          ].join(" ")}
        />
      </button>

      {expanded && (
        <div className="border-t border-slate-800 px-4 py-4">
          {attempt.confidence !== undefined && (
            <div className="mb-4">
              <ConfidenceMeter value={attempt.confidence} />
            </div>
          )}

          {attempt.sources && attempt.sources.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Retrieved Sources
              </div>

              <div className="space-y-2">
                {attempt.sources.map((source, sourceIndex) => (
                  <div
                    key={source.id ?? sourceIndex}
                    className="flex items-center gap-2 rounded-md bg-slate-900/70 px-3 py-2"
                  >
                    <FileText className="h-3.5 w-3.5 text-cyan-400" />

                    <span className="min-w-0 flex-1 truncate text-xs text-slate-300">
                      {source.title ?? `Source ${sourceIndex + 1}`}
                    </span>

                    {source.score !== undefined && (
                      <span className="text-xs font-medium text-slate-500">
                        {Math.round(
                          source.score <= 1
                            ? source.score * 100
                            : source.score
                        )}
                        %
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default RetrievalAttempt;