"use client";

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  addCollectionItem,
  removeCollectionItem,
} from "../api";

import { collectionKeys } from "./use-collections";

import type {
  AddCollectionItemRequest,
  CollectionItemMutationResponse,
  RemoveCollectionItemRequest,
} from "../types";

/**
 * Add a paper to a collection.
 */
export function useAddCollectionItem() {
  const queryClient = useQueryClient();

  return useMutation<
    CollectionItemMutationResponse,
    Error,
    {
      collectionId: number | string;
      payload: AddCollectionItemRequest;
    }
  >({
    mutationFn: ({ collectionId, payload }) =>
      addCollectionItem(collectionId, payload),

    onSuccess: (_, variables) => {
      /**
       * Refresh:
       *
       * - collection list/counts
       * - collection detail
       * - collection items
       */
      queryClient.invalidateQueries({
        queryKey: collectionKeys.all,
      });

      queryClient.invalidateQueries({
        queryKey: collectionKeys.detail(
          variables.collectionId,
        ),
      });

      queryClient.invalidateQueries({
        queryKey: collectionKeys.items(
          variables.collectionId,
        ),
      });
    },
  });
}

/**
 * Remove a paper from a collection.
 */
export function useRemoveCollectionItem() {
  const queryClient = useQueryClient();

  return useMutation<
    void,
    Error,
    {
      collectionId: number | string;
      payload: RemoveCollectionItemRequest;
    }
  >({
    mutationFn: ({ collectionId, payload }) =>
      removeCollectionItem(collectionId, payload),

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: collectionKeys.all,
      });

      queryClient.invalidateQueries({
        queryKey: collectionKeys.detail(
          variables.collectionId,
        ),
      });

      queryClient.invalidateQueries({
        queryKey: collectionKeys.items(
          variables.collectionId,
        ),
      });
    },
  });
}