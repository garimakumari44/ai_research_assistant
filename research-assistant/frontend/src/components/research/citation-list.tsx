import {
  BookOpen,
  ExternalLink,
} from "lucide-react";

import type {
  ResearchCitation,
} from "@/research/types";

export function CitationList({
  citations,
}: {
  citations: ResearchCitation[];
}) {
  if (!citations.length) {
    return null;
  }

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold">
            Citations
          </h2>

          <p className="mt-1 text-xs text-muted-foreground">
            Sources used to ground the generated answer.
          </p>
        </div>

        <span className="rounded-full border px-2 py-1 text-[10px]">
          {citations.length}
        </span>
      </div>

      <div className="space-y-2">
        {citations.map(
          (citation, index) => (
            <div
              key={citation.id}
              className="rounded-xl border p-3"
            >
              <div className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border text-[10px] font-semibold">
                  {index + 1}
                </span>

                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold">
                    {citation.title}
                  </p>

                  {citation.authors &&
                    citation.authors
                      .length > 0 && (
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        {citation.authors.join(
                          ", ",
                        )}
                      </p>
                    )}

                  <div className="mt-2 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
                    {citation.year && (
                      <span>
                        {citation.year}
                      </span>
                    )}

                    {citation.venue && (
                      <span>
                        {citation.venue}
                      </span>
                    )}

                    {citation.evidenceIds && (
                      <span className="flex items-center gap-1">
                        <BookOpen className="h-3 w-3" />
                        {
                          citation
                            .evidenceIds
                            .length
                        }{" "}
                        evidence
                      </span>
                    )}

                    {citation.sourceUrl && (
                      <a
                        href={
                          citation.sourceUrl
                        }
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 hover:underline"
                      >
                        Source
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ),
        )}
      </div>
    </section>
  );
}