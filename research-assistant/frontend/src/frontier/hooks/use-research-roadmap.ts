'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

export type RoadmapStepType =
  | 'gap'
  | 'question'
  | 'hypothesis'
  | 'methodology'
  | 'dataset'
  | 'baseline'
  | 'experiment'
  | 'evaluation'
  | 'contribution';

export interface ResearchRoadmapStep {
  id: string;
  label: string;
  type: RoadmapStepType;
  value: string;
  order: number;

  dependencies?: string[];
  status?: 'pending' | 'active' | 'completed';

  metadata?: Record<string, unknown>;
}

export interface ResearchRoadmapResponse {
  projectId: string;
  steps: ResearchRoadmapStep[];
  generatedAt?: string;
}

export function useResearchRoadmap(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'research-roadmap'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<ResearchRoadmapResponse> => {
      const response = await apiGet<ResearchRoadmapResponse>(
        `/api/v1/projects/${projectId}/frontier/roadmap`,
      );

      return response;
    },

    staleTime: 5 * 60_000,
  });
}

