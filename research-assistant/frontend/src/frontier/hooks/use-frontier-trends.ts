'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface FrontierTrendPoint {
  period: string;
  value: number;
}

export interface FrontierTrendSeries {
  id: string;
  label: string;
  color?: string;
  data: FrontierTrendPoint[];
}

export interface FrontierTrendsResponse {
  publicationGrowth: FrontierTrendSeries[];
  topicGrowth: FrontierTrendSeries[];
  methodAdoption: {
    method: string;
    adoption: number;
    papers: number;
  }[];
  crossDomainConnections: {
    a: string;
    b: string;
    count: number;
  }[];
}

export interface UseFrontierTrendsOptions {
  range?: '1Y' | '3Y' | '5Y' | '10Y' | 'All';
}

export function useFrontierTrends(
  projectId: string,
  options: UseFrontierTrendsOptions = {},
) {
  return useQuery({
    queryKey: [
      'projects',
      projectId,
      'frontier',
      'trends',
      options.range ?? 'All',
    ],

    enabled: Boolean(projectId),

    queryFn: async (): Promise<FrontierTrendsResponse> => {
      const response = await api.get<FrontierTrendsResponse>(
        `/api/v1/projects/${projectId}/frontier/trends`,
        {
          params: {
            range: options.range ?? 'All',
          },
        },
      );

      return response.data;
    },

    staleTime: 5 * 60_000,
  });
}