import {
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
} from "@/lib/api";

import type {
  AddCollectionItemRequest,
  Collection,
  CollectionItem,
  CollectionItemListParams,
  CollectionItemsResponse,
  CollectionListParams,
  CollectionListResponse,
  CreateCollectionRequest,
  RemoveCollectionItemRequest,
  UpdateCollectionRequest,
} from "./types";

/* -------------------------------------------------------------------------- */
/* Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function buildQuery(
  params: Record<
    string,
    string | number | boolean | undefined
  >,
): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(
    ([key, value]) => {
      if (value === undefined) {
        return;
      }

      searchParams.set(
        key,
        String(value),
      );
    },
  );

  const query = searchParams.toString();

  return query ? `?${query}` : "";
}

/**
 * Normalize collection ID.
 *
 * Collection IDs are currently numeric in the backend,
 * but keeping this string-safe makes the API layer robust.
 */
function normalizeCollectionId(
  collectionId: number | string,
): string {
  const id = String(collectionId).trim();

  if (!id) {
    throw new Error(
      "Collection ID is required.",
    );
  }

  return encodeURIComponent(id);
}

/**
 * Normalize paper ID.
 */
function normalizePaperId(
  paperId: number | string,
): string {
  const id = String(paperId).trim();

  if (!id) {
    throw new Error(
      "Paper ID is required.",
    );
  }

  return encodeURIComponent(id);
}

/* -------------------------------------------------------------------------- */
/* Collections                                                                */
/* -------------------------------------------------------------------------- */

/**
 * GET /api/v1/collections
 */
export async function getCollections(
  params: CollectionListParams = {},
): Promise<CollectionListResponse> {
  const query = buildQuery({
    page: params.page,
    page_size: params.page_size,
    search: params.search,
    archived: params.archived,
  });

  return apiGet<CollectionListResponse>(
    `/collections${query}`,
  );
}

/**
 * GET /api/v1/collections/{collection_id}
 *
 * Backend returns:
 *
 * {
 *   id,
 *   user_id,
 *   name,
 *   description,
 *   archived,
 *   created_at,
 *   updated_at,
 *   paper_count,
 *   items: [...]
 * }
 */
export async function getCollection(
  collectionId: number | string,
): Promise<Collection> {
  const id = normalizeCollectionId(
    collectionId,
  );

  return apiGet<Collection>(
    `/collections/${id}`,
  );
}

/**
 * POST /api/v1/collections
 */
export async function createCollection(
  payload: CreateCollectionRequest,
): Promise<Collection> {
  return apiPost<Collection>(
    "/collections",
    payload,
  );
}

/**
 * PATCH /api/v1/collections/{collection_id}
 */
export async function updateCollection(
  collectionId: number | string,
  payload: UpdateCollectionRequest,
): Promise<Collection> {
  const id = normalizeCollectionId(
    collectionId,
  );

  return apiPatch<Collection>(
    `/collections/${id}`,
    payload,
  );
}

/**
 * DELETE /api/v1/collections/{collection_id}
 */
export async function deleteCollection(
  collectionId: number | string,
): Promise<void> {
  const id = normalizeCollectionId(
    collectionId,
  );

  await apiDelete<void>(
    `/collections/${id}`,
  );
}

/* -------------------------------------------------------------------------- */
/* Collection Items                                                           */
/* -------------------------------------------------------------------------- */

/**
 * GET /api/v1/collections/{collection_id}/items
 */
export async function getCollectionItems(
  collectionId: number | string,
  params: CollectionItemListParams = {},
): Promise<CollectionItemsResponse> {
  const id = normalizeCollectionId(
    collectionId,
  );

  const query = buildQuery({
    page: params.page,
    page_size: params.page_size,
  });

  return apiGet<CollectionItemsResponse>(
    `/collections/${id}/items${query}`,
  );
}

/**
 * POST /api/v1/collections/{collection_id}/items
 */
export async function addCollectionItem(
  collectionId: number | string,
  payload: AddCollectionItemRequest,
): Promise<CollectionItem> {
  const id = normalizeCollectionId(
    collectionId,
  );

  return apiPost<CollectionItem>(
    `/collections/${id}/items`,
    payload,
  );
}

/**
 * DELETE /api/v1/collections/{collection_id}/items/{paper_id}
 */
export async function removeCollectionItem(
  collectionId: number | string,
  payload: RemoveCollectionItemRequest,
): Promise<void> {
  const collectionIdValue =
    normalizeCollectionId(
      collectionId,
    );

  const paperId = normalizePaperId(
    payload.paper_id,
  );

  await apiDelete<void>(
    `/collections/${collectionIdValue}/items/${paperId}`,
  );
}