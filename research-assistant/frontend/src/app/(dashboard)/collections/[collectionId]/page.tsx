"use client";

import {
  ArrowLeft,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "../../components/app-shell";
import { CollectionItems } from "../../components/collections/collection-items";
import {
  getCollection,
  getCollectionItems,
  removeCollectionItem,
  type Collection,
  type CollectionItem,
} from "@/collections/api";

/* -------------------------------------------------------------------------- */
/* Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function getCollectionId(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }

  return value ?? "";
}

/* -------------------------------------------------------------------------- */
/* Page                                                                       */
/* -------------------------------------------------------------------------- */

export default function CollectionDetailPage() {
  const params = useParams<{ collectionId: string }>();
  const router = useRouter();

  const collectionId = getCollectionId(params?.collectionId);

  const [collection, setCollection] = useState<Collection | null>(null);
  const [items, setItems] = useState<CollectionItem[]>([]);

  const [isLoadingCollection, setIsLoadingCollection] = useState(true);
  const [isLoadingItems, setIsLoadingItems] = useState(true);

  const [collectionError, setCollectionError] = useState<string | null>(null);
  const [itemsError, setItemsError] = useState<string | null>(null);

  const [removingPaperId, setRemovingPaperId] = useState<number | null>(null);

  /* ------------------------------------------------------------------------ */
  /* Load collection                                                          */
  /* ------------------------------------------------------------------------ */

  const loadCollection = useCallback(async () => {
    if (!collectionId) {
      setCollectionError("Invalid collection ID.");
      setIsLoadingCollection(false);
      return;
    }

    setIsLoadingCollection(true);
    setCollectionError(null);

    try {
      const data = await getCollection(collectionId);
      setCollection(data);
    } catch (error) {
      console.error("Failed to load collection:", error);

      setCollection(null);

      setCollectionError(
        error instanceof Error
          ? error.message
          : "Unable to load this collection.",
      );
    } finally {
      setIsLoadingCollection(false);
    }
  }, [collectionId]);

  /* ------------------------------------------------------------------------ */
  /* Load collection items                                                    */
  /* ------------------------------------------------------------------------ */

  const loadItems = useCallback(async () => {
    if (!collectionId) {
      setItemsError("Invalid collection ID.");
      setIsLoadingItems(false);
      return;
    }

    setIsLoadingItems(true);
    setItemsError(null);

    try {
      const response = await getCollectionItems(collectionId, {
        page: 1,
        page_size: 100,
      });

      setItems(response.items ?? []);
    } catch (error) {
      console.error("Failed to load collection items:", error);

      setItems([]);

      setItemsError(
        error instanceof Error
          ? error.message
          : "Unable to load papers in this collection.",
      );
    } finally {
      setIsLoadingItems(false);
    }
  }, [collectionId]);

  /* ------------------------------------------------------------------------ */
  /* Initial load                                                             */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    void loadCollection();
    void loadItems();
  }, [loadCollection, loadItems]);

  /* ------------------------------------------------------------------------ */
  /* Open paper                                                               */
  /* ------------------------------------------------------------------------ */

  const handleOpenPaper = useCallback(
    (item: CollectionItem) => {
      router.push(`/papers/${item.paper_id}`);
    },
    [router],
  );

  /* ------------------------------------------------------------------------ */
  /* Remove paper                                                             */
  /* ------------------------------------------------------------------------ */

  const handleRemovePaper = useCallback(
    async (item: CollectionItem) => {
      if (!collectionId || !item.paper_id) {
        return;
      }

      setRemovingPaperId(item.paper_id);

      try {
        await removeCollectionItem(collectionId, {
          paper_id: item.paper_id,
        });

        setItems((currentItems) =>
          currentItems.filter(
            (currentItem) => currentItem.paper_id !== item.paper_id,
          ),
        );

        setCollection((currentCollection) => {
          if (!currentCollection) {
            return currentCollection;
          }

          return {
            ...currentCollection,
            item_count: Math.max(
              0,
              Number(currentCollection.item_count ?? items.length) - 1,
            ),
          };
        });
      } catch (error) {
        console.error("Failed to remove collection item:", error);

        window.alert(
          error instanceof Error
            ? error.message
            : "Unable to remove this paper from the collection.",
        );
      } finally {
        setRemovingPaperId(null);
      }
    },
    [collectionId, items.length],
  );

  /* ------------------------------------------------------------------------ */
  /* Refresh                                                                  */
  /* ------------------------------------------------------------------------ */

  const handleRefresh = useCallback(async () => {
    await Promise.all([loadCollection(), loadItems()]);
  }, [loadCollection, loadItems]);

  /* ------------------------------------------------------------------------ */
  /* Loading                                                                  */
  /* ------------------------------------------------------------------------ */

  if (isLoadingCollection) {
    return (
      <AppShell>
        <main className="min-h-full bg-black px-6 py-8">
          <div className="mx-auto max-w-7xl">
            <div className="h-4 w-32 animate-pulse rounded bg-white/5" />

            <div className="mt-8 h-8 w-64 animate-pulse rounded bg-white/5" />

            <div className="mt-3 h-4 w-96 max-w-full animate-pulse rounded bg-white/5" />

            <div className="mt-8 rounded-xl border border-white/10 bg-zinc-950 p-6">
              <div className="h-5 w-24 animate-pulse rounded bg-white/5" />
              <div className="mt-6 space-y-3">
                {[1, 2, 3].map((item) => (
                  <div
                    key={item}
                    className="h-20 animate-pulse rounded-lg bg-white/[0.03]"
                  />
                ))}
              </div>
            </div>
          </div>
        </main>
      </AppShell>
    );
  }

  /* ------------------------------------------------------------------------ */
  /* Collection not found / error                                             */
  /* ------------------------------------------------------------------------ */

  if (collectionError || !collection) {
    return (
      <AppShell>
        <main className="min-h-full bg-black px-6 py-8">
          <div className="mx-auto max-w-7xl">
            <Link
              href="/collections"
              className="inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-200"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Collections
            </Link>

            <div className="mt-12 rounded-xl border border-rose-500/20 bg-rose-500/[0.04] p-8">
              <h1 className="text-lg font-semibold text-zinc-100">
                Collection unavailable
              </h1>

              <p className="mt-2 text-sm text-zinc-500">
                {collectionError ??
                  "The requested collection could not be found."}
              </p>

              <button
                type="button"
                onClick={handleRefresh}
                className="mt-5 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-zinc-300 transition hover:bg-white/[0.08] hover:text-white"
              >
                <RefreshCw className="h-4 w-4" />
                Try again
              </button>
            </div>
          </div>
        </main>
      </AppShell>
    );
  }

  const collectionName = collection.name ?? "Untitled collection";

  const collectionDescription =
    collection.description?.trim() ||
    "Organize and explore papers collected for this research topic.";

  const itemCount =
    collection.item_count ??
    collection.paper_count ??
    items.length;

  return (
    <AppShell>
      <main className="min-h-full bg-black px-6 py-8">
        <div className="mx-auto max-w-7xl">
          {/* ---------------------------------------------------------------- */}
          {/* Header                                                            */}
          {/* ---------------------------------------------------------------- */}

          <div className="flex items-center justify-between gap-4">
            <Link
              href="/collections"
              className="inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-200"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Collections
            </Link>

            <button
              type="button"
              onClick={handleRefresh}
              disabled={isLoadingCollection || isLoadingItems}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs font-medium text-zinc-400 transition hover:bg-white/[0.06] hover:text-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw
                className={[
                  "h-3.5 w-3.5",
                  isLoadingCollection || isLoadingItems
                    ? "animate-spin"
                    : "",
                ].join(" ")}
              />
              Refresh
            </button>
          </div>

          {/* ---------------------------------------------------------------- */}
          {/* Collection heading                                                */}
          {/* ---------------------------------------------------------------- */}

          <section className="mt-8">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-cyan-400/10 bg-cyan-400/[0.06]">
                    <FileText className="h-5 w-5 text-cyan-400" />
                  </div>

                  <div className="min-w-0">
                    <h1 className="truncate text-2xl font-semibold tracking-tight text-zinc-100">
                      {collectionName}
                    </h1>

                    <p className="mt-1 text-xs text-zinc-600">
                      Collection #{collection.id}
                    </p>
                  </div>
                </div>

                <p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-500">
                  {collectionDescription}
                </p>
              </div>

              <button
                type="button"
                className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-white/[0.08] hover:text-white"
              >
                <Plus className="h-4 w-4" />
                Add papers
              </button>
            </div>

            {/* -------------------------------------------------------------- */}
            {/* Stats                                                           */}
            {/* -------------------------------------------------------------- */}

            <div className="mt-7 flex items-center gap-6 border-y border-white/5 py-4">
              <div>
                <p className="text-xl font-semibold text-zinc-100">
                  {itemCount}
                </p>

                <p className="mt-0.5 text-[11px] uppercase tracking-wider text-zinc-600">
                  {itemCount === 1 ? "Paper" : "Papers"}
                </p>
              </div>

              <div className="h-8 w-px bg-white/5" />

              <div>
                <p className="text-sm font-medium text-zinc-400">
                  Research collection
                </p>

                <p className="mt-0.5 text-[11px] text-zinc-600">
                  Papers saved for later exploration
                </p>
              </div>
            </div>
          </section>

          {/* ---------------------------------------------------------------- */}
          {/* Papers                                                            */}
          {/* ---------------------------------------------------------------- */}

          <section className="mt-8">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-zinc-200">
                  Papers
                </h2>

                <p className="mt-1 text-xs text-zinc-600">
                  Papers saved in this collection.
                </p>
              </div>

              {isLoadingItems && (
                <Loader2 className="h-4 w-4 animate-spin text-zinc-600" />
              )}
            </div>

            {itemsError ? (
              <div className="rounded-xl border border-rose-500/20 bg-rose-500/[0.03] p-6">
                <p className="text-sm font-medium text-zinc-300">
                  Unable to load papers
                </p>

                <p className="mt-1 text-xs leading-5 text-zinc-600">
                  {itemsError}
                </p>

                <button
                  type="button"
                  onClick={loadItems}
                  className="mt-4 inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-zinc-400 transition hover:bg-white/[0.08] hover:text-zinc-200"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Retry
                </button>
              </div>
            ) : (
              <CollectionItems
                items={items}
                isLoading={isLoadingItems}
                onOpen={handleOpenPaper}
                onRemove={handleRemovePaper}
              />
            )}

            {removingPaperId !== null && (
              <div className="mt-3 flex items-center gap-2 text-xs text-zinc-600">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Removing paper...
              </div>
            )}
          </section>
        </div>
      </main>
    </AppShell>
  );
}