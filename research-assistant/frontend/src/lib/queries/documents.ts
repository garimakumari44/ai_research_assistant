import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getDocuments,
  getDocument,
  uploadDocument,
  deleteDocument,
} from "../documents";

export const documentQueryKeys = {
  all: ["documents"] as const,

  lists: () =>
    [...documentQueryKeys.all, "list"] as const,

  byPaper: (paperId: string) =>
    [...documentQueryKeys.lists(), "paper", paperId] as const,

  detail: (documentId: string) =>
    [...documentQueryKeys.all, "detail", documentId] as const,
};

export function useDocuments(
  paperId: string | null | undefined
) {
  return useQuery({
    queryKey: documentQueryKeys.byPaper(paperId ?? ""),
    queryFn: () => getDocuments(paperId!),
    enabled: Boolean(paperId),
    select: (response) => response.items,
  });
}

export function useDocument(
  documentId: string | null | undefined
) {
  return useQuery({
    queryKey: documentQueryKeys.detail(documentId ?? ""),
    queryFn: () => getDocument(documentId!),
    enabled: Boolean(documentId),
  });
}

export interface UploadDocumentVariables {
  file: File;
  paperId?: string;
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      paperId,
    }: UploadDocumentVariables) =>
      uploadDocument(file, paperId),

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: documentQueryKeys.all,
      });

      if (variables.paperId) {
        queryClient.invalidateQueries({
          queryKey: documentQueryKeys.byPaper(
            variables.paperId
          ),
        });
      }
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: documentQueryKeys.all,
      });
    },
  });
}