/**
 * Collection domain types.
 *
 * These types mirror the FastAPI collections API.
 */

/* -------------------------------------------------------------------------- */
/* Collection Paper                                                           */
/* -------------------------------------------------------------------------- */

/**
 * Minimal author returned inside a collection paper.
 */
export interface CollectionPaperAuthor {
  id: number;
  full_name: string;
}

/**
 * Minimal venue returned inside a collection paper.
 */
export interface CollectionPaperVenue {
  id: number;
  name: string;
}

/**
 * Minimal topic returned inside a collection paper.
 */
export interface CollectionPaperTopic {
  id: number;
  name: string;
}

/**
 * Lightweight paper representation returned with collection items.
 */
export interface CollectionPaperSummary {
  id: number;
  title: string;
  year: number | null;

  citation_count: number;
  reference_count: number;

  venue: CollectionPaperVenue | null;

  authors: CollectionPaperAuthor[];

  topics: CollectionPaperTopic[];
}

/* -------------------------------------------------------------------------- */
/* Collection Item                                                            */
/* -------------------------------------------------------------------------- */

/**
 * A paper belonging to a collection.
 */
export interface CollectionItem {
  /**
   * Unique collection-item identifier.
   */
  id: number;

  /**
   * Parent collection identifier.
   */
  collection_id: number;

  /**
   * Underlying research paper identifier.
   */
  paper_id: number;

  /**
   * ISO timestamp.
   */
  created_at: string;

  /**
   * Lightweight paper data returned by the backend.
   */
  paper: CollectionPaperSummary | null;
}

/* -------------------------------------------------------------------------- */
/* Collection                                                                 */
/* -------------------------------------------------------------------------- */

/**
 * A research paper collection.
 *
 * Backend CollectionResponse includes the collection's items.
 */
export interface Collection {
  /**
   * Unique collection identifier.
   */
  id: number;

  /**
   * User who owns the collection.
   */
  user_id: number;

  /**
   * Collection name.
   */
  name: string;

  /**
   * Optional collection description.
   */
  description: string | null;

  /**
   * Whether the collection has been archived.
   */
  archived: boolean;

  /**
   * Number of papers/items in the collection.
   */
  paper_count: number;

  /**
   * Collection items returned by the detail endpoint.
   *
   * GET /collections/{collection_id}
   */
  items: CollectionItem[];

  /**
   * ISO timestamp.
   */
  created_at: string;

  /**
   * ISO timestamp.
   */
  updated_at: string;
}

/* -------------------------------------------------------------------------- */
/* Collection List                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Parameters used when requesting collections.
 */
export interface CollectionListParams {
  page?: number;
  page_size?: number;
  search?: string;
  archived?: boolean;
}

/**
 * Paginated collection response.
 */
export interface CollectionListResponse {
  items: Collection[];

  page: number;

  page_size: number;

  total: number;

  pages: number;
}

/* -------------------------------------------------------------------------- */
/* Single Collection Responses                                                */
/* -------------------------------------------------------------------------- */

/**
 * The backend returns a Collection directly.
 */
export type CollectionResponse = Collection;

/**
 * Collection mutation endpoints return a Collection directly
 * unless otherwise specified by the backend.
 */
export type CollectionMutationResponse = Collection;

/* -------------------------------------------------------------------------- */
/* Collection Items List                                                      */
/* -------------------------------------------------------------------------- */

/**
 * Parameters used when requesting collection items.
 */
export interface CollectionItemListParams {
  page?: number;
  page_size?: number;
}

/**
 * Paginated collection-item response.
 */
export interface CollectionItemsResponse {
  items: CollectionItem[];

  page: number;

  page_size: number;

  total: number;

  pages: number;
}

/* -------------------------------------------------------------------------- */
/* Collection Creation                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Request body for creating a collection.
 */
export interface CreateCollectionRequest {
  name: string;
  description?: string | null;
  archived?: boolean;
}

/**
 * Alias retained for compatibility.
 */
export type CollectionCreate = CreateCollectionRequest;

/* -------------------------------------------------------------------------- */
/* Collection Update                                                          */
/* -------------------------------------------------------------------------- */

/**
 * Request body for updating a collection.
 */
export interface UpdateCollectionRequest {
  name?: string;
  description?: string | null;
  archived?: boolean;
}

/* -------------------------------------------------------------------------- */
/* Collection Item Mutations                                                  */
/* -------------------------------------------------------------------------- */

/**
 * Request body for adding a paper to a collection.
 */
export interface AddCollectionItemRequest {
  paper_id: number;
}

/**
 * Request body used when removing a paper from a collection.
 */
export interface RemoveCollectionItemRequest {
  paper_id: number;
}

/**
 * POST collection-item endpoint returns the item directly.
 */
export type CollectionItemMutationResponse = CollectionItem;