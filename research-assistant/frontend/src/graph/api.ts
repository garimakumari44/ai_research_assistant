import type {
  Graph,
  GraphNodeResponse,
  GraphParams,
  GraphTraversalRequest,
  GraphTraversalResponse,
  GraphRequest,
} from "./types";

/**
 * Base API URL.
 *
 * Keep this consistent with the rest of the frontend API layer.
 */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * API prefix.
 */
const GRAPH_BASE_URL = `${API_BASE_URL}/api/v1/graph`;

/**
 * Common request helper.
 */
async function graphRequest<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${GRAPH_BASE_URL}${path}`, {
    ...options,

    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },

    credentials: "include",
  });

  if (!response.ok) {
    let message = `Graph API request failed with status ${response.status}`;

    try {
      const error = await response.json();

      if (typeof error?.detail === "string") {
        message = error.detail;
      } else if (typeof error?.message === "string") {
        message = error.message;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

/**
 * Convert graph parameters into URL query parameters.
 */
function buildQueryString(params: GraphParams = {}): string {
  const searchParams = new URLSearchParams();

  if (params.query) {
    searchParams.set("query", params.query);
  }

  if (params.node_type) {
    searchParams.set("node_type", params.node_type);
  }

  if (params.node_types?.length) {
    searchParams.set("node_types", params.node_types.join(","));
  }

  if (params.edge_types?.length) {
    searchParams.set("edge_types", params.edge_types.join(","));
  }

  if (params.depth !== undefined) {
    searchParams.set("depth", String(params.depth));
  }

  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }

  if (params.offset !== undefined) {
    searchParams.set("offset", String(params.offset));
  }

  const queryString = searchParams.toString();

  return queryString ? `?${queryString}` : "";
}

/**
 * Fetch a graph.
 */
export async function getGraph(
  params: GraphParams = {},
): Promise<Graph> {
  const queryString = buildQueryString(params);

  return graphRequest<Graph>(`/${queryString}`);
}

/**
 * Fetch a graph using an explicit graph request.
 *
 * This is useful when the backend expects a POST request for more
 * complex graph construction.
 */
export async function createGraph(
  request: GraphRequest,
): Promise<Graph> {
  return graphRequest<Graph>("/", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/**
 * Fetch a single graph node.
 */
export async function getGraphNode(
  nodeId: string,
): Promise<GraphNodeResponse> {
  if (!nodeId) {
    throw new Error("nodeId is required");
  }

  return graphRequest<GraphNodeResponse>(
    `/nodes/${encodeURIComponent(nodeId)}`,
  );
}

/**
 * Traverse the graph starting from a node.
 */
export async function traverseGraph(
  request: GraphTraversalRequest,
): Promise<GraphTraversalResponse> {
  if (!request.node_id) {
    throw new Error("node_id is required");
  }

  return graphRequest<GraphTraversalResponse>("/traverse", {
    method: "POST",
    body: JSON.stringify(request),
  });
}