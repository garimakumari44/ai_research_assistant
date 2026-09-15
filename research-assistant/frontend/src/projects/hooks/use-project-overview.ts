'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface ProjectOverview {
  id: string;
  name: string;
  description?: string;

  status?: string;

  paperCount: number;
  evidenceCount: number;
  citationCount?: number;

  topicCount?: number;
  methodCount?: number;
  authorCount?: number;

  latestActivity?: string;

  createdAt?: string;
  updatedAt?: string;

  metadata?: Record<string, unknown>;
}

export interface ProjectOverviewResponse {
  project: ProjectOverview;
}

export function useProjectOverview(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'overview'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<ProjectOverviewResponse> => {
      const response = await api.get<ProjectOverviewResponse>(
        `/api/v1/projects/${projectId}/overview`,
      );

      return response.data;
    },

    staleTime: 60_000,
  });
}