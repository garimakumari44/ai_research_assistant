/**
 * Graph domain types.
 *
 * Represents the research knowledge graph:
 * papers, authors, topics, methods, datasets, citations,
 * concepts, and relationships between them.
 */

export type GraphNodeType =
  | "paper"
  | "author"
  | "topic"
  | "method"
  | "dataset"
  | "venue"
  | "organization"
  | "concept"
  | "claim"
  | "document"
  | "chunk";

export type GraphEdgeType =
  | "cites"
  | "cited_by"
  | "authored_by"
  | "co_authored_with"
  | "published_in"
  | "belongs_to"
  | "uses_method"
  | "uses_dataset"
  | "related_to"
  | "supports"
  | "contradicts"
  | "derived_from"
  | "similar_to"
  | "extends"
  | "improves"
  | "implements";

export interface GraphNode {
  id: string;
  type: GraphNodeType;

  label: string;
  title?: string | null;
  description?: string | null;

  metadata?: Record<string, unknown>;

  score?: number | null;
  relevance_score?: number | null;

  x?: number;
  y?: number;

  created_at?: string | null;
  updated_at?: string | null;
}

export interface GraphEdge {
  id: string;

  source: string;
  target: string;

  type: GraphEdgeType;

  label?: string | null;

  weight?: number | null;
  score?: number | null;

  metadata?: Record<string, unknown>;

  created_at?: string | null;
}

export interface Graph {
  id?: string | null;

  nodes: GraphNode[];
  edges: GraphEdge[];

  node_count?: number;
  edge_count?: number;

  metadata?: Record<string, unknown>;
}

export interface GraphNodeDetail extends GraphNode {
  incoming_edges?: GraphEdge[];
  outgoing_edges?: GraphEdge[];

  neighbors?: GraphNode[];

  properties?: Record<string, unknown>;
}

export interface GraphTraversalRequest {
  node_id: string;

  depth?: number;

  edge_types?: GraphEdgeType[];

  node_types?: GraphNodeType[];

  limit?: number;
}

export interface GraphTraversalResponse {
  root_node: GraphNode;

  nodes: GraphNode[];
  edges: GraphEdge[];

  depth: number;

  node_count?: number;
  edge_count?: number;
}

export interface GraphQuery {
  query: string;

  node_types?: GraphNodeType[];
  edge_types?: GraphEdgeType[];

  limit?: number;
  depth?: number;
}

export interface GraphResponse {
  graph: Graph;

  query?: string | null;

  execution_time_ms?: number | null;
}