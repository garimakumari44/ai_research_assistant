"use client";

import { useQuery } from "@tanstack/react-query";

import { getTrends } from "../api";

import type { Trend } from "../types";

export const trendKeys = {
  all: ["frontier", "trends"] as const,

  list: (params?: {
    topic?: string;
    limit?: number;
    period?: string;
  }) => [...trendKeys.all, params] as const,
};

export function useTrends(
  params?: {
    topic?: string;
    limit?: number;
    period?: string;
  },
) {
  return useQuery<Trend[]>({
    queryKey: trendKeys.list(params),
    queryFn: () => getTrends(params),
    staleTime: 5 * 60 * 1000,
  });
}