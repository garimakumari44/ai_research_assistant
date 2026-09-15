'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

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
      const response = await api.get<ProjectEvidenceResponse>(
        `/api/v1/projects/${projectId}/evidence`,
        {
          params: {
            category:
              options.category && options.category !== 'all'
                ? options.category
                : undefined,

            limit: options.limit,
            query: options.query,
          },
        },
      );

      return response.data;
    },

    staleTime: 60_000,
  });
}