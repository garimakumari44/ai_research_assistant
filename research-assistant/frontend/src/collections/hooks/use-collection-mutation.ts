"use client";

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  addCollectionItem,
  createCollection,
  deleteCollection,
  removeCollectionItem,
  updateCollection,
} from "../api";

import {
  collectionKeys,
} from "./use-collections";

import type {
  AddCollectionItemRequest,
  CreateCollectionRequest,
  RemoveCollectionItemRequest,
  UpdateCollectionRequest,
} from "../types";

/**
 * Create a new collection.
 */
export function useCreateCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      payload: CreateCollectionRequest,
    ) => createCollection(payload),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: collectionKeys.lists(),
      });
    },
  });
}

/**
 * Update an existing collection.
 */
export function useUpdateCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      collectionId,
      payload,
    }: {
      collectionId: number | string;
      payload: UpdateCollectionRequest;
    }) =>
      updateCollection(
        collectionId,
        payload,
      ),

    onSuccess: (collection) => {
      /**
       * Update the detail cache immediately.
       */
      queryClient.setQueryData(
        collectionKeys.detail(collection.id),
        collection,
      );

      /**
       * Refresh collection lists.
       */
      queryClient.invalidateQueries({
        queryKey: collectionKeys.lists(),
      });
    },
  });
}

/**
 * Delete a collection.
 */
export function useDeleteCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      collectionId: number | string,
    ) => deleteCollection(collectionId),

    onSuccess: (_, collectionId) => {
      /**
       * Remove the detail cache.
       */
      queryClient.removeQueries({
        queryKey:
          collectionKeys.detail(collectionId),
      });

      /**
       * Refresh lists.
       */
      queryClient.invalidateQueries({
        queryKey: collectionKeys.lists(),
      });
    },
  });
}

/**
 * Add a paper to a collection.
 */
export function useAddCollectionItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      collectionId,
      payload,
    }: {
      collectionId: number | string;
      payload: AddCollectionItemRequest;
    }) =>
      addCollectionItem(
        collectionId,
        payload,
      ),

    onSuccess: (_, variables) => {
      /**
       * Refresh collection items.
       */
      queryClient.invalidateQueries({
        queryKey:
          collectionKeys.items(
            variables.collectionId,
          ),
      });

      /**
       * Collection item_count may have changed.
       */
      queryClient.invalidateQueries({
        queryKey: collectionKeys.lists(),
      });

      queryClient.invalidateQueries({
        queryKey:
          collectionKeys.detail(
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

  return useMutation({
    mutationFn: ({
      collectionId,
      payload,
    }: {
      collectionId: number | string;
      payload: RemoveCollectionItemRequest;
    }) =>
      removeCollectionItem(
        collectionId,
        payload,
      ),

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey:
          collectionKeys.items(
            variables.collectionId,
          ),
      });

      queryClient.invalidateQueries({
        queryKey: collectionKeys.lists(),
      });

      queryClient.invalidateQueries({
        queryKey:
          collectionKeys.detail(
            variables.collectionId,
          ),
      });
    },
  });
}