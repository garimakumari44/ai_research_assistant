"use client";

import {
  CheckCircle2,
  Search,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";

import type {
  RetrievalResponse,
  RetrievalResult,
} from "@/types/retrieval";

import { EvidenceCard } from "./evidence-card";
import { RetrievalStatus } from "./retrieval-status";

interface RetrievalResultsProps {
  /**
   * Canonical response returned by:
   *
   * POST /retrieval/search
   */
  data?: RetrievalResponse | null;

  /**
   * React Query loading state.
   */
  isLoading?: boolean;

  /**
   * React Query error state.
   */
  isError?: boolean;

  /**
   * Retrieval error.
   */
  error?: Error | null;

  /**
   * Called when a retrieval result is selected.
   */
  onSelect?: (
    result: RetrievalResult,
  ) => void;

  /**
   * Optional retrieval configuration callback.
   */
  onConfigure?: () => void;

  /**
   * Whether to render the results header.
   */
  showHeader?: boolean;
}

export function RetrievalResults({
  data = null,
  isLoading = false,
  isError = false,
  error = null,
  onSelect,
  onConfigure,
  showHeader = true,
}: RetrievalResultsProps) {
  const results =
    data?.results ?? [];

  const evidence =
    data?.evidence ?? [];

  const isEmpty =
    Boolean(data) &&
    !isLoading &&
    !isError &&
    results.length === 0 &&
    evidence.length === 0;

  return (
    <section className="space-y-4">
      {/* ---------------------------------------------------------------- */}
      {/* Status                                                           */}
      {/* ---------------------------------------------------------------- */}

      <RetrievalStatus
        isLoading={isLoading}
        isError={isError}
        error={error}
        isEmpty={isEmpty}
        resultCount={results.length}
        evidenceCount={evidence.length}
        retrievalMode={
          data?.retrieval_mode
        }
      />

      {/* ---------------------------------------------------------------- */}
      {/* Stop here while loading/error/empty                              */}
      {/* ---------------------------------------------------------------- */}

      {(isLoading ||
        isError ||
        isEmpty ||
        !data) && (
        !isLoading &&
        !isError &&
        !data ? (
          <EmptyInitialState />
        ) : null
      )}

      {!data ||
      isLoading ||
      isError ||
      isEmpty ? null : (
        <>
          {/* ------------------------------------------------------------ */}
          {/* Header                                                       */}
          {/* ------------------------------------------------------------ */}

          {showHeader && (
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />

                  <h2 className="text-sm font-semibold text-zinc-200">
                    Retrieved Knowledge
                  </h2>

                  <span className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] font-medium text-zinc-500">
                    {data.total}
                  </span>
                </div>

                <p className="mt-1 truncate text-xs text-zinc-600">
                  {data.query}
                </p>

                <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-wider text-zinc-600">
                  <span>
                    {data.retrieval_mode}
                  </span>

                  <span className="text-zinc-800">
                    •
                  </span>

                  <span>
                    Top K {data.top_k}
                  </span>

                  <span className="text-zinc-800">
                    •
                  </span>

                  <span>
                    {results.length} candidates
                  </span>

                  {evidence.length > 0 && (
                    <>
                      <span className="text-zinc-800">
                        •
                      </span>

                      <span>
                        {evidence.length} evidence
                      </span>
                    </>
                  )}
                </div>
              </div>

              {onConfigure && (
                <button
                  type="button"
                  onClick={onConfigure}
                  className="flex shrink-0 items-center gap-2 rounded-md border border-white/10 px-2.5 py-1.5 text-xs text-zinc-500 transition-colors hover:border-white/20 hover:text-zinc-300"
                >
                  <SlidersHorizontal className="h-3.5 w-3.5" />

                  Retrieval
                </button>
              )}
            </div>
          )}

          {/* ------------------------------------------------------------ */}
          {/* Query analysis                                               */}
          {/* ------------------------------------------------------------ */}

          {data.query_analysis && (
            <QueryAnalysisPanel
              analysis={data.query_analysis}
            />
          )}

          {/* ------------------------------------------------------------ */}
          {/* Query classification                                          */}
          {/* ------------------------------------------------------------ */}

          {data.query_classification && (
            <QueryClassificationPanel
              classification={
                data.query_classification
              }
            />
          )}

          {/* ------------------------------------------------------------ */}
          {/* Retrieved results                                             */}
          {/* ------------------------------------------------------------ */}

          {results.length > 0 && (
            <div className="space-y-3">
              {results.map(
                (result, index) => {
                  /**
                   * Prefer evidence attached directly to
                   * the RetrievalResult.
                   *
                   * Otherwise try to match response-level
                   * evidence by chunk_id.
                   */
                  const attachedEvidence =
                    result.evidence ??
                    evidence.find(
                      (item) =>
                        item.provenance
                          .chunk_id ===
                        result.chunk_id,
                    ) ??
                    null;

                  return (
                    <EvidenceCard
                      key={result.chunk_id}
                      result={result}
                      evidence={
                        attachedEvidence
                      }
                      index={index}
                      onSelect={onSelect}
                    />
                  );
                },
              )}
            </div>
          )}

          {/* ------------------------------------------------------------ */}
          {/* Response-level evidence                                      */}
          {/* ------------------------------------------------------------ */}

          {evidence.length > 0 && (
            <EvidenceSummary
              evidenceCount={
                evidence.length
              }
            />
          )}

          {/* ------------------------------------------------------------ */}
          {/* Metadata                                                     */}
          {/* ------------------------------------------------------------ */}

          {Object.keys(data.metadata)
            .length > 0 && (
            <details className="rounded-lg border border-white/5 bg-black/10">
              <summary className="cursor-pointer px-4 py-3 text-[10px] uppercase tracking-wider text-zinc-700 transition-colors hover:text-zinc-400">
                Retrieval metadata
              </summary>

              <pre className="max-h-80 overflow-auto border-t border-white/5 p-4 text-[10px] leading-5 text-zinc-600">
                {JSON.stringify(
                  data.metadata,
                  null,
                  2,
                )}
              </pre>
            </details>
          )}
        </>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Initial state                                                               */
/* -------------------------------------------------------------------------- */

function EmptyInitialState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-white/10 bg-white/[0.01] px-6 py-12 text-center">
      <Search className="mb-3 h-5 w-5 text-zinc-700" />

      <p className="text-sm font-medium text-zinc-500">
        No retrieval performed
      </p>

      <p className="mt-1 max-w-md text-xs leading-5 text-zinc-700">
        Enter a research question to search the indexed knowledge base.
      </p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Query analysis                                                              */
/* -------------------------------------------------------------------------- */

function QueryAnalysisPanel({
  analysis,
}: {
  analysis: NonNullable<
    RetrievalResponse["query_analysis"]
  >;
}) {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <div className="mb-4 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-blue-400" />

        <h3 className="text-sm font-medium text-zinc-300">
          Query analysis
        </h3>
      </div>

      <div className="space-y-4">
        {/* Normalized query */}

        {analysis.normalized_query && (
          <div>
            <div className="mb-1 text-[9px] uppercase tracking-wider text-zinc-700">
              Normalized query
            </div>

            <p className="text-xs leading-5 text-zinc-500">
              {analysis.normalized_query}
            </p>
          </div>
        )}

        {/* Keywords */}

        {analysis.keywords.length > 0 && (
          <TagGroup
            label="Keywords"
            values={analysis.keywords}
          />
        )}

        {/* Entities */}

        {analysis.entities.length > 0 && (
          <TagGroup
            label="Entities"
            values={analysis.entities}
          />
        )}

        {/* Concepts */}

        {analysis.concepts.length > 0 && (
          <TagGroup
            label="Concepts"
            values={analysis.concepts}
          />
        )}

        {/* Search requirements */}

        <div className="flex flex-wrap gap-2">
          <SearchRequirement
            label="Semantic search"
            enabled={
              analysis.requires_semantic_search
            }
          />

          <SearchRequirement
            label="Keyword search"
            enabled={
              analysis.requires_keyword_search
            }
          />
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Query classification                                                        */
/* -------------------------------------------------------------------------- */

function QueryClassificationPanel({
  classification,
}: {
  classification: NonNullable<
    RetrievalResponse["query_classification"]
  >;
}) {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <h3 className="mb-4 text-sm font-medium text-zinc-300">
        Query classification
      </h3>

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <ClassificationValue
          label="Type"
          value={
            classification.query_type
          }
        />

        <ClassificationValue
          label="Intent"
          value={classification.intent}
        />

        <ClassificationValue
          label="Domain"
          value={
            classification.domain ??
            "General"
          }
        />

        <ClassificationValue
          label="Confidence"
          value={`${(
            classification.confidence *
            100
          ).toFixed(1)}%`}
        />
      </div>

      {classification.labels.length >
        0 && (
        <div className="mt-4">
          <TagGroup
            label="Labels"
            values={
              classification.labels
            }
          />
        </div>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Evidence summary                                                            */
/* -------------------------------------------------------------------------- */

function EvidenceSummary({
  evidenceCount,
}: {
  evidenceCount: number;
}) {
  return (
    <div className="rounded-lg border border-emerald-500/10 bg-emerald-500/[0.03] px-4 py-3">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />

        <span className="text-xs font-medium text-zinc-300">
          Evidence collected
        </span>
      </div>

      <p className="mt-1 text-xs text-zinc-600">
        {evidenceCount} evidence{" "}
        {evidenceCount === 1
          ? "item"
          : "items"}{" "}
        returned with provenance.
      </p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Small UI helpers                                                            */
/* -------------------------------------------------------------------------- */

function TagGroup({
  label,
  values,
}: {
  label: string;
  values: string[];
}) {
  return (
    <div>
      <div className="mb-2 text-[9px] uppercase tracking-wider text-zinc-700">
        {label}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {values.map(
          (value, index) => (
            <span
              key={`${value}-${index}`}
              className="rounded-md border border-white/5 bg-black/20 px-2 py-1 text-[10px] text-zinc-500"
            >
              {value}
            </span>
          ),
        )}
      </div>
    </div>
  );
}

function SearchRequirement({
  label,
  enabled,
}: {
  label: string;
  enabled: boolean;
}) {
  return (
    <span
      className={`rounded-md border px-2 py-1 text-[10px] ${
        enabled
          ? "border-emerald-500/10 bg-emerald-500/5 text-emerald-400/70"
          : "border-white/5 bg-black/10 text-zinc-700"
      }`}
    >
      {label}:{" "}
      {enabled ? "enabled" : "disabled"}
    </span>
  );
}

function ClassificationValue({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-md border border-white/5 bg-black/20 px-3 py-2.5">
      <div className="text-[9px] uppercase tracking-wider text-zinc-700">
        {label}
      </div>

      <div className="mt-1 truncate text-xs font-medium text-zinc-400">
        {value}
      </div>
    </div>
  );
}