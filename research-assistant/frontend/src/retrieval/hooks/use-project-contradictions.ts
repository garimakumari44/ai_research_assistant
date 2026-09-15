'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

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
  items: ProjectContradiction[];
  total: number;
}

export function useProjectContradictions(projectId: string) {
  return useQuery<ProjectContradictionsResponse>({
    queryKey: ['projects', projectId, 'contradictions'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<ProjectContradictionsResponse> => {
      const response = await apiGet<
        Omit<ProjectContradictionsResponse, 'items'> & {
          items?: ProjectContradiction[];
          contradictions?: ProjectContradiction[];
        }
      >(`/api/v1/projects/${projectId}/contradictions`);

      const items =
        response.items ??
        response.contradictions ??
        [];

      return {
        ...response,
        projectId: response.projectId ?? projectId,
        contradictions:
          response.contradictions ?? items,
        items,
        total: response.total ?? items.length,
      };
    },

    staleTime: 60_000,
  });
}