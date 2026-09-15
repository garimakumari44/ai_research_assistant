
import { apiFetch } from "../api";

import type {
  RetrievalRequest,
  RetrievalResponse,
} from "@/types/retrieval";

/**
 * Retrieval search endpoint.
 *
 * If apiFetch automatically prefixes /api/v1, this resolves to:
 *
 *   POST /api/v1/retrieval/search
 *
 * Keep the API contract centralized here.
 */
const RETRIEVAL_SEARCH_ENDPOINT = "/retrieval/search";

/**
 * Execute the unified retrieval pipeline.
 *
 * The backend may use any combination of:
 *
 *   - semantic retrieval
 *   - keyword retrieval
 *   - graph retrieval
 *
 * Graph retrieval is NOT a separate API.
 *
 * It is one retrieval capability inside the unified
 * retrieval pipeline.
 */
export async function retrieveKnowledge(
  request: RetrievalRequest,
): Promise<RetrievalResponse> {
  return apiFetch<RetrievalResponse>(
    RETRIEVAL_SEARCH_ENDPOINT,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

