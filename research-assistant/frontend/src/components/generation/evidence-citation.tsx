"use client";

import {
  CheckCircle2,
  ExternalLink,
  FileText,
  Quote,
} from "lucide-react";

import type { GenerationCitation } from "@/generation/types";

interface EvidenceCitationProps {
  citation: GenerationCitation;
  index?: number;
  highlighted?: boolean;
}

export function EvidenceCitation({
  citation,
  index,
  highlighted = false,
}: EvidenceCitationProps) {
  const marker =
    citation.marker ||
    `[${index !== undefined ? index + 1 : ""}]`;

  return (
    <article
      className={[
        "rounded-xl border p-4 transition-colors",
        highlighted
          ? "border-foreground/20 bg-muted/40"
          : "border-border/60 bg-card",
      ].join(" ")}
    >
      <div className="space-y-4">
        {/* Evidence */}
        <div>
          <div className="mb-2 flex items-center gap-2">
            <Quote className="h-3.5 w-3.5 text-muted-foreground" />

            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Evidence
            </span>
          </div>

          <div className="rounded-lg border border-border/40 bg-muted/20 p-3">
            {citation.excerpt ? (
              <p className="text-sm leading-6 text-foreground">
                {citation.excerpt}
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                No evidence excerpt is available.
              </p>
            )}
          </div>
        </div>

        {/* Citation */}
        <div className="border-t border-border/50 pt-3">
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
              <FileText className="h-4 w-4" />
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground">
                      {marker}
                    </span>

                    <h4 className="truncate text-sm font-semibold">
                      {citation.title ||
                        citation.document_title ||
                        "Source"}
                    </h4>
                  </div>

                  <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
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
                </div>

                {citation.source_url && (
                  <a
                    href={citation.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="shrink-0 text-muted-foreground hover:text-foreground"
                    aria-label="Open source"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>

              {citation.confidence !== undefined && (
                <div className="mt-3 flex items-center gap-2 text-xs">
                  <CheckCircle2 className="h-3.5 w-3.5 text-muted-foreground" />

                  <span className="text-muted-foreground">
                    Citation confidence
                  </span>

                  <span className="font-semibold">
                    {Math.round(
                      citation.confidence * 100,
                    )}
                    %
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

export default EvidenceCitation;