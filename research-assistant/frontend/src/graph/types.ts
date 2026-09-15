/**
 * Graph domain types.
 *
 * These types are intentionally independent from React Flow.
 * The graph API represents domain data, while UI components can
 * transform it into React Flow nodes/edges when necessary.
 */

export type GraphNodeType =
  | "paper"
  | "author"
  | "topic"
  | "method"
  | "dataset"
  | "venue"
  | "organization"
  | "document"
  | "chunk"
  | "unknown";

export type GraphEdgeType =
  | "authored_by"
  | "cites"
  | "cited_by"
  | "related_to"
  | "has_topic"
  | "uses_method"
  | "uses_dataset"
  | "published_in"
  | "affiliated_with"
  | "contains"
  | "derived_from"
  | "references"
  | "unknown";

export interface GraphNode {
  id: string;
  type: GraphNodeType;
  label: string;

  description?: string | null;

  properties?: Record<string, unknown>;

  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;

  source: string;
  target: string;

  type: GraphEdgeType;

  label?: string | null;

  properties?: Record<string, unknown>;

  metadata?: Record<string, unknown>;
}

export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNodeResponse {
  node: GraphNode;

  neighbors?: GraphNode[];

  edges?: GraphEdge[];

  metadata?: Record<string, unknown>;
}

export interface GraphTraversalResponse {
  root: GraphNode;

  nodes: GraphNode[];

  edges: GraphEdge[];

  depth: number;

  metadata?: Record<string, unknown>;
}

/**
 * Generic graph query.
 */
export interface GraphQuery {
  query?: string;

  node_types?: GraphNodeType[];

  edge_types?: GraphEdgeType[];

  paper_id?: number;

  document_id?: number;

  limit?: number;

  offset?: number;
}

/**
 * Request for retrieving a graph around an entity.
 */
export interface GraphRequest {
  node_id?: string;

  node_type?: GraphNodeType;

  query?: string;

  node_types?: GraphNodeType[];

  edge_types?: GraphEdgeType[];

  depth?: number;

  limit?: number;
}

/**
 * Request for traversing from a specific node.
 */
export interface GraphTraversalRequest {
  node_id: string;

  depth?: number;

  direction?: "outgoing" | "incoming" | "both";

  edge_types?: GraphEdgeType[];

  node_types?: GraphNodeType[];

  limit?: number;
}

/**
 * Query parameters used by the graph API.
 */
export interface GraphParams {
  query?: string;

  node_type?: GraphNodeType;

  node_types?: GraphNodeType[];

  edge_types?: GraphEdgeType[];

  depth?: number;

  limit?: number;

  offset?: number;
}