import { apiFetch } from "./api";

import type { Document } from "../types/document";

export interface IngestionResponse {
  document_id?: string | null;
  paper_id?: string | null;
  status: string;
  message?: string | null;
  document?: Document | null;
}

export interface IngestionStatus {
  id: string;
  status: string;
  progress?: number | null;
  message?: string | null;
  error?: string | null;
}

/**
 * Start document ingestion.
 *
 * POST /api/v1/ingestion/documents
 */
export async function ingestDocument(
  documentId: string
): Promise<IngestionResponse> {
  return apiFetch<IngestionResponse>(
    "/ingestion/documents",
    {
      method: "POST",
      body: JSON.stringify({
        document_id: documentId,
      }),
    }
  );
}

/**
 * Get ingestion status.
 *
 * GET /api/v1/ingestion/{ingestion_id}
 */
export async function getIngestionStatus(
  ingestionId: string
): Promise<IngestionStatus> {
  return apiFetch<IngestionStatus>(
    `/ingestion/${encodeURIComponent(
      ingestionId
    )}`
  );
}

/**
 * Cancel ingestion.
 *
 * POST /api/v1/ingestion/{ingestion_id}/cancel
 */
export async function cancelIngestion(
  ingestionId: string
): Promise<void> {
  await apiFetch<void>(
    `/ingestion/${encodeURIComponent(
      ingestionId
    )}/cancel`,
    {
      method: "POST",
    }
  );
}