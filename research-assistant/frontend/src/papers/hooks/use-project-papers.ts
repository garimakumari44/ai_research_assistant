'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

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
      const params = new URLSearchParams();

      if (options.query) params.set('q', options.query);
      if (options.year !== undefined) params.set('year', String(options.year));
      if (options.topic) params.set('topic', options.topic);
      if (options.method) params.set('method', options.method);
      if (options.venue) params.set('venue', options.venue);
      if (options.author) params.set('author', options.author);
      if (options.dataset) params.set('dataset', options.dataset);
      if (options.page !== undefined) params.set('page', String(options.page));

      if (options.pageSize !== undefined) {
        params.set('page_size', String(options.pageSize));
      }

      const queryString = params.toString();

      return apiGet<ProjectPapersResponse>(
        `/api/v1/projects/${projectId}/papers${
          queryString ? `?${queryString}` : ''
        }`,
      );
    },

    staleTime: 60_000,
  });
}
