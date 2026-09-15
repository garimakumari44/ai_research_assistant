import { useQuery } from "@tanstack/react-query";

import {
  getChunks,
  getChunk,
} from "../chunks";

export const chunkQueryKeys = {
  all: ["chunks"] as const,

  lists: () =>
    [...chunkQueryKeys.all, "list"] as const,

  bySection: (sectionId: string) =>
    [
      ...chunkQueryKeys.lists(),
      "section",
      sectionId,
    ] as const,

  byDocument: (documentId: string) =>
    [
      ...chunkQueryKeys.lists(),
      "document",
      documentId,
    ] as const,

  detail: (chunkId: string) =>
    [
      ...chunkQueryKeys.all,
      "detail",
      chunkId,
    ] as const,
};

export function useChunks(
  sectionId: string | null | undefined
) {
  return useQuery({
    queryKey: chunkQueryKeys.bySection(
      sectionId ?? ""
    ),

    queryFn: () => getChunks(sectionId!),

    enabled: Boolean(sectionId),
  });
}

export function useDocumentChunks(
  documentId: string | null | undefined
) {
  return useQuery({
    queryKey: chunkQueryKeys.byDocument(
      documentId ?? ""
    ),

    queryFn: () =>
      getChunks(undefined, documentId!),

    enabled: Boolean(documentId),
  });
}

export function useChunk(
  chunkId: string | null | undefined
) {
  return useQuery({
    queryKey: chunkQueryKeys.detail(
      chunkId ?? ""
    ),

    queryFn: () => getChunk(chunkId!),

    enabled: Boolean(chunkId),
  });
}