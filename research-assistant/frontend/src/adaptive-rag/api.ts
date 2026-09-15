/**
 * Adaptive RAG API client.
 *
 * Adaptive RAG is the orchestration boundary for the research platform.
 *
 * Paper Foundation
 *      ↓
 * Documents
 *      ↓
 * Knowledge
 *      ↓
 * Retrieval
 *      ↓
 * Adaptive RAG
 *      ├── Direct
 *      ├── Dense
 *      ├── Hybrid
 *      ├── Multi Query
 *      ├── Iterative
 *      ├── Corrective
 *      └── Graph Augmented → Graph API
 *      ↓
 * Generation
 *      ↓
 * Research Engine
 *      ↓
 * Frontier
 *      ↓
 * Self Improvement
 *      ↓
 * Reports / Collections
 */

import type {
  AdaptiveRAGConfig,
  AdaptiveRAGExecution,
  AdaptiveRAGExecutionList,
  AdaptiveRAGHealth,
  AdaptiveRAGRequest,
  AdaptiveRAGResponse,
  GraphContext,
  GraphEdge,
  GraphNode,
  RAGStrategy,
  StrategyOption,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

const ADAPTIVE_RAG_BASE =
  `${API_BASE_URL}/api/v1/adaptive-rag`;

/* -------------------------------------------------------------------------- */
/* Error                                                                      */
/* -------------------------------------------------------------------------- */

export class AdaptiveRAGAPIError extends Error {
  status: number;

  details?: unknown;

  constructor(
    message: string,
    status: number,
    details?: unknown,
  ) {
    super(message);

    this.name = "AdaptiveRAGAPIError";

    this.status = status;

    this.details = details;
  }
}

/* -------------------------------------------------------------------------- */
/* Generic Request                                                            */
/* -------------------------------------------------------------------------- */

async function parseResponse<T>(
  response: Response,
): Promise<T> {
  const contentType =
    response.headers.get("content-type") ?? "";

  let data: unknown;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    let message =
      `Adaptive RAG request failed with status ${response.status}`;

    if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data
    ) {
      const detail = (
        data as {
          detail?: unknown;
        }
      ).detail;

      if (typeof detail === "string") {
        message = detail;
      }
    }

    throw new AdaptiveRAGAPIError(
      message,
      response.status,
      data,
    );
  }

  return data as T;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  if (
    options.body &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  headers.set("Accept", "application/json");

  const response = await fetch(
    `${ADAPTIVE_RAG_BASE}${path}`,
    {
      ...options,
      headers,
      cache: "no-store",
    },
  );

  return parseResponse<T>(response);
}

/* -------------------------------------------------------------------------- */
/* Adaptive RAG                                                               */
/* -------------------------------------------------------------------------- */

/**
 * Execute a complete Adaptive RAG workflow.
 *
 * The backend is responsible for orchestrating the individual services.
 */
export async function runAdaptiveRAG(
  payload: AdaptiveRAGRequest,
): Promise<AdaptiveRAGResponse> {
  return request<AdaptiveRAGResponse>(
    "/query",
    {
      method: "POST",

      body: JSON.stringify({
        ...payload,

        /*
         * Graph must be explicitly enabled for graph_augmented
         * execution. This keeps the frontend contract unambiguous.
         */
        enable_graph:
          payload.strategy === "graph_augmented"
            ? true
            : payload.enable_graph,

        /*
         * Adaptive mode lets the backend choose between the
         * available retrieval strategies.
         */
        adaptive:
          payload.strategy === "auto"
            ? true
            : payload.adaptive,
      }),
    },
  );
}

export const executeAdaptiveRAG =
  runAdaptiveRAG;

/* -------------------------------------------------------------------------- */
/* Execution                                                                   */
/* -------------------------------------------------------------------------- */

export async function getAdaptiveRAGExecution(
  executionId: string,
): Promise<AdaptiveRAGExecution> {
  return request<AdaptiveRAGExecution>(
    `/executions/${encodeURIComponent(executionId)}`,
  );
}

export async function getAdaptiveRAGState(
  executionId: string,
): Promise<AdaptiveRAGResponse> {
  return request<AdaptiveRAGResponse>(
    `/executions/${encodeURIComponent(executionId)}/state`,
  );
}

export async function stopAdaptiveRAGExecution(
  executionId: string,
): Promise<void> {
  await request<void>(
    `/executions/${encodeURIComponent(executionId)}/stop`,
    {
      method: "POST",
    },
  );
}

export async function listAdaptiveRAGExecutions(
  params: {
    page?: number;

    page_size?: number;

    status?: string;
  } = {},
): Promise<AdaptiveRAGExecutionList> {
  const searchParams =
    new URLSearchParams();

  if (params.page !== undefined) {
    searchParams.set(
      "page",
      String(params.page),
    );
  }

  if (params.page_size !== undefined) {
    searchParams.set(
      "page_size",
      String(params.page_size),
    );
  }

  if (params.status) {
    searchParams.set(
      "status",
      params.status,
    );
  }

  const query =
    searchParams.toString();

  return request<AdaptiveRAGExecutionList>(
    query
      ? `/executions?${query}`
      : "/executions",
  );
}

/* -------------------------------------------------------------------------- */
/* Health / Configuration                                                     */
/* -------------------------------------------------------------------------- */

export async function getAdaptiveRAGHealth(): Promise<AdaptiveRAGHealth> {
  return request<AdaptiveRAGHealth>(
    "/health",
  );
}

export async function getAdaptiveRAGConfig(): Promise<AdaptiveRAGConfig> {
  return request<AdaptiveRAGConfig>(
    "/config",
  );
}

/* -------------------------------------------------------------------------- */
/* Graph Integration                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Graph API client used by graph-augmented Adaptive RAG.
 *
 * The Adaptive RAG backend should normally orchestrate graph retrieval
 * server-side. These methods are provided for frontend graph exploration,
 * previews, and explicit graph context loading.
 *
 * Expected backend routes:
 *
 * GET /api/v1/graph/nodes
 * GET /api/v1/graph/edges
 * POST /api/v1/graph/traversal
 */

const GRAPH_BASE =
  `${API_BASE_URL}/api/v1/graph`;

async function graphRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(
    options.headers,
  );

  if (
    options.body &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  headers.set(
    "Accept",
    "application/json",
  );

  const response = await fetch(
    `${GRAPH_BASE}${path}`,
    {
      ...options,
      headers,
      cache: "no-store",
    },
  );

  return parseResponse<T>(response);
}

/**
 * Fetch graph context for a query.
 *
 * Used by graph-augmented RAG previews and UI.
 */
export async function getGraphContext(
  params: {
    query?: string;

    node_ids?: string[];

    depth?: number;

    node_types?: string[];

    edge_types?: string[];

    limit?: number;
  } = {},
): Promise<GraphContext> {
  const searchParams =
    new URLSearchParams();

  if (params.query) {
    searchParams.set(
      "query",
      params.query,
    );
  }

  if (params.node_ids?.length) {
    searchParams.set(
      "node_ids",
      params.node_ids.join(","),
    );
  }

  if (params.depth !== undefined) {
    searchParams.set(
      "depth",
      String(params.depth),
    );
  }

  if (params.node_types?.length) {
    searchParams.set(
      "node_types",
      params.node_types.join(","),
    );
  }

  if (params.edge_types?.length) {
    searchParams.set(
      "edge_types",
      params.edge_types.join(","),
    );
  }

  if (params.limit !== undefined) {
    searchParams.set(
      "limit",
      String(params.limit),
    );
  }

  const query =
    searchParams.toString();

  return graphRequest<GraphContext>(
    query
      ? `/?${query}`
      : "/",
  );
}

/**
 * Get a single graph node.
 */
export async function getGraphNode(
  nodeId: string,
): Promise<GraphNode> {
  return graphRequest<GraphNode>(
    `/nodes/${encodeURIComponent(nodeId)}`,
  );
}

/**
 * Get graph edges connected to a node.
 */
export async function getGraphNodeEdges(
  nodeId: string,
): Promise<GraphEdge[]> {
  return graphRequest<GraphEdge[]>(
    `/nodes/${encodeURIComponent(nodeId)}/edges`,
  );
}

/**
 * Execute graph traversal.
 */
export async function traverseGraph(
  payload: {
    node_ids: string[];

    depth?: number;

    node_types?: string[];

    edge_types?: string[];
  },
): Promise<GraphContext> {
  return graphRequest<GraphContext>(
    "/traversal",
    {
      method: "POST",

      body: JSON.stringify(payload),
    },
  );
}

/* -------------------------------------------------------------------------- */
/* Strategy Metadata                                                          */
/* -------------------------------------------------------------------------- */

const STRATEGY_METADATA: Record<
  Exclude<RAGStrategy, "auto">,
  Omit<
    StrategyOption,
    "id" | "enabled"
  >
> = {
  direct: {
    name: "Direct RAG",

    description:
      "Single-pass retrieval followed by generation.",

    requires_graph: false,

    requires_retrieval: true,

    supports_multi_query: false,

    supports_correction: false,
  },

  dense: {
    name: "Dense RAG",

    description:
      "Semantic vector retrieval followed by generation.",

    requires_graph: false,

    requires_retrieval: true,

    supports_multi_query: false,

    supports_correction: false,
  },

  hybrid: {
    name: "Hybrid RAG",

    description:
      "Combines semantic and keyword retrieval for stronger evidence coverage.",

    requires_graph: false,

    requires_retrieval: true,

    supports_multi_query: false,

    supports_correction: true,
  },

  multi_query: {
    name: "Multi-Query RAG",

    description:
      "Generates multiple query variants to improve retrieval coverage.",

    requires_graph: false,

    requires_retrieval: true,

    supports_multi_query: true,

    supports_correction: false,
  },

  iterative: {
    name: "Iterative RAG",

    description:
      "Repeatedly retrieves, evaluates, and refines evidence until confidence is sufficient.",

    requires_graph: false,

    requires_retrieval: true,

    supports_multi_query: true,

    supports_correction: true,
  },

  corrective: {
    name: "Corrective RAG",

    description:
      "Evaluates retrieved evidence and performs corrective retrieval when required.",

    requires_graph: false,

    requires_retrieval: true,

    supports_multi_query: true,

    supports_correction: true,
  },

  graph_augmented: {
    name: "Graph-Augmented RAG",

    description:
      "Combines evidence retrieval with Research Graph traversal and connected research knowledge.",

    requires_graph: true,

    requires_retrieval: true,

    supports_multi_query: true,

    supports_correction: true,
  },
};

/* -------------------------------------------------------------------------- */
/* Strategies                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * Get strategies supported by the backend.
 *
 * The backend remains the source of truth.
 */
export async function getAdaptiveRAGStrategies(): Promise<
  StrategyOption[]
> {
  const config =
    await getAdaptiveRAGConfig();

  const strategies =
    config.enabled_strategies;

  return strategies.map(
    (strategy) => {
      if (strategy === "auto") {
        return {
          id: "auto",

          name: "Adaptive",

          description:
            "Automatically selects the most appropriate retrieval strategy.",

          enabled: true,

          recommended:
            config.default_strategy ===
            "auto",

          requires_graph: false,

          requires_retrieval: true,

          supports_multi_query: true,

          supports_correction: true,
        };
      }

      const metadata =
        STRATEGY_METADATA[strategy];

      return {
        id: strategy,

        ...metadata,

        enabled: true,

        recommended:
          strategy ===
          config.default_strategy,
      };
    },
  );
}

/* -------------------------------------------------------------------------- */
/* Convenience API                                                            */
/* -------------------------------------------------------------------------- */

export const adaptiveRAGAPI = {
  /* Adaptive RAG */

  run: runAdaptiveRAG,

  execute: executeAdaptiveRAG,

  /* Execution */

  getExecution:
    getAdaptiveRAGExecution,

  getState:
    getAdaptiveRAGState,

  stopExecution:
    stopAdaptiveRAGExecution,

  listExecutions:
    listAdaptiveRAGExecutions,

  /* Platform */

  health:
    getAdaptiveRAGHealth,

  config:
    getAdaptiveRAGConfig,

  strategies:
    getAdaptiveRAGStrategies,

  /* Research Graph */

  graph: {
    context:
      getGraphContext,

    node:
      getGraphNode,

    nodeEdges:
      getGraphNodeEdges,

    traverse:
      traverseGraph,
  },
};

export default adaptiveRAGAPI;