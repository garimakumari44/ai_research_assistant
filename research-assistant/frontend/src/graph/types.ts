/**
 * Canonical graph domain types.
 *
 * These types are shared by the API, graph hooks, and graph UI.
 * React Flow-specific fields are optional so the domain model remains
 * independent from React Flow while still supporting visualization.
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
  | "unknown"
  | string;

export interface GraphNode {
  id: string;
  type: GraphNodeType;
  label: string;

  /**
   * Optional display/source name used by some graph views.
   */
  name?: string;

  description?: string | null;

  /**
   * Optional graph-layout fields.
   */
  position?: {
    x: number;
    y: number;
  };

  x?: number;
  y?: number;
  size?: number;
  connections?: number;
  relevance?: number;

  selected?: boolean;

  properties?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;

  source: string;
  target: string;

  /**
   * Some API responses expose source/target under from/to.
   */
  from?: string;
  to?: string;

  type: GraphEdgeType;

  label?: string | null;

  strength?: number;
  animated?: boolean;

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

export interface GraphQuery {
  query?: string;
  node_types?: GraphNodeType[];
  edge_types?: GraphEdgeType[];
  paper_id?: number;
  document_id?: number;
  limit?: number;
  offset?: number;
}

export interface GraphRequest {
  node_id?: string;
  node_type?: GraphNodeType;
  query?: string;
  node_types?: GraphNodeType[];
  edge_types?: GraphEdgeType[];
  depth?: number;
  limit?: number;
}

export interface GraphTraversalRequest {
  node_id: string;
  depth?: number;
  direction?: "outgoing" | "incoming" | "both";
  edge_types?: GraphEdgeType[];
  node_types?: GraphNodeType[];
  limit?: number;
}

export interface GraphParams {
  query?: string;
  node_type?: GraphNodeType;
  node_types?: GraphNodeType[];
  edge_types?: GraphEdgeType[];
  depth?: number;
  limit?: number;
  offset?: number;
}
