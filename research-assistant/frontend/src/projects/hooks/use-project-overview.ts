'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

export type ProjectStatus =
  | 'pending'
  | 'done'
  | 'active'
  | 'paused'
  | 'archived'
  | string;

export interface ProjectOverview {
  id: string;
  name: string;
  title?: string;
  question?: string;
  researchQuestion?: string;

  description?: string | null;
  status?: ProjectStatus;

  paperCount: number;
  evidenceCount: number;
  gapCount: number;
  hypothesisCount: number;
  citationCount?: number;

  topicCount?: number;
  methodCount?: number;
  authorCount?: number;

  currentFrontier?: unknown;
  latestActivity?: string;

  createdAt?: string;
  updatedAt?: string;

  metadata?: Record<string, unknown>;
}

export interface ProjectOverviewResponse extends ProjectOverview {
  project?: ProjectOverview;
}

interface WrappedProjectOverviewResponse {
  project: ProjectOverview;
}

function isWrappedResponse(
  response: ProjectOverviewResponse | WrappedProjectOverviewResponse,
): response is WrappedProjectOverviewResponse {
  return (
    'project' in response &&
    response.project !== undefined
  );
}

export function useProjectOverview(projectId: string) {
  return useQuery<ProjectOverviewResponse>({
    queryKey: ['projects', projectId, 'overview'],
    enabled: Boolean(projectId),

    queryFn: async (): Promise<ProjectOverviewResponse> => {
      const response = await apiGet<
        ProjectOverviewResponse | WrappedProjectOverviewResponse
      >(`/api/v1/projects/${projectId}/overview`);

      if (isWrappedResponse(response)) {
        return {
          ...response.project,
          project: response.project,
        };
      }

      return response;
    },

    staleTime: 60_000,
  });
}