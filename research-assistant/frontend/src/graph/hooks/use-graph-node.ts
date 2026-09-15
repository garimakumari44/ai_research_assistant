"use client";

import {
  useQuery,
} from "@tanstack/react-query";

import {
  getGraphNode,
} from "../api";

import {
  graphKeys,
} from "./use-graph";

import type {
  GraphNodeResponse,
} from "../types";

/**
 * Fetch an individual graph node.
 */
export function useGraphNode(
  nodeId?: string | null,
  options?: {
    enabled?: boolean;
  },
) {
  const hasNodeId = Boolean(nodeId);

  return useQuery<GraphNodeResponse, Error>({
    queryKey: graphKeys.node(nodeId ?? ""),

    queryFn: () => {
      if (!nodeId) {
        throw new Error("A graph node ID is required");
      }

      return getGraphNode(nodeId);
    },

    enabled:
      (options?.enabled ?? true) &&
      hasNodeId,

    staleTime: 60_000,

    retry: 2,
  });
}