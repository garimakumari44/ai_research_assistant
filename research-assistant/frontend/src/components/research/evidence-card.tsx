import {
  BookOpen,
  FileText,
  GitBranch,
  KeyRound,
  Network,
  Search,
} from "lucide-react";

import type {
  Evidence,
} from "@/research/types";

const sourceConfig: Record<
  string,
  {
    label: string;
    icon: typeof Search;
  }
> = {
  semantic: {
    label: "Semantic",
    icon: Search,
  },

  keyword: {
    label: "Keyword",
    icon: KeyRound,
  },

  graph: {
    label: "Graph",
    icon: GitBranch,
  },
};

export function EvidenceCard({
  evidence,
}: {
  evidence: Evidence;
}) {
  const sourceType =
    evidence.sourceType ?? "semantic";

  const config =
    sourceConfig[sourceType] ??
    sourceConfig.semantic;

  const Icon = config.icon;

  return (
    <article className="rounded-2xl border bg-background p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border">
            <Icon className="h-4 w-4" />
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold">
                {config.label} Evidence
              </span>

              {evidence.score !== undefined && (
                <span className="text-[10px] text-muted-foreground">
                  {Math.round(
                    evidence.score * 100,
                  )}
                  %
                </span>
              )}
            </div>

            {evidence.title && (
              <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                {evidence.title}
              </p>
            )}
          </div>
        </div>

        {evidence.confidence !== undefined && (
          <span className="rounded-full border px-2 py-1 text-[10px]">
            {Math.round(
              evidence.confidence * 100,
            )}
            % confidence
          </span>
        )}
      </div>

      <div className="mt-4 rounded-xl bg-muted/40 p-3">
        <p className="text-sm leading-6">
          {evidence.content}
        </p>
      </div>

      {sourceType === "graph" && (
        <div className="mt-3 flex items-center gap-2 rounded-xl border p-3">
          <Network className="h-4 w-4 shrink-0" />

          <div className="text-xs">
            <span className="font-medium">
              Graph relation
            </span>

            {evidence.relation && (
              <span className="ml-2 text-muted-foreground">
                {evidence.relation}
              </span>
            )}
          </div>
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px] text-muted-foreground">
        {evidence.paperId && (
          <span className="flex items-center gap-1">
            <BookOpen className="h-3 w-3" />
            Paper {evidence.paperId}
          </span>
        )}

        {evidence.documentId && (
          <span className="flex items-center gap-1">
            <FileText className="h-3 w-3" />
            Document {evidence.documentId}
          </span>
        )}

        {evidence.page !== undefined && (
          <span>
            Page {evidence.page}
          </span>
        )}

        {evidence.sectionId && (
          <span>
            Section {evidence.sectionId}
          </span>
        )}
      </div>
    </article>
  );
}