"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getCollection,
  getCollectionItems,
  type Collection,
  type CollectionItem,
} from "@/collections/api";

/* ========================================================================== */
/* QUERY KEYS                                                                 */
/* ========================================================================== */

export const collectionKeys = {
  /**
   * Root collection key.
   */
  all: ["collections"] as const,

  /**
   * All collection-list queries.
   */
  lists: () =>
    [
      ...collectionKeys.all,
      "list",
    ] as const,

  /**
   * Specific collection-list query.
   */
  list: (
    params: Record<string, unknown> = {},
  ) =>
    [
      ...collectionKeys.lists(),
      params,
    ] as const,

  /**
   * Root for collection-detail queries.
   */
  details: () =>
    [
      ...collectionKeys.all,
      "detail",
    ] as const,

  /**
   * Specific collection detail.
   *
   * IDs are normalized to strings so:
   *
   *   21
   *
   * and:
   *
   *   "21"
   *
   * use the same cache entry.
   */
  detail: (
    collectionId:
      | string
      | number,
  ) =>
    [
      ...collectionKeys.details(),
      String(collectionId),
    ] as const,

  /**
   * Collection items query.
   */
  items: (
    collectionId:
      | string
      | number,
    page: number,
    pageSize: number,
  ) =>
    [
      ...collectionKeys.detail(
        collectionId,
      ),
      "items",
      page,
      pageSize,
    ] as const,
};

/* ========================================================================== */
/* HELPERS                                                                    */
/* ========================================================================== */

/**
 * Normalize collection IDs.
 *
 * IMPORTANT:
 * Never use Number() here.
 *
 * Collection IDs may be:
 *
 * - numeric IDs
 * - numeric strings
 * - UUIDs
 */
export function normalizeCollectionId(
  collectionId:
    | string
    | number
    | null
    | undefined,
): string | null {
  if (
    collectionId === null ||
    collectionId === undefined
  ) {
    return null;
  }

  const value =
    String(collectionId).trim();

  if (!value) {
    return null;
  }

  return value;
}

/**
 * Extract HTTP status from an unknown error.
 */
function getErrorStatus(
  error: unknown,
): number | undefined {
  if (
    typeof error !== "object" ||
    error === null
  ) {
    return undefined;
  }

  if (!("status" in error)) {
    return undefined;
  }

  const status = Number(
    (
      error as {
        status?: unknown;
      }
    ).status,
  );

  return Number.isFinite(status)
    ? status
    : undefined;
}

/**
 * Determine whether an error is a 404.
 */
function isNotFoundError(
  error: unknown,
): boolean {
  return (
    getErrorStatus(error) === 404
  );
}

/* ========================================================================== */
/* COLLECTION DETAIL                                                          */
/* ========================================================================== */

/**
 * Fetch a single collection.
 *
 * `enabled` can be controlled by the caller.
 *
 * This is important because the collection list
 * may temporarily contain stale data while a newly
 * created collection is being synchronized.
 */
export function useCollection(
  collectionId:
    | string
    | number
    | null
    | undefined,
  options?: {
    enabled?: boolean;
  },
) {
  const normalizedId =
    normalizeCollectionId(
      collectionId,
    );

  const enabled =
    Boolean(normalizedId) &&
    (options?.enabled ?? true);

  return useQuery<
    Collection | null,
    Error
  >({
    queryKey: normalizedId
      ? collectionKeys.detail(
          normalizedId,
        )
      : [
          ...collectionKeys.details(),
          "empty",
        ],

    queryFn: async () => {
      if (!normalizedId) {
        return null;
      }

      try {
        return await getCollection(
          normalizedId,
        );
      } catch (error: unknown) {
        if (
          isNotFoundError(error)
        ) {
          console.warn(
            `[collections] Collection ${normalizedId} was not found.`,
          );

          return null;
        }

        throw error;
      }
    },

    /*
     * No request when:
     *
     * - there is no collection ID
     * - the caller knows the collection is not
     *   currently present in the collection list
     */
    enabled,

    /*
     * Avoid unnecessary requests while
     * navigating between collections.
     */
    staleTime: 30_000,

    /*
     * Do not retry missing collections.
     */
    retry: (
      failureCount,
      error,
    ) => {
      if (
        isNotFoundError(error)
      ) {
        return false;
      }

      return failureCount < 2;
    },
  });
}

/* ========================================================================== */
/* COLLECTION ITEMS                                                           */
/* ========================================================================== */

/**
 * Fetch papers/items belonging to a collection.
 */
export function useCollectionItems(
  collectionId:
    | string
    | number
    | null
    | undefined,
  page = 1,
  pageSize = 100,
  options?: {
    enabled?: boolean;
  },
) {
  const normalizedId =
    normalizeCollectionId(
      collectionId,
    );

  const normalizedPage =
    Number.isFinite(page) &&
    page > 0
      ? Math.floor(page)
      : 1;

  const normalizedPageSize =
    Number.isFinite(pageSize) &&
    pageSize > 0
      ? Math.floor(pageSize)
      : 100;

  const enabled =
    Boolean(normalizedId) &&
    (options?.enabled ?? true);

  return useQuery<
    CollectionItem[],
    Error
  >({
    queryKey: normalizedId
      ? collectionKeys.items(
          normalizedId,
          normalizedPage,
          normalizedPageSize,
        )
      : [
          ...collectionKeys.all,
          "items",
          "empty",
        ],

    queryFn: async () => {
      if (!normalizedId) {
        return [];
      }

      try {
        const result =
          await getCollectionItems(
            normalizedId,
            {
              page:
                normalizedPage,
              page_size:
                normalizedPageSize,
            },
          );

        /*
         * ARRAY RESPONSE
         */
        if (
          Array.isArray(result)
        ) {
          return result;
        }

        /*
         * PAGINATED RESPONSE
         */
        if (
          result &&
          typeof result ===
            "object" &&
          "items" in result
        ) {
          const items = (
            result as {
              items?: unknown;
            }
          ).items;

          if (
            Array.isArray(items)
          ) {
            return items as CollectionItem[];
          }
        }

        /*
         * SAFE FALLBACK
         */
        return [];
      } catch (error: unknown) {
        if (
          isNotFoundError(error)
        ) {
          console.warn(
            `[collections] Items for collection ${normalizedId} were not found.`,
          );

          return [];
        }

        throw error;
      }
    },

    /*
     * Prevent requests when the selected
     * collection is known to be invalid.
     */
    enabled,

    staleTime: 30_000,

    retry: (
      failureCount,
      error,
    ) => {
      if (
        isNotFoundError(error)
      ) {
        return false;
      }

      return failureCount < 2;
    },
  });
}

/* ========================================================================== */
/* ALIASES                                                                    */
/* ========================================================================== */

/**
 * Backwards-compatible alias.
 */
export const useCollectionDetail =
  useCollection;

/**
 * Backwards-compatible alias.
 */
export const useCollectionItemsQuery =
  useCollectionItems;