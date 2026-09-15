"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";

import type {
  GraphEdge,
  GraphNode,
  GraphNodeType,
} from "@/graph/types";

export type { GraphNodeType };

export type ProjectGraphNode = GraphNode;
export type ProjectGraphEdge = GraphEdge;

export interface ProjectGraphMetadata {
  generated_at?: string;
  [key: string]: unknown;
}

export interface ProjectGraphResponse {
  nodes: ProjectGraphNode[];
  edges: ProjectGraphEdge[];

  total_nodes?: number;
  total_edges?: number;

  metadata?: ProjectGraphMetadata;
}

export const graphKeys = {
  all: ["graph"] as const,
  node: (id: string) => ["graph", "node", id] as const,
  traversal: (id: string, depth: number) =>
    ["graph", "traversal", id, depth] as const,
};

export interface UseGraphOptions {
  depth?: number;
  node_type?: GraphNodeType;
  edge_type?: string;
  search?: string;
  enabled?: boolean;
}

export function useGraph(options: UseGraphOptions = {}) {
  const {
    depth = 2,
    node_type,
    edge_type,
    search,
    enabled = true,
  } = options;

  return useQuery<ProjectGraphResponse>({
    queryKey: [
      "graph",
      depth,
      node_type ?? null,
      edge_type ?? null,
      search?.trim() || null,
    ],

    enabled,

    queryFn: async () => {
      const params = new URLSearchParams();

      params.set("depth", String(depth));

      if (node_type) {
        params.set("node_type", node_type);
      }

      if (edge_type) {
        params.set("edge_type", edge_type);
      }

      const normalizedSearch = search?.trim();

      if (normalizedSearch) {
        params.set("search", normalizedSearch);
      }

      const response = await apiGet<ProjectGraphResponse>(
        `/graph?${params.toString()}`,
      );

      return response;
    },

    staleTime: 60_000,

    placeholderData: (previousData) => previousData,
  });
}