'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

export type EvidenceTrustCategory =
  | 'evidence'
  | 'inference'
  | 'forecast'
  | 'hypothesis';

export interface ProjectEvidence {
  id: string;
  quote: string;
  paperId?: string;
  paperTitle: string;
  section?: string;
  page?: number;
  category?: string;
  trustCategory: EvidenceTrustCategory;
  relevance: number;
  confidence?: number;
  chunkId?: string;
  documentId?: string;

  provenance?: {
    source?: string;
    retrievalMethod?: string;
    score?: number;
  };

  metadata?: Record<string, unknown>;
}

export interface ProjectEvidenceResponse {
  projectId: string;
  evidence: ProjectEvidence[];
  total: number;
}

export interface UseProjectEvidenceOptions {
  category?: EvidenceTrustCategory | 'all';
  limit?: number;
  query?: string;
}

export function useProjectEvidence(
  projectId: string,
  options: UseProjectEvidenceOptions = {},
) {
  return useQuery({
    queryKey: [
      'projects',
      projectId,
      'evidence',
      options,
    ],

    enabled: Boolean(projectId),

    queryFn: async (): Promise<ProjectEvidenceResponse> => {
      const params = new URLSearchParams();

      if (options.category && options.category !== 'all') {
        params.set('category', options.category);
      }

      if (options.limit !== undefined) {
        params.set('limit', String(options.limit));
      }

      if (options.query) {
        params.set('query', options.query);
      }

      const queryString = params.toString();

      return apiGet<ProjectEvidenceResponse>(
        `/api/v1/projects/${projectId}/evidence${
          queryString ? `?${queryString}` : ''
        }`,
      );
    },

    staleTime: 60_000,
  });
}
