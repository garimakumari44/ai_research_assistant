"use client";

import {
  BookOpen,
  ExternalLink,
  FileText,
  Hash,
} from "lucide-react";

import type { GenerationCitation } from "@/generation/types";

interface CitationListProps {
  citations: GenerationCitation[];
  title?: string;
  compact?: boolean;
}

function getCitationIcon(type: GenerationCitation["type"]) {
  switch (type) {
    case "web":
      return ExternalLink;

    case "page":
      return FileText;

    case "section":
      return BookOpen;

    default:
      return Hash;
  }
}

export function CitationList({
  citations,
  title = "Citations",
  compact = false,
}: CitationListProps) {
  if (citations.length === 0) {
    return (
      <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
        <div className="flex items-center gap-2 text-sm font-medium">
          <BookOpen className="h-4 w-4 text-muted-foreground" />
          {title}
        </div>

        <p className="mt-2 text-sm text-muted-foreground">
          No citations were attached to this answer.
        </p>
      </div>
    );
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center gap-2">
        <BookOpen className="h-4 w-4 text-muted-foreground" />

        <h3 className="text-sm font-semibold">
          {title}
        </h3>

        <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
          {citations.length}
        </span>
      </div>

      <div className="space-y-2">
        {citations.map((citation, index) => {
          const Icon = getCitationIcon(citation.type);
          const marker = citation.marker || `[${index + 1}]`;

          return (
            <article
              key={citation.id}
              className="rounded-xl border border-border/60 bg-card p-3 transition-colors hover:bg-muted/30"
            >
              <div className="flex gap-3">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-muted">
                  <Icon className="h-3.5 w-3.5" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="shrink-0 text-xs font-semibold text-muted-foreground">
                        {marker}
                      </span>

                      <h4 className="truncate text-sm font-medium">
                        {citation.title ||
                          citation.document_title ||
                          "Untitled source"}
                      </h4>
                    </div>

                    {citation.source_url && (
                      <a
                        href={citation.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="shrink-0 text-muted-foreground transition-colors hover:text-foreground"
                        aria-label="Open source"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    )}
                  </div>

                  {!compact && (
                    <>
                      {(citation.document_title ||
                        citation.page_number !== undefined ||
                        citation.section) && (
                        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
                          {citation.document_title && (
                            <span>
                              {citation.document_title}
                            </span>
                          )}

                          {citation.page_number !== undefined && (
                            <span>
                              Page {citation.page_number}
                            </span>
                          )}

                          {citation.section && (
                            <span>{citation.section}</span>
                          )}
                        </div>
                      )}

                      {citation.excerpt && (
                        <p className="mt-2 line-clamp-3 text-xs leading-5 text-muted-foreground">
                          {citation.excerpt}
                        </p>
                      )}
                    </>
                  )}

                  {citation.confidence !== undefined && (
                    <div className="mt-2 text-[11px] text-muted-foreground">
                      Citation confidence{" "}
                      <span className="font-medium text-foreground">
                        {Math.round(
                          citation.confidence * 100,
                        )}
                        %
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default CitationList;