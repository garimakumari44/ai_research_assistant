import { apiFetch } from "./api";

import type {
  Chunk,
  ChunkCreate,
  ChunkUpdate,
  ChunkListResponse,
} from "../types/chunk";

/**
 * GET /api/v1/chunks
 */
export async function getChunks(
  sectionId?: string,
  documentId?: string
): Promise<ChunkListResponse> {
  const params = new URLSearchParams();

  if (sectionId) {
    params.set(
      "section_id",
      sectionId
    );
  }

  if (documentId) {
    params.set(
      "document_id",
      documentId
    );
  }

  const query = params.toString();

  return apiFetch<ChunkListResponse>(
    `/chunks${query ? `?${query}` : ""}`
  );
}

/**
 * GET /api/v1/chunks/{chunk_id}
 */
export async function getChunk(
  chunkId: string
): Promise<Chunk> {
  return apiFetch<Chunk>(
    `/chunks/${encodeURIComponent(chunkId)}`
  );
}

/**
 * POST /api/v1/chunks
 */
export async function createChunk(
  data: ChunkCreate
): Promise<Chunk> {
  return apiFetch<Chunk>(
    "/chunks",
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

/**
 * PATCH /api/v1/chunks/{chunk_id}
 */
export async function updateChunk(
  chunkId: string,
  data: ChunkUpdate
): Promise<Chunk> {
  return apiFetch<Chunk>(
    `/chunks/${encodeURIComponent(chunkId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

/**
 * DELETE /api/v1/chunks/{chunk_id}
 */
export async function deleteChunk(
  chunkId: string
): Promise<void> {
  await apiFetch<void>(
    `/chunks/${encodeURIComponent(chunkId)}`,
    {
      method: "DELETE",
    }
  );
}