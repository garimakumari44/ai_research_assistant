"use client";

import {
  ExternalLink,
  FileText,
  Quote,
} from "lucide-react";

export interface FrontierEvidenceItem {
  id: string;
  title?: string;
  source?: string;
  excerpt?: string;
  relevance?: number;
  url?: string;
}

interface FrontierEvidenceProps {
  evidence: FrontierEvidenceItem[];
  title?: string;
  emptyMessage?: string;
  onOpen?: (item: FrontierEvidenceItem) => void;
}

export function FrontierEvidence({
  evidence,
  title = "Supporting evidence",
  emptyMessage = "No supporting evidence available.",
  onOpen,
}: FrontierEvidenceProps) {
  return (
    <section className="rounded-xl border border-white/10 bg-zinc-950">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <Quote className="h-3.5 w-3.5 text-zinc-500" />

          <h3 className="text-xs font-medium text-zinc-300">
            {title}
          </h3>
        </div>

        <span className="text-[10px] text-zinc-600">
          {evidence.length} sources
        </span>
      </div>

      {evidence.length === 0 ? (
        <div className="px-4 py-8 text-center text-xs text-zinc-600">
          {emptyMessage}
        </div>
      ) : (
        <div className="divide-y divide-white/5">
          {evidence.map((item) => (
            <EvidenceItem
              key={item.id}
              item={item}
              onOpen={onOpen}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function EvidenceItem({
  item,
  onOpen,
}: {
  item: FrontierEvidenceItem;
  onOpen?: (item: FrontierEvidenceItem) => void;
}) {
  const relevance =
    item.relevance !== undefined
      ? Math.round(item.relevance * 100)
      : undefined;

  const handleOpen = () => {
    if (onOpen) {
      onOpen(item);
      return;
    }

    if (item.url) {
      window.open(
        item.url,
        "_blank",
        "noopener,noreferrer",
      );
    }
  };

  return (
    <article className="p-4 transition hover:bg-white/[0.015]">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-white/5">
          <FileText className="h-3.5 w-3.5 text-zinc-500" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h4 className="truncate text-xs font-medium text-zinc-300">
                {item.title ?? "Untitled source"}
              </h4>

              {item.source && (
                <p className="mt-0.5 truncate text-[10px] text-zinc-600">
                  {item.source}
                </p>
              )}
            </div>

            {(item.url || onOpen) && (
              <button
                type="button"
                onClick={handleOpen}
                className="shrink-0 rounded-md p-1.5 text-zinc-600 hover:bg-white/5 hover:text-zinc-300"
                aria-label="Open evidence"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {item.excerpt && (
            <blockquote className="mt-2 border-l border-white/10 pl-3 text-xs leading-relaxed text-zinc-500">
              {item.excerpt}
            </blockquote>
          )}

          {relevance !== undefined && (
            <div className="mt-3 flex items-center gap-2">
              <span className="text-[10px] text-zinc-600">
                Relevance
              </span>

              <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-blue-500/70"
                  style={{
                    width: `${relevance}%`,
                  }}
                />
              </div>

              <span className="text-[10px] text-zinc-500">
                {relevance}%
              </span>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}