'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type ContradictionStance =
  | 'support'
  | 'contradict'
  | 'qualify';

export interface ContradictionPaper {
  id: string;
  title: string;
  note: string;
  stance: ContradictionStance;
  paperId?: string;
  evidenceId?: string;
}

export interface ProjectContradiction {
  id: string;
  claim: string;

  supporting: number;
  contradicting: number;
  qualifying: number;

  reasons: string[];

  papers: ContradictionPaper[];

  confidence?: number;

  metadata?: Record<string, unknown>;
}

export interface ProjectContradictionsResponse {
  projectId: string;
  contradictions: ProjectContradiction[];
  total: number;
}

export function useProjectContradictions(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'contradictions'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<ProjectContradictionsResponse> => {
      const response = await api.get<ProjectContradictionsResponse>(
        `/api/v1/projects/${projectId}/contradictions`,
      );

      return response.data;
    },

    staleTime: 60_000,
  });
}