"use client";

import {
  useMutation,
  useQuery,
} from "@tanstack/react-query";

import {
  traverseGraph,
} from "../api";

import {
  graphKeys,
} from "./use-graph";

import type {
  GraphTraversalRequest,
  GraphTraversalResponse,
} from "../types";

/**
 * Fetch a graph traversal.
 *
 * This hook is useful when a page needs to display the neighborhood
 * around a selected node.
 */
export function useGraphTraversal(
  request?: GraphTraversalRequest | null,
  options?: {
    enabled?: boolean;
  },
) {
  const hasRequest = Boolean(
    request?.node_id,
  );

  return useQuery<
    GraphTraversalResponse,
    Error
  >({
    queryKey: graphKeys.traversal(
      request ?? {},
    ),

    queryFn: () => {
      if (!request?.node_id) {
        throw new Error(
          "A graph node ID is required for traversal",
        );
      }

      return traverseGraph(request);
    },

    enabled:
      (options?.enabled ?? true) &&
      hasRequest,

    staleTime: 30_000,

    retry: 2,
  });
}

/**
 * Imperative traversal mutation.
 *
 * Useful for UI interactions such as:
 *
 * - Expand node
 * - Explore neighbors
 * - Load more relationships
 * - Traverse from selected node
 */
export function useTraverseGraph() {
  return useMutation<
    GraphTraversalResponse,
    Error,
    GraphTraversalRequest
  >({
    mutationFn: traverseGraph,
  });
}