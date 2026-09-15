"use client";

import {
  FileText,
  Folder,
  MoreHorizontal,
  Star,
} from "lucide-react";
import { useRouter } from "next/navigation";

export interface Collection {
  id: number | string;
  name: string;
  description?: string;
  itemCount?: number;
  item_count?: number;
  paper_count?: number;
  createdAt?: string;
  updatedAt?: string;
  isFavorite?: boolean;
  color?: string;
}

interface CollectionCardProps {
  collection: Collection;
  onClick?: (collection: Collection) => void;
  onFavorite?: (collection: Collection) => void;
  onMenu?: (collection: Collection) => void;
}

export function CollectionCard({
  collection,
  onClick,
  onFavorite,
  onMenu,
}: CollectionCardProps) {
  const router = useRouter();

  const itemCount =
    collection.itemCount ??
    collection.item_count ??
    collection.paper_count ??
    0;

  const handleOpen = () => {
    onClick?.(collection);

    router.push(`/collections/${collection.id}`);
  };

  return (
    <article
      className="group cursor-pointer rounded-xl border border-white/10 bg-zinc-950 p-4 transition hover:border-white/20 hover:bg-white/[0.02]"
      onClick={handleOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          handleOpen();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <div className="flex items-start justify-between gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-lg"
          style={{
            backgroundColor: `${collection.color ?? "#3b82f6"}15`,
          }}
        >
          <Folder
            className="h-5 w-5"
            style={{
              color: collection.color ?? "#3b82f6",
            }}
          />
        </div>

        <div className="flex items-center gap-1">
          {/* Favorite */}

          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onFavorite?.(collection);
            }}
            aria-label={
              collection.isFavorite
                ? "Remove from favorites"
                : "Add to favorites"
            }
            className="rounded-md p-1.5 text-zinc-600 opacity-0 transition hover:bg-white/5 hover:text-zinc-300 group-hover:opacity-100"
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

          {/* Menu */}

          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onMenu?.(collection);
            }}
            aria-label="Collection menu"
            className="rounded-md p-1.5 text-zinc-600 opacity-0 transition hover:bg-white/5 hover:text-zinc-300 group-hover:opacity-100"
          >
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Collection name */}

      <h3 className="mt-4 truncate text-sm font-medium text-zinc-100">
        {collection.name}
      </h3>

      {/* Description */}

      {collection.description && (
        <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-zinc-500">
          {collection.description}
        </p>
      )}

      {/* Metadata */}

      <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3">
        <div className="flex items-center gap-1.5 text-[11px] text-zinc-600">
          <FileText className="h-3 w-3" />

          <span>
            {itemCount}{" "}
            {itemCount === 1 ? "item" : "items"}
          </span>
        </div>

        {collection.updatedAt && (
          <span className="text-[10px] text-zinc-700">
            Updated {formatDate(collection.updatedAt)}
          </span>
        )}
      </div>
    </article>
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