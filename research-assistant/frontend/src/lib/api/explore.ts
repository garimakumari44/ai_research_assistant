import { apiFetch } from "../api";

import type {
  ExploreRequest,
  ExploreResponse,
} from "@/types/explore";

const EXPLORE_ENDPOINT = "/explore";

/**
 * Execute the unified Explore workflow.
 *
 * POST /api/v1/explore
 *
 * Explore is the orchestration boundary between
 * the frontend and the retrieval/adaptive-RAG system.
 */
export async function explore(
  request: ExploreRequest,
): Promise<ExploreResponse> {
  return apiFetch<ExploreResponse>(
    EXPLORE_ENDPOINT,
    {
      method: "POST",
      body: JSON.stringify(request),
    },
  );
}

export const exploreApi = {
  explore,
};

export default exploreApi;
