"use client";

import {
  AlertCircle,
  CheckCircle2,
  Circle,
  FileCheck2,
  Link2,
} from "lucide-react";

import ConfidenceMeter from "./confidence-meter";

export interface EvidenceItem {
  id?: string;
  title?: string;
  source?: string;
  relevance?: number;
  quality?: number;
  support?: number;
  supported?: boolean;
  reason?: string;
}

interface EvidenceEvaluationProps {
  evidence: EvidenceItem[];
  className?: string;
}

function EvidenceRow({ item }: { item: EvidenceItem }) {
  const supported = item.supported;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
      <div className="flex items-start gap-3">
        <div className="mt-0.5">
          {supported === true ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          ) : supported === false ? (
            <AlertCircle className="h-4 w-4 text-amber-400" />
          ) : (
            <Circle className="h-4 w-4 text-slate-600" />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-slate-200">
            {item.title ?? "Evidence"}
          </div>

          {item.source && (
            <div className="mt-1 flex items-center gap-1 text-xs text-slate-500">
              <Link2 className="h-3 w-3" />
              {item.source}
            </div>
          )}

          {item.reason && (
            <p className="mt-2 text-xs leading-5 text-slate-400">
              {item.reason}
            </p>
          )}

          {(item.relevance !== undefined ||
            item.quality !== undefined ||
            item.support !== undefined) && (
            <div className="mt-3 space-y-2">
              {item.relevance !== undefined && (
                <ConfidenceMeter
                  value={item.relevance}
                  label="Relevance"
                  size="sm"
                />
              )}

              {item.quality !== undefined && (
                <ConfidenceMeter
                  value={item.quality}
                  label="Quality"
                  size="sm"
                />
              )}

              {item.support !== undefined && (
                <ConfidenceMeter
                  value={item.support}
                  label="Support"
                  size="sm"
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function EvidenceEvaluation({
  evidence,
  className = "",
}: EvidenceEvaluationProps) {
  const supportedCount = evidence.filter(
    (item) => item.supported === true
  ).length;

  return (
    <section
      className={[
        "rounded-xl border border-slate-800 bg-slate-950/40",
        className,
      ].join(" ")}
    >
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <FileCheck2 className="h-4 w-4 text-cyan-400" />

          <h3 className="text-sm font-semibold text-slate-200">
            Evidence Evaluation
          </h3>
        </div>

        <span className="text-xs text-slate-500">
          {supportedCount}/{evidence.length} supported
        </span>
      </div>

      <div className="space-y-2 p-4">
        {evidence.length === 0 ? (
          <div className="py-6 text-center text-sm text-slate-500">
            No evidence evaluated yet.
          </div>
        ) : (
          evidence.map((item, index) => (
            <EvidenceRow
              key={item.id ?? index}
              item={item}
            />
          ))
        )}
      </div>
    </section>
  );
}

export default EvidenceEvaluation;