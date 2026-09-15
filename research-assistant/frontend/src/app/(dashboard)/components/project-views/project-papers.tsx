"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search,
  FileText,
} from "lucide-react";

import { MetricLabel } from "../../components/primitives";
import { cn } from "../lib/utils";
import { useProjectPapers } from "@/papers/hooks/use-project-papers";

const filters = [
  "Year",
  "Topic",
  "Method",
  "Venue",
  "Author",
  "Dataset",
];

export function ProjectPapers({
  projectId,
}: {
  projectId: string;
}) {
  const [query, setQuery] = useState("");
  const [activeFilter, setActiveFilter] =
    useState<string | null>(null);

  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useProjectPapers(projectId, {
    query: query || undefined,
  });

  const papers = data?.papers ?? [];

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 h-10 animate-pulse rounded-md bg-surface" />

        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-24 rounded-md bg-surface animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-5xl py-12 text-center">
        <p className="mb-3 text-sm text-muted-foreground">
          Unable to load project papers.
        </p>

        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-md border border-border px-3 py-1.5 text-xs"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6">
        <div className="flex items-center gap-2.5 rounded-md border border-border bg-surface px-3.5 py-2.5">
          <Search className="h-3.5 w-3.5 text-faint" />

          <input
            value={query}
            onChange={(event) =>
              setQuery(event.target.value)
            }
            placeholder="Search papers, methods, authors, datasets..."
            className="flex-1 bg-transparent text-[13px] text-foreground placeholder:text-faint outline-none"
          />
        </div>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-2">
        {filters.map((filter) => (
          <button
            key={filter}
            type="button"
            onClick={() =>
              setActiveFilter(
                activeFilter === filter
                  ? null
                  : filter,
              )
            }
            className={cn(
              "rounded-full border px-3 py-1 text-[12px] transition-colors",
              activeFilter === filter
                ? "border-primary bg-primary/10 text-primary-soft"
                : "border-border text-muted-foreground hover:border-strong-border hover:text-foreground",
            )}
          >
            {filter}
          </button>
        ))}

        <div className="ml-auto">
          <MetricLabel>
            {data?.total ?? papers.length} results
          </MetricLabel>
        </div>
      </div>

      <div>
        {papers.map((paper, index) => (
          <div
            key={paper.id}
            className="group -mx-2 flex items-start gap-4 rounded border-b border-border/50 px-2 py-4 transition-colors hover:bg-surface/50"
          >
            <span className="mt-0.5 w-6 shrink-0 font-mono-tech text-[11px] tabular-nums text-faint">
              {String(index + 1).padStart(2, "0")}
            </span>

            <div className="min-w-0 flex-1">
              <Link
                href={`/papers/${paper.id}`}
                className="text-[14px] font-medium text-foreground transition-colors hover:text-primary-soft"
              >
                {paper.title}
              </Link>

              <p className="mb-1.5 mt-0.5 text-[12px] text-faint">
                {paper.authors?.join(", ")}
                {" · "}
                {paper.venue}
                {" · "}
                {paper.year}
              </p>

              {paper.abstract && (
                <p className="mb-2 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                  {paper.abstract}
                </p>
              )}

              <div className="flex flex-wrap items-center gap-1.5">
                {paper.tags?.map((tag) => (
                  <span
                    key={tag}
                    className="rounded border border-border px-1.5 py-0.5 font-mono-tech text-[10px] text-muted-foreground"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="shrink-0 text-right">
              <p className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                Citations
              </p>

              <p className="font-mono-tech text-sm tabular-nums text-secondary-foreground">
                {paper.citations ?? 0}
              </p>
            </div>
          </div>
        ))}
      </div>

      {papers.length === 0 && (
        <div className="py-16 text-center">
          <FileText className="mx-auto mb-3 h-6 w-6 text-faint" />

          <p className="mb-1 text-[14px] text-muted-foreground">
            No papers match your search.
          </p>

          <p className="text-[12px] text-faint">
            Try a different query or clear filters.
          </p>
        </div>
      )}
    </div>
  );
}