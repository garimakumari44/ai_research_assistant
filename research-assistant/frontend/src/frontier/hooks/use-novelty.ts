"use client";

import { useMutation } from "@tanstack/react-query";

import { getNovelty } from "../api";

import type { NoveltyAnalysis } from "../types";

export const noveltyKeys = {
  all: ["frontier", "novelty"] as const,
};

export function useNovelty() {
  return useMutation<
    NoveltyAnalysis,
    Error,
    {
      query: string;
      topic?: string;
    }
  >({
    mutationFn: getNovelty,
  });
}