'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface FrontierItem {
  id: string;
  name: string;
  momentum: number;
  convergence: number;
  novelty: number;
  confidence: number;
  supportingEvidence: number;
  counterSignals: number;
  relevantPapers: number;
  forecast: string;
  reasons: string[];
  metadata?: Record<string, unknown>;
}

export interface FrontierResponse {
  projectId: string;
  items: FrontierItem[];
  generatedAt?: string;
}

export function useFrontier(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'frontier'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<FrontierResponse> => {
      const response = await api.get<FrontierResponse>(
        `/api/v1/projects/${projectId}/frontier`,
      );

      return response.data;
    },

    staleTime: 5 * 60_000,
  });
}