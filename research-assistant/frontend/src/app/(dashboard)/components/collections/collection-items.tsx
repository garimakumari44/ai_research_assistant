"use client";

import {
  ExternalLink,
  FileText,
  MoreHorizontal,
  Trash2,
} from "lucide-react";

/* -------------------------------------------------------------------------- */
/* Types                                                                      */
/* -------------------------------------------------------------------------- */

export interface CollectionPaperAuthor {
  id: number;
  full_name: string;
}

export interface CollectionPaperVenue {
  id: number;
  name: string;
}

export interface CollectionPaperTopic {
  id: number;
  name: string;
}

export interface CollectionPaperSummary {
  id: number;
  title: string;
  year: number | null;
  citation_count: number;
  reference_count: number;
  venue: CollectionPaperVenue | null;
  authors: CollectionPaperAuthor[];
  topics: CollectionPaperTopic[];
}

export interface CollectionItem {
  id: number;
  collection_id: number;
  paper_id: number;
  created_at: string;
  paper: CollectionPaperSummary | null;
}

/* -------------------------------------------------------------------------- */
/* Props                                                                      */
/* -------------------------------------------------------------------------- */

interface CollectionItemsProps {
  items: CollectionItem[];
  isLoading?: boolean;
  onOpen?: (item: CollectionItem) => void;
  onRemove?: (item: CollectionItem) => void;
  onAdd?: () => void;
}

/* -------------------------------------------------------------------------- */
/* Main Component                                                             */
/* -------------------------------------------------------------------------- */

export function CollectionItems({
  items,
  isLoading = false,
  onOpen,
  onRemove,
  onAdd,
}: CollectionItemsProps) {
  return (
    <section className="rounded-xl border border-white/10 bg-zinc-950">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div>
          <h2 className="text-xs font-medium text-zinc-300">
            Collection items
          </h2>

          <p className="mt-0.5 text-[10px] text-zinc-600">
            Research papers contained in this collection.
          </p>
        </div>

        <span className="text-[10px] text-zinc-600">
          {items.length} {items.length === 1 ? "item" : "items"}
        </span>
      </div>

      {/* Loading */}
      {isLoading ? (
        <div className="divide-y divide-white/5">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-20 animate-pulse bg-white/[0.01]"
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        /* Empty */
        <div className="px-6 py-12 text-center">
          <FileText className="mx-auto h-5 w-5 text-zinc-700" />

          <p className="mt-3 text-xs text-zinc-500">
            This collection is empty.
          </p>

          <p className="mt-1 text-[10px] text-zinc-700">
            Add research papers to start building this collection.
          </p>

          {onAdd && (
            <button
              type="button"
              onClick={onAdd}
              className="mt-4 rounded-md border border-white/10 bg-white/[0.03] px-3 py-1.5 text-[10px] font-medium text-zinc-400 transition hover:border-white/20 hover:bg-white/[0.05] hover:text-zinc-200"
            >
              Add papers
            </button>
          )}
        </div>
      ) : (
        /* Items */
        <div className="divide-y divide-white/5">
          {items.map((item) => (
            <CollectionItemRow
              key={item.id}
              item={item}
              onOpen={onOpen}
              onRemove={onRemove}
            />
          ))}
        </div>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/* Item Row                                                                   */
/* -------------------------------------------------------------------------- */

function CollectionItemRow({
  item,
  onOpen,
  onRemove,
}: {
  item: CollectionItem;
  onOpen?: (item: CollectionItem) => void;
  onRemove?: (item: CollectionItem) => void;
}) {
  const paper = item.paper;

  const authorText =
    paper?.authors
      ?.map((author) => author.full_name)
      .filter(Boolean)
      .join(", ") ?? "";

  const topicText =
    paper?.topics
      ?.map((topic) => topic.name)
      .filter(Boolean)
      .join(", ") ?? "";

  const handleOpen = () => {
    onOpen?.(item);
  };

  return (
    <article
      className="group flex items-start gap-3 px-4 py-3 transition hover:bg-white/[0.015]"
      onDoubleClick={handleOpen}
    >
      {/* Icon */}
      <button
        type="button"
        onClick={handleOpen}
        aria-label={`Open ${paper?.title ?? `Paper #${item.paper_id}`}`}
        className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white/5 transition hover:bg-white/10"
      >
        <FileText className="h-4 w-4 text-zinc-500" />
      </button>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <button
          type="button"
          onClick={handleOpen}
          className="block max-w-full truncate text-left text-xs font-medium text-zinc-300 transition hover:text-white"
        >
          {paper?.title ?? `Paper #${item.paper_id}`}
        </button>

        <div className="mt-1 flex flex-wrap items-center gap-2">
          {paper?.year != null && (
            <span className="rounded bg-white/5 px-1.5 py-0.5 text-[9px] text-zinc-600">
              {paper.year}
            </span>
          )}

          {paper?.venue?.name && (
            <span className="max-w-[220px] truncate text-[10px] text-zinc-600">
              {paper.venue.name}
            </span>
          )}

          <span className="rounded bg-white/5 px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-zinc-600">
            paper
          </span>
        </div>

        {authorText && (
          <p className="mt-1.5 line-clamp-1 text-[10px] text-zinc-600">
            {authorText}
          </p>
        )}

        {topicText && (
          <p className="mt-1 line-clamp-1 text-[10px] text-zinc-700">
            {topicText}
          </p>
        )}

        {paper && (
          <div className="mt-1.5 flex items-center gap-3 text-[10px] text-zinc-700">
            <span>
              {paper.citation_count}{" "}
              {paper.citation_count === 1 ? "citation" : "citations"}
            </span>

            <span>
              {paper.reference_count}{" "}
              {paper.reference_count === 1 ? "reference" : "references"}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex shrink-0 items-center gap-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            handleOpen();
          }}
          className="rounded-md p-1.5 text-zinc-600 transition hover:bg-white/5 hover:text-zinc-300"
          aria-label="Open item"
        >
          <ExternalLink className="h-3.5 w-3.5" />
        </button>

        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onRemove?.(item);
          }}
          className="rounded-md p-1.5 text-zinc-600 transition hover:bg-red-500/10 hover:text-red-400"
          aria-label="Remove item"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>

        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
          }}
          className="rounded-md p-1.5 text-zinc-600 transition hover:bg-white/5 hover:text-zinc-300"
          aria-label="More options"
        >
          <MoreHorizontal className="h-3.5 w-3.5" />
        </button>
      </div>
    </article>
  );
}