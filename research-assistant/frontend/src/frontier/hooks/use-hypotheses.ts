'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

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
  items: ProjectHypothesis[];
  total: number;
}

export function useHypotheses(projectId: string) {
  return useQuery<HypothesesResponse>({
    queryKey: ['projects', projectId, 'hypotheses'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<HypothesesResponse> => {
      const response = await apiGet<
        Omit<HypothesesResponse, 'items'> & {
          items?: ProjectHypothesis[];
          hypotheses?: ProjectHypothesis[];
        }
      >(`/api/v1/projects/${projectId}/frontier/hypotheses`);

      const items =
        response.items ??
        response.hypotheses ??
        [];

      return {
        ...response,
        projectId: response.projectId ?? projectId,
        hypotheses:
          response.hypotheses ?? items,
        items,
        total: response.total ?? items.length,
      };
    },

    staleTime: 5 * 60_000,
  });
}