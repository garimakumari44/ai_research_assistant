"use client";

import {
  FolderPlus,
  Search,
} from "lucide-react";

import { useMemo, useState } from "react";

import {
  CollectionCard,
  type Collection,
} from "./collection-card";

interface CollectionListProps {
  collections: Collection[];
  isLoading?: boolean;
  onSelect?: (collection: Collection) => void;
  onCreate?: () => void;
  onFavorite?: (collection: Collection) => void;
  onMenu?: (collection: Collection) => void;
}

export function CollectionList({
  collections,
  isLoading = false,
  onSelect,
  onCreate,
  onFavorite,
  onMenu,
}: CollectionListProps) {
  const [search, setSearch] = useState("");

  const filteredCollections = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return collections;
    }

    return collections.filter((collection) => {
      return (
        collection.name.toLowerCase().includes(query) ||
        collection.description?.toLowerCase().includes(query)
      );
    });
  }, [collections, search]);

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100">
            Collections
          </h2>

          <p className="mt-1 text-xs text-zinc-500">
            Organize research material into reusable collections.
          </p>
        </div>

        {onCreate && (
          <button
            type="button"
            onClick={onCreate}
            className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-blue-600 px-3 text-xs font-medium text-white transition hover:bg-blue-500"
          >
            <FolderPlus className="h-3.5 w-3.5" />
            New collection
          </button>
        )}
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-600" />

        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search collections..."
          className="h-10 w-full rounded-lg border border-white/10 bg-zinc-950 pl-9 pr-3 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-white/20"
        />
      </div>

      {isLoading ? (
        <CollectionSkeleton />
      ) : filteredCollections.length === 0 ? (
        <EmptyCollections
          hasSearch={Boolean(search.trim())}
          onCreate={onCreate}
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {filteredCollections.map((collection) => (
            <CollectionCard
              key={collection.id}
              collection={collection}
              onClick={onSelect}
              onFavorite={onFavorite}
              onMenu={onMenu}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function CollectionSkeleton() {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="h-44 animate-pulse rounded-xl border border-white/10 bg-white/[0.02]"
        />
      ))}
    </div>
  );
}

function EmptyCollections({
  hasSearch,
  onCreate,
}: {
  hasSearch: boolean;
  onCreate?: () => void;
}) {
  return (
    <div className="rounded-xl border border-dashed border-white/10 bg-zinc-950 px-6 py-12 text-center">
      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-white/5">
        <FolderPlus className="h-5 w-5 text-zinc-600" />
      </div>

      <h3 className="mt-4 text-sm font-medium text-zinc-300">
        {hasSearch
          ? "No collections found"
          : "No collections yet"}
      </h3>

      <p className="mx-auto mt-1.5 max-w-sm text-xs text-zinc-600">
        {hasSearch
          ? "Try a different search term."
          : "Create a collection to organize papers, documents, and research evidence."}
      </p>

      {!hasSearch && onCreate && (
        <button
          type="button"
          onClick={onCreate}
          className="mt-4 text-xs font-medium text-blue-400 hover:text-blue-300"
        >
          Create your first collection
        </button>
      )}
    </div>
  );
}