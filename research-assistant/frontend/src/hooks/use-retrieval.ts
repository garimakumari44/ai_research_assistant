"use client";

import { useMutation } from "@tanstack/react-query";

import { retrieveKnowledge } from "@/lib/api/retrieval";

import type {
  RetrievalRequest,
  RetrievalResponse,
} from "@/types/retrieval";

/**
 * React Query keys for the retrieval domain.
 */
export const retrievalKeys = {
  all: ["retrieval"] as const,

  search: () =>
    [...retrievalKeys.all, "search"] as const,
};

/**
 * Execute the unified retrieval pipeline.
 *
 * Example:
 *
 * const retrieval = useRetrieval();
 *
 * retrieval.mutate({
 *   query: "transformer architecture",
 *   top_k: 10,
 *   vector_weight: 0.7,
 *   keyword_weight: 0.3,
 *   graph_enabled: true,
 * });
 *
 * The backend decides which retrieval capabilities
 * are actually required.
 */
export function useRetrieval() {
  return useMutation<
    RetrievalResponse,
    Error,
    RetrievalRequest
  >({
    mutationKey: retrievalKeys.search(),
    mutationFn: retrieveKnowledge,
  });
}

