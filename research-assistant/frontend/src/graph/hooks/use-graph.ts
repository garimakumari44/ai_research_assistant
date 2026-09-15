'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

export type GraphNodeType =
  | 'paper'
  | 'topic'
  | 'method'
  | 'author'
  | 'dataset';

export type GraphEdgeType = string;

export interface ProjectGraphNode {
  id: string;
  type: GraphNodeType;
  label: string;

  x?: number;
  y?: number;
  size?: number;
  connections?: number;

  metadata?: Record<string, unknown>;
  relevance?: number;
}

export interface ProjectGraphEdge {
  id?: string;

  /**
   * ReactFlow-style source/target.
   */
  source: string;
  target: string;

  strength?: number;
  type?: GraphEdgeType;

  metadata?: Record<string, unknown>;
}

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

export interface UseGraphOptions {
  depth?: number;
  node_type?: GraphNodeType;
  edge_type?: GraphEdgeType;
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
      'graph',
      depth,
      node_type ?? null,
      edge_type ?? null,
      search?.trim() || null,
    ],

    enabled,

    queryFn: async () => {
      const params = new URLSearchParams();

      params.set('depth', String(depth));

      if (node_type) {
        params.set('node_type', node_type);
      }

      if (edge_type) {
        params.set('edge_type', edge_type);
      }

      const normalizedSearch = search?.trim();

      if (normalizedSearch) {
        params.set('search', normalizedSearch);
      }

      const queryString = params.toString();

      const response = await apiGet<ProjectGraphResponse>(
        `/graph?${queryString}`,
      );

      return response;
    },

    staleTime: 60_000,

    placeholderData: (previousData) => previousData,
  });
}

