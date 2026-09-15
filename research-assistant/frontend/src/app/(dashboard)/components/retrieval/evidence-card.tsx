"use client";

import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileText,
  ShieldCheck,
} from "lucide-react";

import { useState } from "react";

import type {
  Evidence,
  RetrievalResult,
} from "@/types/retrieval";

import { ChunkPreview } from "./chunk-preview";
import { SourceCitation } from "./source-citation";

interface EvidenceCardProps {
  /**
   * Retrieval result associated with this evidence.
   */
  result: RetrievalResult;

  /**
   * Final evidence representation.
   */
  evidence?: Evidence | null;

  /**
   * Display position in the ranked list.
   */
  index?: number;

  /**
   * Called when the result is selected.
   */
  onSelect?: (
    result: RetrievalResult,
  ) => void;
}

function formatScore(
  value?: number | null,
): string {
  if (
    value === undefined ||
    value === null
  ) {
    return "—";
  }

  return `${(value * 100).toFixed(1)}%`;
}

export function EvidenceCard({
  result,
  evidence,
  index,
  onSelect,
}: EvidenceCardProps) {
  const [expanded, setExpanded] =
    useState(false);

  /**
   * Backend ranking values.
   */
  const relevance =
    result.score;

  const vectorScore =
    result.vector_score;

  const keywordScore =
    result.keyword_score;

  const rerankScore =
    result.rerank_score;

  const evidenceScore =
    evidence?.score;

  const rank =
    evidence?.rank ??
    result.rank ??
    index !== undefined
      ? index + 1
      : null;

  const provenance =
    evidence?.provenance ??
    result.provenance;

  const metadata =
    evidence?.metadata ??
    result.metadata;

  return (
    <article
      className="group rounded-lg border border-white/10 bg-white/[0.02] p-4 transition-colors hover:border-white/20 hover:bg-white/[0.04]"
      onClick={() => onSelect?.(result)}
    >
      {/* Header */}

      <div className="mb-3 flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-2.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-500/10 text-blue-400">
            <FileText className="h-4 w-4" />
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              {rank != null && (
                <span className="text-xs font-medium text-zinc-600">
                  #{rank}
                </span>
              )}

              <h3 className="text-sm font-medium text-zinc-200">
                Retrieved evidence
              </h3>
            </div>

            <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-zinc-600">
              <span>
                {result.retrieval_method}
              </span>

              {provenance?.section && (
                <>
                  <span className="text-zinc-800">
                    •
                  </span>

                  <span className="max-w-[240px] truncate">
                    {provenance.section}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Score */}

        <div className="shrink-0 text-right">
          <div className="text-sm font-semibold text-zinc-200">
            {formatScore(
              evidenceScore ??
                relevance,
            )}
          </div>

          <div className="text-[9px] uppercase tracking-wider text-zinc-600">
            {evidence
              ? "evidence"
              : "relevance"}
          </div>
        </div>
      </div>

      {/* Chunk */}

      <ChunkPreview
        result={result}
        evidence={evidence}
        maxLength={
          expanded ? 2400 : 650
        }
      />

      {/* Score metrics */}

      <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <ScoreMetric
          label="Relevance"
          value={formatScore(relevance)}
        />

        <ScoreMetric
          label="Vector"
          value={formatScore(vectorScore)}
        />

        <ScoreMetric
          label="Keyword"
          value={formatScore(keywordScore)}
        />

        <ScoreMetric
          label="Rerank"
          value={formatScore(rerankScore)}
        />
      </div>

      {/* Footer */}

      <div className="mt-4 flex items-center justify-between gap-4">
        <SourceCitation
          result={result}
          evidence={evidence}
        />

        <div className="flex shrink-0 items-center gap-3">
          {/* Expand */}

          <button
            type="button"
            className="flex items-center gap-1 text-xs text-zinc-600 transition-colors hover:text-zinc-300"
            onClick={(event) => {
              event.stopPropagation();

              setExpanded(
                (value) => !value,
              );
            }}
          >
            {expanded ? (
              <>
                Collapse

                <ChevronUp className="h-3 w-3" />
              </>
            ) : (
              <>
                Expand

                <ChevronDown className="h-3 w-3" />
              </>
            )}
          </button>

          {/* Open */}

          {onSelect && (
            <button
              type="button"
              className="flex items-center gap-1 text-xs text-zinc-500 opacity-0 transition-opacity hover:text-zinc-200 group-hover:opacity-100"
              onClick={(event) => {
                event.stopPropagation();

                onSelect(result);
              }}
            >
              Open

              <ExternalLink className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Provenance */}

      {provenance && (
        <div className="mt-3 flex items-center gap-2 border-t border-white/5 pt-3 text-[10px] text-zinc-600">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500/70" />

          <span>
            Provenance available
          </span>

          {provenance.page != null && (
            <>
              <span className="text-zinc-800">
                •
              </span>

              <span>
                Page {provenance.page}
              </span>
            </>
          )}
        </div>
      )}

      {/* Metadata */}

      {Object.keys(metadata).length > 0 && (
        <details
          className="mt-3 border-t border-white/5 pt-3"
          onClick={(event) =>
            event.stopPropagation()
          }
        >
          <summary className="cursor-pointer text-[10px] uppercase tracking-wider text-zinc-700 transition-colors hover:text-zinc-400">
            Metadata
          </summary>

          <pre className="mt-2 max-h-60 overflow-auto rounded-md bg-black/30 p-3 text-[10px] leading-5 text-zinc-600">
            {JSON.stringify(
              metadata,
              null,
              2,
            )}
          </pre>
        </details>
      )}
    </article>
  );
}

function ScoreMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-white/5 bg-black/20 px-2.5 py-2">
      <div className="text-[9px] uppercase tracking-wider text-zinc-700">
        {label}
      </div>

      <div className="mt-0.5 text-xs font-medium text-zinc-400">
        {value}
      </div>
    </div>
  );
}