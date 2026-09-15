'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

export interface FrontierGap {
  id: string;
  title: string;
  description: string;

  importance: number;
  novelty: number;
  evidenceCount: number;
  relatedPapers: number;
  confidence: number;

  reasons: string[];

  status?: 'open' | 'active' | 'addressed';

  metadata?: Record<string, unknown>;
}

export interface FrontierGapsResponse {
  projectId: string;
  gaps: FrontierGap[];
  items: FrontierGap[];
  total: number;
  generatedAt?: string;
}

export function useFrontierGaps(projectId: string) {
  return useQuery<FrontierGapsResponse>({
    queryKey: ['projects', projectId, 'frontier', 'gaps'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<FrontierGapsResponse> => {
      const response = await apiGet<
        Omit<FrontierGapsResponse, 'items'> & {
          items?: FrontierGap[];
          gaps?: FrontierGap[];
        }
      >(`/api/v1/projects/${projectId}/frontier/gaps`);

      const items =
        response.items ??
        response.gaps ??
        [];

      return {
        ...response,
        projectId: response.projectId ?? projectId,
        gaps: response.gaps ?? items,
        items,
        total: response.total ?? items.length,
      };
    },

    staleTime: 5 * 60_000,
  });
}