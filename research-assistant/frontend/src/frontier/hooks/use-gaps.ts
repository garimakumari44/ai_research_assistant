"use client";

import { useQuery } from "@tanstack/react-query";

import { getGaps } from "../api";

import type { Gap } from "../types";

export const gapKeys = {
  all: ["frontier", "gaps"] as const,

  list: (params?: {
    topic?: string;
    limit?: number;
    minConfidence?: number;
  }) => [...gapKeys.all, params] as const,
};

export function useGaps(
  params?: {
    topic?: string;
    limit?: number;
    minConfidence?: number;
  },
) {
  return useQuery<Gap[]>({
    queryKey: gapKeys.list(params),
    queryFn: () => getGaps(params),
    staleTime: 5 * 60 * 1000,
  });
}