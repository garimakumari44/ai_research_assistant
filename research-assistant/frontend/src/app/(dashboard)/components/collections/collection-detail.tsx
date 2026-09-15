"use client";

import {
  ArrowLeft,
  Edit3,
  FileText,
  Folder,
  MoreHorizontal,
  Star,
  Trash2,
} from "lucide-react";

import type { Collection } from "./collection-card";
import { CollectionItems, type CollectionItem } from "./collection-items";

interface CollectionDetailProps {
  collection: Collection | null;
  items?: CollectionItem[];
  isLoading?: boolean;

  onBack?: () => void;
  onEdit?: (collection: Collection) => void;
  onDelete?: (collection: Collection) => void;
  onFavorite?: (collection: Collection) => void;

  onOpenItem?: (item: CollectionItem) => void;
  onRemoveItem?: (item: CollectionItem) => void;
}

export function CollectionDetail({
  collection,
  items = [],
  isLoading = false,
  onBack,
  onEdit,
  onDelete,
  onFavorite,
  onOpenItem,
  onRemoveItem,
}: CollectionDetailProps) {
  if (!collection) {
    return (
      <div className="flex min-h-[400px] items-center justify-center rounded-xl border border-white/10 bg-zinc-950">
        <div className="text-center">
          <Folder className="mx-auto h-6 w-6 text-zinc-700" />

          <p className="mt-3 text-xs text-zinc-600">
            Select a collection to view its details.
          </p>
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs text-zinc-500 transition hover:text-zinc-200"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Collections
        </button>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onFavorite?.(collection)}
            className="rounded-md p-2 text-zinc-600 hover:bg-white/5 hover:text-zinc-300"
            aria-label="Toggle favorite"
          >
            <Star
              className={[
                "h-4 w-4",
                collection.isFavorite
                  ? "fill-current text-amber-400"
                  : "",
              ].join(" ")}
            />
          </button>

          <button
            type="button"
            onClick={() => onEdit?.(collection)}
            className="rounded-md p-2 text-zinc-600 hover:bg-white/5 hover:text-zinc-300"
            aria-label="Edit collection"
          >
            <Edit3 className="h-4 w-4" />
          </button>

          <button
            type="button"
            onClick={() => onDelete?.(collection)}
            className="rounded-md p-2 text-zinc-600 hover:bg-red-500/10 hover:text-red-400"
            aria-label="Delete collection"
          >
            <Trash2 className="h-4 w-4" />
          </button>

          <button
            type="button"
            className="rounded-md p-2 text-zinc-600 hover:bg-white/5 hover:text-zinc-300"
            aria-label="More options"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </div>
      </div>

      <header className="rounded-xl border border-white/10 bg-zinc-950 p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
            style={{
              backgroundColor: `${collection.color ?? "#3b82f6"}15`,
            }}
          >
            <Folder
              className="h-6 w-6"
              style={{
                color: collection.color ?? "#3b82f6",
              }}
            />
          </div>

          <div className="min-w-0 flex-1">
            <h1 className="text-lg font-semibold text-zinc-100">
              {collection.name}
            </h1>

            {collection.description && (
              <p className="mt-1.5 max-w-3xl text-xs leading-relaxed text-zinc-500">
                {collection.description}
              </p>
            )}

            <div className="mt-4 flex flex-wrap items-center gap-4 text-[11px] text-zinc-600">
              <span className="inline-flex items-center gap-1.5">
                <FileText className="h-3 w-3" />
                {collection.itemCount ?? items.length} items
              </span>

              {collection.updatedAt && (
                <span>
                  Updated {formatDate(collection.updatedAt)}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <CollectionItems
        items={items}
        isLoading={isLoading}
        onOpen={onOpenItem}
        onRemove={onRemoveItem}
      />
    </section>
  );
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}