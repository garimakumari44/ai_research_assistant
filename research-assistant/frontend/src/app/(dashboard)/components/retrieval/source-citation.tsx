"use client";

import {
  ExternalLink,
  FileText,
  Hash,
  Layers3,
  MapPin,
} from "lucide-react";

import type {
  Evidence,
  Provenance,
  RetrievalResult,
} from "@/types/retrieval";

interface SourceCitationProps {
  /**
   * Retrieval result containing provenance.
   */
  result: RetrievalResult;

  /**
   * Optional evidence containing its own provenance.
   */
  evidence?: Evidence | null;
}

export function SourceCitation({
  result,
  evidence,
}: SourceCitationProps) {
  /**
   * Evidence provenance is preferred because evidence is
   * the final representation of the retrieved source.
   *
   * Fall back to result provenance when evidence does not
   * provide one.
   */
  const provenance: Provenance | null =
    evidence?.provenance ??
    result.provenance;

  if (!provenance) {
    return (
      <div className="flex items-center gap-1.5 text-xs text-zinc-700">
        <FileText className="h-3.5 w-3.5" />

        <span>
          Source information unavailable
        </span>
      </div>
    );
  }

  return (
    <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-zinc-600">
      {/* Paper */}

      {provenance.paper_id && (
        <div className="flex min-w-0 items-center gap-1.5">
          <FileText className="h-3.5 w-3.5 shrink-0" />

          <span>
            Paper
          </span>

          <span className="max-w-[140px] truncate text-zinc-700">
            {provenance.paper_id}
          </span>
        </div>
      )}

      {/* Document */}

      {provenance.document_id && (
        <div className="flex min-w-0 items-center gap-1.5">
          <Layers3 className="h-3.5 w-3.5 shrink-0" />

          <span>
            Document
          </span>

          <span className="max-w-[140px] truncate text-zinc-700">
            {provenance.document_id}
          </span>
        </div>
      )}

      {/* Section */}

      {provenance.section && (
        <div className="flex min-w-0 items-center gap-1.5">
          <MapPin className="h-3.5 w-3.5 shrink-0" />

          <span className="max-w-[200px] truncate">
            {provenance.section}
          </span>
        </div>
      )}

      {/* Page */}

      {provenance.page != null && (
        <div className="flex items-center gap-1.5">
          <span>
            p. {provenance.page}
          </span>
        </div>
      )}

      {/* Chunk */}

      <div className="flex min-w-0 items-center gap-1.5">
        <Hash className="h-3.5 w-3.5 shrink-0" />

        <span className="max-w-[150px] truncate">
          {provenance.chunk_id}
        </span>
      </div>

      {/* Source */}

      {provenance.source && (
        <a
          href={provenance.source}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 transition-colors hover:text-blue-400"
          onClick={(event) =>
            event.stopPropagation()
          }
        >
          <ExternalLink className="h-3.5 w-3.5" />

          Source
        </a>
      )}
    </div>
  );
}