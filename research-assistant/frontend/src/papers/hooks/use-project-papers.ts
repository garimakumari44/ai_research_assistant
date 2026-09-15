'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface ProjectPaper {
  id: string;
  title: string;

  authors: string[];

  venue?: string;
  year?: number;

  abstract?: string;

  tags: string[];

  citations?: number;

  doi?: string;
  arxivId?: string;

  metadata?: Record<string, unknown>;
}

export interface ProjectPapersResponse {
  projectId: string;
  papers: ProjectPaper[];
  total: number;
  page?: number;
  pageSize?: number;
}

export interface UseProjectPapersOptions {
  query?: string;
  year?: number;
  topic?: string;
  method?: string;
  venue?: string;
  author?: string;
  dataset?: string;

  page?: number;
  pageSize?: number;
}

export function useProjectPapers(
  projectId: string,
  options: UseProjectPapersOptions = {},
) {
  return useQuery({
    queryKey: [
      'projects',
      projectId,
      'papers',
      options,
    ],

    enabled: Boolean(projectId),

    queryFn: async (): Promise<ProjectPapersResponse> => {
      const response = await api.get<ProjectPapersResponse>(
        `/api/v1/projects/${projectId}/papers`,
        {
          params: {
            q: options.query,
            year: options.year,
            topic: options.topic,
            method: options.method,
            venue: options.venue,
            author: options.author,
            dataset: options.dataset,
            page: options.page,
            page_size: options.pageSize,
          },
        },
      );

      return response.data;
    },

    staleTime: 60_000,
  });
}