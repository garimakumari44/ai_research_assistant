'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type HypothesisStatus =
  | 'draft'
  | 'testing'
  | 'validated'
  | 'rejected';

export interface ProjectHypothesis {
  id: string;
  statement: string;
  status: HypothesisStatus;

  evidence: string;
  gap: string;
  whyItMatters: string;
  potentialContribution: string;

  method: string;
  dataset: string;
  baseline: string;

  metrics: string[];

  supportingEvidence?: number;
  counterEvidence?: number;

  confidence?: number;

  metadata?: Record<string, unknown>;
}

export interface HypothesesResponse {
  projectId: string;
  hypotheses: ProjectHypothesis[];
  total: number;
}

export function useHypotheses(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'hypotheses'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<HypothesesResponse> => {
      const response = await api.get<HypothesesResponse>(
        `/api/v1/projects/${projectId}/frontier/hypotheses`,
      );

      return response.data;
    },

    staleTime: 5 * 60_000,
  });
}