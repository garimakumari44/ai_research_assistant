'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

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
  total: number;
  generatedAt?: string;
}

export function useFrontierGaps(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'frontier', 'gaps'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<FrontierGapsResponse> => {
      const response = await api.get<FrontierGapsResponse>(
        `/api/v1/projects/${projectId}/frontier/gaps`,
      );

      return response.data;
    },

    staleTime: 5 * 60_000,
  });
}