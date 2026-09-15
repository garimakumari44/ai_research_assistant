"use client";

import {
  AlertCircle,
  Check,
  Database,
  FileSearch,
  Loader2,
  Search,
} from "lucide-react";

interface RetrievalStatusProps {
  /**
   * Whether the retrieval mutation is running.
   */
  isLoading?: boolean;

  /**
   * Whether retrieval failed.
   */
  isError?: boolean;

  /**
   * Retrieval error.
   */
  error?: Error | null;

  /**
   * Whether retrieval completed but returned no results.
   */
  isEmpty?: boolean;

  /**
   * Number of results returned.
   */
  resultCount?: number;

  /**
   * Number of evidence items returned.
   */
  evidenceCount?: number;

  /**
   * Retrieval mode returned by the backend.
   */
  retrievalMode?: string | null;
}

export function RetrievalStatus({
  isLoading = false,
  isError = false,
  error = null,
  isEmpty = false,
  resultCount = 0,
  evidenceCount = 0,
  retrievalMode = null,
}: RetrievalStatusProps) {
  /* ---------------------------------------------------------------------- */
  /* Error                                                                  */
  /* ---------------------------------------------------------------------- */

  if (isError) {
    return (
      <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-red-500/10">
            <AlertCircle className="h-4 w-4 text-red-400" />
          </div>

          <div className="min-w-0">
            <p className="text-sm font-medium text-red-300">
              Retrieval failed
            </p>

            <p className="mt-1 text-xs leading-5 text-zinc-500">
              {error?.message ??
                "Unable to retrieve knowledge from the knowledge base."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Loading                                                                */
  /* ---------------------------------------------------------------------- */

  if (isLoading) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-500/10">
            <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
          </div>

          <div>
            <p className="text-sm font-medium text-zinc-300">
              Retrieving knowledge
            </p>

            <p className="mt-1 text-xs leading-5 text-zinc-600">
              Searching indexed research knowledge and ranking relevant chunks.
            </p>
          </div>
        </div>
      </div>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Empty                                                                  */
  /* ---------------------------------------------------------------------- */

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-white/10 bg-white/[0.02] px-6 py-12 text-center">
        <Search className="mb-3 h-5 w-5 text-zinc-600" />

        <p className="text-sm font-medium text-zinc-400">
          No relevant knowledge found
        </p>

        <p className="mt-1 max-w-md text-xs leading-5 text-zinc-600">
          Try changing the research question or adjusting
          the retrieval parameters.
        </p>
      </div>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Completed                                                              */
  /* ---------------------------------------------------------------------- */

  if (resultCount > 0) {
    return (
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-md border border-emerald-500/10 bg-emerald-500/5 px-3 py-2 text-xs text-zinc-500">
        <Check className="h-3.5 w-3.5 text-emerald-400" />

        <span>
          Retrieval completed
        </span>

        <span className="text-zinc-700">
          •
        </span>

        <Database className="h-3.5 w-3.5 text-zinc-600" />

        <span>
          {resultCount} result
          {resultCount === 1
            ? ""
            : "s"}
        </span>

        {evidenceCount > 0 && (
          <>
            <span className="text-zinc-700">
              •
            </span>

            <span>
              {evidenceCount} evidence
              {evidenceCount === 1
                ? ""
                : " items"}
            </span>
          </>
        )}

        {retrievalMode && (
          <>
            <span className="text-zinc-700">
              •
            </span>

            <FileSearch className="h-3.5 w-3.5 text-zinc-600" />

            <span>
              {retrievalMode}
            </span>
          </>
        )}
      </div>
    );
  }

  /* ---------------------------------------------------------------------- */
  /* Idle                                                                   */
  /* ---------------------------------------------------------------------- */

  return (
    <div className="flex items-center gap-3 rounded-md border border-white/10 bg-white/[0.02] px-4 py-3">
      <Search className="h-4 w-4 text-zinc-600" />

      <div>
        <p className="text-sm font-medium text-zinc-400">
          Retrieval ready
        </p>

        <p className="mt-1 text-xs text-zinc-600">
          Enter a research question to search the knowledge base.
        </p>
      </div>
    </div>
  );
}