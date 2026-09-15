"use client";

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createCollection,
  getCollections,
} from "../api";

import type {
  Collection,
  CollectionListParams,
  CollectionListResponse,
  CreateCollectionRequest,
} from "../types";

/* -------------------------------------------------------------------------- */
/* Query Keys                                                                 */
/* -------------------------------------------------------------------------- */

export const collectionKeys = {
  all: ["collections"] as const,

  lists: () =>
    [...collectionKeys.all, "list"] as const,

  list: (
    params: CollectionListParams = {},
  ) =>
    [
      ...collectionKeys.lists(),
      params,
    ] as const,

  details: () =>
    [...collectionKeys.all, "detail"] as const,

  detail: (
    id: number | string,
  ) =>
    [
      ...collectionKeys.details(),
      String(id),
    ] as const,

  items: (
    id: number | string,
  ) =>
    [
      ...collectionKeys.detail(id),
      "items",
    ] as const,
};

/* -------------------------------------------------------------------------- */
/* Hooks                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Fetch collections and provide collection mutations.
 */
export function useCollections(
  params: CollectionListParams = {},
) {
  const queryClient = useQueryClient();

  /* ------------------------------------------------------------------------ */
  /* List Query                                                               */
  /* ------------------------------------------------------------------------ */

  const collectionsQuery = useQuery<
    CollectionListResponse,
    Error
  >({
    queryKey: collectionKeys.list(params),

    queryFn: () =>
      getCollections(params),

    placeholderData: keepPreviousData,

    staleTime: 30_000,
  });

  /* ------------------------------------------------------------------------ */
  /* Create Collection                                                        */
  /* ------------------------------------------------------------------------ */

  const createMutation = useMutation<
    Collection,
    Error,
    CreateCollectionRequest
  >({
    mutationFn: (
      payload: CreateCollectionRequest,
    ) => createCollection(payload),

    onSuccess: async (createdCollection) => {
      console.log(
        "Collection created successfully:",
        createdCollection,
      );

      /*
       * Refresh every collection list query.
       *
       * This is important because the current page may be using
       * a different list query key depending on pagination/search.
       */
      await queryClient.invalidateQueries({
        queryKey: collectionKeys.lists(),
      });

      /*
       * If the created collection is later opened,
       * make sure its detail query can be fetched fresh.
       */
      if (createdCollection?.id != null) {
        await queryClient.invalidateQueries({
          queryKey: collectionKeys.detail(
            createdCollection.id,
          ),
        });
      }
    },

    onError: (error) => {
      console.error(
        "Failed to create collection:",
        error,
      );
    },
  });

  /* ------------------------------------------------------------------------ */
  /* Return                                                                   */
  /* ------------------------------------------------------------------------ */

  return {
    /* Query */
    data: collectionsQuery.data,
    error: collectionsQuery.error,

    isLoading: collectionsQuery.isLoading,
    isFetching: collectionsQuery.isFetching,
    isError: collectionsQuery.isError,
    isSuccess: collectionsQuery.isSuccess,

    refetch: collectionsQuery.refetch,

    /* Create mutation */
    createCollection: createMutation.mutateAsync,

    isCreating: createMutation.isPending,

    createError: createMutation.error,

    createSuccess: createMutation.isSuccess,

    resetCreate: createMutation.reset,
  };
}