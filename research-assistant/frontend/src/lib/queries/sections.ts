import { useQuery } from "@tanstack/react-query";

import {
  getSections,
  getSection,
} from "../sections";

export const sectionQueryKeys = {
  all: ["sections"] as const,

  lists: () =>
    [...sectionQueryKeys.all, "list"] as const,

  byDocument: (documentId: string) =>
    [
      ...sectionQueryKeys.lists(),
      "document",
      documentId,
    ] as const,

  detail: (sectionId: string) =>
    [
      ...sectionQueryKeys.all,
      "detail",
      sectionId,
    ] as const,
};

export function useSections(
  documentId: string | null | undefined
) {
  return useQuery({
    queryKey: sectionQueryKeys.byDocument(
      documentId ?? ""
    ),

    queryFn: () => getSections(documentId!),

    enabled: Boolean(documentId),
  });
}

export function useSection(
  sectionId: string | null | undefined
) {
  return useQuery({
    queryKey: sectionQueryKeys.detail(
      sectionId ?? ""
    ),

    queryFn: () => getSection(sectionId!),

    enabled: Boolean(sectionId),
  });
}