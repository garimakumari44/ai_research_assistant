import { useQuery } from "@tanstack/react-query";

import {
  getPapers,
  getPaper,
  searchPapers,
} from "../papers";

import type { PaperSearchParams } from "../../types/paper";

export const paperQueryKeys = {
  all: ["papers"] as const,

  lists: () =>
    [...paperQueryKeys.all, "list"] as const,

  list: (params?: PaperSearchParams) =>
    [...paperQueryKeys.lists(), params ?? {}] as const,

  details: () =>
    [...paperQueryKeys.all, "detail"] as const,

  detail: (paperId: string) =>
    [...paperQueryKeys.details(), paperId] as const,

  search: (params: PaperSearchParams) =>
    [...paperQueryKeys.all, "search", params] as const,
};

export function usePapers(
  params?: PaperSearchParams
) {
  return useQuery({
    queryKey: paperQueryKeys.list(params),
    queryFn: () => getPapers(params),
  });
}

export function usePaper(
  paperId: string | null | undefined
) {
  return useQuery({
    queryKey: paperQueryKeys.detail(paperId ?? ""),
    queryFn: () => getPaper(paperId!),
    enabled: Boolean(paperId),
  });
}

export function usePaperSearch(
  params: PaperSearchParams
) {
  return useQuery({
    queryKey: paperQueryKeys.search(params),
    queryFn: () => searchPapers(params),
    enabled: Object.values(params).some(
      (value) =>
        value !== undefined &&
        value !== null &&
        String(value).trim() !== ""
    ),
  });
}