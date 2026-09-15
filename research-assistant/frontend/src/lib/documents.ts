
import { apiFetch } from "./api";

import type {
  Document,
  DocumentListResponse,
} from "../types/document";

/* -------------------------------------------------------------------------- */
/* List documents                                                             */
/* -------------------------------------------------------------------------- */

/**
 * GET /api/v1/documents
 */
export async function getDocuments(
  paperId?: string,
): Promise<DocumentListResponse> {
  const params = new URLSearchParams();

  if (paperId) {
    params.set("paper_id", paperId);
  }

  const query = params.toString();

  return apiFetch<DocumentListResponse>(
    `/documents${query ? `?${query}` : ""}`,
    {
      method: "GET",
    },
  );
}

/* -------------------------------------------------------------------------- */
/* Get document                                                               */
/* -------------------------------------------------------------------------- */

/**
 * GET /api/v1/documents/{document_id}
 */
export async function getDocument(
  documentId: string,
): Promise<Document> {
  return apiFetch<Document>(
    `/documents/${encodeURIComponent(documentId)}`,
    {
      method: "GET",
    },
  );
}

/* -------------------------------------------------------------------------- */
/* Upload document                                                            */
/* -------------------------------------------------------------------------- */

/**
 * POST /api/v1/documents
 *
 * Backend expects:
 *
 * multipart/form-data
 *   file: UploadFile
 */
export async function uploadDocument(
  file: File,
): Promise<Document> {
  const formData = new FormData();

  formData.append("file", file);

  return apiFetch<Document>(
    "/documents",
    {
      method: "POST",
      body: formData,
    },
  );
}

/* -------------------------------------------------------------------------- */
/* Delete document                                                            */
/* -------------------------------------------------------------------------- */

/**
 * DELETE /api/v1/documents/{document_id}
 */
export async function deleteDocument(
  documentId: string,
): Promise<void> {
  await apiFetch<void>(
    `/documents/${encodeURIComponent(documentId)}`,
    {
      method: "DELETE",
    },
  );
}

