"use client";

import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type MouseEvent,
} from "react";

import Link from "next/link";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";

import {
  addCollectionItem,
  createCollection as createCollectionApi,
  deleteCollection as deleteCollectionApi,
} from "@/collections/api";

import {
  type Collection,
  type CollectionItem,
} from "@/collections/types";

import { useCollections } from "@/collections/hooks/use-collections";

import {
  collectionKeys,
  useCollection,
} from "@/collections/hooks/use-collection";

import { getPapers } from "@/lib/papers";

import type { Paper } from "@/types/paper";

import { SectionLabel } from "../components/primitives";
import { cn } from "./lib/utils";

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

const PAGE_SIZE_OPTIONS = [10, 25, 50] as const;

const DEFAULT_PAGE_SIZE = 10;

const PAPER_PICKER_PAGE_SIZE = 20;

/* -------------------------------------------------------------------------- */
/* Generic API helpers                                                        */
/* -------------------------------------------------------------------------- */

type CollectionLike = {
  id: string | number;
  name?: string | null;
  description?: string | null;
  paper_count?: number | null;
};

function normalizePaperId(value: unknown): number | null {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return null;
  }

  const id = Number(value);

  if (!Number.isInteger(id) || id <= 0) {
    return null;
  }

  return id;
}

function normalizeCollectionId(
  value: unknown,
): string | null {
  if (
    value === null ||
    value === undefined
  ) {
    return null;
  }

  const id = String(value).trim();

  return id.length > 0 ? id : null;
}

function normalizeCollections(
  data: unknown,
): CollectionLike[] {
  if (Array.isArray(data)) {
    return data as CollectionLike[];
  }

  if (
    data &&
    typeof data === "object" &&
    "items" in data
  ) {
    const items = (
      data as {
        items?: unknown;
      }
    ).items;

    if (Array.isArray(items)) {
      return items as CollectionLike[];
    }
  }

  return [];
}

function normalizePapers(
  data: unknown,
): Paper[] {
  if (Array.isArray(data)) {
    return data as Paper[];
  }

  if (
    data &&
    typeof data === "object" &&
    "items" in data
  ) {
    const items = (
      data as {
        items?: unknown;
      }
    ).items;

    if (Array.isArray(items)) {
      return items as Paper[];
    }
  }

  return [];
}

/* -------------------------------------------------------------------------- */
/* Error helpers                                                              */
/* -------------------------------------------------------------------------- */

function getErrorMessage(
  error: unknown,
): string {
  if (error instanceof Error) {
    return (
      error.message ||
      "Something went wrong. Please try again."
    );
  }

  if (
    error &&
    typeof error === "object"
  ) {
    const value =
      error as Record<
        string,
        unknown
      >;

    if (
      typeof value.message === "string" &&
      value.message.trim()
    ) {
      return value.message;
    }

    if (
      typeof value.detail === "string" &&
      value.detail.trim()
    ) {
      return value.detail;
    }

    if (
      typeof value.error === "string" &&
      value.error.trim()
    ) {
      return value.error;
    }

    if (
      typeof value.code === "string" &&
      value.code.trim()
    ) {
      return value.code;
    }
  }

  return "Something went wrong. Please try again.";
}

function getErrorDetails(
  error: unknown,
): {
  name?: string;
  message?: string;
  stack?: string;
  status?: number;
  code?: string;
  details?: unknown;
  data?: unknown;
  detail?: unknown;
  error?: unknown;
  value?: unknown;
} {
  if (error instanceof Error) {
    const candidate =
      error as Error & {
        status?: unknown;
        code?: unknown;
        details?: unknown;
        data?: unknown;
        detail?: unknown;
        error?: unknown;
      };

    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
      status:
        typeof candidate.status ===
        "number"
          ? candidate.status
          : undefined,
      code:
        typeof candidate.code ===
        "string"
          ? candidate.code
          : undefined,
      details: candidate.details,
      data: candidate.data,
      detail: candidate.detail,
      error: candidate.error,
    };
  }

  if (
    error &&
    typeof error === "object"
  ) {
    const value =
      error as Record<
        string,
        unknown
      >;

    return {
      name:
        typeof value.name ===
        "string"
          ? value.name
          : undefined,
      message:
        typeof value.message ===
        "string"
          ? value.message
          : undefined,
      stack:
        typeof value.stack ===
        "string"
          ? value.stack
          : undefined,
      status:
        typeof value.status ===
        "number"
          ? value.status
          : undefined,
      code:
        typeof value.code ===
        "string"
          ? value.code
          : undefined,
      details: value.details,
      data: value.data,
      detail: value.detail,
      error: value.error,
    };
  }

  return {
    value: error,
  };
}

/* -------------------------------------------------------------------------- */
/* Author helpers                                                             */
/* -------------------------------------------------------------------------- */

function renderAuthors(
  authors: unknown,
): string | null {
  if (!authors) {
    return null;
  }

  if (Array.isArray(authors)) {
    const values =
      authors
        .map((author) => {
          if (
            author &&
            typeof author === "object" &&
            "full_name" in author
          ) {
            const fullName = (
              author as {
                full_name?: unknown;
              }
            ).full_name;

            return typeof fullName ===
              "string"
              ? fullName.trim()
              : "";
          }

          if (
            author &&
            typeof author === "object" &&
            "name" in author
          ) {
            const name = (
              author as {
                name?: unknown;
              }
            ).name;

            return typeof name ===
              "string"
              ? name.trim()
              : "";
          }

          return String(author).trim();
        })
        .filter(Boolean);

    return values.length > 0
      ? values.join(", ")
      : null;
  }

  const value =
    String(authors).trim();

  return value || null;
}

/* -------------------------------------------------------------------------- */
/* Collection helpers                                                         */
/* -------------------------------------------------------------------------- */

function getPaperCount(
  collection: CollectionLike,
): number {
  return typeof collection.paper_count ===
    "number"
    ? collection.paper_count
    : 0;
}

/* -------------------------------------------------------------------------- */
/* Component                                                                  */
/* -------------------------------------------------------------------------- */

export function CollectionsPage() {
  const queryClient =
    useQueryClient();

  /* ------------------------------------------------------------------------ */
  /* Collections                                                              */
  /* ------------------------------------------------------------------------ */

  const {
    data: collectionsData,
    isLoading: collectionsLoading,
    error: collectionsError,
  } = useCollections();

  const collections =
    useMemo(
      () =>
        normalizeCollections(
          collectionsData,
        ),
      [collectionsData],
    );

  /* ------------------------------------------------------------------------ */
  /* Local state                                                              */
  /* ------------------------------------------------------------------------ */

  const [
    activeCollectionId,
    setActiveCollectionId,
  ] = useState<string | null>(
    null,
  );

  const [
    createMode,
    setCreateMode,
  ] = useState(false);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    currentPage,
    setCurrentPage,
  ] = useState(1);

  const [
    pageSize,
    setPageSize,
  ] = useState<number>(
    DEFAULT_PAGE_SIZE,
  );

  const [
    collectionName,
    setCollectionName,
  ] = useState("");

  const [
    collectionDescription,
    setCollectionDescription,
  ] = useState("");

  const [
    paperPickerSearch,
    setPaperPickerSearch,
  ] = useState("");

  const [
    selectedPaperIds,
    setSelectedPaperIds,
  ] = useState<number[]>(
    [],
  );

  const [
    createError,
    setCreateError,
  ] = useState<string | null>(
    null,
  );

  const [
    addPaperErrors,
    setAddPaperErrors,
  ] = useState<string[]>(
    [],
  );

  /* ------------------------------------------------------------------------ */
  /* Active collection                                                        */
  /* ------------------------------------------------------------------------ */

  const activeCollection =
    useMemo(() => {
      if (!activeCollectionId) {
        return null;
      }

      return (
        collections.find(
          (item) =>
            String(item.id) ===
            String(
              activeCollectionId,
            ),
        ) ?? null
      );
    }, [
      collections,
      activeCollectionId,
    ]);

  /* ------------------------------------------------------------------------ */
  /* Collection detail                                                        */
  /* ------------------------------------------------------------------------ */

  const {
    data: collection,
    isLoading: collectionLoading,
    error: collectionError,
  } = useCollection(
    activeCollectionId ?? undefined,
    {
      enabled:
        !createMode &&
        Boolean(activeCollectionId) &&
        Boolean(activeCollection),
    },
  );

  /* ------------------------------------------------------------------------ */
  /* Paper picker                                                             */
  /* ------------------------------------------------------------------------ */

  const {
    data: papersData,
    isLoading: papersLoading,
  } = useQuery({
    queryKey: [
      "papers",
      "collection-picker",
      paperPickerSearch.trim(),
    ],

    queryFn: () =>
      getPapers({
        page: 1,
        page_size:
          PAPER_PICKER_PAGE_SIZE,

        // FIX:
        // PaperSearchParams uses `query`, not `search`.
        query:
          paperPickerSearch.trim() ||
          undefined,
      }),

    enabled: createMode,

    staleTime: 30_000,
  });

  const papers =
    useMemo(
      () =>
        normalizePapers(
          papersData,
        ),
      [papersData],
    );

  /* ------------------------------------------------------------------------ */
  /* Collection filtering                                                     */
  /* ------------------------------------------------------------------------ */

  const filteredCollections =
    useMemo(() => {
      const query =
        search
          .trim()
          .toLowerCase();

      if (!query) {
        return collections;
      }

      return collections.filter(
        (item) => {
          const name =
            typeof item.name ===
            "string"
              ? item.name.toLowerCase()
              : "";

          const description =
            typeof item.description ===
            "string"
              ? item.description.toLowerCase()
              : "";

          return (
            name.includes(query) ||
            description.includes(
              query,
            )
          );
        },
      );
    }, [
      collections,
      search,
    ]);

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        filteredCollections.length /
          pageSize,
      ),
    );

  const visibleCollections =
    useMemo(() => {
      const start =
        (currentPage - 1) *
        pageSize;

      return filteredCollections.slice(
        start,
        start + pageSize,
      );
    }, [
      filteredCollections,
      currentPage,
      pageSize,
    ]);

  /* ------------------------------------------------------------------------ */
  /* Mutations                                                                */
  /* ------------------------------------------------------------------------ */

  const createCollection =
    useMutation({
      mutationFn:
        createCollectionApi,
    });

  const addCollectionItemMutation =
    useMutation({
      mutationFn: ({
        collectionId,
        paperId,
      }: {
        collectionId:
          | string
          | number;
        paperId:
          | number
          | string;
      }) =>
        addCollectionItem(
          collectionId,
          {
            paper_id:
              Number(paperId),
          },
        ),
    });

  const addToCollection =
    addCollectionItemMutation
      .mutateAsync;

  const addToCollectionPending =
    addCollectionItemMutation
      .isPending;

  const deleteCollection =
    useMutation({
      mutationFn: (
        collectionId:
          | string
          | number,
      ) =>
        deleteCollectionApi(
          collectionId,
        ),
    });

  /* ------------------------------------------------------------------------ */
  /* Synchronize active collection                                           */
  /* ------------------------------------------------------------------------ */

  useEffect(() => {
    if (createMode) {
      return;
    }

    if (collections.length === 0) {
      if (
        activeCollectionId !==
        null
      ) {
        setActiveCollectionId(
          null,
        );
      }

      return;
    }

    if (
      activeCollectionId ===
      null
    ) {
      const firstId =
        normalizeCollectionId(
          collections[0]?.id,
        );

      if (firstId) {
        setActiveCollectionId(
          firstId,
        );
      }

      return;
    }

    const exists =
      collections.some(
        (item) =>
          String(item.id) ===
          String(
            activeCollectionId,
          ),
      );

    if (!exists) {
      const firstId =
        normalizeCollectionId(
          collections[0]?.id,
        );

      if (firstId) {
        setActiveCollectionId(
          firstId,
        );
      }
    }
  }, [
    collections,
    activeCollectionId,
    createMode,
  ]);

  useEffect(() => {
    if (
      currentPage >
      totalPages
    ) {
      setCurrentPage(
        totalPages,
      );
    }
  }, [
    currentPage,
    totalPages,
  ]);

  /* ------------------------------------------------------------------------ */
  /* Create helpers                                                           */
  /* ------------------------------------------------------------------------ */

  function resetCreateForm() {
    setCollectionName("");
    setCollectionDescription("");
    setSelectedPaperIds([]);
    setPaperPickerSearch("");
    setCreateError(null);
    setAddPaperErrors([]);
  }

  function openCreateCollection() {
    resetCreateForm();
    setCreateMode(true);
  }

  function cancelCreateCollection() {
    if (
      createCollection.isPending ||
      addToCollectionPending
    ) {
      return;
    }

    resetCreateForm();
    setCreateMode(false);
  }

  function handleTogglePaper(
    paperId: unknown,
  ) {
    const normalizedId =
      normalizePaperId(
        paperId,
      );

    if (
      normalizedId ===
      null
    ) {
      return;
    }

    setSelectedPaperIds(
      (previous) => {
        if (
          previous.includes(
            normalizedId,
          )
        ) {
          return previous.filter(
            (id) =>
              id !==
              normalizedId,
          );
        }

        return [
          ...previous,
          normalizedId,
        ];
      },
    );
  }

  /* ------------------------------------------------------------------------ */
  /* Create collection                                                        */
  /* ------------------------------------------------------------------------ */

  async function handleCreateCollection(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      createCollection.isPending ||
      addToCollectionPending
    ) {
      return;
    }

    setCreateError(null);
    setAddPaperErrors([]);

    const name =
      collectionName.trim();

    const description =
      collectionDescription.trim();

    if (!name) {
      setCreateError(
        "Collection name is required.",
      );

      return;
    }

    const papersToAdd =
      Array.from(
        new Set(
          selectedPaperIds
            .map(
              normalizePaperId,
            )
            .filter(
              (
                id,
              ): id is number =>
                id !== null,
            ),
        ),
      );

    try {
      console.log(
        "[collections] Creating collection",
        {
          name,
          description,
          papersToAdd,
        },
      );

      const created =
        await createCollection.mutateAsync(
          {
            name,
            description:
              description ||
              null,
            archived: false,
          },
        );

      console.log(
        "[collections] Collection created",
        created,
      );

      const createdCollectionId =
        normalizeCollectionId(
          created?.id,
        );

      if (
        !createdCollectionId
      ) {
        throw new Error(
          "The server created the collection but did not return a valid collection ID.",
        );
      }

      const failedPapers: string[] =
        [];

      let successfulPapers =
        0;

      for (
        const paperId of
        papersToAdd
      ) {
        try {
          console.log(
            "[collections] Linking selected paper",
            {
              collectionId:
                createdCollectionId,
              paperId,
            },
          );

          await addToCollection({
            collectionId:
              createdCollectionId,
            paperId,
          });

          successfulPapers += 1;

          console.log(
            "[collections] Selected paper linked",
            {
              collectionId:
                createdCollectionId,
              paperId,
            },
          );
        } catch (
          paperError
        ) {
          const message =
            getErrorMessage(
              paperError,
            );

          const details =
            getErrorDetails(
              paperError,
            );

          console.error(
            "[collections] Failed to link selected paper",
            {
              collectionId:
                createdCollectionId,
              paperId,
              message,
              ...details,
            },
          );

          failedPapers.push(
            `Paper ${paperId}: ${message}`,
          );
        }
      }

      await queryClient.invalidateQueries(
        {
          queryKey:
            collectionKeys.all,
        },
      );

      await queryClient.invalidateQueries(
        {
          queryKey:
            collectionKeys.detail(
              createdCollectionId,
            ),
        },
      );

      setActiveCollectionId(
        createdCollectionId,
      );

      setSearch("");
      setCurrentPage(1);

      setCreateMode(false);

      setCollectionName("");
      setCollectionDescription("");
      setSelectedPaperIds([]);
      setPaperPickerSearch("");
      setCreateError(null);

      if (
        failedPapers.length > 0
      ) {
        setAddPaperErrors(
          failedPapers,
        );
      }

      console.log(
        "[collections] Creation completed",
        {
          collectionId:
            createdCollectionId,
          requestedPapers:
            papersToAdd.length,
          successfullyAdded:
            successfulPapers,
          failedPapers:
            failedPapers.length,
          failedPaperMessages:
            failedPapers,
        },
      );
    } catch (error) {
      const message =
        getErrorMessage(error);

      const details =
        getErrorDetails(error);

      console.error(
        "[collections] CREATE COLLECTION FAILED",
        {
          message,
          ...details,
        },
      );

      setCreateError(
        message,
      );
    }
  }

  /* ------------------------------------------------------------------------ */
  /* Delete collection                                                        */
  /* ------------------------------------------------------------------------ */

  async function handleDeleteCollection(
    event: MouseEvent<HTMLButtonElement>,
    collectionId:
      | string
      | number,
  ) {
    event.stopPropagation();

    if (
      deleteCollection.isPending
    ) {
      return;
    }

    const normalizedId =
      normalizeCollectionId(
        collectionId,
      );

    if (!normalizedId) {
      console.error(
        "[collections] Cannot delete collection: invalid ID",
        {
          collectionId,
        },
      );

      return;
    }

    const confirmed =
      window.confirm(
        "Are you sure you want to delete this collection?",
      );

    if (!confirmed) {
      return;
    }

    try {
      await deleteCollection.mutateAsync(
        normalizedId,
      );

      queryClient.removeQueries(
        {
          queryKey:
            collectionKeys.detail(
              normalizedId,
            ),
          exact: false,
        },
      );

      if (
        String(
          activeCollectionId,
        ) === normalizedId
      ) {
        setActiveCollectionId(
          null,
        );
      }

      await queryClient.invalidateQueries(
        {
          queryKey:
            collectionKeys.all,
        },
      );

      console.log(
        "[collections] Collection deleted",
        {
          collectionId:
            normalizedId,
        },
      );
    } catch (error) {
      const message =
        getErrorMessage(error);

      const details =
        getErrorDetails(error);

      console.error(
        "[collections] DELETE FAILED",
        {
          collectionId:
            normalizedId,
          message,
          ...details,
        },
      );
    }
  }

  /* ------------------------------------------------------------------------ */
  /* Errors                                                                   */
  /* ------------------------------------------------------------------------ */

  const collectionListError =
    collectionsError
      ? getErrorMessage(
          collectionsError,
        )
      : null;

  const detailError =
    collectionError
      ? getErrorMessage(
          collectionError,
        )
      : null;

  /* ------------------------------------------------------------------------ */
  /* Render                                                                   */
  /* ------------------------------------------------------------------------ */

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex shrink-0 items-center justify-between border-b px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">
            Collections
          </h1>

          <p className="mt-1 text-sm text-muted-foreground">
            Organize your research papers into collections.
          </p>
        </div>

        <button
          type="button"
          onClick={
            openCreateCollection
          }
          disabled={createMode}
          className={cn(
            "inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground",
            "hover:opacity-90",
            createMode &&
              "cursor-not-allowed opacity-60",
          )}
        >
          <Plus className="h-4 w-4" />
          New collection
        </button>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-[320px_minmax(0,1fr)]">
        <aside className="flex min-h-0 flex-col border-r">
          <div className="border-b p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />

              <input
                value={search}
                onChange={(event) => {
                  setSearch(
                    event.target.value,
                  );

                  setCurrentPage(1);
                }}
                placeholder="Search collections..."
                disabled={createMode}
                className="w-full rounded-md border bg-background py-2 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
              />
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            {collectionsLoading ? (
              <div className="p-6 text-sm text-muted-foreground">
                Loading collections...
              </div>
            ) : collectionListError ? (
              <div className="p-6 text-sm text-destructive">
                {collectionListError}
              </div>
            ) : visibleCollections.length ===
              0 ? (
              <div className="p-6 text-sm text-muted-foreground">
                {search.trim()
                  ? "No collections match your search."
                  : "No collections found."}
              </div>
            ) : (
              <div className="space-y-1 p-3">
                {visibleCollections.map(
                  (item) => {
                    const normalizedId =
                      normalizeCollectionId(
                        item.id,
                      );

                    if (
                      !normalizedId
                    ) {
                      return null;
                    }

                    const isActive =
                      !createMode &&
                      normalizedId ===
                        activeCollectionId;

                    const paperCount =
                      getPaperCount(
                        item,
                      );

                    return (
                      <div
                        key={
                          normalizedId
                        }
                        className={cn(
                          "group flex w-full items-center gap-1 rounded-md transition",
                          isActive
                            ? "bg-muted"
                            : "hover:bg-muted/60",
                        )}
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setCreateMode(
                              false,
                            );

                            setActiveCollectionId(
                              normalizedId,
                            );
                          }}
                          className="flex min-w-0 flex-1 items-center gap-3 rounded-md px-3 py-3 text-left"
                          aria-current={
                            isActive
                              ? "true"
                              : undefined
                          }
                        >
                          <FolderOpen className="h-4 w-4 shrink-0" />

                          <div className="min-w-0 flex-1">
                            <div className="truncate text-sm font-medium">
                              {item.name ||
                                "Untitled collection"}
                            </div>

                            <div className="mt-0.5 text-xs text-muted-foreground">
                              {
                                paperCount
                              }{" "}
                              {paperCount ===
                              1
                                ? "paper"
                                : "papers"}
                            </div>
                          </div>
                        </button>

                        <button
                          type="button"
                          onClick={(
                            event,
                          ) =>
                            handleDeleteCollection(
                              event,
                              normalizedId,
                            )
                          }
                          disabled={
                            deleteCollection.isPending
                          }
                          className="mr-2 rounded p-1 opacity-0 transition hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100 disabled:cursor-not-allowed disabled:opacity-50"
                          aria-label={`Delete ${
                            item.name ??
                            "collection"
                          }`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    );
                  },
                )}
              </div>
            )}
          </div>

          <div className="flex shrink-0 items-center justify-between border-t p-3">
            <select
              value={pageSize}
              onChange={(event) => {
                const nextSize =
                  Number(
                    event.target
                      .value,
                  );

                if (
                  !PAGE_SIZE_OPTIONS.includes(
                    nextSize as (typeof PAGE_SIZE_OPTIONS)[number],
                  )
                ) {
                  return;
                }

                setPageSize(
                  nextSize,
                );

                setCurrentPage(1);
              }}
              disabled={createMode}
              className="rounded border bg-background px-2 py-1 text-xs disabled:opacity-50"
              aria-label="Collections per page"
            >
              {PAGE_SIZE_OPTIONS.map(
                (size) => (
                  <option
                    key={size}
                    value={size}
                  >
                    {size}
                  </option>
                ),
              )}
            </select>

            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled={
                  createMode ||
                  currentPage <=
                    1
                }
                onClick={() =>
                  setCurrentPage(
                    (page) =>
                      Math.max(
                        1,
                        page - 1,
                      ),
                  )
                }
                className="rounded p-1 hover:bg-muted disabled:opacity-40"
                aria-label="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              <span className="px-2 text-xs text-muted-foreground">
                {currentPage} /{" "}
                {totalPages}
              </span>

              <button
                type="button"
                disabled={
                  createMode ||
                  currentPage >=
                    totalPages
                }
                onClick={() =>
                  setCurrentPage(
                    (page) =>
                      Math.min(
                        totalPages,
                        page + 1,
                      ),
                  )
                }
                className="rounded p-1 hover:bg-muted disabled:opacity-40"
                aria-label="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </aside>

        <main className="min-h-0 overflow-y-auto">
          {createMode ? (
            <div className="mx-auto w-full max-w-4xl p-8">
              <div className="flex items-start justify-between gap-6 border-b pb-6">
                <div>
                  <h2 className="text-2xl font-semibold tracking-tight">
                    Create collection
                  </h2>

                  <p className="mt-2 text-sm text-muted-foreground">
                    Create a collection and select the research papers it should contain.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={
                    cancelCreateCollection
                  }
                  disabled={
                    createCollection.isPending ||
                    addToCollectionPending
                  }
                  className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <X className="h-4 w-4" />
                  Cancel
                </button>
              </div>

              <form
                onSubmit={
                  handleCreateCollection
                }
                className="mt-8"
              >
                <div className="space-y-7">
                  <div>
                    <label
                      htmlFor="collection-name"
                      className="mb-2 block text-sm font-medium"
                    >
                      Name
                    </label>

                    <input
                      id="collection-name"
                      value={
                        collectionName
                      }
                      onChange={(
                        event,
                      ) => {
                        setCollectionName(
                          event.target
                            .value,
                        );

                        if (
                          createError
                        ) {
                          setCreateError(
                            null,
                          );
                        }
                      }}
                      placeholder="e.g. RAG Research"
                      autoFocus
                      disabled={
                        createCollection.isPending ||
                        addToCollectionPending
                      }
                      className="w-full rounded-md border bg-background px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                    />
                  </div>

                  <div>
                    <label
                      htmlFor="collection-description"
                      className="mb-2 block text-sm font-medium"
                    >
                      Description
                    </label>

                    <textarea
                      id="collection-description"
                      value={
                        collectionDescription
                      }
                      onChange={(
                        event,
                      ) =>
                        setCollectionDescription(
                          event.target
                            .value,
                        )
                      }
                      placeholder="Optional description"
                      rows={4}
                      disabled={
                        createCollection.isPending ||
                        addToCollectionPending
                      }
                      className="w-full resize-none rounded-md border bg-background px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                    />
                  </div>

                  {createError && (
                    <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                      {createError}
                    </div>
                  )}

                  <div>
                    <div className="mb-3 flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-medium">
                          Papers
                        </h3>

                        <p className="mt-1 text-xs text-muted-foreground">
                          Select the papers that should belong to this collection.
                        </p>
                      </div>

                      <span className="rounded-full border px-2.5 py-1 text-xs font-medium text-muted-foreground">
                        {
                          selectedPaperIds.length
                        }{" "}
                        selected
                      </span>
                    </div>

                    <div className="relative mb-3">
                      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />

                      <input
                        value={
                          paperPickerSearch
                        }
                        onChange={(
                          event,
                        ) =>
                          setPaperPickerSearch(
                            event.target
                              .value,
                          )
                        }
                        placeholder="Search papers..."
                        disabled={
                          createCollection.isPending ||
                          addToCollectionPending
                        }
                        className="w-full rounded-md border bg-background py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
                      />
                    </div>

                    <div className="overflow-hidden rounded-lg border">
                      {papersLoading ? (
                        <div className="p-8 text-center text-sm text-muted-foreground">
                          Loading papers...
                        </div>
                      ) : papers.length ===
                        0 ? (
                        <div className="p-8 text-center">
                          <FolderOpen className="mx-auto h-8 w-8 text-muted-foreground" />

                          <p className="mt-3 text-sm font-medium">
                            No papers found
                          </p>

                          <p className="mt-1 text-xs text-muted-foreground">
                            Try a different search.
                          </p>
                        </div>
                      ) : (
                        <div className="max-h-[420px] overflow-y-auto">
                          {papers.map(
                            (
                              paper,
                            ) => {
                              const paperId =
                                normalizePaperId(
                                  paper.id,
                                );

                              if (
                                paperId ===
                                null
                              ) {
                                return null;
                              }

                              const selected =
                                selectedPaperIds.includes(
                                  paperId,
                                );

                              const authors =
                                renderAuthors(
                                  paper.authors,
                                );

                              return (
                                <button
                                  key={
                                    paperId
                                  }
                                  type="button"
                                  onClick={() =>
                                    handleTogglePaper(
                                      paperId,
                                    )
                                  }
                                  disabled={
                                    createCollection.isPending ||
                                    addToCollectionPending
                                  }
                                  className={cn(
                                    "flex w-full items-center gap-4 border-b p-4 text-left transition last:border-b-0 hover:bg-muted/50 disabled:cursor-not-allowed disabled:opacity-60",
                                    selected &&
                                      "bg-muted/70",
                                  )}
                                >
                                  <span
                                    className={cn(
                                      "flex h-5 w-5 shrink-0 items-center justify-center rounded border text-xs font-semibold transition",
                                      selected &&
                                        "border-primary bg-primary text-primary-foreground",
                                    )}
                                    aria-hidden="true"
                                  >
                                    {selected
                                      ? "✓"
                                      : ""}
                                  </span>

                                  <span className="min-w-0 flex-1">
                                    <span className="block truncate text-sm font-medium">
                                      {paper.title ||
                                        "Untitled paper"}
                                    </span>

                                    {authors && (
                                      <span className="mt-1 block truncate text-xs text-muted-foreground">
                                        {authors}
                                      </span>
                                    )}
                                  </span>
                                </button>
                              );
                            },
                          )}
                        </div>
                      )}
                    </div>

                    <p className="mt-3 text-xs text-muted-foreground">
                      The papers you select here will appear in the collection after it is created.
                    </p>
                  </div>
                </div>

                <div className="mt-8 flex items-center justify-end gap-3 border-t pt-6">
                  <button
                    type="button"
                    onClick={
                      cancelCreateCollection
                    }
                    disabled={
                      createCollection.isPending ||
                      addToCollectionPending
                    }
                    className="rounded-md border px-4 py-2.5 text-sm font-medium hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={
                      !collectionName.trim() ||
                      createCollection.isPending ||
                      addToCollectionPending
                    }
                    className="rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {createCollection.isPending ||
                    addToCollectionPending
                      ? "Creating..."
                      : "Create collection"}
                  </button>
                </div>
              </form>
            </div>
          ) : !activeCollectionId ? (
            <div className="flex h-full items-center justify-center p-10">
              <div className="max-w-md text-center">
                <FolderOpen className="mx-auto h-10 w-10 text-muted-foreground" />

                <h2 className="mt-4 text-lg font-medium">
                  No collection selected
                </h2>

                <p className="mt-1 text-sm text-muted-foreground">
                  Create a collection to organize your research papers.
                </p>

                <button
                  type="button"
                  onClick={
                    openCreateCollection
                  }
                  className="mt-5 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
                >
                  <Plus className="h-4 w-4" />
                  Create collection
                </button>
              </div>
            </div>
          ) : !activeCollection ? (
            <div className="p-8 text-sm text-muted-foreground">
              Synchronizing collection...
            </div>
          ) : collectionLoading ? (
            <div className="p-8 text-sm text-muted-foreground">
              Loading collection...
            </div>
          ) : detailError ? (
            <div className="p-8">
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4">
                <div className="text-sm font-medium text-destructive">
                  Failed to load collection
                </div>

                <div className="mt-1 text-sm text-muted-foreground">
                  {detailError}
                </div>
              </div>
            </div>
          ) : !collection ? (
            <div className="p-8 text-sm text-muted-foreground">
              Collection not found.
            </div>
          ) : (
            <div className="mx-auto w-full max-w-5xl p-8">
              <div className="flex items-start justify-between gap-6 border-b pb-6">
                <div className="min-w-0">
                  <h2 className="truncate text-2xl font-semibold tracking-tight">
                    {collection.name}
                  </h2>

                  {collection.description && (
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                      {
                        collection.description
                      }
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={(
                    event,
                  ) =>
                    handleDeleteCollection(
                      event,
                      collection.id,
                    )
                  }
                  disabled={
                    deleteCollection.isPending
                  }
                  className="inline-flex shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-destructive/10 hover:text-destructive disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </button>
              </div>

              {addPaperErrors.length >
                0 && (
                <div className="mt-5 rounded-md border border-amber-500/30 bg-amber-500/10 px-4 py-3">
                  <div className="text-sm font-medium text-amber-700 dark:text-amber-400">
                    Some selected papers could not be linked to this collection.
                  </div>

                  <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                    {addPaperErrors.map(
                      (
                        message,
                        index,
                      ) => (
                        <li
                          key={`${message}-${index}`}
                        >
                          {message}
                        </li>
                      ),
                    )}
                  </ul>

                  <button
                    type="button"
                    onClick={() =>
                      setAddPaperErrors(
                        [],
                      )
                    }
                    className="mt-3 text-xs font-medium text-amber-700 hover:underline dark:text-amber-400"
                  >
                    Dismiss
                  </button>
                </div>
              )}

              <div className="mt-8">
                <div className="flex items-center justify-between">
                  <SectionLabel>
                    Papers
                  </SectionLabel>

                  <span className="text-xs text-muted-foreground">
                    {
                      collection.items
                        ?.length ??
                      0
                    }{" "}
                    {(
                      collection.items
                        ?.length ??
                      0
                    ) === 1
                      ? "paper"
                      : "papers"}
                  </span>
                </div>

                {!collection.items ||
                collection.items.length ===
                  0 ? (
                  <div className="mt-3 rounded-lg border border-dashed p-10 text-center">
                    <FolderOpen className="mx-auto h-9 w-9 text-muted-foreground" />

                    <p className="mt-3 text-sm font-medium">
                      No papers in this collection
                    </p>

                    <p className="mt-1 text-sm text-muted-foreground">
                      No papers were selected when this collection was created.
                    </p>
                  </div>
                ) : (
                  <div className="mt-4 space-y-3">
                    {collection.items.map(
                      (
                        item: CollectionItem,
                      ) => {
                        const paper =
                          item.paper;

                        const paperId =
                          normalizePaperId(
                            item.paper_id ??
                              paper?.id,
                          );

                        if (
                          paperId ===
                          null
                        ) {
                          return null;
                        }

                        const authors =
                          renderAuthors(
                            paper?.authors,
                          );

                        return (
                          <Link
                            key={
                              item.id
                            }
                            href={`/papers/${paperId}`}
                            className="group block rounded-lg border bg-background p-5 transition hover:border-primary/40 hover:bg-muted/30"
                          >
                            <div className="flex items-start justify-between gap-6">
                              <div className="min-w-0 flex-1">
                                <h3 className="text-sm font-semibold leading-6 group-hover:underline">
                                  {paper?.title ||
                                    "Untitled paper"}
                                </h3>

                                {authors && (
                                  <p className="mt-1.5 truncate text-xs text-muted-foreground">
                                    {authors}
                                  </p>
                                )}

                                <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
                                  {paper?.year !==
                                    null &&
                                    paper?.year !==
                                      undefined && (
                                      <span>
                                        {
                                          paper.year
                                        }
                                      </span>
                                    )}

                                  {paper?.year !==
                                    null &&
                                    paper?.year !==
                                      undefined &&
                                    paper?.venue && (
                                      <span>
                                        •
                                      </span>
                                    )}

                                  {paper?.venue && (
                                    <span className="truncate">
                                      {
                                        paper
                                          .venue
                                          .name
                                      }
                                    </span>
                                  )}
                                </div>
                              </div>

                              <span className="shrink-0 text-xs font-medium text-primary opacity-70 transition group-hover:opacity-100">
                                Open paper →
                              </span>
                            </div>
                          </Link>
                        );
                      },
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
