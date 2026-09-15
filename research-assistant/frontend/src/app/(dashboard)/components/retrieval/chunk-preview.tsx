"use client";

import {
  ChevronDown,
  ChevronUp,
  FileText,
  Quote,
} from "lucide-react";

import { useState } from "react";

import type {
  Evidence,
  RetrievalResult,
} from "@/types/retrieval";

interface ChunkPreviewProps {
  /**
   * Canonical retrieval result returned by the backend.
   */
  result: RetrievalResult;

  /**
   * Optional evidence associated with this result.
   */
  evidence?: Evidence | null;

  /**
   * Maximum visible text length.
   */
  maxLength?: number;
}

function truncateText(
  text: string,
  maxLength: number,
): string {
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength).trim()}…`;
}

export function ChunkPreview({
  result,
  evidence,
  maxLength = 650,
}: ChunkPreviewProps) {
  const [expanded, setExpanded] = useState(false);

  /**
   * Evidence content takes precedence when explicitly supplied.
   * Otherwise use the canonical RetrievalResult.content field.
   */
  const content =
    evidence?.content ??
    result.content ??
    "No content available.";

  const visibleContent = expanded
    ? content
    : truncateText(content, maxLength);

  const hasMoreContent =
    content.length > maxLength;

  const provenance = result.provenance;

  return (
    <div className="rounded-md border border-white/5 bg-black/20">
      {/* Content */}

      <div className="relative px-4 py-3">
        <Quote className="absolute left-2 top-2 h-3 w-3 text-zinc-700" />

        <p className="pl-4 whitespace-pre-wrap text-sm leading-6 text-zinc-400">
          {visibleContent}
        </p>

        {hasMoreContent && (
          <button
            type="button"
            onClick={() =>
              setExpanded((value) => !value)
            }
            className="mt-2 ml-4 flex items-center gap-1 text-[10px] uppercase tracking-wider text-zinc-600 transition-colors hover:text-zinc-300"
          >
            {expanded ? (
              <>
                Show less
                <ChevronUp className="h-3 w-3" />
              </>
            ) : (
              <>
                Show more
                <ChevronDown className="h-3 w-3" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Source metadata */}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-white/5 px-4 py-2 text-[10px] text-zinc-600">
        <div className="flex items-center gap-1.5">
          <FileText className="h-3 w-3" />

          <span>
            Rank #{result.rank}
          </span>
        </div>

        <span>
          Score {result.score.toFixed(4)}
        </span>

        <span>
          {result.retrieval_method}
        </span>

        {provenance?.page != null && (
          <span>
            Page {provenance.page}
          </span>
        )}

        {provenance?.section && (
          <span className="max-w-[220px] truncate">
            {provenance.section}
          </span>
        )}
      </div>
    </div>
  );
}