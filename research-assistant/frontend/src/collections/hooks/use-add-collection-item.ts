"use client";

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  addCollectionItem,
} from "@/collections/api";

import type {
  AddCollectionItemRequest,
  CollectionItem,
} from "@/collections/types";

import {
  collectionKeys,
} from "./use-collection";

/* ========================================================================== */
/* TYPES                                                                      */
/* ========================================================================== */

export interface AddCollectionItemVariables {
  collectionId: string | number;
  paperId: number;
}

/* ========================================================================== */
/* HOOK                                                                       */
/* ========================================================================== */

/**
 * React Query mutation hook for adding a paper
 * to a collection.
 *
 * Backend:
 *
 * POST /api/v1/collections/:collectionId/items
 *
 * Body:
 *
 * {
 *   paper_id: number
 * }
 *
 * Public usage:
 *
 *   await addToCollection(
 *     collectionId,
 *     paperId,
 *   );
 */
export function useAddCollectionItem() {
  const queryClient =
    useQueryClient();

  const mutation =
    useMutation<
      CollectionItem,
      Error,
      AddCollectionItemVariables
    >({
      mutationFn: async ({
        collectionId,
        paperId,
      }) => {
        /* -------------------------------------------------------------- */
        /* Validate collection ID                                         */
        /* -------------------------------------------------------------- */

        if (
          collectionId === null ||
          collectionId === undefined ||
          String(collectionId).trim() === ""
        ) {
          throw new Error(
            "Collection ID is required.",
          );
        }

        /* -------------------------------------------------------------- */
        /* Validate paper ID                                              */
        /* -------------------------------------------------------------- */

        const normalizedPaperId =
          Number(paperId);

        if (
          !Number.isInteger(
            normalizedPaperId,
          ) ||
          normalizedPaperId <= 0
        ) {
          throw new Error(
            `Paper ID must be a positive integer. Received: ${paperId}`,
          );
        }

        /* -------------------------------------------------------------- */
        /* Normalize collection ID                                        */
        /* -------------------------------------------------------------- */

        const normalizedCollectionId =
          String(collectionId).trim();

        /* -------------------------------------------------------------- */
        /* Build API payload                                              */
        /* -------------------------------------------------------------- */

        const payload: AddCollectionItemRequest =
          {
            paper_id:
              normalizedPaperId,
          };

        console.log(
          "[collections] POST add item:",
          {
            url: `/collections/${normalizedCollectionId}/items`,
            collectionId:
              normalizedCollectionId,
            paperId:
              normalizedPaperId,
            payload,
          },
        );

        /* -------------------------------------------------------------- */
        /* API REQUEST                                                    */
        /* -------------------------------------------------------------- */

        try {
          const result =
            await addCollectionItem(
              normalizedCollectionId,
              payload,
            );

          console.log(
            "[collections] Add item succeeded:",
            {
              collectionId:
                normalizedCollectionId,
              paperId:
                normalizedPaperId,
              result,
            },
          );

          return result;
        } catch (error: unknown) {
          console.error(
            "[collections] Add item API request failed:",
            {
              collectionId:
                normalizedCollectionId,
              paperId:
                normalizedPaperId,
              error,
            },
          );

          if (
            error instanceof Error
          ) {
            throw error;
          }

          throw new Error(
            "Failed to add paper to collection.",
          );
        }
      },

      /* -------------------------------------------------------------- */
      /* SUCCESS                                                        */
      /* -------------------------------------------------------------- */

      onSuccess: async (
        _data,
        variables,
      ) => {
        const collectionId =
          String(
            variables.collectionId,
          ).trim();

        console.log(
          "[collections] Invalidating collection queries:",
          collectionId,
        );

        /* ------------------------------------------------------------ */
        /* Collection detail                                            */
        /* ------------------------------------------------------------ */

        await queryClient.invalidateQueries(
          {
            queryKey:
              collectionKeys.detail(
                collectionId,
              ),
          },
        );

        /* ------------------------------------------------------------ */
        /* Collection items                                             */
        /* ------------------------------------------------------------ */

        await queryClient.invalidateQueries(
          {
            queryKey:
              collectionKeys.detail(
                collectionId,
              ),
            exact: false,
          },
        );

        /* ------------------------------------------------------------ */
        /* Collection list/counts                                       */
        /* ------------------------------------------------------------ */

        await queryClient.invalidateQueries(
          {
            queryKey:
              collectionKeys.lists(),
          },
        );
      },
    });

  /* ====================================================================== */
  /* PUBLIC FUNCTION                                                       */
  /* ====================================================================== */

  /**
   * IMPORTANT:
   *
   * Do NOT expose raw mutation.mutateAsync
   * here because the page uses:
   *
   *   addToCollection(
   *     collectionId,
   *     paperId,
   *   )
   *
   * Instead we adapt the arguments into
   * the mutation variables expected internally.
   */
  const addToCollection = async (
    collectionId:
      | string
      | number,
    paperId: number,
  ): Promise<CollectionItem> => {
    return mutation.mutateAsync({
      collectionId,
      paperId,
    });
  };

  /* ====================================================================== */
  /* RETURN                                                                 */
  /* ====================================================================== */

  return {
    /**
     * Main public API.
     */
    addToCollection,

    /**
     * Mutation state.
     */
    isAdding:
      mutation.isPending,

    isPending:
      mutation.isPending,

    isError:
      mutation.isError,

    isSuccess:
      mutation.isSuccess,

    /**
     * Error returned by the mutation.
     */
    addError:
      mutation.error,

    error:
      mutation.error,

    /**
     * Reset mutation state.
     */
    reset:
      mutation.reset,
  };
}