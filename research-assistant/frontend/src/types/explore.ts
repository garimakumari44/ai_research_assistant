import type {
  AdaptiveRAGResponse,
  RAGStrategy,
  RetrievalMode,
} from "@/adaptive-rag/types";

import type {
  RetrievalResponse,
  RetrievalResult,
} from "@/types/retrieval";

/* -------------------------------------------------------------------------- */
/* Request                                                                    */
/* -------------------------------------------------------------------------- */

export interface ExploreRequest {
  query: string;

  top_k?: number;

  retrieval_mode?: RetrievalMode;

  adaptive?: boolean;

  strategy?: RAGStrategy | null;

  max_iterations?: number;

  confidence_threshold?: number;

  paper_id?: string | null;

  document_id?: string | null;

  filters?: Record<string, unknown>;

  enable_graph?: boolean;

  enable_multi_query?: boolean;

  enable_correction?: boolean;

  metadata?: Record<string, unknown>;
}

/* -------------------------------------------------------------------------- */
/* Response                                                                   */
/* -------------------------------------------------------------------------- */

export interface ExploreResponse {
  query: string;

  retrieval?: RetrievalResponse | null;

  adaptive_rag?: AdaptiveRAGResponse | null;

  answer?: string | null;

  sources: unknown[];

  confidence?: number | null;

  metadata: Record<string, unknown>;

  duration_ms?: number | null;

  success: boolean;
}

/* -------------------------------------------------------------------------- */
/* Type Guards                                                                */
/* -------------------------------------------------------------------------- */

export function isAdaptiveExploreResponse(
  response: ExploreResponse,
): response is ExploreResponse & {
  adaptive_rag: AdaptiveRAGResponse;
} {
  return response.adaptive_rag !== null &&
    response.adaptive_rag !== undefined;
}

export function isRetrievalExploreResponse(
  response: ExploreResponse,
): response is ExploreResponse & {
  retrieval: RetrievalResponse;
} {
  return response.retrieval !== null &&
    response.retrieval !== undefined;
}

/* -------------------------------------------------------------------------- */
/* Result Helpers                                                             */
/* -------------------------------------------------------------------------- */

export function getExploreResults(
  response: ExploreResponse,
): unknown[] {
  if (response.adaptive_rag) {
    return response.adaptive_rag.sources ?? [];
  }

  if (response.retrieval) {
    return response.retrieval.results ?? [];
  }

  return response.sources ?? [];
}

export function getExploreRetrievalResults(
  response: ExploreResponse,
): RetrievalResult[] {
  if (!response.retrieval) {
    return [];
  }

  return response.retrieval.results;
}
