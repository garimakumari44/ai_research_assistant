'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';

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
      const params = new URLSearchParams();
      params.set('range', options.range ?? 'All');

      return apiGet<FrontierTrendsResponse>(
        `/api/v1/projects/${projectId}/frontier/trends?${params.toString()}`,
      );
    },

    staleTime: 5 * 60_000,
  });
}
