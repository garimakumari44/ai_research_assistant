import { apiFetch } from "./api";

import type {
  Section,
  SectionCreate,
  SectionUpdate,
  SectionListResponse,
} from "../types/section";

/**
 * GET /api/v1/sections
 */
export async function getSections(
  documentId?: string
): Promise<SectionListResponse> {
  const params = new URLSearchParams();

  if (documentId) {
    params.set(
      "document_id",
      documentId
    );
  }

  const query = params.toString();

  return apiFetch<SectionListResponse>(
    `/sections${query ? `?${query}` : ""}`
  );
}

/**
 * GET /api/v1/sections/{section_id}
 */
export async function getSection(
  sectionId: string
): Promise<Section> {
  return apiFetch<Section>(
    `/sections/${encodeURIComponent(sectionId)}`
  );
}

/**
 * POST /api/v1/sections
 */
export async function createSection(
  data: SectionCreate
): Promise<Section> {
  return apiFetch<Section>(
    "/sections",
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}

/**
 * PATCH /api/v1/sections/{section_id}
 */
export async function updateSection(
  sectionId: string,
  data: SectionUpdate
): Promise<Section> {
  return apiFetch<Section>(
    `/sections/${encodeURIComponent(sectionId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}

/**
 * DELETE /api/v1/sections/{section_id}
 */
export async function deleteSection(
  sectionId: string
): Promise<void> {
  await apiFetch<void>(
    `/sections/${encodeURIComponent(sectionId)}`,
    {
      method: "DELETE",
    }
  );
}