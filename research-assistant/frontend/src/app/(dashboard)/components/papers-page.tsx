"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import {
  Search,
  FileText,
  Loader2,
  Plus,
  X,
  Check,
} from "lucide-react";

import {
  getPaperSearchResults,
} from "../../../lib/papers";

import type {
  PaperSearchResult,
} from "../../../types/paper";

import { MetricLabel } from "./primitives";

import { useCollections } from "@/collections/hooks/use-collections";
import { useAddCollectionItem } from "@/collections/hooks/use-collection-item";

const filters = [
  "Year",
  "Topic",
  "Venue",
  "Author",
];

export function PapersPage() {
  const [query, setQuery] = useState("");

  const [papers, setPapers] =
    useState<PaperSearchResult[]>([]);

  const [total, setTotal] = useState(0);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  /**
   * Paper currently being added.
   */
  const [selectedPaper, setSelectedPaper] =
    useState<PaperSearchResult | null>(null);

  /**
   * Load collections for the Add modal.
   */
  const {
    data: collectionsResponse,
    isLoading: collectionsLoading,
  } = useCollections({
    page: 1,
    page_size: 100,
    archived: false,
  });

  const collections =
    collectionsResponse?.items ?? [];

  /**
   * Add paper mutation.
   */
  const {
    mutateAsync: addPaperToCollection,
    isPending: isAdding,
    error: addError,
  } = useAddCollectionItem();

  /**
   * Collection currently selected while
   * adding the paper.
   */
  const [addingToCollectionId, setAddingToCollectionId] =
    useState<number | null>(null);

  /**
   * Successfully added collection IDs.
   */
  const [addedCollectionIds, setAddedCollectionIds] =
    useState<number[]>([]);

  async function loadPapers(
    searchQuery = "",
  ) {
    try {
      setLoading(true);
      setError(null);

      const response =
        await getPaperSearchResults({
          query:
            searchQuery.trim() || undefined,

          page: 1,

          page_size: 20,

          sort_by:
            "publication_date",

          sort_order: "desc",
        });

      setPapers(
        response.papers ?? [],
      );

      setTotal(
        response.total ?? 0,
      );
    } catch (err) {
      console.error(
        "Failed to load papers:",
        err,
      );

      setError(
        err instanceof Error
          ? err.message
          : "Failed to load papers",
      );

      setPapers([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer =
      setTimeout(() => {
        loadPapers(query);
      }, 350);

    return () =>
      clearTimeout(timer);
  }, [query]);

  /**
   * Open Add modal.
   */
  function openAddModal(
    paper: PaperSearchResult,
  ) {
    setSelectedPaper(paper);
    setAddingToCollectionId(null);
    setAddedCollectionIds([]);
  }

  /**
   * Close Add modal.
   */
  function closeAddModal() {
    if (isAdding) {
      return;
    }

    setSelectedPaper(null);
    setAddingToCollectionId(null);
    setAddedCollectionIds([]);
  }

  /**
   * Add paper to selected collection.
   */
  async function handleAddToCollection(
    collectionId: number,
  ) {
    if (!selectedPaper?.id) {
      return;
    }

    try {
      setAddingToCollectionId(
        collectionId,
      );

      await addPaperToCollection({
        collectionId,
        payload: {
          paper_id: Number(
            selectedPaper.id,
          ),
        },
      });

      setAddedCollectionIds((current) =>
        current.includes(collectionId)
          ? current
          : [...current, collectionId],
      );
    } catch (err) {
      console.error(
        "Failed to add paper to collection:",
        err,
      );
    } finally {
      setAddingToCollectionId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-10 md:px-10">
      <h1 className="mb-6 text-xl font-medium tracking-tight text-foreground">
        Papers
      </h1>

      {/* Search */}
      <div className="mb-6">
        <div className="flex items-center gap-2.5 rounded-md border border-border bg-surface px-3.5 py-2.5">
          <Search className="h-3.5 w-3.5 text-faint" />

          <input
            value={query}
            onChange={(e) =>
              setQuery(e.target.value)
            }
            placeholder="Search papers, authors, venues..."
            className="flex-1 bg-transparent text-[13px] text-foreground placeholder:text-faint outline-none"
          />

          {loading && (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-faint" />
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        {filters.map((filter) => (
          <button
            key={filter}
            type="button"
            className="rounded-full border border-border px-3 py-1 text-[12px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
          >
            {filter}
          </button>
        ))}

        <div className="ml-auto">
          <MetricLabel>
            {total} results
          </MetricLabel>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 rounded-md border border-border bg-surface p-4">
          <p className="text-[13px] text-muted-foreground">
            Unable to load papers.
          </p>

          <p className="mt-1 text-[11px] text-faint">
            {error}
          </p>
        </div>
      )}

      {/* Loading */}
      {loading &&
        papers.length === 0 && (
          <div className="py-16 text-center">
            <Loader2 className="mx-auto mb-3 h-5 w-5 animate-spin text-faint" />

            <p className="text-[13px] text-muted-foreground">
              Loading papers...
            </p>
          </div>
        )}

      {/* Papers */}
      {!loading &&
        !error &&
        papers.length > 0 && (
          <div className="space-y-0">
            {papers.map(
              (paper, index) => (
                <div
                  key={
                    paper.id ??
                    `${paper.title}-${index}`
                  }
                  className="group flex items-start gap-4 rounded border-b border-border/50 px-2 py-4 transition-colors hover:bg-surface/50"
                >
                  {/* Number */}
                  <span className="mt-0.5 w-6 shrink-0 font-mono-tech text-[11px] tabular-nums text-faint">
                    {String(
                      index + 1,
                    ).padStart(2, "0")}
                  </span>

                  <div className="min-w-0 flex-1">
                    {/* Title */}
                    {paper.id ? (
                      <Link
                        href={`/papers/${paper.id}`}
                        className="text-[14px] font-medium text-foreground transition-colors hover:text-primary-soft"
                      >
                        {paper.title}
                      </Link>
                    ) : (
                      <p className="text-[14px] font-medium text-foreground">
                        {paper.title}
                      </p>
                    )}

                    {/* Metadata */}
                    <p className="mb-1.5 mt-0.5 text-[12px] text-faint">
                      {paper.authors.length >
                      0
                        ? paper.authors.join(
                            ", ",
                          )
                        : "Unknown authors"}

                      {paper.venue &&
                        ` · ${paper.venue}`}

                      {paper.publication_date &&
                        ` · ${new Date(
                          paper.publication_date,
                        ).getFullYear()}`}
                    </p>

                    {/* Abstract */}
                    {paper.abstract && (
                      <p className="mb-2 line-clamp-2 text-[12px] leading-relaxed text-muted-foreground">
                        {paper.abstract}
                      </p>
                    )}

                    {/* Source / DOI */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      {paper.source && (
                        <span className="rounded border border-border px-1.5 py-0.5 font-mono-tech text-[10px] text-muted-foreground">
                          {paper.source}
                        </span>
                      )}

                      {paper.doi && (
                        <span className="rounded border border-border px-1.5 py-0.5 font-mono-tech text-[10px] text-muted-foreground">
                          DOI
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Citations / Actions */}
                  <div className="flex shrink-0 flex-col items-end gap-2">
                    <div className="text-right">
                      <p className="font-mono-tech text-[10px] uppercase tracking-wider text-faint">
                        Citations
                      </p>

                      <p className="font-mono-tech text-sm tabular-nums text-secondary-foreground">
                        {paper.citation_count}
                      </p>
                    </div>

                    <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      {paper.id && (
                        <Link
                          href={`/papers/${paper.id}`}
                          className="rounded border border-border px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
                        >
                          Open
                        </Link>
                      )}

                      {/* ADD BUTTON */}
                      {paper.id && (
                        <button
                          type="button"
                          onClick={() =>
                            openAddModal(
                              paper,
                            )
                          }
                          className="inline-flex items-center gap-1 rounded border border-border px-2 py-1 text-[11px] text-muted-foreground transition-colors hover:border-strong-border hover:text-foreground"
                        >
                          <Plus className="h-3 w-3" />
                          Add
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ),
            )}
          </div>
        )}

      {/* Empty state */}
      {!loading &&
        !error &&
        papers.length === 0 && (
          <div className="py-16 text-center">
            <FileText className="mx-auto mb-3 h-6 w-6 text-faint" />

            <p className="mb-1 text-[14px] text-muted-foreground">
              No papers found.
            </p>

            <p className="text-[12px] text-faint">
              Try a different search query.
            </p>
          </div>
        )}

      {/* Add to collection modal */}
      {selectedPaper && (
        <AddToCollectionModal
          paper={selectedPaper}
          collections={collections}
          collectionsLoading={
            collectionsLoading
          }
          addingToCollectionId={
            addingToCollectionId
          }
          addedCollectionIds={
            addedCollectionIds
          }
          isAdding={isAdding}
          error={addError}
          onAdd={
            handleAddToCollection
          }
          onClose={closeAddModal}
        />
      )}
    </div>
  );
}

/* ========================================================================== */
/* Add To Collection Modal                                                    */
/* ========================================================================== */

interface AddToCollectionModalProps {
  paper: PaperSearchResult;

  collections: {
    id: number;
    name: string;
    paper_count?: number;
    item_count?: number;
    count?: number;
  }[];

  collectionsLoading: boolean;

  addingToCollectionId:
    | number
    | null;

  addedCollectionIds: number[];

  isAdding: boolean;

  error: Error | null;

  onAdd: (
    collectionId: number,
  ) => void;

  onClose: () => void;
}

function AddToCollectionModal({
  paper,
  collections,
  collectionsLoading,
  addingToCollectionId,
  addedCollectionIds,
  isAdding,
  error,
  onAdd,
  onClose,
}: AddToCollectionModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose();
        }
      }}
    >
      <div className="w-full max-w-md rounded-lg border border-border bg-surface shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-sm font-medium text-foreground">
              Add to collection
            </h2>

            <p className="mt-1 line-clamp-2 text-[11px] text-faint">
              {paper.title}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isAdding}
            className="rounded-md p-1.5 text-faint transition-colors hover:bg-elevated hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Body */}
        <div className="max-h-[400px] overflow-y-auto px-5 py-4">
          {collectionsLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-5 w-5 animate-spin text-faint" />
            </div>
          ) : collections.length ===
            0 ? (
            <div className="py-8 text-center">
              <p className="text-[13px] text-muted-foreground">
                No collections yet.
              </p>

              <p className="mt-1 text-[11px] text-faint">
                Create a collection first.
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {collections.map(
                (collection) => {
                  const isAdded =
                    addedCollectionIds.includes(
                      collection.id,
                    );

                  const isThisAdding =
                    addingToCollectionId ===
                    collection.id;

                  return (
                    <button
                      key={
                        collection.id
                      }
                      type="button"
                      disabled={
                        isAdding ||
                        isAdded
                      }
                      onClick={() =>
                        onAdd(
                          collection.id,
                        )
                      }
                      className="flex w-full items-center justify-between rounded-md border border-transparent px-3 py-3 text-left transition-colors hover:border-border hover:bg-elevated disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-medium text-foreground">
                          {
                            collection.name
                          }
                        </p>

                        <p className="mt-0.5 text-[11px] text-faint">
                          {collection.paper_count ??
                            collection.item_count ??
                            collection.count ??
                            0}{" "}
                          papers
                        </p>
                      </div>

                      {isThisAdding ? (
                        <Loader2 className="h-4 w-4 animate-spin text-faint" />
                      ) : isAdded ? (
                        <Check className="h-4 w-4 text-primary" />
                      ) : (
                        <Plus className="h-4 w-4 text-faint" />
                      )}
                    </button>
                  );
                },
              )}
            </div>
          )}

          {error && (
            <div className="mt-3 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2.5">
              <p className="text-[12px] text-destructive">
                Failed to add paper to collection.
              </p>

              <p className="mt-1 text-[11px] text-faint">
                {error.message}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-border px-5 py-3.5">
          <button
            type="button"
            onClick={onClose}
            disabled={isAdding}
            className="rounded-md px-3 py-2 text-[12px] text-muted-foreground transition-colors hover:bg-elevated hover:text-foreground"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}